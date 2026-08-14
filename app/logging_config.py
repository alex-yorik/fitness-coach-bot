import logging
import os
from logging.handlers import RotatingFileHandler

LOG_PATH = os.getenv("LOG_PATH", "/app/logs/bot.log")
WEB_LOG_PATH = os.getenv("WEB_LOG_PATH", "/app/logs/web.log")
MAX_LOG_BYTES = 10 * 1024 * 1024
LOG_BACKUP_COUNT = 5
LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def _build_handler(path: str) -> logging.Handler | None:
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        handler = RotatingFileHandler(
            path, maxBytes=MAX_LOG_BYTES, backupCount=LOG_BACKUP_COUNT, encoding="utf-8"
        )
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        return handler
    except OSError:
        return None


def setup_logging(path: str = LOG_PATH) -> None:
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    for handler in list(root.handlers):
        root.removeHandler(handler)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    handler = _build_handler(path)
    if handler is None:
        root.addHandler(logging.NullHandler())
        return
    root.addHandler(handler)
