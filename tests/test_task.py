"""测试：任务接口。"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.db import Base, get_db
from backend.main import app
from backend.models import feishu_token, task, user  # noqa: F401 注册模型
import backend.api.v1.task as task_api


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_create_task_returns_planned_tasks(client, monkeypatch):
    monkeypatch.setattr(
        task_api,
        "plan",
        lambda text: {
            "tasks": [
                {"action": "写邮件", "target": "项目组", "params": "", "high_risk": False},
                {"action": "发送邮件", "target": "项目组", "params": "", "high_risk": True},
            ],
            "question": None,
        },
    )
    resp = client.post("/api/v1/tasks", json={"text": "给项目组发邮件"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "planned"
    assert body["text"] == "给项目组发邮件"
    assert len(body["tasks"]) == 2
    assert body["tasks"][1]["high_risk"] is True
    assert body["question"] is None
    assert body["task_id"]


def test_create_task_asks_clarification(client, monkeypatch):
    monkeypatch.setattr(
        task_api,
        "plan",
        lambda text: {"tasks": [], "question": "你想处理什么？"},
    )
    resp = client.post("/api/v1/tasks", json={"text": "帮我处理一下"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "need_clarify"
    assert body["tasks"] == []
    assert body["question"] == "你想处理什么？"


def test_task_saved_and_queryable(client, monkeypatch):
    monkeypatch.setattr(
        task_api,
        "plan",
        lambda text: {
            "tasks": [
                {"action": "写邮件", "target": "项目组", "params": "", "high_risk": False},
                {"action": "发送邮件", "target": "项目组", "params": "", "high_risk": True},
            ],
            "question": None,
        },
    )
    resp = client.post("/api/v1/tasks", json={"text": "给项目组发邮件"})
    task_id = resp.json()["task_id"]

    hist = client.get("/api/v1/tasks")
    assert hist.status_code == 200
    items = hist.json()["items"]
    record = next(item for item in items if item["task_id"] == task_id)
    assert record["status"] == "planned"
    assert len(record["tasks"]) == 2
    assert record["tasks"][0]["action"] == "写邮件"


def test_create_task_rejects_empty(client):
    resp = client.post("/api/v1/tasks", json={"text": ""})
    assert resp.status_code == 422