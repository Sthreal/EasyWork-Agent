"""轻量幂等迁移：为旧库补齐新增列（不破坏现有数据，失败只告警）。"""
import logging

from sqlalchemy import text

logger = logging.getLogger(__name__)


_NEW_COLUMNS = (
    ("preview", "TEXT DEFAULT ''"),
    ("in_workspace", "BOOLEAN DEFAULT 1"),
    ("deferred_at", "DATETIME"),
)


def ensure_confirmations_columns(engine) -> None:
    """confirmations 表补齐新增列（SQLite，幂等；缺啥补啥，不破坏现有数据）。"""
    try:
        if not str(engine.url).startswith("sqlite"):
            return
        with engine.connect() as conn:
            cols = [row[1] for row in conn.execute(text("PRAGMA table_info(confirmations)"))]
            for name, ddl in _NEW_COLUMNS:
                if name not in cols:
                    conn.execute(text(f"ALTER TABLE confirmations ADD COLUMN {name} {ddl}"))
                    logger.info("迁移：confirmations 表新增 %s 列", name)
            conn.commit()
    except Exception:  # noqa: BLE001
        logger.warning("confirmations 迁移跳过（不影响启动）", exc_info=True)


def ensure_confirmations_preview(engine) -> None:
    """兼容旧调用：补齐 confirmations 全部新增列（含 preview）。"""
    ensure_confirmations_columns(engine)
