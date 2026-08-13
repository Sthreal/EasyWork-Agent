"""飞书 API 客户端（统一封装调用）。"""
import httpx

from config.settings import settings

FEISHU_OPEN_BASE = "https://open.feishu.cn/open-apis"
FEISHU_ACCOUNTS_BASE = "https://accounts.feishu.cn/open-apis"
FEISHU_OAUTH_TOKEN_URL = "https://accounts.feishu.cn/oauth/v3/token"


class FeishuError(RuntimeError):
    """飞书接口调用失败。"""


class FeishuClient:
    """飞书接口客户端：换取令牌、刷新令牌、获取用户信息。"""

    def __init__(self, app_id: str = "", app_secret: str = ""):
        self.app_id = app_id or settings.feishu_app_id
        self.app_secret = app_secret or settings.feishu_app_secret

    def get_user_access_token(self, code: str) -> dict:
        """用授权码换 user_access_token（新版 OAuth2：POST /oauth/v3/token）。"""
        resp = httpx.post(
            FEISHU_OAUTH_TOKEN_URL,
            json={
                "grant_type": "authorization_code",
                "client_id": self.app_id,
                "client_secret": self.app_secret,
                "code": code,
                "redirect_uri": settings.feishu_redirect_uri,
            },
            timeout=10,
        )
        body = _unwrap(resp, "换取 user_access_token")
        return {
            "access_token": body["access_token"],
            "refresh_token": body.get("refresh_token", ""),
            "expires_in": int(body.get("expires_in", 7200)),
        }

    def refresh_user_access_token(self, refresh_token: str) -> dict:
        """用 refresh_token 换新令牌（refresh_token 只能用一次，响应会返回新的）。"""
        resp = httpx.post(
            FEISHU_OAUTH_TOKEN_URL,
            json={
                "grant_type": "refresh_token",
                "client_id": self.app_id,
                "client_secret": self.app_secret,
                "refresh_token": refresh_token,
            },
            timeout=10,
        )
        body = _unwrap(resp, "刷新 user_access_token")
        return {
            "access_token": body["access_token"],
            "refresh_token": body.get("refresh_token", ""),
            "expires_in": int(body.get("expires_in", 7200)),
        }

    def get_user_info(self, access_token: str) -> dict:
        """用 user_access_token 获取用户信息（GET /authen/v1/user_info）。"""
        resp = httpx.get(
            f"{FEISHU_OPEN_BASE}/authen/v1/user_info",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        data = _unwrap(resp, "获取用户信息")["data"]
        return {
            "open_id": data["open_id"],
            "name": data.get("name", ""),
            "avatar_url": data.get("avatar_url", ""),
        }


def _unwrap(resp: httpx.Response, context: str = "") -> dict:
    resp.raise_for_status()
    try:
        body = resp.json()
    except ValueError:
        raise FeishuError(f"飞书接口响应不是 JSON（{context}）：{resp.text[:200]}") from None
    if body.get("code", 0) != 0:
        msg = body.get("msg") or body.get("error_description") or body.get("error") or ""
        raise FeishuError(f"飞书接口错误（{context}）：code={body.get('code')}, msg={msg!r}, body={body}")
    return body