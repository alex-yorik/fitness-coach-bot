import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CONTENT_FILE = BASE_DIR / "content" / "teacher.json"

_content = None


def load_content():
    global _content

    if _content is None:
        with open(CONTENT_FILE, "r", encoding="utf-8") as f:
            _content = json.load(f)

    return _content


def get_teacher():
    return load_content().get("teacher", {})


def get_menu():
    return load_content().get("menu", [])


def get_page(page_id):
    pages = load_content().get("pages", {})
    return pages.get(page_id, {})


def get_setting(key, default=None):
    settings = load_content().get("settings", {})
    return settings.get(key, default)


def reload_content():
    global _content
    _content = None
    return load_content()
