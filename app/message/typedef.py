from datetime import datetime
from typing import Optional, List
from app.util import Model


class Message(Model):
    id: Optional[int]
    type: Optional[int]
    send_id: Optional[int]
    receive_id: Optional[int]
    content: Optional[str]
    create_time: Optional[datetime]


class Notice(Model):
    id: Optional[int]
    version: Optional[str]
    user_class: Optional[int]
    title: Optional[str]
    content: Optional[str]
    create_time: Optional[datetime]


class AskNoticeReq(Model):
    id: int


class AskNotice(Model):
    id: int
    version: str
    title: str
    content: str
    create_time: datetime


class SendMessage(Message):
    receive_id: int
    content: str


class ReceiveMessage(Model):
    id: int


class MessageSub(Model):
    content: str
    create_time: datetime


class ReceiveMessageRespSub(Model):
    send_id: int
    contents: List[MessageSub]


class ReceiveMessageResp(Model):
    max_id: int
    type: int
    contents: List[ReceiveMessageRespSub]
