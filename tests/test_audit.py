"""测试：业务审计。"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.db import Base, get_db
from backend.main import app
from backend.models import audit, confirmation, feishu_token, task, user  # noqa: F401 注册模型
from backend.models.audit import AuditLog
from backend.safety.gate import create_confirmation
import backend.services.task_service as task_service
import backend.api.v1.confirmation as conf_api


@pytest.fixture()
def env(monkeypatch):
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    monkeypatch.setattr("backend.agent.executor.SessionLocal", testing_session)

    def override_get_db():
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app, raise_server_exceptions=False)
    yield client, testing_session
    app.dependency_overrides.clear()


def test_task_create_audit(env, monkeypatch):
    client, testing_session = env
    monkeypatch.setattr(
        task_service,
        "plan",
        lambda text: {"tasks": [{"action": "读取", "target": "报名表", "params": "", "high_risk": False,
                                 "tool": "sheets", "args": {"action": "read", "filename": "报名表.xlsx"}}],
                      "question": None},
    )
    monkeypatch.setattr(task_service, "execute_item", lambda item_id, **kwargs: {"ok": True, "message": "done", "data": {}})
    resp = client.post("/api/v1/tasks", json={"text": "读取报名表", "user_id": 1})
    assert resp.status_code == 200
    s = testing_session()
    rows = s.query(AuditLog).filter_by(action_type="task.create").all()
    assert len(rows) >= 1
    assert rows[0].user_id == 1
    s.close()


def test_decide_audit(env, monkeypatch):
    client, testing_session = env
    monkeypatch.setattr(
        task_service,
        "plan",
        lambda text: {"tasks": [{"action": "发送邮件", "target": "项目组", "params": "", "high_risk": True,
                                 "tool": "email", "args": {"action": "send", "to": "a@b.com", "subject": "s"}}],
                      "question": None},
    )
    monkeypatch.setattr(task_service, "execute_item", lambda item_id, **kwargs: {"ok": True, "message": "done", "data": {}})
    resp = client.post("/api/v1/tasks", json={"text": "发邮件", "user_id": 1})
    cid = resp.json()["tasks"][0]["confirmation_id"]
    monkeypatch.setattr(conf_api, "execute_item", lambda item_id: {"ok": True, "message": "已执行", "data": {}})
    dec = client.post(f"/api/v1/confirmations/{cid}/decide", json={"approve": True, "user_id": 1})
    assert dec.status_code == 200
    s = testing_session()
    rows = s.query(AuditLog).filter_by(action_type="confirmation.approve").all()
    assert len(rows) >= 1
    assert rows[0].confirmation_id == cid
    s.close()


def test_audit_endpoint(env, monkeypatch):
    client, _ = env
    monkeypatch.setattr(
        task_service,
        "plan",
        lambda text: {"tasks": [{"action": "读取", "target": "报名表", "params": "", "high_risk": False,
                                 "tool": "sheets", "args": {"action": "read", "filename": "报名表.xlsx"}}],
                      "question": None},
    )
    monkeypatch.setattr(task_service, "execute_item", lambda item_id, **kwargs: {"ok": True, "message": "done", "data": {}})
    client.post("/api/v1/tasks", json={"text": "读取报名表", "user_id": 1})
    resp = client.get("/api/v1/audit", params={"user_id": 1})
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert any(i["action_type"] == "task.create" for i in items)