from telegram import ReplyKeyboardMarkup, KeyboardButton

from app.content_loader import load_content


def main_keyboard():
    data = load_content()

    keyboard = [
        [
            KeyboardButton(data["about"]["title"]),
            KeyboardButton(data["formats"]["title"])
        ],
        [
            KeyboardButton(data["trial"]["button"])
        ],
    ]
    if "parents" in data and "title" in data["parents"]:
        keyboard.append([KeyboardButton(data["parents"]["title"])])

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        is_persistent=True
    )


def back_keyboard():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("◀️ Назад")],
            [KeyboardButton("❌ Отменить")]
        ],
        resize_keyboard=True
    )
