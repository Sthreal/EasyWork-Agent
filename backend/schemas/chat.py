"""聊天消息请求/响应结构。"""
from pydantic import BaseModel


class ChatMessageCreate(BaseModel):
    user_id: int | None = None
    role: str = "user"
    text: str = ""
    payload: dict | None = None


class ChatMessageResponse(BaseModel):
    id: int
    role: str
    text: str
    payload: dict | None = None
    created_at: str | None = None


class ChatMessageListResponse(BaseModel):
    items: list[ChatMessageResponse] = []
