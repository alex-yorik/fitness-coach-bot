import sqlite3

import pytest
from telegram.constants import ParseMode
from telegram.ext import ConversationHandler

import app.database as database
import app.handlers.trial as trial
from app.handlers.trial import (
    AGE,
    CONTACT,
    GOAL,
    NAME,
    back_step,
    cancel,
    get_age,
    get_contact,
    get_goal,
    get_name,
    get_trial_handler,
    trial_start,
)


@pytest.fixture
def content() -> dict:
    return {
        "trial": {
            "title": "📝 Запись на пробную тренировку",
            "button": "Записаться на консультацию",
            "steps": [
                {
                    "key": "name",
                    "question": "Как вас зовут?",
                    "validation": "text",
                    "error": "⚠️ Введите имя",
                },
                {
                    "key": "age",
                    "question": "Сколько вам лет?",
                    "validation": "age",
                    "error": "⚠️ Введите возраст",
                },
                {
                    "key": "goal",
                    "question": "Ваша цель?",
                    "validation": "text",
                    "error": "⚠️ Введите цель",
                },
                {
                    "key": "contact",
                    "question": "Контакт?",
                    "validation": "contact",
                    "error": "⚠️ Введите контакт",
                },
            ],
            "success": "✅ Заявка принята!",
            "cancelled": "❌ Отменено.",
        }
    }


@pytest.fixture
def patch_content(monkeypatch, content):
    monkeypatch.setattr(trial, "load_content", lambda filename=None: content)
    return content


@pytest.fixture
def patch_db(tmp_path, monkeypatch):
    db_path = tmp_path / "trial.db"
    monkeypatch.setattr(database, "DATABASE_PATH", str(db_path))

    def _conn():
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn

    monkeypatch.setattr(trial, "get_connection", _conn)
    database.init_db()
    return str(db_path)


class MockMessage:
    def __init__(self, text=None):
        self.text = text
        self.replies = []

    async def reply_text(self, *args, **kwargs):
        self.replies.append((args, kwargs))


class MockUpdate:
    def __init__(self, text=None):
        self.message = MockMessage(text)


class MockBot:
    def __init__(self):
        self.sent = []

    async def send_message(self, *args, **kwargs):
        self.sent.append((args, kwargs))


class MockContext:
    def __init__(self):
        self.user_data = {}
        self.bot = MockBot()


def _reply_text(update: MockUpdate, index: int = 0) -> str:
    return update.message.replies[index][0][0]


class TestTrialStart:
    async def test_returns_name_state(self, patch_content):
        update = MockUpdate("Записаться на консультацию")
        context = MockContext()

        result = await trial_start(update, context)

        assert result == NAME
        text = _reply_text(update)
        assert "📝 Запись на пробную тренировку" in text
        assert "Шаг 1 из 4" in text
        assert "Как вас зовут?" in text
        args, kwargs = update.message.replies[0]
        assert kwargs["parse_mode"] == ParseMode.HTML
        assert kwargs["reply_markup"] is not None


class TestGetName:
    async def test_valid(self, patch_content):
        update = MockUpdate("  Иван  ")
        context = MockContext()

        result = await get_name(update, context)

        assert result == AGE
        assert context.user_data["name"] == "  Иван  "
        assert context.user_data["trial_step"] == 1
        assert "Сколько вам лет?" in _reply_text(update)

    async def test_invalid(self, patch_content):
        update = MockUpdate("И")
        context = MockContext()

        result = await get_name(update, context)

        assert result == NAME
        assert _reply_text(update) == "⚠️ Введите имя"
        assert "name" not in context.user_data


class TestGetAge:
    @pytest.mark.parametrize("bad_age", ["abc", "0", "101", "тридцать"])
    async def test_invalid(self, patch_content, bad_age):
        update = MockUpdate(bad_age)
        context = MockContext()

        result = await get_age(update, context)

        assert result == AGE
        assert _reply_text(update) == "⚠️ Введите возраст"
        assert "age" not in context.user_data

    async def test_valid(self, patch_content):
        update = MockUpdate("30")
        context = MockContext()

        result = await get_age(update, context)

        assert result == GOAL
        assert context.user_data["age"] == "30"
        assert context.user_data["trial_step"] == 2
        assert "Ваша цель?" in _reply_text(update)


class TestGetGoal:
    async def test_invalid(self, patch_content):
        update = MockUpdate("")
        context = MockContext()

        result = await get_goal(update, context)

        assert result == GOAL
        assert _reply_text(update) == "⚠️ Введите цель"

    async def test_valid(self, patch_content):
        update = MockUpdate("Похудение")
        context = MockContext()

        result = await get_goal(update, context)

        assert result == CONTACT
        assert context.user_data["goal"] == "Похудение"
        assert context.user_data["trial_step"] == 3
        assert "Контакт?" in _reply_text(update)


