"""登录接口（含飞书OAuth回调）。"""
import json
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Header, Query
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlalchemy.orm import Session

from backend.db import get_db
from backend.feishu.auth import build_authorize_url, exchange_code
from backend.feishu.token_store import save_token
from backend.models.user import User
from backend.schemas.auth import AuthCallbackResponse, AuthStatusResponse
from backend.security import create_token
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
    db: Session = Depends(get_db),
    accept: str = Header(""),
    code: str | None = Query(None),
    error: str | None = Query(None),
):
    """飞书授权回调：换令牌 → 取用户信息 → 落库用户 → 存令牌 → 签发 JWT。"""
    if not code or error:
        reason = error or "未收到授权码，请重新登录"
        if "application/json" in accept:
            return JSONResponse(status_code=400, content={"detail": f"授权失败：{reason}"})
        return _render_failure_page(reason)

    result = exchange_code(code)
    feishu_token, user_info = result["token"], result["user_info"]

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

    save_token(db, user.id, feishu_token)
    jwt_token = create_token(user.id)

    if "application/json" in accept:
        return AuthCallbackResponse(
            user_id=user.id,
            open_id=user.feishu_open_id,
            name=user.name,
            avatar_url=user.avatar_url,
            token=jwt_token,
        )
    return _render_success_page(user, jwt_token)


def _render_success_page(user: User, jwt_token: str) -> HTMLResponse:
    data = {
        "user_id": user.id,
        "open_id": user.feishu_open_id,
        "name": user.name,
        "avatar_url": user.avatar_url,
        "token": jwt_token,
    }
    query = urlencode({"user": json.dumps(data, ensure_ascii=False)})
    target = f"{settings.frontend_url}/?{query}"
    html = f"""<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>登录成功</title></head>
<body>
<script>
  location.replace('{target}');
</script>
</body>
</html>"""
    return HTMLResponse(content=html)


def _render_failure_page(reason: str) -> HTMLResponse:
    html = f"""<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>登录失败</title></head>
<body>
  <h2>登录失败</h2>
  <p>{reason}</p>
  <p><a href="{settings.frontend_url}">返回重新登录</a></p>
</body>
</html>"""
    return HTMLResponse(content=html)