"""业务审计：结构化记录（谁、何时、对什么、diff、审批人）。"""
import json

from sqlalchemy.orm import Session

from backend.models.audit import AuditLog


def _json(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, ensure_ascii=False, default=str)
    except Exception:
        return str(value)


def log_audit(
    db: Session,
    *,
    user_id: int | None,
    action: str,
    target: str = "",
    detail=None,
    diff_before=None,
    diff_after=None,
    status: str = "ok",
    confirmation_id: int | None = None,
) -> None:
    """写一条审计记录（不提交，由调用方随业务一起提交）。"""
    db.add(
        AuditLog(
            user_id=user_id,
            action_type=action,
            target=target,
            detail=_json(detail),
            diff_before=_json(diff_before),
            diff_after=_json(diff_after),
            status=status,
            confirmation_id=confirmation_id,
        )
    )