"""统一配置：读取环境变量（只此一处读配置）。"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "办公自动化 Agent"
    debug: bool = False
    database_url: str = "sqlite:///./office_agent.db"

    # 飞书
    feishu_app_id: str = ""
    feishu_app_secret: str = ""
    feishu_redirect_uri: str = ""
    feishu_scopes: str = "calendar:calendar:readonly,calendar:calendar"

    # 前端
    frontend_url: str = "http://localhost:5173"

    # 表格工具允许操作的目录
    sheets_data_dir: str = "D:/download new/ai_coding/Cool note/Excel数据"

    # QQ 邮箱（IMAP/SMTP）
    qq_mail_address: str = ""
    qq_mail_auth_code: str = ""

    # 大模型（境内，OpenAI 兼容格式）
    llm_api_key: str = ""
    llm_base_url: str = ""
    llm_model: str = ""

    # 鉴权（JWT）
    auth_required: bool = False
    jwt_secret: str = "dev-secret-change-me-please-32bytes-min"


settings = Settings()