"""测试：任务接口。"""
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_create_task_returns_pending():
    resp = client.post("/api/v1/tasks", json={"text": "给项目组发邮件"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "pending"
    assert body["text"] == "给项目组发邮件"
    assert body["task_id"]


def test_create_task_rejects_empty():
    resp = client.post("/api/v1/tasks", json={"text": ""})
    assert resp.status_code == 422