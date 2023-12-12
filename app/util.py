"""web的一些注入解析等小功能"""
import logging
import os.path
from datetime import datetime
from functools import wraps
from typing import Any, Optional
from flask.json.provider import DefaultJSONProvider
from flask_jwt_extended import verify_jwt_in_request
from flask_jwt_extended.view_decorators import LocationType
from pydantic import BaseModel

from util.config import dev
from util.database import build_model
from flask import request, jsonify, current_app

log = logging.getLogger(__name__)

_static_folder = os.path.realpath(os.path.join(os.path.dirname(__file__), os.pardir, 'static'))
user_picture_folder = os.path.join(_static_folder, 'user_picture')
flag_picture_folder = os.path.join(_static_folder, 'flag_picture')


def custom_jwt(
    optional: bool = False,
    fresh: bool = False,
    refresh: bool = False,
    locations: Optional[LocationType] = None,
    verify_type: bool = True,
    skip_revocation_check: bool = False,
) -> Any:
    """重写jwt_required，dev环境下不开启dev"""
    if optional is None:
        optional = dev

    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request(
                optional, fresh, refresh, locations, verify_type, skip_revocation_check
            )
            return current_app.ensure_sync(fn)(*args, **kwargs)
        return decorator
    return wrapper


def resp(msg: str, code: int = 0, **kwargs):
    return jsonify({'msg': msg, 'code': code, **kwargs})


def parse(model):
    return build_model(model, None, request.json)


def args_parse(model):
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            param = build_model(model, None, request.json)
            return fn(param, *args, **kwargs)
            # return current_app.ensure_sync(fn)(param, *args, **kwargs)
        return decorator
    return wrapper


class JSONProvider(DefaultJSONProvider):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')

        return super().default(obj)


class Model(BaseModel):
    def __init__(self, *args, **kwargs):
        cls = type(self)
        base_cls = cls if cls.__base__ is Model else cls.__bases__[-1]
        kw = {k: None for k in base_cls.__annotations__}
        kw.update(kwargs)
        [kw.pop(i) for i in args if kw[i] is None]
        super().__init__(**kw)

