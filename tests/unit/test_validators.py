import json

import pytest

from app.validators import (
    ContentValidationError,
    get_content_summary,
    validate_answer,
    validate_content,
    validate_content_file,
)


def _valid_content() -> dict:
    return {
        "name": "Тренер",
        "profession": "Фитнес-тренер",
        "welcome": {"title": "Добро пожаловать", "text": "Текст приветствия"},
        "trial": {
            "button": "Записаться",
            "steps": [
                {"key": "name", "question": "Как вас зовут?", "validation": "text"},
                {"key": "age", "question": "Сколько вам лет?", "validation": "age"},
            ],
            "success": "ok",
            "cancelled": "no",
        },
        "ui": {"btn_back": "◀️ Назад", "btn_cancel": "❌ Отменить"},
    }


class TestValidateAnswer:
    @pytest.mark.parametrize("value", ["", "   ", None])
    def test_empty_value(self, value):
        assert validate_answer("text", value) == (False, "empty")

    @pytest.mark.parametrize(
        "value,expected",
        [
            ("A", (False, "length")),
            ("AB", (True, None)),
            ("x" * 200, (True, None)),
            ("x" * 201, (False, "length")),
        ],
    )
    def test_text(self, value, expected):
        assert validate_answer("text", value) == expected

    @pytest.mark.parametrize(
        "value,expected",
        [
            ("abc", (False, "not_a_number")),
            ("-5", (False, "not_a_number")),
            ("0", (False, "age_range")),
            ("101", (False, "age_range")),
            ("1", (True, None)),
            ("100", (True, None)),
            ("30", (True, None)),
        ],
    )
    def test_age(self, value, expected):
        assert validate_answer("age", value) == expected

    @pytest.mark.parametrize(
        "value,expected",
        [
            ("abc", (False, "not_a_number")),
            ("1000001", (False, "number_range")),
            ("0", (True, None)),
            ("1000000", (True, None)),
            ("42", (True, None)),
        ],
    )
    def test_number(self, value, expected):
        assert validate_answer("number", value) == expected

    @pytest.mark.parametrize(
        "value,expected",
        [
            ("123456", (False, "phone_format")),
            ("1234567", (True, None)),
            ("+1 (999) 123-45-67", (True, None)),
            ("123456789012345", (True, None)),
            ("1234567890123456", (False, "phone_format")),
        ],
    )
    def test_phone(self, value, expected):
        assert validate_answer("phone", value) == expected

    @pytest.mark.parametrize(
        "value,expected",
        [
            ("user@example.com", (True, None)),
            ("a@b.co", (True, None)),
            ("user", (False, "email_format")),
            ("user@localhost", (False, "email_format")),
            ("user name@example.com", (False, "email_format")),
        ],
    )
    def test_email(self, value, expected):
        assert validate_answer("email", value) == expected

    @pytest.mark.parametrize(
        "value,expected",
        [
            ("@username", (True, None)),
            ("1234567", (True, None)),
            ("abcd", (True, None)),
            ("abc", (False, "contact_format")),
            ("@ab", (False, "contact_format")),
            ("", (False, "empty")),
        ],
    )
    def test_contact(self, value, expected):
        assert validate_answer("contact", value) == expected

    def test_unknown_validation_type(self):
        assert validate_answer("unknown_type", "anything") == (True, None)