class TestGetContact:
    async def test_valid_saves_application(self, patch_content, patch_db):
        update = MockUpdate("1234567")
        context = MockContext()
        context.user_data.update({"name": "Иван", "age": "30", "goal": "Похудение"})

        result = await get_contact(update, context)

        assert result == ConversationHandler.END
        assert context.user_data == {}
        assert "✅ Заявка принята!" in _reply_text(update)
        assert "👤 Имя: Иван" in _reply_text(update)

        conn = sqlite3.connect(patch_db)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM applications").fetchone()
        conn.close()
        assert row["name"] == "Иван"
        assert row["age"] == 30
        assert row["goal"] == "Похудение"
        assert row["contact"] == "1234567"
        assert row["status"] == "new"

    async def test_invalid(self, patch_content, patch_db):
        update = MockUpdate("ab")
        context = MockContext()

        result = await get_contact(update, context)

        assert result == CONTACT
        assert _reply_text(update) == "⚠️ Введите контакт"
        assert "contact" not in context.user_data

    async def test_db_error_fail_closed(self, patch_content, patch_db):
        conn = sqlite3.connect(patch_db)
        conn.execute("DROP TABLE applications")
        conn.commit()
        conn.close()

        update = MockUpdate("1234567")
        context = MockContext()
        context.user_data.update({"name": "Иван", "age": "30", "goal": "Цель"})

        result = await get_contact(update, context)

        assert result == ConversationHandler.END
        assert context.user_data == {}
        assert "Произошла ошибка" in _reply_text(update)


class TestSaveApplication:
    async def test_success_no_admin_notify(self, patch_db):
        context = MockContext()
        answers = {"name": "Иван", "age": "30", "goal": "Цель", "contact": "@ivan"}

        await trial._save_application(context, answers)

        assert context.bot.sent == []
        conn = sqlite3.connect(patch_db)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM applications").fetchone()
        conn.close()
        assert row["name"] == "Иван"

    async def test_error_notifies_admin(self, patch_db, monkeypatch):
        monkeypatch.setattr(trial, "ADMIN_CHAT_ID", "12345")
        conn = sqlite3.connect(patch_db)
        conn.execute("DROP TABLE applications")
        conn.commit()
        conn.close()

        context = MockContext()
        answers = {"name": "Иван", "contact": "@ivan"}

        with pytest.raises(Exception):
            await trial._save_application(context, answers)

        assert len(context.bot.sent) == 1
        (args, kwargs) = context.bot.sent[0]
        assert kwargs["chat_id"] == "12345"
        assert "Ошибка при сохранении заявки" in kwargs["text"]


class TestSuccessReply:
    async def test_escapes_user_data(self, patch_content):
        update = MockUpdate()
        answers = {
            "name": "<script>",
            "age": "30",
            "goal": "x&y",
            "contact": "@ivan",
        }

        await trial._success_reply(update, answers)

        text = _reply_text(update)
        assert "&lt;script&gt;" in text
        assert "x&amp;y" in text
        assert "✅ Заявка принята!" in text


class TestBackStep:
    async def test_at_first_step(self, patch_content):
        update = MockUpdate("◀️ Назад")
        context = MockContext()
        context.user_data["trial_step"] = 0

        result = await back_step(update, context)

        assert result == NAME
        assert "Вы уже на первом шаге." in _reply_text(update)

    async def test_goes_back(self, patch_content):
        update = MockUpdate("◀️ Назад")
        context = MockContext()
        context.user_data.update({"name": "Иван", "age": "30", "trial_step": 2})

        result = await back_step(update, context)

        assert result == AGE
        assert context.user_data["trial_step"] == 1
        text = _reply_text(update)
        assert "Сколько вам лет?" in text
        assert "Текущий ответ: 30" in text


class TestCancel:
    async def test_cancels(self, patch_content):
        update = MockUpdate("❌ Отменить")
        context = MockContext()
        context.user_data["name"] = "Иван"

        result = await cancel(update, context)

        assert result == ConversationHandler.END
        assert context.user_data == {}
        assert "❌ Отменено." in _reply_text(update)


class TestGetTrialHandler:
    def test_structure(self):
        handler = get_trial_handler("Записаться на консультацию")

        assert len(handler.entry_points) == 1
        assert len(handler.fallbacks) == 3
        assert set(handler.states.keys()) == {NAME, AGE, GOAL, CONTACT}

    def test_empty_button(self):
        handler = get_trial_handler("  ")
        assert len(handler.entry_points) == 1
