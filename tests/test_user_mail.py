"""测试：用户邮箱绑定。"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.db import Base, get_db
from backend.main import app
from backend.models import confirmation, feishu_token, task, user  # noqa: F401 注册模型
import backend.api.v1.user as user_api


@pytest.fixture()
def env(monkeypatch):
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
    session = testing_session()
    u = user.User(feishu_open_id="ou_mail", name="邮箱测试", qq_mail_address="", qq_mail_auth_code="")
    session.add(u)
    session.commit()
    session.refresh(u)
    uid = u.id
    session.close()
    client = TestClient(app)
    yield client, uid
    app.dependency_overrides.clear()


def test_save_and_masked_read(env):
    client, uid = env
    resp = client.put("/api/v1/users/me/mail", json={
        "user_id": uid, "qq_mail_address": "me@qq.com", "qq_mail_auth_code": "abcdefgh1234",
    })
    assert resp.status_code == 200
    assert resp.json()["qq_mail_address"] == "me@qq.com"
    assert "*" in resp.json()["qq_mail_auth_code_masked"]
    assert "abcdefgh1234" not in resp.json()["qq_mail_auth_code_masked"]

    got = client.get("/api/v1/users/me/mail", params={"user_id": uid}).json()
    assert got["qq_mail_address"] == "me@qq.com"
    assert "abcdefgh1234" not in got["qq_mail_auth_code_masked"]


def test_save_invalid_email(env):
    client, uid = env
    resp = client.put("/api/v1/users/me/mail", json={
        "user_id": uid, "qq_mail_address": "not-an-email", "qq_mail_auth_code": "abcd1234",
    })
    assert resp.status_code == 422


def test_test_mail_endpoint(env, monkeypatch):
    client, uid = env
    monkeypatch.setattr(
        user_api.EmailTool if hasattr(user_api, "EmailTool") else None,  # 占位，下面直接替换模块
        "send",
        lambda self, **kwargs: __import__("backend.tools.base", fromlist=["ToolResult"]).ToolResult(
            ok=True, message="测试邮件已发送"
        ),
    ) if hasattr(user_api, "EmailTool") else None
    # 直接 monkeypatch email 工具
    import backend.tools.email as email_mod
    monkeypatch.setattr(
        email_mod.EmailTool,
        "send",
        lambda self, subject, to, body, mail_address=None, mail_auth_code=None: __import__(
            "backend.tools.base", fromlist=["ToolResult"]
        ).ToolResult(ok=True, message=f"已用 {mail_address} 发送"),
    )
    resp = client.post("/api/v1/users/me/mail/test", json={
        "user_id": uid, "qq_mail_address": "me@qq.com", "qq_mail_auth_code": "abcd1234",
    })
    assert resp.status_code == 200
    assert resp.json()["ok"] is True
    assert "me@qq.com" in resp.json()["message"]