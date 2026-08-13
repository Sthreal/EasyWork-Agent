"""日志配置：统一日志输出（文件 + 控制台，文件不可用时仅控制台）。"""
import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parents[1] / "logs"
LOG_FILE = LOG_DIR / "app.log"
LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"


def setup_logging(log_file: Path | None = None, level: int = logging.INFO) -> None:
    """初始化根日志：同时输出到文件和控制台。文件写入失败不崩溃，仅控制台。"""
    log_file = log_file or LOG_FILE
    log_file.parent.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(level)

    for handler in list(root.handlers):
        if isinstance(handler, (logging.StreamHandler, TimedRotatingFileHandler)):
            root.removeHandler(handler)

    try:
        file_handler = TimedRotatingFileHandler(
            log_file, when="midnight", backupCount=7, encoding="utf-8"
        )
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        root.addHandler(file_handler)
    except OSError as exc:
        logging.getLogger("config.logging").warning("日志文件不可用，仅控制台输出：%s", exc)

    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter(LOG_FORMAT))
    root.addHandler(console)