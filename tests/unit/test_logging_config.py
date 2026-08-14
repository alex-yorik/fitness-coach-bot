import logging
from logging.handlers import RotatingFileHandler

import pytest

from app import logging_config as lc


@pytest.fixture(autouse=True)
def _reset_root_logger():
    root = logging.getLogger()
    before = list(root.handlers)
    yield
    for handler in list(root.handlers):
        root.removeHandler(handler)
    for handler in before:
        root.addHandler(handler)


class TestSetupLogging:
    def test_writes_to_file(self, tmp_path):
        path = str(tmp_path / "bot.log")
        lc.setup_logging(path)
        logging.getLogger("test.logging_config").info("hello world")
        for handler in logging.getLogger().handlers:
            handler.flush()
        assert "hello world" in open(path, encoding="utf-8").read()

    def test_rotating_handler_config(self, tmp_path):
        lc.setup_logging(str(tmp_path / "bot.log"))
        handlers = logging.getLogger().handlers
        rotating = [h for h in handlers if isinstance(h, RotatingFileHandler)]
        assert rotating
        assert rotating[0].maxBytes == 10 * 1024 * 1024
        assert rotating[0].backupCount == 5

    def test_fallback_null_handler_when_unwritable(self, monkeypatch):
        def boom(*args, **kwargs):
            raise OSError("read-only filesystem")

        monkeypatch.setattr(lc.os, "makedirs", boom)
        lc.setup_logging("/proc/definitely/not/writable/bot.log")
        assert any(isinstance(h, logging.NullHandler) for h in logging.getLogger().handlers)

    def test_idempotent(self, tmp_path):
        lc.setup_logging(str(tmp_path / "a.log"))
        first = len(logging.getLogger().handlers)
        lc.setup_logging(str(tmp_path / "b.log"))
        assert len(logging.getLogger().handlers) == first

    def test_default_path_used(self, tmp_path, monkeypatch):
        monkeypatch.setattr(lc, "LOG_PATH", str(tmp_path / "env_bot.log"))
        lc.setup_logging()
        assert any(isinstance(h, RotatingFileHandler) for h in logging.getLogger().handlers)

    def test_httpx_quieted(self, tmp_path):
        lc.setup_logging(str(tmp_path / "bot.log"))
        assert logging.getLogger("httpx").level == logging.WARNING


class TestGetLogger:
    def test_returns_logger(self):
        assert isinstance(lc.get_logger("some.name"), logging.Logger)
