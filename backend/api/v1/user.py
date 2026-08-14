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

router = APIRouter(prefix="/users")


@router.get("/me/mail", response_model=MailConfigResponse)
def get_mail(user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    return MailConfigResponse(
        qq_mail_address=user.qq_mail_address,
        qq_mail_auth_code_masked=_mask(user.qq_mail_auth_code),
    )


@router.put("/me/mail", response_model=MailConfigResponse)
def save_mail(payload: MailConfigSaveRequest, db: Session = Depends(get_db)):
    if "@" not in payload.qq_mail_address:
        raise HTTPException(status_code=422, detail="邮箱格式不正确")
    user = db.get(User, payload.user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.qq_mail_address = payload.qq_mail_address.strip()
    user.qq_mail_auth_code = payload.qq_mail_auth_code.strip()
    db.commit()
    return MailConfigResponse(
        qq_mail_address=user.qq_mail_address,
        qq_mail_auth_code_masked=_mask(user.qq_mail_auth_code),
    )


@router.post("/me/mail/test", response_model=MailTestResponse)
def test_mail(payload: MailTestRequest, db: Session = Depends(get_db)):
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