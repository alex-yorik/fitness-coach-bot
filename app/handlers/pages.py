from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from app.content_loader import load_content
from app.keyboards import main_keyboard


async def show_about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_content()
    section = data["about"]

    await update.message.reply_text(
        text=f"<b>{section['title']}</b>\n\n{section['text']}",
        parse_mode=ParseMode.HTML,
        reply_markup=main_keyboard()
    )


async def show_formats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_content()
    section = data["formats"]

    await update.message.reply_text(
        text=f"<b>{section['title']}</b>\n\n{section['text']}",
        parse_mode=ParseMode.HTML,
        reply_markup=main_keyboard()
    )


async def show_parents(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_content()
    section = data["parents"]

    await update.message.reply_text(
        text=f"<b>{section['title']}</b>\n\n{section['text']}",
        parse_mode=ParseMode.HTML,
        reply_markup=main_keyboard()
    )


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_content()
    welcome = data["welcome"]

    await update.message.reply_text(
        text=f"<b>{welcome['title']}</b>\n\n👇 Выберите нужный раздел:",
        parse_mode=ParseMode.HTML,
        reply_markup=main_keyboard()
    )
