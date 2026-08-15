"""JWT 签发与校验（真实登录态）。"""
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Header, HTTPException

from config.settings import settings

ALGORITHM = "HS256"
TOKEN_TTL_DAYS = 7


def create_token(user_id: int) -> str:
    """签发 JWT（含 user_id，7 天有效）。"""
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(days=TOKEN_TTL_DAYS),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def decode_token(token: str) -> int | None:
    """校验并解析 JWT，返回 user_id；无效返回 None。"""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
        return int(payload["sub"])
    except Exception:
        return None


def get_current_user(authorization: str | None = Header(default=None)) -> int | None:
    """FastAPI 依赖：从 Authorization Bearer 解析 user_id。

    - 有有效 token → 返回 user_id
    - 无 token：AUTH_REQUIRED=True 抛 401；否则返回 None（兼容旧调用）
    """
    if authorization and authorization.lower().startswith("bearer "):
        user_id = decode_token(authorization[7:].strip())
        if user_id is not None:
            return user_id
    if settings.auth_required:
        raise HTTPException(status_code=401, detail="未登录或登录已过期")
    return None