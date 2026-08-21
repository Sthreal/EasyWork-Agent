"""大模型统一封装（全项目只此一处调模型）。"""
import httpx

from config.settings import settings


class LLMError(RuntimeError):
    """大模型调用失败。"""


class LLMClient:
    """OpenAI 兼容 chat/completions 客户端；未配置 Key 时不可用（走假数据）。"""

    def __init__(self, api_key: str = "", base_url: str = "", model: str = ""):
        self.api_key = api_key or settings.llm_api_key
        self.base_url = (base_url or settings.llm_base_url).rstrip("/")
        self.model = model or settings.llm_model

    @property
    def available(self) -> bool:
        return bool(self.api_key and self.base_url and self.model)

    def chat(self, messages: list[dict], temperature: float = 0.2) -> str:
        """调用 chat/completions，返回模型回复文本。"""
        if not self.available:
            raise LLMError("大模型未配置（LLM_API_KEY / LLM_BASE_URL / LLM_MODEL）")
        resp = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={"model": self.model, "messages": messages, "temperature": temperature},
            timeout=30,
            trust_env=False,  # 忽略失效环境代理，直连
        )
        resp.raise_for_status()
        body = resp.json()
        try:
            return body["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            raise LLMError(f"大模型响应格式异常：{body}") from None