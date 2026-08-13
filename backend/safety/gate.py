"""确认闸门（待确认/超时挂起/放行/拒绝）。"""
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from backend.models.confirmation import Confirmation
from backend.safety.high_risk import is_high_risk

TIMEOUT_MINUTES = 30


def create_confirmation(
    db: Session,
    task_id: int | None,
    action: str,
    target: str = "",
    params: str = "",
) -> Confirmation | None:
    """高危动作创建确认记录；非高危直接返回 None。"""
    if not is_high_risk(action, target, params):
        return None
    row = Confirmation(task_id=task_id, action=action, target=target, params=params, status="pending")
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def decide_confirmation(db: Session, confirmation_id: int, approve: bool) -> Confirmation | None:
    """确认/拒绝；已决或不存在返回 None。"""
    row = db.get(Confirmation, confirmation_id)
    if row is None or row.status != "pending":
        return None
    row.status = "approved" if approve else "rejected"
    row.decided_at = datetime.utcnow()
    db.commit()
    db.refresh(row)
    return row


def is_expired(row: Confirmation, timeout_minutes: int = TIMEOUT_MINUTES) -> bool:
    """超时未确认视为挂起（不自动执行）。"""
    if row.created_at is None:
        return False
    return datetime.utcnow() >= row.created_at + timedelta(minutes=timeout_minutes)