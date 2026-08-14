"""测试：执行编排。"""

import json



import pytest



from backend.agent import executor

from backend.models.task import TaskItem





class FakeTool:

    name = "fake"



    def execute(self, **kwargs):

        from backend.tools.base import ToolResult

        return ToolResult(ok=True, message="done", data=kwargs)





def test_run_with_missing_args(monkeypatch):

    monkeypatch.setattr(executor, "get_tool", lambda name: FakeTool())

    item = TaskItem(tool="email", args=json.dumps({"action": "send", "to": ""}))

    result = executor._run(item)

    assert result["ok"] is False

    assert "参数不足" in result["message"]





def test_run_unknown_tool(monkeypatch):

    monkeypatch.setattr(executor, "get_tool", lambda name: None)

    item = TaskItem(tool="ghost", args="{}")

    result = executor._run(item)

    assert result["ok"] is False

    assert "无法识别工具" in result["message"]





def test_run_success(monkeypatch):

    monkeypatch.setattr(executor, "get_tool", lambda name: FakeTool())

    item = TaskItem(tool="email", args=json.dumps({"action": "read"}))

    result = executor._run(item)

    assert result["ok"] is True

    assert result["message"] == "done"





def test_calendar_normalize():

    item = TaskItem(tool="calendar", args=json.dumps({"action": "create", "summary": "开会", "start_ts": "2026-08-14T15:00", "end_ts": "2026-08-14T16:00"}))

    args = json.loads(item.args)

    executor._normalize("calendar", args)

    assert isinstance(args["start_ts"], int)

def test_run_email_injects_user_mail(monkeypatch):
    from backend.agent import executor
    from backend.models.task import Task, TaskItem
    from backend.models.user import User
    from backend.db import Base as _B, SessionLocal as _SL
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    _B.metadata.create_all(bind=engine)
    monkeypatch.setattr(executor, "SessionLocal", testing_session)

    session = testing_session()
    u = User(feishu_open_id="ou_x", name="x", qq_mail_address="mine@qq.com", qq_mail_auth_code="secret123")
    session.add(u)
    session.flush()
    t = Task(user_id=u.id, text="发邮件", status="planned")
    session.add(t)
    session.flush()
    item = TaskItem(task_id=t.id, action="发送邮件", tool="email", args='{"action": "send", "to": "a@b.com", "subject": "s", "body": "b"}')
    session.add(item)
    session.flush()
    session.commit()
    item_id = item.id
    session.close()

    captured = {}

    class FakeTool:
        def execute(self, **kwargs):
            captured.update(kwargs)
            from backend.tools.base import ToolResult
            return ToolResult(ok=True, message="sent")

    monkeypatch.setattr(executor, "get_tool", lambda name: FakeTool())
    executor.execute_item(item_id)
    assert captured.get("mail_address") == "mine@qq.com"
    assert captured.get("mail_auth_code") == "secret123"


def test_run_email_fallback_no_binding(monkeypatch):
    from backend.agent import executor
    from backend.models.task import Task, TaskItem
    from backend.models.user import User
    from backend.db import Base as _B
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    _B.metadata.create_all(bind=engine)
    monkeypatch.setattr(executor, "SessionLocal", testing_session)

    session = testing_session()
    u = User(feishu_open_id="ou_y", name="y", qq_mail_address="", qq_mail_auth_code="")
    session.add(u)
    session.flush()
    t = Task(user_id=u.id, text="发邮件", status="planned")
    session.add(t)
    session.flush()
    item = TaskItem(task_id=t.id, action="发送邮件", tool="email", args='{"action": "send", "to": "a@b.com", "subject": "s", "body": "b"}')
    session.add(item)
    session.flush()
    session.commit()
    item_id = item.id
    session.close()

    captured = {}

    class FakeTool2:
        def execute(self, **kwargs):
            captured.update(kwargs)
            from backend.tools.base import ToolResult
            return ToolResult(ok=True, message="sent")

    monkeypatch.setattr(executor, "get_tool", lambda name: FakeTool2())
    executor.execute_item(item_id)
    assert "mail_address" not in captured
