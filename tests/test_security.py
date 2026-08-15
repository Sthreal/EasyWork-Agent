"""测试：JWT 鉴权。"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.db import Base, get_db
from backend.main import app
from backend.models import confirmation, feishu_token, task, user  # noqa: F401 注册模型
from backend.security import create_token, decode_token
from config.settings import settings
import backend.services.task_service as task_service


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


def test_token_roundtrip():
    token = create_token(7)
    assert decode_token(token) == 7
    assert decode_token(token + "x") is None
    assert decode_token("not-a-jwt") is None


def test_token_identity_wins_over_body(env, monkeypatch):
    client, testing_session = env

    def fake_plan(text):
        return {"tasks": [{"action": "读取", "target": "报名表", "params": "", "high_risk": False, "tool": "sheets",
                           "args": {"action": "read", "filename": "报名表.xlsx"}}], "question": None}

    monkeypatch.setattr(task_service, "plan", fake_plan)
    monkeypatch.setattr(task_service, "execute_item", lambda item_id, **kwargs: {"ok": True, "message": "done", "data": {}})
    token = create_token(7)
    resp = client.post(
        "/api/v1/tasks",
        json={"text": "读取报名表", "user_id": 8},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    s = testing_session()
    t = s.query(task.Task).order_by(task.Task.id.desc()).first()
    assert t.user_id == 7  # token 身份优先
    s.close()


def test_auth_required_blocks_without_token(env, monkeypatch):
    client, _ = env
    monkeypatch.setattr(settings, "auth_required", True)
    resp = client.get("/api/v1/tasks")
    assert resp.status_code == 401
    token = create_token(1)
    resp2 = client.get("/api/v1/tasks", headers={"Authorization": f"Bearer {token}"})
    assert resp2.status_code == 200