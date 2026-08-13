"""授权令牌存取与刷新。"""
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.feishu.client import FeishuClient, FeishuError
from backend.models.feishu_token import FeishuToken


def save_token(db: Session, user_id: int, token: dict) -> FeishuToken:
    """保存一份授权令牌（登录或刷新成功后写入）。"""
    expires_at = datetime.utcnow() + timedelta(seconds=int(token.get("expires_in", 7200)))
    row = FeishuToken(
        user_id=user_id,
        access_token=token["access_token"],
        refresh_token=token.get("refresh_token", ""),
        expires_at=expires_at,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_valid_token(db: Session, user_id: int) -> FeishuToken:
    """取最新令牌；过期或临近过期时自动用 refresh_token 刷新。"""
    row = db.execute(
        select(FeishuToken)
        .where(FeishuToken.user_id == user_id)
        .order_by(FeishuToken.id.desc())
        .limit(1)
    ).scalar_one_or_none()
    if row is None:
        raise FeishuError("未找到授权令牌，请重新登录")
    if not _is_expired(row):
        return row
    return _refresh(db, row)


def _is_expired(row: FeishuToken, buffer_seconds: int = 60) -> bool:
    """是否过期（提前 60 秒视为过期，避免临界失效）。"""
    if row.expires_at is None:
        return True
    return datetime.utcnow() + timedelta(seconds=buffer_seconds) >= row.expires_at


def _refresh(db: Session, row: FeishuToken) -> FeishuToken:
    if not row.refresh_token:
        raise FeishuError("令牌已过期且无 refresh_token，请重新登录")
    client = FeishuClient()
    new_token = client.refresh_user_access_token(row.refresh_token)
    # refresh_token 只能用一次，这里把新令牌作为新记录保存（旋转）
    return save_token(db, row.user_id, new_token)