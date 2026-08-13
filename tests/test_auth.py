"""测试：飞书登录（mock 飞书接口）。"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.db import Base, get_db
from backend.main import app
from backend.models import feishu_token, user  # noqa: F401 注册模型
import backend.feishu.auth as feishu_auth
import backend.api.v1.auth as api_auth


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


def test_login_redirect(client, monkeypatch):
    monkeypatch.setattr(feishu_auth.settings, "feishu_app_id", "cli_test")
    monkeypatch.setattr(
        feishu_auth.settings,
        "feishu_redirect_uri",
        "http://localhost:8000/api/v1/auth/callback",
    )
    resp = client.get("/api/v1/auth/login", follow_redirects=False)
    assert resp.status_code in (302, 307)
    url = resp.headers["location"]
    assert "accounts.feishu.cn/open-apis/authen/v1/authorize" in url
    assert "client_id=cli_test" in url
    assert "redirect_uri=" in url


def test_callback_creates_user(client, monkeypatch):
    def fake_exchange(code):
        return {
            "token": {"access_token": "t1", "refresh_token": "r1", "expires_in": 7200},
            "user_info": {"open_id": "ou_test", "name": "测试用户", "avatar_url": "http://avatar"},
        }

    monkeypatch.setattr(api_auth, "exchange_code", fake_exchange)

    resp = client.get("/api/v1/auth/callback", params={"code": "code123"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["open_id"] == "ou_test"
    assert body["name"] == "测试用户"
    assert body["user_id"] == 1

    resp2 = client.get("/api/v1/auth/callback", params={"code": "code456"})
    assert resp2.status_code == 200
    assert resp2.json()["user_id"] == body["user_id"]


def test_status_reflects_env(client, monkeypatch):
    monkeypatch.setattr(feishu_auth.settings, "feishu_app_id", "")
    monkeypatch.setattr(feishu_auth.settings, "feishu_app_secret", "")
    resp = client.get("/api/v1/auth/status")
    assert resp.status_code == 200
    assert resp.json()["configured"] is False