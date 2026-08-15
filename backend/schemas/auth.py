"""登录请求/响应结构。"""
from pydantic import BaseModel


class LoginUrlResponse(BaseModel):
    login_url: str


class AuthCallbackResponse(BaseModel):
    user_id: int
    open_id: str
    name: str
    avatar_url: str
    token: str = ""


class AuthStatusResponse(BaseModel):
    configured: bool
    redirect_uri: str