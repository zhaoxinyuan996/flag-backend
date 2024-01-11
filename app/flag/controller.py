import json
import os
import logging
from typing import List, Tuple, Union
from uuid import UUID

from app.user.dao import dao as user_dao
from app.flag.dao import dao
from flask import Blueprint, request, Response, g
from flask_jwt_extended import get_jwt_identity
from app.constants import UserClass, flag_picture_size, FileType, allow_picture_type, RespMsg, CacheTimeout
from app.flag.typedef import AddFlag, UpdateFlag, SetFlagType, \
    AddComment, AddSubComment, FlagId, GetFlagByMap, Flag, GetFlagByFlag, GetFlagByUser
from app.user.controller import get_user_info
from app.user.typedef import UserInfo
from app.util import args_parse, resp, custom_jwt, get_request_list
from util.database import db, redis_cli
from util.up_oss import up_oss

module_name = os.path.basename(os.path.dirname(__file__))
bp = Blueprint(module_name, __name__, url_prefix=f'/api/{module_name}')

log = logging.getLogger(__name__)


# with open(os.path.join(os.path.dirname(__file__), 'location_code.json'), encoding='utf-8') as city_file:
#     location_code = json.loads(city_file.read())


def ex_user(f: Flag) -> set:
    return {'user_id'} if str(f.user_id) != g.user_id and f.hide else {}


def get_region_flag(user_id: UUID, get: GetFlagByMap) -> Tuple[int, List[dict]]:
    """根据定位位置获取区域内所有的点位"""
    code = dao.get_city_by_location(get.location) or 0
    if not code:
        return 0, []
    key = f'region-flag-{get.type}-{code}'
    # 缓存
    if value := redis_cli.get(key):
        return code, json.loads(value)
    else:
        value = [f.model_dump() for f in dao.get_flag_by_city(user_id, code, get)]
        redis_cli.set(key, json.dumps(value), ex=CacheTimeout.region_flag)
        return code, value


def _build(content: str) -> List[Tuple[str, bytes]]:
    """集成各种校验，返回图片"""
    pictures = request.files.getlist('pic')
    info: UserInfo = get_user_info()
    if info.user_class == UserClass.normal and len(pictures) > 1:
        return resp(RespMsg.too_large)
    elif info.user_class == UserClass.vip and len(pictures) > 9:
        return resp(RespMsg.too_large)
    length = 0
    datas = []
    for p in pictures:
        _, suffix = p.filename.rsplit('.', 1)
        if suffix not in allow_picture_type:
            return resp(RespMsg.user_picture_format_error + str(allow_picture_type), -1)

        data = p.stream.read()
        length += len(data)
        if length > flag_picture_size:
            return resp(RespMsg.too_large)

        datas.append((suffix, data))

    if len(content) > 300:
        return resp(RespMsg.too_long)

    return datas


def _add_or_update(model: Union[type(AddFlag), type(UpdateFlag)], new: bool):
    """新增和修改"""
    user_id = g.user_id
    _flag = get_request_list(request.form)
    _flag['user_id'] = user_id
    _flag['pictures'] = []
    if isinstance(_flag.get('location'), str):
        _flag['location'] = json.loads(_flag['location'])
    flag = model(**_flag)

    # 获取用户级别
    user_class = get_user_info().user_class
    # 构建图片数据
    datas = _build(flag.content)
    if isinstance(datas, Response):
        return datas
    # 新建和修改走同一个函数
    with db.auto_commit():
        # 新标记要新建一个标记
        if new:
            g.error_resp = RespMsg.flag_cant_cover_others_flag
            user_dao.add_flag(user_id)
            flag.id = dao.add(flag, user_class)

        for i, data in enumerate(datas):
            suffix, b = data
            flag.pictures.append(up_oss.get_url(f'{flag.id}.{suffix}', FileType.flag_pic))
            up_oss.upload(FileType.flag_pic, f'{flag.id}-{i}.{suffix}', b)


        flag_id = dao.update(flag)
        if not flag_id:
            return resp(RespMsg.flag_not_exist, -1)
    return resp(RespMsg.success, flag_id=flag.id)

