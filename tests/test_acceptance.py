"""验收：制造错误 → 项目不崩 + 能查到原因。"""
import logging

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.db import Base, get_db
from backend.main import app
from backend.models import confirmation, feishu_token, task, user  # noqa: F401 注册模型
from config.logging import setup_logging
import backend.services.task_service as task_service
import backend.agent.executor as executor_mod


@pytest.fixture()
def env(tmp_path, monkeypatch):
    log_file = tmp_path / "app.log"
    setup_logging(log_file=log_file, level=logging.INFO)
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    monkeypatch.setattr(executor_mod, "SessionLocal", testing_session)

    def override_get_db():
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app, raise_server_exceptions=False)
    yield client, log_file
    app.dependency_overrides.clear()


def test_bad_json_returns_422(env):
    client, _ = env
    resp = client.post("/api/v1/tasks", content="not-json", headers={"Content-Type": "application/json"})
    assert resp.status_code == 422


def test_empty_text_returns_422(env):
    client, _ = env
    resp = client.post("/api/v1/tasks", json={"text": ""})
    assert resp.status_code == 422


def test_unexpected_error_returns_500_and_logged(env, monkeypatch):
    client, log_file = env

    def boom(text):
        raise RuntimeError("验收错误 boom")

    monkeypatch.setattr(task_service, "plan", boom)
    resp = client.post("/api/v1/tasks", json={"text": "制造错误"})
    assert resp.status_code == 500
    assert "服务器内部错误" in resp.json()["detail"]
    assert "boom" in log_file.read_text(encoding="utf-8")


def test_invalid_tool_args_marks_failed(env, monkeypatch):
    client, _ = env
    monkeypatch.setattr(
        task_service,
        "plan",
        lambda text: {
            "tasks": [
                {"action": "发送邮件", "target": "", "params": "", "high_risk": False,
                 "tool": "email", "args": {"action": "send", "to": "not-an-email", "subject": "x"}}
            ],
            "question": None,
        },
    )
    resp = client.post("/api/v1/tasks", json={"text": "发邮件"})
    assert resp.status_code == 200
    item = resp.json()["tasks"][0]
    assert item["status"] == "failed"
    assert "参数不合法" in item["result"]


def test_whitelist_rejected_marks_failed(env, monkeypatch):
    client, _ = env
    monkeypatch.setattr(
        task_service,
        "plan",
        lambda text: {
            "tasks": [
                {"action": "删除文件", "target": "", "params": "", "high_risk": False,
                 "tool": "sheets", "args": {"action": "delete", "filename": "a.xlsx"}}
            ],
            "question": None,
        },
    )
    resp = client.post("/api/v1/tasks", json={"text": "删除"})
    assert resp.status_code == 200
    item = resp.json()["tasks"][0]
    assert item["status"] == "failed"
    assert "白名单" in item["result"]


def test_service_alive_after_errors(env, monkeypatch):
    client, _ = env

    def boom(text):
        raise RuntimeError("再崩一次")

    monkeypatch.setattr(task_service, "plan", boom)
    client.post("/api/v1/tasks", json={"text": "错误"})
    resp = client.get("/health")
    assert resp.status_code == 200