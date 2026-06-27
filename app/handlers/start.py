from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from app.content_loader import load_content
from app.keyboards import main_keyboard


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_content()
    welcome = data["welcome"]

    text = (
        f"<b>{welcome['title']}</b>\n\n"
        f"{welcome['text']}\n\n"
        "👇 Выберите нужный раздел:"
    )

    await update.message.reply_text(
        text=text,
        parse_mode=ParseMode.HTML,
        reply_markup=main_keyboard()
    )
