"""聊天消息接口（工作台悬浮聊天持久化）。"""
import json

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.db import get_db
from backend.models.chat_message import ChatMessage
from backend.schemas.chat import ChatMessageCreate, ChatMessageListResponse, ChatMessageResponse

router = APIRouter(prefix="/chat")


@router.post("/messages", response_model=ChatMessageResponse)
def save_message(payload: ChatMessageCreate, db: Session = Depends(get_db)):
    """保存一条聊天消息（user 问题 / agent 完整结果）。"""
    row = ChatMessage(
        user_id=payload.user_id,
        role=payload.role,
        text=payload.text,
        payload=json.dumps(payload.payload, ensure_ascii=False) if payload.payload is not None else "",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _to_response(row)


@router.get("/messages", response_model=ChatMessageListResponse)
def list_messages(
    user_id: int | None = None,
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """按用户取最近 N 条聊天消息（正序返回，便于直接渲染）。"""
    query = db.query(ChatMessage)
    if user_id is not None:
        query = query.filter(ChatMessage.user_id == user_id)
    rows = query.order_by(ChatMessage.id.desc()).limit(limit).all()
    rows.reverse()
    return ChatMessageListResponse(items=[_to_response(r) for r in rows])


def _to_response(row: ChatMessage) -> ChatMessageResponse:
    try:
        payload = json.loads(row.payload) if row.payload else None
    except json.JSONDecodeError:
        payload = None
    return ChatMessageResponse(
        id=row.id,
        role=row.role,
        text=row.text,
        payload=payload if isinstance(payload, dict) else None,
        created_at=row.created_at.isoformat() if row.created_at else None,
    )
