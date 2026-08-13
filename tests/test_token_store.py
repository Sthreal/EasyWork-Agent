"""测试：令牌存取与刷新。"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.db import Base
from backend.feishu import token_store
from backend.feishu.client import FeishuError
from backend.models.feishu_token import FeishuToken


@pytest.fixture()
def db():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = testing_session()
    yield session
    session.close()


def test_fresh_token_no_refresh(db, monkeypatch):
    token_store.save_token(db, user_id=1, token={"access_token": "a1", "refresh_token": "r1", "expires_in": 7200})

    def boom(*args, **kwargs):
        raise AssertionError("未过期不应调用刷新")

    monkeypatch.setattr(token_store.FeishuClient, "refresh_user_access_token", boom)
    row = token_store.get_valid_token(db, 1)
    assert row.access_token == "a1"


def test_expired_token_auto_refresh(db, monkeypatch):
    token_store.save_token(db, user_id=1, token={"access_token": "a1", "refresh_token": "r1", "expires_in": -100})

    monkeypatch.setattr(
        token_store.FeishuClient,
        "refresh_user_access_token",
        lambda self, refresh_token: {"access_token": "a2", "refresh_token": "r2", "expires_in": 7200},
    )
    row = token_store.get_valid_token(db, 1)
    assert row.access_token == "a2"
    assert row.refresh_token == "r2"
    # 旋转：旧记录保留，新记录追加
    rows = db.query(FeishuToken).filter_by(user_id=1).order_by(FeishuToken.id).all()
    assert len(rows) == 2


def test_expired_without_refresh_token_raises(db):
    token_store.save_token(db, user_id=1, token={"access_token": "a1", "refresh_token": "", "expires_in": -100})
    with pytest.raises(FeishuError):
        token_store.get_valid_token(db, 1)


def test_no_token_raises(db):
    with pytest.raises(FeishuError):
        token_store.get_valid_token(db, 99)