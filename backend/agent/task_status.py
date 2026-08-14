"""任务级状态聚合：按子任务状态回写 Task.status。"""
from sqlalchemy.orm import Session

from backend.models.task import Task

# 优先级：pending_confirm > rejected > failed > pending > executed
def _aggregate(item_statuses: list[str]) -> str:
    if any(s == "pending_confirm" for s in item_statuses):
        return "pending_confirm"
    if any(s == "rejected" for s in item_statuses):
        return "rejected"
    if any(s == "failed" for s in item_statuses):
        return "failed"
    if any(s == "pending" for s in item_statuses):
        return "pending_confirm"
    return "executed"


def refresh_task_status(db: Session, task_id: int) -> str:
    """按子任务状态聚合回写任务状态；返回新状态。need_clarify 任务保持原值。"""
    task = db.get(Task, task_id)
    if task is None:
        return ""
    if task.status == "need_clarify" or not task.items:
        return task.status
    task.status = _aggregate([i.status for i in task.items])
    return task.status