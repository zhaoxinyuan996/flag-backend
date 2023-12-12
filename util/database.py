import logging
from functools import partial
from pydantic import BaseModel
from sqlalchemy import text, Row
from sqlalchemy.engine.result import RMKeyView
from typing import Tuple, Any, Optional, Callable, Union
from contextlib import contextmanager
from util.config import config
from flask_sqlalchemy import SQLAlchemy as _SQLAlchemy


log = logging.getLogger(__name__)


class SQLAlchemy(_SQLAlchemy):
    @contextmanager
    def auto_commit(self):
        try:
            yield
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def execute(self, sql: str, **kwargs) -> Optional[Tuple[RMKeyView, Any]]:
        log.info(sql)
        response = self.session.execute(text(sql), kwargs)
        self.session.commit()
        if response.returns_rows:
            records = response.fetchall()
            log.info(str(records))
            return response.keys(), records
        return None


db = SQLAlchemy()


def wrap(self, f: Callable, *args, **kwargs) -> Any:
    """装饰器，如果dao方法声明了返回值，则按照返回值格式化"""
    if ret := getattr(f, '__annotations__').get('return', None):
        resp = f(self, *args, **kwargs)
        model, entry = resp
        return build_model(ret, model, entry)
    f(self, *args, **kwargs)
    return None


_ele = {int, float, str}
_builtins = {dict, list, set, int, float, str}


def build_model(t, keys, struct) -> Any:
    """
    sql返回结果结合pydantic
    :param t: 类型
    :param keys: 读数据库时候的key
    :param struct: 数据体
    """
    if type_ := getattr(t, '__origin__', None):

        if type_ in _builtins:
            assert type_ is type(struct)
        if type_ is list:
            return [build_model(t.__args__[0], keys, i) for i in struct]
        elif type_ is tuple:
            return struct[0]
        elif type_ is dict:
            return t(**struct)
        elif type_ is int or type_ is float or type_ is str:
            return struct
        elif type_ is Union:
            if type(None) in t.__args__:
                if not struct:
                    return None
                else:
                    return build_model(t.__args__[0], keys, struct)
            else:
                return build_model(t.__args__[0], keys, struct)
    if keys is None:
        return t(**struct)
    if t in _ele:
        if isinstance(struct, Row):
            return struct
        return struct[0][0]
    return t(**dict(zip(keys, struct[0] if isinstance(struct, list) else struct)))


class Dao:

    def __init__(self):
        for k, v in type(self).__dict__.items():
            if not k.startswith('__'):
                setattr(self, k, partial(wrap, self, getattr(type(self), k)))

    @staticmethod
    def execute(sql: str, **kwargs) -> Any:
        return db.execute(sql, **kwargs)


if __name__ == '__main__':
    from typing import *

    class Test(BaseModel):
        f1: int
        f2: str
        f3: List[int]
        f4: List[str]
        f5: dict

    from app import app
    with app.app_context():

        insert = '''insert into test values(1,'2', array[1,2,3], array['2', '3', '4'], '{"test": 123}')'''
        delete = 'delete from 1test'
        select = 'select * from test'
        print(config)

        res = db.execute(select)
        print(res)
