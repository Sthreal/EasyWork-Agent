"""测试：日志记录与统一异常处理。"""
import logging

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from config.logging import setup_logging
import backend.services.task_service as task_service


@pytest.fixture()
def log_file(tmp_path):
    return tmp_path / "app.log"


@pytest.fixture()
def client(log_file):
    setup_logging(log_file=log_file, level=logging.INFO)
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


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