"""
上传图片流程
新建
添加标记    /add
上传图片    /upload-pictures
更新至数据库
上传到oss
修改
修改标记    /update
客户端域名区分，把差量图片记录
上传图片    /upload-pictures
查表把所有oss图片找到
删除oss的数据
更新表
上传新的oss数据
"""

# @bp.route('/upload-pictures-done', methods=['post'])
# @args_parse(FlagId)
# @custom_jwt()
# def upload_pictures_done(flag: FlagId):
#
#     if pictures_data := redis_cli.get():
#         # data是k-v
#         for data in pictures_data:
#             suffix = data['name'].rsplit('.', 1)[1]
#             new_filename = f'{flag.id}.{file_minio.random_str()}.{suffix}'
#             new_url = file_minio.get_file_url(new_filename, FileType.head_pic)
#     dao.upload_pictures(flag.id, )
#
#
#     # 生成文件名
#
#
#     # 获取旧的图片，删除旧图片
#     old_url = dao.get_avatar_url(user_id)
#     file_minio.remove_object(old_url, FileType.head_pic)
#     # 设置数据库，再上传
#     dao.set_avatar_url(user_id, new_url)
#     file_minio.upload(new_filename, FileType.head_pic, b)
#
#     return resp(RespMsg.success)


# def inspect(req: Union[AddFlag, UpdateFlag]):
#     """检查，判断用户级别和可用量"""
#     info: UserInfo = get_user_info()
#     if info.user_class == UserClass.normal and len(req.pictures) > 1:
#         return resp(RespMsg.too_large)
#     elif info.user_class == UserClass.vip and len(req.pictures) > 9:
#         return resp(RespMsg.too_large)


@bp.route('/add', methods=['post'])
@args_parse(AddFlag)
@custom_jwt()
def add(flag: AddFlag):
    """新增标记"""
    info = get_user_info()
    if info.allow_flag_num < 0:
        return resp(RespMsg.flag_limit)
    # 获取用户级别
    user_id = g.user_id
    user_class = get_user_info().user_class
    # 新建标记
    g.error_resp = RespMsg.flag_cant_cover_others_flag
    with db.auto_commit():
        user_dao.add_flag(user_id)
        flag_p = dao.add(user_id, flag, user_class)

    return resp(RespMsg.success, flag_id=flag_p.id)


@bp.route('/update', methods=['post'])
@args_parse(UpdateFlag)
@custom_jwt()
def update(flag: UpdateFlag):
    """更新标记"""
    flag_p = dao.update(g.user_id, flag)
    if flag_p:
        return resp(RespMsg.success, flag_id=flag_p.id, pictures=flag_p.pictures)
    return resp(RespMsg.success)


@bp.route('/upload-pictures', methods=['post'])
@custom_jwt()
def upload_pictures():
    flag_id = UUID(request.form['id'])
    pictures = get_request_list(request.files)['file']
    if not isinstance(pictures, list):
        pictures = [pictures]

    # 先构建名字
    names = [f"{flag_id}{up_oss.random_str()}-{p.filename.rsplit('.', 1)[1]}" for p in pictures]
    # 再存表
    dao.upload_pictures(flag_id, names)
    # 最后上传
    for i in range(len(pictures)):
        up_oss.upload(FileType.flag_pic, names[i], pictures[i].stream.read())


@bp.route('/get-flag-by-user', methods=['post'])
@args_parse(GetFlagByUser)
@custom_jwt()
def get_flag_by_user(get: GetFlagByUser):
    return resp([f.model_dump(exclude=ex_user(f)) for f in dao.get_flag_by_user(get.id, g.user_id, get)])


@bp.route('/get-flag-by-flag', methods=['post'])
@args_parse(GetFlagByFlag)
@custom_jwt()
def get_flag_by_flag(get: GetFlagByFlag):
    flag = dao.get_flag_by_flag(get.id, get_jwt_identity())
    return resp(flag.model_dump(exclude=ex_user(flag)) if flag else None)


