"""登录接口（含飞书OAuth回调）。"""
from fastapi import APIRouter

router = APIRouter(prefix="/auth")


@router.get("/status")
def status():
    """登录状态（开发中：M1-3 实现飞书登录）。"""
    return {"logged_in": False, "detail": "登录功能开发中"}
