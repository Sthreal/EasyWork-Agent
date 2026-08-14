"""测试：增强功能（筛选/分页/force/is_expired/任务状态聚合）。"""
import json
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.db import Base, get_db
from backend.main import app
from backend.models import confirmation, feishu_token, task, user  # noqa: F401 注册模型
from backend.models.task import Task, TaskItem
from backend.safety.gate import create_confirmation
import backend.api.v1.task as task_api
import backend.api.v1.confirmation as conf_api
import backend.agent.task_status as task_status


@pytest.fixture()
def env(monkeypatch):
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    monkeypatch.setattr("backend.agent.executor.SessionLocal", testing_session)

    def override_get_db():
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app, raise_server_exceptions=False)
    yield client, testing_session
    app.dependency_overrides.clear()


def _post_ok(monkeypatch, items, question=None):
    def fake_plan(text):
        return {"tasks": items, "question": question}

    monkeypatch.setattr(task_api, "plan", fake_plan)
    monkeypatch.setattr(task_api, "execute_item", lambda item_id, **kwargs: {"ok": True, "message": "done", "data": {}})


def test_refresh_task_status_precedence(env):
    _, testing_session = env
    s = testing_session()

    def make(statuses):
        t = Task(user_id=1, text="x", status="planned")
        s.add(t)
        s.flush()
        for st in statuses:
            s.add(TaskItem(task_id=t.id, action="a", tool="email", status=st))
        s.flush()
        return t.id

    tid_pc = make(["executed", "pending_confirm"])
    assert task_status.refresh_task_status(s, tid_pc) == "pending_confirm"
    tid_rej = make(["executed", "rejected"])
    assert task_status.refresh_task_status(s, tid_rej) == "rejected"
    tid_fail = make(["executed", "failed"])
    assert task_status.refresh_task_status(s, tid_fail) == "failed"
    tid_ok = make(["executed"])
    assert task_status.refresh_task_status(s, tid_ok) == "executed"
    s.close()


def test_create_low_risk_all_success_executed(env, monkeypatch):
    client, _ = env
    _post_ok(
        monkeypatch,
        [{"action": "创建日程", "target": "", "params": "", "high_risk": False, "tool": "calendar",
          "args": {"action": "create", "summary": "开会", "start_ts": "2026-08-15T15:00", "end_ts": "2026-08-15T16:00"}}],
    )
    resp = client.post("/api/v1/tasks", json={"text": "创建日程"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "executed"


def test_force_bypass_dedup(env, monkeypatch):
    client, _ = env
    calls = {"n": 0}

    def fake_plan(text):
        calls["n"] += 1
        return {"tasks": [{"action": "读取", "target": "报名表", "params": "", "high_risk": False, "tool": "sheets",
                           "args": {"action": "read", "filename": "报名表.xlsx"}}], "question": None}

    monkeypatch.setattr(task_api, "plan", fake_plan)
    monkeypatch.setattr(task_api, "execute_item", lambda item_id, **kwargs: {"ok": True, "message": "done", "data": {}})
    r1 = client.post("/api/v1/tasks", json={"text": "读取报名表", "force": True})
    r2 = client.post("/api/v1/tasks", json={"text": "读取报名表", "force": True})
    assert r1.json()["task_id"] != r2.json()["task_id"]
    assert calls["n"] == 2


def test_list_filters_and_pagination(env):
    client, testing_session = env
    s = testing_session()
    now = datetime.utcnow()
    tasks = [
        Task(user_id=1, text="给张三发邮件", status="executed", created_at=now),
        Task(user_id=1, text="给李四建日程", status="pending_confirm", created_at=now - timedelta(days=1)),
        Task(user_id=1, text="读取报名表", status="need_clarify", created_at=now - timedelta(days=2)),
    ]
    s.add_all(tasks)
    s.commit()
    s.close()

    r = client.get("/api/v1/tasks", params={"user_id": 1, "q": "发邮件"}).json()
    assert r["total"] == 1
    assert "给张三发邮件" in r["items"][0]["text"]

    r = client.get("/api/v1/tasks", params={"user_id": 1, "status": "executed,rejected"}).json()
    assert r["total"] == 1

    r = client.get("/api/v1/tasks", params={"user_id": 1, "date_from": (now - timedelta(days=1)).strftime("%Y-%m-%d")}).json()
    assert r["total"] == 2

    r = client.get("/api/v1/tasks", params={"user_id": 1, "limit": 1, "offset": 0}).json()
    assert r["total"] == 3
    assert len(r["items"]) == 1


def test_confirmation_is_expired(env):
    client, testing_session = env
    s = testing_session()
    old = create_confirmation(s, task_id=None, action="发送邮件", target="旧", task_item_id=None)
    old.created_at = datetime.utcnow() - timedelta(minutes=31)
    new = create_confirmation(s, task_id=None, action="发送邮件", target="新", task_item_id=None)
    s.commit()
    old_id, new_id = old.id, new.id
    s.close()

    items = client.get("/api/v1/confirmations").json()["items"]
    by_id = {i["id"]: i for i in items}
    assert by_id[old_id]["is_expired"] is True
    assert by_id[new_id]["is_expired"] is False


def test_decide_reject_marks_rejected(env, monkeypatch):
    client, testing_session = env
    _post_ok(
        monkeypatch,
        [{"action": "发送邮件", "target": "项目组", "params": "", "high_risk": True, "tool": "email",
          "args": {"action": "send", "to": "a@b.com", "subject": "s"}}],
    )
    resp = client.post("/api/v1/tasks", json={"text": "发邮件"})
    cid = resp.json()["tasks"][0]["confirmation_id"]
    dec = client.post(f"/api/v1/confirmations/{cid}/decide", json={"approve": False})
    assert dec.status_code == 200
    assert dec.json()["status"] == "rejected"
    # 任务状态聚合为 rejected，子任务标记 rejected
    s = testing_session()
    item = s.query(TaskItem).order_by(TaskItem.id.desc()).first()
    assert item.status == "rejected"
    task_row = s.query(Task).filter(Task.id == item.task_id).first()
    assert task_row.status == "rejected"
    s.close()


def test_decide_approve_updates_status(env, monkeypatch):
    client, testing_session = env
    _post_ok(
        monkeypatch,
        [{"action": "发送邮件", "target": "项目组", "params": "", "high_risk": True, "tool": "email",
          "args": {"action": "send", "to": "a@b.com", "subject": "s"}}],
    )
    resp = client.post("/api/v1/tasks", json={"text": "发邮件"})
    cid = resp.json()["tasks"][0]["confirmation_id"]

    def fake_execute(item_id):
        s = testing_session()
        it = s.get(TaskItem, item_id)
        it.status = "executed"
        it.result = json.dumps({"ok": True, "message": "已执行"}, ensure_ascii=False)
        s.commit()
        s.close()
        return {"ok": True, "message": "已执行", "data": {}}

    monkeypatch.setattr(conf_api, "execute_item", fake_execute)
    dec = client.post(f"/api/v1/confirmations/{cid}/decide", json={"approve": True})
    assert dec.status_code == 200
    assert dec.json().get("execution_result", {}).get("ok") is True
    s = testing_session()
    item = s.query(TaskItem).order_by(TaskItem.id.desc()).first()
    task_row = s.query(Task).filter(Task.id == item.task_id).first()
    assert task_row.status == "executed"
    s.close()