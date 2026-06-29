"""
Validator for checking content.json structure
"""
import json
from typing import Dict, Any


class ContentValidationError(Exception):
    """Exception for content validation errors"""
    pass


def validate_content(data: Dict[str, Any]) -> bool:
    errors = []
    
    # Check required top-level fields
    required_top_fields = ["name", "profession", "welcome", "trial", "ui"]
    for field in required_top_fields:
        if field not in data:
            errors.append(f"Missing required field: '{field}'")
    
    # Check welcome section
    if "welcome" in data:
        welcome = data["welcome"]
        if "title" not in welcome:
            errors.append("Missing 'title' in 'welcome' section")
        if "text" not in welcome:
            errors.append("Missing 'text' in 'welcome' section")
    
    # Check trial section
    if "trial" in data:
        trial = data["trial"]
        
        if "button" not in trial:
            errors.append("Missing 'button' in 'trial' section")
        if "steps" not in trial:
            errors.append("Missing 'steps' in 'trial' section")
        elif not isinstance(trial["steps"], list):
            errors.append("'trial.steps' must be a list")
        else:
            for i, step in enumerate(trial["steps"]):
                if not isinstance(step, dict):
                    errors.append(f"Step {i+1} must be a dictionary")
                    continue
                
                if "key" not in step:
                    errors.append(f"Step {i+1} missing 'key' field")
                if "question" not in step:
                    errors.append(f"Step {i+1} missing 'question' field")
                
                if "validation" in step:
                    valid_validations = ["text", "age", "contact", "email", "phone", "number"]
                    if step["validation"] not in valid_validations:
                        errors.append(
                            f"Invalid 'validation' in step {i+1}: {step['validation']}. "
                            f"Allowed: {', '.join(valid_validations)}"
                        )
        
        if "success" in trial and not isinstance(trial["success"], str):
            errors.append("'trial.success' must be a string")
        if "cancelled" in trial and not isinstance(trial["cancelled"], str):
            errors.append("'trial.cancelled' must be a string")
    
    # Check ui section
    if "ui" in data:
        ui = data["ui"]
        if "btn_back" not in ui:
            errors.append("Missing 'btn_back' in 'ui' section")
        if "btn_cancel" not in ui:
            errors.append("Missing 'btn_cancel' in 'ui' section")
    
    # Check media sections
    optional_sections = ["about", "formats", "parents", "services", "portfolio"]
    for section in optional_sections:
        if section in data:
            section_data = data[section]
            
            if "media" in section_data:
                media = section_data["media"]
                if not isinstance(media, list):
                    errors.append(f"'{section}.media' must be a list")
                else:
                    for i, item in enumerate(media):
                        if not isinstance(item, dict):
                            errors.append(f"Item {i+1} in '{section}.media' must be a dictionary")
                            continue
                        
                        if "type" not in item:
                            errors.append(f"Item {i+1} in '{section}.media' missing 'type'")
                        elif item["type"] not in ["photo", "video", "document"]:
                            errors.append(
                                f"Invalid 'type' in item {i+1} '{section}.media': {item['type']}. "
                                f"Allowed: photo, video, document"
                            )
                        
                        if "file" not in item:
                            errors.append(f"Item {i+1} in '{section}.media' missing 'file'")
    
    if "name" in data and not isinstance(data["name"], str):
        errors.append("'name' must be a string")
    if "profession" in data and not isinstance(data["profession"], str):
        errors.append("'profession' must be a string")
    
    if errors:
        error_message = "Content validation errors:\n\n" + "\n".join(errors)
        raise ContentValidationError(error_message)
    
    return True


def validate_content_file(file_path: str) -> bool:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"JSON parsing error in file {file_path}: {e.msg}",
            e.doc,
            e.pos
        )
    
    return validate_content(data)


def get_content_summary(data: Dict[str, Any]) -> str:
    summary = []
    
    summary.append(f"👤 Name: {data.get('name', 'Not specified')}")
    summary.append(f"💼 Profession: {data.get('profession', 'Not specified')}")
    
    pages = []
    for section in ["about", "formats", "parents", "services", "portfolio"]:
        if section in data:
            pages.append(section)
    
    summary.append(f"📄 Pages: {len(pages)} ({', '.join(pages) if pages else 'none'})")
    
    if "trial" in data and "steps" in data["trial"]:
        steps_count = len(data["trial"]["steps"])
        summary.append(f"📝 Form steps: {steps_count}")
    
    media_count = 0
    for section in ["about", "formats", "parents", "services", "portfolio"]:
        if section in data and "media" in data[section]:
            media_count += len(data[section]["media"])
    
    summary.append(f"🖼 Media files: {media_count}")
    
    return "\n".join(summary)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python validators.py <path_to_json>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    try:
        validate_content_file(file_path)
        print(f"✅ Validation passed: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print("\n" + get_content_summary(data))
        
    except Exception as e:
        print(f"\n{e}")
        sys.exit(1)
