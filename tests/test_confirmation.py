"""测试：确认接口。"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.db import Base, get_db
from backend.main import app
from backend.models import confirmation, feishu_token, task, user  # noqa: F401 注册模型
from backend.safety import gate


@pytest.fixture()
def engine():
    return create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )


@pytest.fixture()
def client(engine):
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


def test_pending_list_and_decide(engine, client):
    session = sessionmaker(bind=engine)()
    gate.create_confirmation(session, task_id=1, action="发送邮件", target="项目组")
    session.close()

    resp = client.get("/api/v1/confirmations")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    cid = items[0]["id"]

    resp2 = client.post(f"/api/v1/confirmations/{cid}/decide", json={"approve": True})
    assert resp2.status_code == 200
    assert resp2.json()["status"] == "approved"

    resp3 = client.get("/api/v1/confirmations")
    assert resp3.json()["items"] == []


def test_decide_not_found(client):
    resp = client.post("/api/v1/confirmations/999/decide", json={"approve": True})
    assert resp.status_code == 404