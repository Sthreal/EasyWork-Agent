"""飞书 API 客户端（统一封装调用）。"""
import httpx

from config.settings import settings

FEISHU_OPEN_BASE = "https://open.feishu.cn/open-apis"
FEISHU_ACCOUNTS_BASE = "https://accounts.feishu.cn/open-apis"


class FeishuError(RuntimeError):
    """飞书接口调用失败。"""


class FeishuClient:
    """飞书接口客户端：换取令牌、获取用户信息。"""

    def __init__(self, app_id: str = "", app_secret: str = ""):
        self.app_id = app_id or settings.feishu_app_id
        self.app_secret = app_secret or settings.feishu_app_secret

    def get_user_access_token(self, code: str) -> dict:
        """用授权码换 user_access_token（POST /authen/v1/oidc/access_token）。"""
        resp = httpx.post(
            f"{FEISHU_OPEN_BASE}/authen/v1/oidc/access_token",
            json={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": self.app_id,
                "client_secret": self.app_secret,
            },
            timeout=10,
        )
        data = _unwrap(resp, "换取 user_access_token")
        return {
            "access_token": data["access_token"],
            "refresh_token": data.get("refresh_token", ""),
            "expires_in": int(data.get("expires_in", 7200)),
        }

    def get_user_info(self, access_token: str) -> dict:
        """用 user_access_token 获取用户信息（GET /authen/v1/user_info）。"""
        resp = httpx.get(
            f"{FEISHU_OPEN_BASE}/authen/v1/user_info",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        data = _unwrap(resp, "获取用户信息")
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
        raise FeishuError(
            f"飞书接口错误（{context}）：code={body.get('code')}, msg={body.get('msg')!r}, body={body}"
        )
    return body["data"]