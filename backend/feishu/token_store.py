"""授权令牌存取与刷新。"""
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from backend.models.feishu_token import FeishuToken


def save_token(db: Session, user_id: int, token: dict) -> FeishuToken:
    """保存一份授权令牌（刷新逻辑后续 M1-4 补齐）。"""
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
