"""确认请求/响应结构。"""
from pydantic import BaseModel


class ConfirmationResponse(BaseModel):
    id: int
    task_id: str | None
    action: str
    target: str
    params: str
    preview: list | None = None
    status: str
    created_at: str | None = None
    execution_result: dict | None = None
    is_expired: bool = False


class ConfirmationListResponse(BaseModel):
    items: list[ConfirmationResponse] = []


class ConfirmationDecideRequest(BaseModel):
    approve: bool
    user_id: int | None = None