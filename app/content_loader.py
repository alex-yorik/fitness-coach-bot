import json
import logging
from pathlib import Path

from app.validators import ContentValidationError, validate_content

logger = logging.getLogger(__name__)

CONTENT_PATH = Path(__file__).parent.parent / "content"

_CACHE: dict[str, tuple[float, dict]] = {}


def load_content(filename: str = "fitness_coach.json") -> dict:
    file_path = CONTENT_PATH / (filename or "fitness_coach.json")

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    mtime = file_path.stat().st_mtime
    cached = _CACHE.get(str(file_path))
    if cached is not None and cached[0] == mtime:
        return cached[1]

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    try:
        validate_content(data)
    except ContentValidationError as e:
        logger.warning("Content validation failed: %s", e)
        data = {}
    else:
        logger.info("Content validated successfully: %s", file_path.name)

    _CACHE[str(file_path)] = (mtime, data)
    return data


def get_menu(data: dict) -> list:
    menu = []

    for key in ["about", "formats", "services", "portfolio", "parents"]:
        if key in data and "title" in data[key]:
            menu.append(data[key]["title"])

    if "trial" in data and "button" in data["trial"]:
        menu.append(data["trial"]["button"])

    return menu


def get_page(data: dict, page_id: str) -> dict:
    return data.get(page_id, {})


def get_setting(data: dict, key: str, default=None):
    return data.get(key, default)


def reload_content(filename: str = None) -> dict:
    return load_content(filename)
