from telegram.ext import Application

import app.bot as bot


def _content() -> dict:
    return {
        "trial": {"button": "Записаться на консультацию"},
        "about": {"title": "Обо мне"},
        "formats": {"title": "Форматы"},
        "gallery": {"title": "Галерея"},
        "parents": {"title": "Родителям"},
    }


class TestMain:
    def test_requires_token(self, monkeypatch, capsys):
        calls = []
        monkeypatch.setattr(bot, "BOT_TOKEN", None)
        monkeypatch.setattr(bot, "init_db", lambda: calls.append("init"))

        bot.main()

        out = capsys.readouterr().out
        assert "BOT_TOKEN" in out
        assert calls == ["init"]

    def test_registers_handlers_and_runs(self, monkeypatch):
        calls = []
        handlers = []

        class FakeApp:
            def add_handler(self, handler):
                handlers.append(type(handler).__name__)

            def run_polling(self):
                calls.append("polling")

        class FakeBuilder:
            def token(self, token):
                calls.append(f"token:{token}")
                return self

            def build(self):
                calls.append("build")
                return FakeApp()

        monkeypatch.setattr(Application, "builder", classmethod(lambda cls: FakeBuilder()))
        monkeypatch.setattr(bot, "BOT_TOKEN", "123:test-token")
        monkeypatch.setattr(bot, "init_db", lambda: calls.append("init"))
        monkeypatch.setattr(bot, "load_content", lambda: _content())

        bot.main()

        assert "init" in calls
        assert "token:123:test-token" in calls
        assert "build" in calls
        assert "polling" in calls
        assert "ConversationHandler" in handlers
        assert "CommandHandler" in handlers
        assert "MessageHandler" in handlers
