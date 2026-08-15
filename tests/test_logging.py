"""测试：日志记录与统一异常处理。"""
import logging

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.db import Base, get_db
from backend.main import app
from backend.models import audit, confirmation, feishu_token, task, user  # noqa: F401 注册模型
from config.logging import setup_logging
import backend.services.task_service as task_service


@pytest.fixture()
def log_file(tmp_path):
    return tmp_path / "app.log"


@pytest.fixture()
def client(log_file):
    setup_logging(log_file=log_file, level=logging.INFO)
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
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()


def test_request_written_to_log_file(client, log_file):
    resp = client.get("/health")
    assert resp.status_code == 200
    content = log_file.read_text(encoding="utf-8")
    assert "GET /health -> 200" in content


def test_unexpected_error_logged_and_returns_500(client, log_file, monkeypatch):
    def boom(text):
        raise RuntimeError("人造错误 boom")

    monkeypatch.setattr(task_service, "plan", boom)
    resp = client.post("/api/v1/tasks", json={"text": "制造错误"})
    assert resp.status_code == 500
    content = log_file.read_text(encoding="utf-8")
    assert "boom" in content