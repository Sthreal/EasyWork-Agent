"""高危确认接口（确认/挂起列表）。"""
from fastapi import APIRouter

router = APIRouter(prefix="/confirmations")


@router.get("")
def list_confirmations():
    """待确认列表（开发中：M2-6 实现确认闸门）。"""
    return {"items": [], "detail": "确认功能开发中"}
