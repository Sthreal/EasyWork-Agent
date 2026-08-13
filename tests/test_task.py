"""测试：任务接口。"""
from fastapi.testclient import TestClient

from backend.main import app
import backend.api.v1.task as task_api

client = TestClient(app)


def test_create_task_returns_planned_tasks(monkeypatch):
    monkeypatch.setattr(
        task_api,
        "plan",
        lambda text: [
            {"action": "写邮件", "target": "项目组", "params": "", "high_risk": False},
            {"action": "发送邮件", "target": "项目组", "params": "", "high_risk": True},
        ],
    )
    resp = client.post("/api/v1/tasks", json={"text": "给项目组发邮件"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "planned"
    assert body["text"] == "给项目组发邮件"
    assert len(body["tasks"]) == 2
    assert body["tasks"][1]["high_risk"] is True
    assert body["task_id"]


def test_create_task_rejects_empty():
    resp = client.post("/api/v1/tasks", json={"text": ""})
    assert resp.status_code == 422