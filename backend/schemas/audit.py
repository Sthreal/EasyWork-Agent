"""审计记录结构。"""
from pydantic import BaseModel


class AuditRecord(BaseModel):
    id: int
    user_id: int | None
    action_type: str
    target: str
    detail: str
    diff_before: str
    diff_after: str
    status: str
    created_at: str | None = None


class AuditListResponse(BaseModel):
    items: list[AuditRecord] = []