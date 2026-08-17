"""高危确认记录表。"""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.db import Base


class Confirmation(Base):
    __tablename__ = "confirmations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    task_id: Mapped[int | None] = mapped_column(ForeignKey("tasks.id"), nullable=True, index=True)
    task_item_id: Mapped[int | None] = mapped_column(ForeignKey("task_items.id"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(128))
    target: Mapped[str] = mapped_column(String(256), default="")
    params: Mapped[str] = mapped_column(Text, default="")
    preview: Mapped[str] = mapped_column(Text, default="")  # 结构化 diff 预览（JSON 字符串）
    in_workspace: Mapped[bool] = mapped_column(Boolean, default=True)  # True=在工作区等确认，False=已转待确认队列
    deferred_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)  # 转入待确认队列的时间
    status: Mapped[str] = mapped_column(String(32), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    decided_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)