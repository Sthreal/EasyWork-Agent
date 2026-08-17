"""确认闸门（待确认/超时挂起/放行/拒绝）。"""
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from backend.models.confirmation import Confirmation
from backend.safety.high_risk import is_high_risk

TIMEOUT_MINUTES = 30
WORKSPACE_TIMEOUT_MINUTES = 5


def create_confirmation(
    db: Session,
    task_id: int | None,
    action: str,
    target: str = "",
    params: str = "",
    preview: str = "",
    in_workspace: bool = True,
    task_item_id: int | None = None,
) -> Confirmation | None:
    """高危动作创建确认记录；非高危直接返回 None。in_workspace=True 表示先在工作区等确认。"""
    if not is_high_risk(action, target, params):
        return None
    row = Confirmation(
        task_id=task_id,
        task_item_id=task_item_id,
        action=action,
        target=target,
        params=params,
        preview=preview,
        in_workspace=in_workspace,
        status="pending",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def defer_confirmation(db: Session, confirmation_id: int) -> Confirmation | None:
    """「稍后」：把工作区确认转入待确认队列；已转/已决返回 None。"""
    row = db.get(Confirmation, confirmation_id)
    if row is None or row.status != "pending" or not row.in_workspace:
        return None
    row.in_workspace = False
    row.deferred_at = datetime.utcnow()
    db.commit()
    db.refresh(row)
    return row


def defer_expired_workspace(db: Session, timeout_minutes: int = WORKSPACE_TIMEOUT_MINUTES) -> int:
    """惰性超时迁移：工作区确认超过时限未操作 → 自动转入待确认队列。返回迁移数量。"""
    cutoff = datetime.utcnow() - timedelta(minutes=timeout_minutes)
    rows = (
        db.query(Confirmation)
        .filter(
            Confirmation.status == "pending",
            Confirmation.in_workspace.is_(True),
            Confirmation.created_at < cutoff,
        )
        .all()
    )
    for row in rows:
        row.in_workspace = False
        row.deferred_at = row.deferred_at or datetime.utcnow()
    if rows:
        db.commit()
    return len(rows)


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