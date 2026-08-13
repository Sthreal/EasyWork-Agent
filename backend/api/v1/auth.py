"""登录接口（含飞书OAuth回调）。"""
import json

from fastapi import APIRouter, Depends, Header, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from backend.db import get_db
from backend.feishu.auth import build_authorize_url, exchange_code
from backend.feishu.token_store import save_token
from backend.models.user import User
from backend.schemas.auth import AuthCallbackResponse, AuthStatusResponse
from config.settings import settings

router = APIRouter(prefix="/auth")


@router.get("/status", response_model=AuthStatusResponse)
def status():
    """调试用：查看飞书凭证是否已配置。"""
    return AuthStatusResponse(
        configured=bool(settings.feishu_app_id and settings.feishu_app_secret),
        redirect_uri=settings.feishu_redirect_uri,
    )


@router.get("/login")
def login():
    """浏览器访问直接跳转飞书授权页。"""
    return RedirectResponse(url=build_authorize_url())


@router.get("/callback")
def callback(
    code: str = Query(...),
    db: Session = Depends(get_db),
    accept: str = Header(""),
):
    """飞书授权回调：换令牌 → 取用户信息 → 落库用户 → 存令牌。"""
    result = exchange_code(code)
    token, user_info = result["token"], result["user_info"]

    user = db.query(User).filter_by(feishu_open_id=user_info["open_id"]).first()
    if user is None:
        user = User(
            feishu_open_id=user_info["open_id"],
            name=user_info["name"],
            avatar_url=user_info["avatar_url"],
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    save_token(db, user.id, token)

    if "application/json" in accept:
        return AuthCallbackResponse(
            user_id=user.id,
            open_id=user.feishu_open_id,
            name=user.name,
            avatar_url=user.avatar_url,
        )
    return _render_success_page(user)


def _render_success_page(user: User) -> HTMLResponse:
    """浏览器场景：把用户信息写入 localStorage 后自动跳转到前端。"""
    data = json.dumps(
        {
            "user_id": user.id,
            "open_id": user.feishu_open_id,
            "name": user.name,
            "avatar_url": user.avatar_url,
        },
        ensure_ascii=False,
    )
    html = f"""<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>登录成功</title></head>
<body>
<script>
  localStorage.setItem('office_agent_user', {data});
  location.replace('{settings.frontend_url}');
</script>
</body>
</html>"""
    return HTMLResponse(content=html)