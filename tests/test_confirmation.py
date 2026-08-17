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
import backend.api.v1.confirmation as conf_api


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
    gate.create_confirmation(session, task_id=1, action="发送邮件", target="项目组", in_workspace=False)
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


def test_decide_approve_triggers_execution(engine, client, monkeypatch):
    session = sessionmaker(bind=engine)()
    row = gate.create_confirmation(session, task_id=1, task_item_id=5, action="发送邮件", target="项目组")
    session.close()
    monkeypatch.setattr(
        conf_api,
        "execute_item",
        lambda item_id: {"ok": True, "message": "已执行", "data": {}},
    )
    resp = client.post(f"/api/v1/confirmations/{row.id}/decide", json={"approve": True})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "approved"
    assert body["execution_result"]["ok"] is True

def test_decide_idempotent(engine, client, monkeypatch):
    session = sessionmaker(bind=engine)()
    row = gate.create_confirmation(session, task_id=1, task_item_id=7, action="发送邮件", target="项目组")
    session.close()
    calls = {"n": 0}

    def fake_execute(item_id):
        calls["n"] += 1
        return {"ok": True, "message": "已执行", "data": {}}

    monkeypatch.setattr(conf_api, "execute_item", fake_execute)
    r1 = client.post(f"/api/v1/confirmations/{row.id}/decide", json={"approve": True})
    assert r1.status_code == 200
    r2 = client.post(f"/api/v1/confirmations/{row.id}/decide", json={"approve": True})
    assert r2.status_code == 200
    assert r2.json()["status"] == "approved"
    assert calls["n"] == 1


def test_decide_cross_user_forbidden(engine, client):
    from backend.models.task import Task

    session = sessionmaker(bind=engine)()
    task = Task(user_id=7, text="改表格", status="planned")
    session.add(task)
    session.flush()
    conf = gate.create_confirmation(session, task_id=task.id, action="发送邮件", target="项目组", task_item_id=None)
    session.close()

    r_other = client.post(f"/api/v1/confirmations/{conf.id}/decide", json={"approve": True, "user_id": 8})
    assert r_other.status_code == 403

    r_owner = client.post(f"/api/v1/confirmations/{conf.id}/decide", json={"approve": True, "user_id": 7})
    assert r_owner.status_code == 200
    assert r_owner.json()["status"] == "approved"


def test_confirmation_response_includes_preview(engine, client):
    session = sessionmaker(bind=engine)()
    gate.create_confirmation(
        session,
        task_id=1,
        action="修改表格",
        target="报名表.xlsx",
        params="将修改 报名表.xlsx：姓名=张三 的 电话，138 → 139",
        preview='[{"row": 2, "column": "B", "old": "138", "new": "139"}]',
        in_workspace=False,
    )
    session.close()

    resp = client.get("/api/v1/confirmations")
    assert resp.status_code == 200
    item = resp.json()["items"][0]
    assert item["preview"] == [{"row": 2, "column": "B", "old": "138", "new": "139"}]
    assert "138 → 139" in item["params"]


def test_migration_adds_preview_column(tmp_path):
    from sqlalchemy import create_engine, text

    from backend.db_migrate import ensure_confirmations_preview

    db_file = tmp_path / "old.db"
    engine = create_engine(f"sqlite:///{db_file}")
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE confirmations (id INTEGER PRIMARY KEY, params TEXT)"))
    ensure_confirmations_preview(engine)
    with engine.connect() as conn:
        cols = [row[1] for row in conn.execute(text("PRAGMA table_info(confirmations)"))]
    assert "preview" in cols



def test_workspace_confirm_not_in_queue_until_defer(engine, client):
    session = sessionmaker(bind=engine)()
    row = gate.create_confirmation(session, task_id=1, action="修改表格", target="报名表.xlsx")
    session.close()

    # 刚产生在工作区：队列为空
    resp = client.get("/api/v1/confirmations")
    assert resp.json()["items"] == []

    # 稍后 → 进入队列
    resp2 = client.post(f"/api/v1/confirmations/{row.id}/defer")
    assert resp2.status_code == 200
    assert resp2.json()["in_workspace"] is False
    assert resp2.json()["deferred_at"] is not None

    resp3 = client.get("/api/v1/confirmations")
    items = resp3.json()["items"]
    assert len(items) == 1
    assert items[0]["id"] == row.id


def test_defer_idempotent(engine, client):
    session = sessionmaker(bind=engine)()
    row = gate.create_confirmation(session, task_id=1, action="修改表格", target="报名表.xlsx")
    session.close()

    r1 = client.post(f"/api/v1/confirmations/{row.id}/defer")
    r2 = client.post(f"/api/v1/confirmations/{row.id}/defer")
    assert r1.status_code == 200 and r2.status_code == 200
    assert r2.json()["in_workspace"] is False


def test_defer_not_found(client):
    resp = client.post("/api/v1/confirmations/999/defer")
    assert resp.status_code == 404


def test_expired_workspace_auto_moves_to_queue(engine, client):
    from datetime import datetime, timedelta

    session = sessionmaker(bind=engine)()
    row = gate.create_confirmation(session, task_id=1, action="修改表格", target="报名表.xlsx")
    row_id = row.id
    row.created_at = datetime.utcnow() - timedelta(minutes=6)
    session.commit()
    session.close()

    # 查询队列时惰性迁移：工作区超 5 分钟未操作 → 自动进队列
    resp = client.get("/api/v1/confirmations")
    items = resp.json()["items"]
    assert len(items) == 1
    assert items[0]["id"] == row_id
    assert items[0]["in_workspace"] is False
    assert items[0]["deferred_at"] is not None
