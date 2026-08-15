"""用户接口（邮箱绑定）。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.db import get_db
from backend.models.user import User
from backend.schemas.user import (
    MailConfigResponse,
    MailConfigSaveRequest,
    MailTestRequest,
    MailTestResponse,
)
from backend.security import get_current_user

router = APIRouter(prefix="/users")


def _resolve(db: Session, user_id: int | None, current_user: int | None) -> User:
    uid = current_user if current_user is not None else user_id
    if uid is None:
        raise HTTPException(status_code=401, detail="未提供身份")
    user = db.get(User, uid)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


@router.get("/me/mail", response_model=MailConfigResponse)
def get_mail(
    user_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: int | None = Depends(get_current_user),
):
    user = _resolve(db, user_id, current_user)
    return MailConfigResponse(
        qq_mail_address=user.qq_mail_address,
        qq_mail_auth_code_masked=_mask(user.qq_mail_auth_code),
    )


@router.put("/me/mail", response_model=MailConfigResponse)
def save_mail(
    payload: MailConfigSaveRequest,
    db: Session = Depends(get_db),
    current_user: int | None = Depends(get_current_user),
):
    if "@" not in payload.qq_mail_address:
        raise HTTPException(status_code=422, detail="邮箱格式不正确")
    user = _resolve(db, payload.user_id, current_user)
    user.qq_mail_address = payload.qq_mail_address.strip()
    user.qq_mail_auth_code = payload.qq_mail_auth_code.strip()
    db.commit()
    return MailConfigResponse(
        qq_mail_address=user.qq_mail_address,
        qq_mail_auth_code_masked=_mask(user.qq_mail_auth_code),
    )


@router.post("/me/mail/test", response_model=MailTestResponse)
def test_mail(
    payload: MailTestRequest,
    db: Session = Depends(get_db),
    current_user: int | None = Depends(get_current_user),
):
    _resolve(db, payload.user_id, current_user)
    from backend.tools.email import EmailTool

    result = EmailTool().send(
        subject="邮箱配置测试",
        to=payload.qq_mail_address,
        body="这是一封来自办公自动化 Agent 的配置测试邮件，收到即表示你的邮箱配置可用。",
        mail_address=payload.qq_mail_address,
        mail_auth_code=payload.qq_mail_auth_code,
    )
    return MailTestResponse(ok=result.ok, message=result.message)


def _mask(code: str) -> str:
    if not code:
        return ""
    if len(code) <= 4:
        return "*" * len(code)
    return code[:4] + "*" * (len(code) - 4)