"""用户邮箱配置请求/响应结构。"""
from pydantic import BaseModel, Field


class MailConfigResponse(BaseModel):
    qq_mail_address: str = ""
    qq_mail_auth_code_masked: str = ""


class MailConfigSaveRequest(BaseModel):
    user_id: int
    qq_mail_address: str = Field(..., description="QQ邮箱")
    qq_mail_auth_code: str = Field(..., min_length=4, description="授权码")


class MailTestRequest(BaseModel):
    user_id: int
    qq_mail_address: str
    qq_mail_auth_code: str


class MailTestResponse(BaseModel):
    ok: bool
    message: str