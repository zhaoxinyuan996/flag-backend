from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import constr, conint
from app.base_typedef import LOCATION, URL
from app.constants import UserClass, FlagNum, UndefinedError
from app.util import Model


_NICKNAME = constr(max_length=10)
_SIGNATURE = constr(max_length=50)


class User(Model):
    id: Optional[UUID]

    nickname: Optional[_NICKNAME]
    username: Optional[str]
    password: Optional[str]
    phone: Optional[int]
    sex: Optional[int]
    flag_num: Optional[int]

    wechat_id: Optional[str]

    signature: Optional[_SIGNATURE]
    avatar_url: Optional[str]

    create_time: Optional[datetime]
    vip_deadline: Optional[datetime]
    block_deadline: Optional[datetime]
    alive_deadline: Optional[datetime]

    belong: Optional[str]
    location: Optional[LOCATION]


class UserInfo(Model):
    flag_num: int
    create_time: datetime
    vip_deadline: datetime
    block_deadline: datetime
    alive_deadline: datetime

    @property
    def user_class(self) -> UserClass:
        if self.block_deadline > datetime.now():
            return UserClass.block
        elif self.vip_deadline > datetime.now():
            return UserClass.vip
        else:
            return UserClass.normal

    @property
    def allow_flag_num(self) -> int:
        if self.user_class == UserClass.block:
            return 0
        elif self.user_class == UserClass.normal:
            return FlagNum.normal_user - self.flag_num
        elif self.user_class == UserClass.vip:
            return FlagNum.vip_user - self.flag_num
        raise UndefinedError('user class')


class SignUp(User):
    username: str
    password: str


class SignWechat(Model):
    code: str


class SignIn(User):
    username: str
    password: str


class UserId(User):
    id: UUID


class SetUserinfo(Model):
    nickname: Optional[_NICKNAME]
    is_man: Optional[bool]
    phone: Optional[conint(lt=19999999999)]
    signature: Optional[_SIGNATURE]
    avatar_url: Optional[URL]


if __name__ == '__main__':
    ...
