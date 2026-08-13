"""测试：应用入口与健康检查。"""
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_api_prefix_works():
    resp = client.get("/api/v1/tasks")
    assert resp.status_code == 200
