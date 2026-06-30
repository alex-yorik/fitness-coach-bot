import json
from pathlib import Path
from app.validators import validate_content, ContentValidationError

CONTENT_PATH = Path(__file__).parent.parent / "content"


def load_content(filename: str = None) -> dict:
    if filename:
        file_path = CONTENT_PATH / filename
    else:
        json_files = list(CONTENT_PATH.glob("*.json"))
        if not json_files:
            raise FileNotFoundError(f"No JSON files found in {CONTENT_PATH}")
        file_path = json_files[0]
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    try:
        validate_content(data)
    except ContentValidationError as e:
        print(f"⚠️  Warning: {e}")
        return {}
    
    print(f"✅ Content validated successfully: {file_path.name}")
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
