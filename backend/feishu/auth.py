"""飞书登录/授权（OAuth 流程）。"""
from urllib.parse import urlencode

from config.settings import settings
from backend.feishu.client import FEISHU_ACCOUNTS_BASE, FeishuClient

# offline_access：授权时声明，换取 refresh_token（用于 M1-4 令牌刷新）
OAUTH_SCOPE = "offline_access calendar:calendar:readonly calendar:calendar"


def build_authorize_url(state: str = "") -> str:
    """生成飞书授权页 URL。"""
    params = {
        "client_id": settings.feishu_app_id,
        "response_type": "code",
        "redirect_uri": settings.feishu_redirect_uri,
        "state": state,
        "scope": OAUTH_SCOPE,
    }
    return f"{FEISHU_ACCOUNTS_BASE}/authen/v1/authorize?{urlencode(params)}"


def exchange_code(code: str) -> dict:
    """用授权码换取令牌并获取用户信息。"""
    client = FeishuClient()
    token = client.get_user_access_token(code)
    user_info = client.get_user_info(token["access_token"])
    return {"token": token, "user_info": user_info}