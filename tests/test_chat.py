"""测试：聊天消息持久化接口。"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.db import Base, get_db
from backend.main import app
from backend.models import chat_message, confirmation, feishu_token, task, user  # noqa: F401 注册模型


@pytest.fixture()
def client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
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


def test_save_and_list(client):
    r1 = client.post("/api/v1/chat/messages", json={"user_id": 1, "role": "user", "text": "统计报名表"})
    assert r1.status_code == 200
    r2 = client.post(
        "/api/v1/chat/messages",
        json={"user_id": 1, "role": "agent", "text": "", "payload": {"task_id": "9", "status": "executed"}},
    )
    assert r2.status_code == 200

    resp = client.get("/api/v1/chat/messages?user_id=1")
    items = resp.json()["items"]
    assert len(items) == 2
    assert items[0]["role"] == "user"
    assert items[0]["text"] == "统计报名表"
    assert items[1]["role"] == "agent"
    assert items[1]["payload"]["status"] == "executed"


def test_order_and_limit(client):
    for i in range(5):
        client.post("/api/v1/chat/messages", json={"user_id": 1, "role": "user", "text": f"msg-{i}"})

    resp = client.get("/api/v1/chat/messages?user_id=1&limit=3")
    items = resp.json()["items"]
    assert len(items) == 3
    # 正序：取最近 3 条（msg-2, msg-3, msg-4）
    assert [it["text"] for it in items] == ["msg-2", "msg-3", "msg-4"]


def test_user_isolation(client):
    client.post("/api/v1/chat/messages", json={"user_id": 1, "role": "user", "text": "a"})
    client.post("/api/v1/chat/messages", json={"user_id": 2, "role": "user", "text": "b"})

    r1 = client.get("/api/v1/chat/messages?user_id=1")
    assert len(r1.json()["items"]) == 1
    assert r1.json()["items"][0]["text"] == "a"

    r2 = client.get("/api/v1/chat/messages?user_id=2")
    assert len(r2.json()["items"]) == 1
    assert r2.json()["items"][0]["text"] == "b"
