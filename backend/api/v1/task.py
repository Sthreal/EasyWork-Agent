"""任务接口（发起/查询/结果）。"""
import uuid

from fastapi import APIRouter

from backend.agent.planner import plan
from backend.schemas.task import TaskCreate, TaskResponse

router = APIRouter(prefix="/tasks")


@router.get("")
def list_tasks():
    """任务列表（开发中：M1-9 实现落库）。"""
    return {"items": [], "detail": "任务功能开发中"}


@router.post("", response_model=TaskResponse)
def create_task(payload: TaskCreate):
    """接收任务 → 意图拆解 → 返回子任务列表（执行 M2 接入）。"""
    tasks = plan(payload.text)
    return TaskResponse(task_id=str(uuid.uuid4()), status="planned", text=payload.text, tasks=tasks)