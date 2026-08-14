import pytest
from telegram.constants import ParseMode

import app.handlers.pages as pages
import app.handlers.start as start


@pytest.fixture
def content() -> dict:
    return {
        "welcome": {"title": "Добро пожаловать", "text": "Привет, я твой тренер!"},
        "about": {"title": "Обо мне", "text": "Текст обо мне"},
        "formats": {"title": "Форматы"},
        "trial": {"button": "Записаться"},
        "parents": {"title": "Родителям"},
    }


@pytest.fixture
def patch_start_content(monkeypatch, content):
    monkeypatch.setattr(start, "load_content", lambda filename=None: content)


@pytest.fixture
def patch_pages_content(monkeypatch, content):
    monkeypatch.setattr(pages, "load_content", lambda filename=None: content)


class MockMessage:
    def __init__(self):
        self.replies = []

    async def reply_text(self, *args, **kwargs):
        self.replies.append((args, kwargs))


class MockUpdate:
    def __init__(self):
        self.message = MockMessage()


class TestStart:
    async def test_start_replies_welcome(self, patch_start_content):
        update = MockUpdate()
        context = object()

        await start.start(update, context)

        (args, kwargs) = update.message.replies[0]
        assert "<b>Добро пожаловать</b>" in kwargs["text"]
        assert "Привет, я твой тренер!" in kwargs["text"]
        assert kwargs["parse_mode"] == ParseMode.HTML
        assert kwargs["reply_markup"] is not None


class TestShowContentPage:
    async def test_section_with_text(self, patch_pages_content):
        update = MockUpdate()
        context = object()

        await pages.show_content_page(update, context, "about")

        (args, kwargs) = update.message.replies[0]
        assert "<b>Обо мне</b>" in kwargs["text"]
        assert "Текст обо мне" in kwargs["text"]
        assert kwargs["parse_mode"] == ParseMode.HTML

    async def test_section_without_text(self, patch_pages_content):
        update = MockUpdate()
        context = object()

        await pages.show_content_page(update, context, "formats")

        (args, kwargs) = update.message.replies[0]
        assert "<b>Форматы</b>" in kwargs["text"]
        assert "Текст обо мне" not in kwargs["text"]

    async def test_missing_section(self, patch_pages_content):
        update = MockUpdate()
        context = object()

        await pages.show_content_page(update, context, "nope")

        (args, kwargs) = update.message.replies[0]
        assert "Извините, раздел не найден." in args[0]


class TestShowMainMenu:
    async def test_returns_menu(self, patch_pages_content):
        update = MockUpdate()
        context = object()

        await pages.show_main_menu(update, context)

        (args, kwargs) = update.message.replies[0]
        assert "<b>Добро пожаловать</b>" in kwargs["text"]
        assert kwargs["parse_mode"] == ParseMode.HTML
        assert kwargs["reply_markup"] is not None
