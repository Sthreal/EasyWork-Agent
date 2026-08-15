"""测试：多轮执行循环。"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.db import Base, get_db
from backend.main import app
from backend.models import audit, confirmation, feishu_token, task, user  # noqa: F401 注册模型
from backend.models.task import Task
from backend.agent import loop
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


def test_parse_continue():
    assert loop._parse_continue('{"done": true, "tasks": []}') == {"done": True, "tasks": []}
    parsed = loop._parse_continue('{"done": false, "tasks": [{"action": "建日历", "tool": "calendar", "args": {"action": "create"}}]}')
    assert parsed["done"] is False
    assert parsed["tasks"][0]["action"] == "建日历"
    assert parsed["tasks"][0]["args"] == {"action": "create"}


def test_should_continue_terminates_when_llm_unavailable(monkeypatch):
    from config.settings import settings as app_settings

    monkeypatch.setattr(app_settings, "llm_api_key", "")
    monkeypatch.setattr(app_settings, "llm_base_url", "")
    monkeypatch.setattr(app_settings, "llm_model", "")
    t = Task(text="读取报名表", status="planned")
    res = loop.should_continue(t, "1. 读取 报名表（executed）", 1)
    assert res == {"done": True, "tasks": []}


def test_multi_step_task_service(env, monkeypatch):
    client, testing_session = env

    def fake_plan(text):
        return {"tasks": [{"action": "读取", "target": "报名表", "params": "", "high_risk": False,
                           "tool": "sheets", "args": {"action": "read", "filename": "报名表.xlsx"}}], "question": None}

    def fake_continue(task, summary, step):
        if step == 1:
            return {"done": False, "tasks": [{"action": "建日历", "target": "复盘", "params": "", "high_risk": False,
                                              "tool": "calendar",
                                              "args": {"action": "create", "summary": "复盘", "start_ts": "2026-08-16T10:00", "end_ts": "2026-08-16T11:00"}}]}
        return {"done": True, "tasks": []}

    monkeypatch.setattr(task_service, "plan", fake_plan)
    monkeypatch.setattr(task_service, "should_continue", fake_continue)
    monkeypatch.setattr(task_service, "execute_item", lambda item_id, **kwargs: {"ok": True, "message": "done", "data": {}})
    resp = client.post("/api/v1/tasks", json={"text": "读取报名表", "user_id": 1})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["tasks"]) == 2
    s = testing_session()
    t = s.query(Task).order_by(Task.id.desc()).first()
    assert t.step == 2
    assert t.status == "executed"
    s.close()


def test_max_steps_terminates(env, monkeypatch):
    client, testing_session = env

    def fake_plan(text):
        return {"tasks": [{"action": "读取", "target": "报名表", "params": "", "high_risk": False,
                           "tool": "sheets", "args": {"action": "read", "filename": "报名表.xlsx"}}], "question": None}

    def fake_continue(task, summary, step):
        if step >= 3:
            return {"done": True, "tasks": []}
        return {"done": False, "tasks": [{"action": "读取", "target": "报名表", "params": "", "high_risk": False,
                                          "tool": "sheets", "args": {"action": "read", "filename": "报名表.xlsx"}}]}

    monkeypatch.setattr(task_service, "plan", fake_plan)
    monkeypatch.setattr(task_service, "should_continue", fake_continue)
    monkeypatch.setattr(task_service, "execute_item", lambda item_id, **kwargs: {"ok": True, "message": "done", "data": {}})
    resp = client.post("/api/v1/tasks", json={"text": "读取报名表", "user_id": 1})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["tasks"]) == 3  # 最多 3 轮
    s = testing_session()
    t = s.query(Task).order_by(Task.id.desc()).first()
    assert t.step == 3
    s.close()