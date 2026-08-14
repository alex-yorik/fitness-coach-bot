import json
import os

import pytest

import app.content_loader as cl


@pytest.fixture
def content_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(cl, "CONTENT_PATH", tmp_path)
    cl._CACHE.clear()
    yield tmp_path
    cl._CACHE.clear()


def _valid_content() -> dict:
    return {
        "name": "Тренер",
        "profession": "Фитнес",
        "welcome": {"title": "Привет", "text": "Добро пожаловать"},
        "trial": {
            "button": "Записаться",
            "steps": [{"key": "name", "question": "Имя?", "validation": "text"}],
            "success": "ok",
            "cancelled": "no",
        },
        "ui": {"btn_back": "◀️", "btn_cancel": "❌"},
    }


def _write(path, data: dict):
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


class TestLoadContent:
    def test_load_valid(self, content_dir):
        _write(content_dir / "fitness_coach.json", _valid_content())
        data = cl.load_content()
        assert data["name"] == "Тренер"
        assert data["trial"]["button"] == "Записаться"

    def test_custom_filename(self, content_dir):
        _write(content_dir / "other.json", _valid_content())
        assert cl.load_content("other.json")["name"] == "Тренер"

    def test_cache_hit_returns_same_object(self, content_dir):
        _write(content_dir / "fitness_coach.json", _valid_content())
        first = cl.load_content()
        second = cl.load_content()
        assert first is second

    def test_reloads_when_file_changed(self, content_dir):
        path = content_dir / "fitness_coach.json"
        _write(path, _valid_content())
        first = cl.load_content()
        assert first["name"] == "Тренер"

        _write(path, {**_valid_content(), "name": "Тренер 2"})
        os.utime(path, (1_700_000_000, 1_700_000_001))
        second = cl.load_content()
        assert second["name"] == "Тренер 2"
        assert first is not second

    def test_file_not_found(self, content_dir):
        with pytest.raises(FileNotFoundError):
            cl.load_content("missing.json")

    def test_invalid_json(self, content_dir):
        (content_dir / "fitness_coach.json").write_text("{bad json", encoding="utf-8")
        with pytest.raises(json.JSONDecodeError):
            cl.load_content()

    def test_validation_failure_returns_empty_dict(self, content_dir):
        data = _valid_content()
        data["trial"]["steps"] = [{"key": "x", "validation": "bogus", "question": "?"}]
        _write(content_dir / "fitness_coach.json", data)
        assert cl.load_content() == {}

    def test_reload_content(self, content_dir):
        _write(content_dir / "fitness_coach.json", _valid_content())
        data = cl.reload_content()
        assert data["name"] == "Тренер"
        assert cl.load_content() is data


class TestGetMenu:
    def test_menu_order_with_trial_button(self):
        data = {
            "about": {"title": "Обо мне"},
            "formats": {"title": "Форматы"},
            "services": {"title": "Услуги"},
            "portfolio": {"title": "Портфолио"},
            "parents": {"title": "Родителям"},
            "trial": {"button": "Записаться"},
        }
        assert cl.get_menu(data) == [
            "Обо мне",
            "Форматы",
            "Услуги",
            "Портфолио",
            "Родителям",
            "Записаться",
        ]

    def test_menu_empty(self):
        assert cl.get_menu({}) == []
        assert cl.get_menu({"trial": {"steps": []}}) == []


class TestGetPage:
    def test_get_page(self):
        data = {"about": {"title": "Обо мне"}}
        assert cl.get_page(data, "about") == {"title": "Обо мне"}

    def test_get_missing_page(self):
        assert cl.get_page({}, "about") == {}
        assert cl.get_page({"about": {"title": "x"}}, "nope") == {}


class TestGetSetting:
    def test_existing_key(self):
        assert cl.get_setting({"key": "value"}, "key") == "value"

    def test_missing_key_uses_default(self):
        assert cl.get_setting({}, "missing") is None
        assert cl.get_setting({}, "missing", "default") == "default"
