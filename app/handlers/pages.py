from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from app.content_loader import load_content
from app.keyboards import main_keyboard


async def show_content_page(update: Update, context: ContextTypes.DEFAULT_TYPE, section_key: str):
    data = load_content()
    section = data.get(section_key)

    if not section:
        await update.message.reply_text("Извините, раздел не найден.")
        return

    text = (
        f"<b>{section['title']}</b>\n\n{section['text']}"
        if "text" in section
        else f"<b>{section['title']}</b>"
    )

    await update.message.reply_text(
        text=text, parse_mode=ParseMode.HTML, reply_markup=main_keyboard()
    )


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_content()
    welcome = data["welcome"]

    await update.message.reply_text(
        text=f"<b>{welcome['title']}</b>\n\n👇 Выберите нужный раздел:",
        parse_mode=ParseMode.HTML,
        reply_markup=main_keyboard(),
    )
