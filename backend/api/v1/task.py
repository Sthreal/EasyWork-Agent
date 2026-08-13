"""任务接口（发起/查询/结果）。"""
from fastapi import APIRouter

router = APIRouter(prefix="/tasks")


@router.get("")
def list_tasks():
    """任务列表（开发中：M1-9 实现落库）。"""
    return {"items": [], "detail": "任务功能开发中"}
