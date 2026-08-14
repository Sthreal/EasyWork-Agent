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


def test_sheets_write_preview_in_confirmation(client, monkeypatch):
    import backend.tools.sheets as sheets_mod

    monkeypatch.setattr(
        sheets_mod.SheetTool,
        "find_cell",
        lambda self, filename, key_column, key_value, field, header_row=1: {"row": 2, "column": "B", "old": "13800000000"},
    )
    monkeypatch.setattr(
        task_api,
        "plan",
        lambda text: {
            "tasks": [
                {"action": "更新电话", "target": "报名表", "params": "", "high_risk": True, "tool": "sheets",
                 "args": {"action": "write_by_key", "filename": "报名表.xlsx", "key_column": "姓名", "key_value": "张三", "field": "电话", "value": "13866667777"}}
            ],
            "question": None,
        },
    )
    resp = client.post("/api/v1/tasks", json={"text": "把张三电话改为13866667777"})
    assert resp.status_code == 200
    item = resp.json()["tasks"][0]
    assert item["status"] == "pending_confirm"
    assert item["confirmation_id"] is not None
    # 确认记录 params 应包含预览（通过待确认列表接口验证）
    pending = client.get("/api/v1/confirmations").json()["items"]
    assert any("将修改" in p["params"] and "第2行B列" in p["params"] for p in pending)


def test_sheets_write_locate_failure_marks_failed(client, monkeypatch):
    import backend.tools.sheets as sheets_mod

    def boom(self, filename, key_column, key_value, field, header_row=1):
        raise ValueError("找不到表头：电话")

    monkeypatch.setattr(sheets_mod.SheetTool, "find_cell", boom)
    monkeypatch.setattr(
        task_api,
        "plan",
        lambda text: {
            "tasks": [
                {"action": "更新电话", "target": "报名表", "params": "", "high_risk": True, "tool": "sheets",
                 "args": {"action": "write_by_key", "filename": "报名表.xlsx", "key_column": "姓名", "key_value": "张三", "field": "电话", "value": "138"}}
            ],
            "question": None,
        },
    )
    resp = client.post("/api/v1/tasks", json={"text": "把张三电话改了"})
    assert resp.status_code == 200
    item = resp.json()["tasks"][0]
    assert item["status"] == "failed"
    assert "找不到表头" in item["result"]


def test_create_task_with_user_and_filter(client, monkeypatch):
    monkeypatch.setattr(task_api, "plan", lambda text: {
        "tasks": [{"action": "读取", "target": "报名表", "params": "", "high_risk": False, "tool": "sheets",
                   "args": {"action": "read", "filename": "报名表.xlsx"}}],
        "question": None,
    })
    monkeypatch.setattr(task_api, "execute_item", lambda item_id, **kwargs: {"ok": True, "message": "done", "data": {}})
    resp = client.post("/api/v1/tasks", json={"text": "读取报名表内容", "user_id": 7})
    assert resp.status_code == 200
    hist7 = client.get("/api/v1/tasks", params={"user_id": 7}).json()["items"]
    assert any(i["task_id"] == resp.json()["task_id"] for i in hist7)
    hist8 = client.get("/api/v1/tasks", params={"user_id": 8}).json()["items"]
    assert not any(i["task_id"] == resp.json()["task_id"] for i in hist8)


def test_dedup_scoped_by_user(client, monkeypatch):
    calls = {"n": 0}

    def fake_plan(text):
        calls["n"] += 1
        return {"tasks": [{"action": "读取", "target": "报名表", "params": "", "high_risk": False, "tool": "sheets",
                           "args": {"action": "read", "filename": "报名表.xlsx"}}], "question": None}

    monkeypatch.setattr(task_api, "plan", fake_plan)
    monkeypatch.setattr(task_api, "execute_item", lambda item_id, **kwargs: {"ok": True, "message": "done", "data": {}})
    r1 = client.post("/api/v1/tasks", json={"text": "读取报名表内容", "user_id": 7})
    r2 = client.post("/api/v1/tasks", json={"text": "读取报名表内容", "user_id": 7})
    assert r1.json()["task_id"] == r2.json()["task_id"]
    assert calls["n"] == 1
    r3 = client.post("/api/v1/tasks", json={"text": "读取报名表内容", "user_id": 8})
    assert r3.json()["task_id"] != r1.json()["task_id"]
    assert calls["n"] == 2
