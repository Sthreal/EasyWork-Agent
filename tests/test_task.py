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

def test_high_risk_task_creates_confirmation(client, monkeypatch):
    monkeypatch.setattr(
        task_api,
        "plan",
        lambda text: {
            "tasks": [
                {
                    "action": "发送邮件",
                    "target": "项目组",
                    "params": "",
                    "high_risk": True,
                    "tool": "email",
                    "args": {"action": "send", "to": "a@b.com", "subject": "会议变更", "body": "改到3点"},
                }
            ],
            "question": None,
        },
    )
    resp = client.post("/api/v1/tasks", json={"text": "给项目组发邮件"})
    assert resp.status_code == 200
    task_item = resp.json()["tasks"][0]
    assert task_item["status"] == "pending_confirm"
    assert task_item["confirmation_id"] is not None


def test_low_risk_task_executes(client, monkeypatch):
    monkeypatch.setattr(task_api, "plan", lambda text: {
        "tasks": [
            {"action": "创建日程", "target": "", "params": "", "high_risk": False, "tool": "calendar",
             "args": {"action": "create", "summary": "开会", "start_ts": "2026-08-14T15:00", "end_ts": "2026-08-14T16:00"}}
        ],
        "question": None,
    })
    monkeypatch.setattr(
        task_api, "execute_item",
        lambda item_id, **kwargs: {"ok": True, "message": "已创建", "data": {"event_id": "e1"}},
    )
    resp = client.post("/api/v1/tasks", json={"text": "创建日程"})
    task_item = resp.json()["tasks"][0]
    assert task_item["status"] == "executed"

def test_duplicate_submission_reuses_result(client, monkeypatch):
    calls = {"n": 0}

    def fake_plan(text):
        calls["n"] += 1
        return {"tasks": [{"action": "创建日程", "target": "", "params": "", "high_risk": False,
                           "tool": "calendar",
                           "args": {"action": "create", "summary": "开会", "start_ts": "2026-08-14T15:00", "end_ts": "2026-08-14T16:00"}}],
                "question": None}

    monkeypatch.setattr(task_api, "plan", fake_plan)
    monkeypatch.setattr(task_api, "execute_item", lambda item_id, **kwargs: {"ok": True, "message": "done", "data": {}})
    r1 = client.post("/api/v1/tasks", json={"text": "创建开会日程"})
    r2 = client.post("/api/v1/tasks", json={"text": "创建开会日程"})
    assert r1.json()["task_id"] == r2.json()["task_id"]
    assert calls["n"] == 1


def test_max_rounds(client, monkeypatch):
    monkeypatch.setattr(task_api, "plan", lambda text: {"tasks": [], "question": "你想处理什么？"})
    resp = client.post("/api/v1/tasks", json={"text": "帮我处理一下", "round": 4})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "too_many_rounds"
    assert "上限" in body["message"]