@bp.route('/get-flag-by-map', methods=['post'])
@args_parse(GetFlagByMap)
@custom_jwt()
def get_flag_by_map(get: GetFlagByMap):
    # 10公里内4倍检索，返回详细标记
    print(get)
    if get.distance < 10000:
        get.distance *= 4
        return resp({
            'code': None,
            'detail': True,
            'flags': [f.model_dump(exclude=ex_user(f)) for f in dao.get_flag_by_map(g.user_id, get)]})
    # 10公里-100公里2.25倍检索，返回以区县层级的嵌套
    else:
        code, data = get_region_flag(g.user_id, get)
        return resp({'code': code, 'detail': False, 'flags': data})


@bp.route('/set-flag-type', methods=['post'])
@args_parse(SetFlagType)
@custom_jwt()
def set_flag_type(set_: SetFlagType):
    dao.set_flag_type(g.user_id, set_.id, set_.type)
    return resp(RespMsg.success)


@bp.route('/delete', methods=['post'])
@args_parse(FlagId)
@custom_jwt()
def delete(delete_: FlagId):
    """删除标记"""
    user_id = g.user_id
    with db.auto_commit():
        # 先删除，如果存在则更新用户表
        dao.delete(user_id, delete_.id) is None or user_dao.delete_flag(user_id)
    return resp(RespMsg.success)


@bp.route('/get-fav', methods=['post'])
@custom_jwt()
def get_fav():
    """我的收藏"""
    user_id = g.user_id

    return resp([i.model_dump() for i in dao.get_fav(user_id)])


@bp.route('/add-fav', methods=['post'])
@args_parse(FlagId)
@custom_jwt()
def add_fav(delete_: FlagId):
    """删除收藏"""
    user_id = g.user_id
    dao.add_fav(user_id, delete_.id)
    return resp(RespMsg.success)


@bp.route('/delete-fav', methods=['post'])
@args_parse(FlagId)
@custom_jwt()
def delete_fav(delete_: FlagId):
    """删除收藏"""
    user_id = g.user_id
    dao.delete_fav(user_id, delete_.id)
    return resp(RespMsg.success)


@bp.route('/add-comment', methods=['post'])
@args_parse(AddComment)
@custom_jwt()
def add_comment(add_: AddComment):
    """添加标记"""
    user_id = g.user_id
    if not dao.flag_exist(user_id, add_.flag_id):
        return resp(RespMsg.flag_not_exist)
    dao.add_comment(add_.flag_id, user_id, add_.content, add_.location, None, None)
    return resp(RespMsg.success)


@bp.route('/add-sub-comment', methods=['post'])
@args_parse(AddSubComment)
@custom_jwt()
def add_sub_comment(add_: AddSubComment):
    user_id = g.user_id
    # 标记是否存在
    if not dao.flag_exist(user_id, add_.flag_id):
        return resp(RespMsg.comment_not_exist)

    # 这里要做一个系统通知
    # 获取用户昵称
    # 评论层级只能2层，回复评论的root_comment_id一定是null
    ask_user_nickname = dao.get_nickname_by_comment_id(user_id, add_.flag_id, add_.root_comment_id)
    if not ask_user_nickname:
        return resp(RespMsg.comment_not_exist)

    dao.add_comment(add_.flag_id, user_id, add_.content, add_.location, add_.root_comment_id, ask_user_nickname)
    return resp(RespMsg.success)


@bp.route('/get-comment', methods=['post'])
@args_parse(FlagId)
@custom_jwt()
def get_comment(flag: FlagId):
    """获取评论"""
    user_id = g.user_id
    if not dao.flag_is_open(user_id, flag.id):
        return resp(RespMsg.flag_not_exist)
    return resp([c.model_dump() for c in dao.get_comment(flag, user_id)])


@bp.route('/delete-comment', methods=['post'])
@args_parse(FlagId)
@custom_jwt()
def delete_comment(flag: FlagId):
    """删除评论"""
    dao.delete_comment(flag.id, get_jwt_identity())
    return resp(RespMsg.success)

# @bp.route('/get-city', methods=['post'])
# @custom_jwt()
# def get_city():
#     return resp(location_code)
