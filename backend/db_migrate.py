"""轻量幂等迁移：为旧库补齐新增列（不破坏现有数据，失败只告警）。"""
import logging

from sqlalchemy import text

logger = logging.getLogger(__name__)


def ensure_confirmations_preview(engine) -> None:
    """confirmations 表缺 preview 列时补上（SQLite，幂等）。"""
    try:
        if not str(engine.url).startswith("sqlite"):
            return
        with engine.connect() as conn:
            cols = [row[1] for row in conn.execute(text("PRAGMA table_info(confirmations)"))]
            if "preview" not in cols:
                conn.execute(text("ALTER TABLE confirmations ADD COLUMN preview TEXT DEFAULT ''"))
                conn.commit()
                logger.info("迁移：confirmations 表新增 preview 列")
    except Exception:  # noqa: BLE001
        logger.warning("confirmations.preview 迁移跳过（不影响启动）", exc_info=True)