class TestValidateContent:
    def test_valid_content(self):
        assert validate_content(_valid_content()) is True

    def test_missing_top_level_fields(self):
        with pytest.raises(ContentValidationError) as exc:
            validate_content({})
        for field in ["name", "profession", "welcome", "trial", "ui"]:
            assert f"'{field}'" in str(exc.value)

    def test_welcome_missing_fields(self):
        data = _valid_content()
        data["welcome"] = {}
        with pytest.raises(ContentValidationError) as exc:
            validate_content(data)
        assert "'title' in 'welcome'" in str(exc.value)
        assert "'text' in 'welcome'" in str(exc.value)

    def test_trial_missing_button_and_steps(self):
        data = _valid_content()
        data["trial"] = {}
        with pytest.raises(ContentValidationError) as exc:
            validate_content(data)
        assert "'button' in 'trial'" in str(exc.value)
        assert "'steps' in 'trial'" in str(exc.value)

    def test_trial_steps_not_list(self):
        data = _valid_content()
        data["trial"]["steps"] = "not-a-list"
        with pytest.raises(ContentValidationError) as exc:
            validate_content(data)
        assert "'trial.steps' must be a list" in str(exc.value)

    def test_trial_step_not_dict(self):
        data = _valid_content()
        data["trial"]["steps"] = [1]
        with pytest.raises(ContentValidationError) as exc:
            validate_content(data)
        assert "Step 1 must be a dictionary" in str(exc.value)

    def test_trial_step_missing_key_question(self):
        data = _valid_content()
        data["trial"]["steps"] = [{"validation": "text"}]
        with pytest.raises(ContentValidationError) as exc:
            validate_content(data)
        assert "missing 'key' field" in str(exc.value)
        assert "missing 'question' field" in str(exc.value)

    def test_trial_invalid_validation(self):
        data = _valid_content()
        data["trial"]["steps"][0]["validation"] = "bogus"
        with pytest.raises(ContentValidationError) as exc:
            validate_content(data)
        assert "Invalid 'validation' in step 1" in str(exc.value)

    @pytest.mark.parametrize("field", ["success", "cancelled"])
    def test_trial_non_string_success_cancelled(self, field):
        data = _valid_content()
        data["trial"][field] = 123
        with pytest.raises(ContentValidationError) as exc:
            validate_content(data)
        assert f"'trial.{field}' must be a string" in str(exc.value)

    @pytest.mark.parametrize("field", ["btn_back", "btn_cancel"])
    def test_ui_missing_buttons(self, field):
        data = _valid_content()
        del data["ui"][field]
        with pytest.raises(ContentValidationError) as exc:
            validate_content(data)
        assert f"Missing '{field}' in 'ui' section" in str(exc.value)

    def test_media_not_list(self):
        data = _valid_content()
        data["about"] = {"media": "not-a-list"}
        with pytest.raises(ContentValidationError) as exc:
            validate_content(data)
        assert "'about.media' must be a list" in str(exc.value)

    def test_media_item_not_dict(self):
        data = _valid_content()
        data["about"] = {"media": ["str"]}
        with pytest.raises(ContentValidationError) as exc:
            validate_content(data)
        assert "Item 1 in 'about.media' must be a dictionary" in str(exc.value)

    def test_media_missing_type_and_file(self):
        data = _valid_content()
        data["about"] = {"media": [{"file": "x.jpg"}]}
        with pytest.raises(ContentValidationError) as exc:
            validate_content(data)
        assert "missing 'type'" in str(exc.value)

        data = _valid_content()
        data["about"] = {"media": [{"type": "photo"}]}
        with pytest.raises(ContentValidationError) as exc:
            validate_content(data)
        assert "missing 'file'" in str(exc.value)

    def test_media_invalid_type(self):
        data = _valid_content()
        data["about"] = {"media": [{"type": "gif", "file": "x"}]}
        with pytest.raises(ContentValidationError) as exc:
            validate_content(data)
        assert "Invalid 'type' in item 1 'about.media': gif" in str(exc.value)

    @pytest.mark.parametrize("field", ["name", "profession"])
    def test_field_types(self, field):
        data = _valid_content()
        data[field] = 123
        with pytest.raises(ContentValidationError) as exc:
            validate_content(data)
        assert f"'{field}' must be a string" in str(exc.value)


class TestValidateContentFile:
    def test_valid_file(self, tmp_path):
        path = tmp_path / "content.json"
        path.write_text(json.dumps(_valid_content()), encoding="utf-8")
        assert validate_content_file(str(path)) is True

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            validate_content_file("/nonexistent/path/content.json")

    def test_invalid_json(self, tmp_path):
        path = tmp_path / "content.json"
        path.write_text("{not valid json", encoding="utf-8")
        with pytest.raises(json.JSONDecodeError):
            validate_content_file(str(path))

    def test_invalid_structure(self, tmp_path):
        path = tmp_path / "content.json"
        path.write_text(json.dumps({"name": "X"}), encoding="utf-8")
        with pytest.raises(ContentValidationError):
            validate_content_file(str(path))


class TestGetContentSummary:
    def test_summary(self):
        data = {
            "name": "Тренер",
            "profession": "Фитнес",
            "about": {"title": "Обо мне", "media": [{"type": "photo", "file": "a.jpg"}]},
            "formats": {"title": "Форматы"},
            "trial": {"button": "B", "steps": [1, 2, 3]},
        }
        summary = get_content_summary(data)
        assert "👤 Name: Тренер" in summary
        assert "💼 Profession: Фитнес" in summary
        assert "📄 Pages: 2 (about, formats)" in summary
        assert "📝 Form steps: 3" in summary
        assert "🖼 Media files: 1" in summary

    def test_summary_defaults(self):
        summary = get_content_summary({})
        assert "👤 Name: Not specified" in summary
        assert "📄 Pages: 0 (none)" in summary
        assert "🖼 Media files: 0" in summary
