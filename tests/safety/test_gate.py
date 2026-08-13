"""测试：确认闸门。"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.db import Base
from backend.models import confirmation  # noqa: F401 注册模型
from backend.safety import gate
from backend.safety.high_risk import is_high_risk


@pytest.fixture()
def db():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    s = sessionmaker(bind=engine)()
    yield s
    s.close()


def test_high_risk_keywords():
    assert is_high_risk("发送邮件", "项目组") is True
    assert is_high_risk("删除文件") is True
    assert is_high_risk("创建日程") is False


def test_create_confirmation_only_for_high_risk(db):
    row = gate.create_confirmation(db, task_id=1, action="发送邮件", target="项目组")
    assert row is not None
    assert row.status == "pending"
    assert gate.create_confirmation(db, task_id=1, action="创建日程") is None


def test_decide_approve_and_reject(db):
    row = gate.create_confirmation(db, task_id=1, action="发送邮件", target="项目组")
    approved = gate.decide_confirmation(db, row.id, True)
    assert approved.status == "approved"
    assert gate.decide_confirmation(db, row.id, False) is None


def test_is_expired(db):
    row = gate.create_confirmation(db, task_id=1, action="发送邮件", target="项目组")
    assert gate.is_expired(row, timeout_minutes=0) is True
    assert gate.is_expired(row, timeout_minutes=30) is False