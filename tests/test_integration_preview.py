"""集成测试：高危改表格任务 → 确认记录携带结构化 diff 预览（切片A端到端）。"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.db import Base, get_db
from backend.main import app
from backend.models import confirmation, feishu_token, task, user  # noqa: F401 注册模型

import backend.services.task_service as task_service


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


def test_high_risk_sheet_task_creates_confirmation_with_preview(client, monkeypatch, tmp_path):
    from backend.tools import sheets as sheets_mod

    csv_path = tmp_path / "报名表.csv"
    csv_path.write_text("姓名,电话\n张三,138\n李四,139\n", encoding="utf-8")
    monkeypatch.setattr(sheets_mod, "DATA_DIR", tmp_path)

    def fake_plan(user_text):
        return {
            "tasks": [
                {
                    "action": "修改表格",
                    "target": "报名表.csv",
                    "params": "",
                    "high_risk": True,
                    "tool": "sheets",
                    "args": {
                        "action": "write_by_key",
                        "filename": "报名表.csv",
                        "key_column": "姓名",
                        "key_value": "张三",
                        "field": "电话",
                        "value": "1380000",
                    },
                }
            ],
            "question": None,
        }

    monkeypatch.setattr(task_service, "plan", fake_plan)
    monkeypatch.setattr(task_service, "should_continue", lambda *a, **k: {"done": True, "tasks": []})

    resp = client.post("/api/v1/tasks", json={"text": "把张三的电话改成1380000"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "pending_confirm"
    step = body["tasks"][0]
    assert step["in_workspace"] is True
    assert step["preview"] == [{"row": 2, "column": "B", "old": "138", "new": "1380000"}]

    # 工作区确认不在待确认队列
    resp2 = client.get("/api/v1/confirmations")
    assert resp2.json()["items"] == []

    # 稍后 → 进入待确认队列，确认页可看到 diff 预览
    resp3 = client.post(f"/api/v1/confirmations/{step['confirmation_id']}/defer")
    assert resp3.status_code == 200
    resp4 = client.get("/api/v1/confirmations")
    items = resp4.json()["items"]
    assert len(items) == 1
    assert items[0]["preview"] == [{"row": 2, "column": "B", "old": "138", "new": "1380000"}]