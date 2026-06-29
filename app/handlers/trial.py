from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
    CommandHandler,
)

from app.config import ADMIN_CHAT_ID
from app.content_loader import load_content
from app.keyboards import main_keyboard, back_keyboard
from app.database import get_connection

NAME, AGE, GOAL, CONTACT = range(4)


async def trial_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📝 <b>Запись на пробный урок</b>\n\n"
        "Шаг 1 из 4\n\n"
        "Как вас зовут (или имя ребёнка)?",
        parse_mode=ParseMode.HTML,
        reply_markup=back_keyboard()
    )
    return NAME


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text(
        "Шаг 2 из 4\n\n"
        "Сколько лет ученику?",
        reply_markup=back_keyboard()
    )
    return AGE


async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["age"] = update.message.text
    await update.message.reply_text(
        "Шаг 3 из 4\n\n"
        "Какова цель обучения?\n"
        "Например: школьная программа, разговорный, ОГЭ, бизнес...",
        reply_markup=back_keyboard()
    )
    return GOAL


async def get_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["goal"] = update.message.text
    await update.message.reply_text(
        "Шаг 4 из 4\n\n"
        "Оставьте контакт для связи:\n"
        "Телефон, Telegram или WhatsApp",
        reply_markup=back_keyboard()
    )
    return CONTACT


async def get_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["contact"] = update.message.text

    name = context.user_data.get("name")
    age = context.user_data.get("age")
    goal = context.user_data.get("goal")
    contact = context.user_data.get("contact")

    conn = get_connection()
    conn.execute(
        "INSERT INTO applications (name, age, goal, contact) VALUES (?, ?, ?, ?)",
        (name, age, goal, contact)
    )
    conn.commit()
    conn.close()

    data = load_content()
    await update.message.reply_text(
        data["trial"]["success"] + "\n\n"
        f"👤 Имя: {name}\n"
        f"🎂 Возраст: {age}\n"
        f"🎯 Цель: {goal}\n"
        f"📞 Контакт: {contact}\n\n"
        "Тренер свяжется с вами в ближайшее время для согласования времени пробной тренировки.",
        parse_mode=ParseMode.HTML,
        reply_markup=main_keyboard()
    )

    if ADMIN_CHAT_ID:
        user = update.effective_user
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=(
                "🔔 <b>Новая заявка на пробный урок!</b>\n\n"
                f"👤 Имя: {name}\n"
                f"🎂 Возраст: {age}\n"
                f"🎯 Цель: {goal}\n"
                f"📞 Контакт: {contact}\n\n"
                f"Telegram пользователя: @{user.username or 'не указан'}\n"
                f"ID: {user.id}"
            ),
            parse_mode=ParseMode.HTML
        )

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "❌ Запись отменена.",
        reply_markup=main_keyboard()
    )
    return ConversationHandler.END


def get_trial_handler(trial_button: str):
    return ConversationHandler(
        entry_points=[
            MessageHandler(filters.Text([trial_button]), trial_start)
        ],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_age)],
            GOAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_goal)],
            CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_contact)],
        },
        fallbacks=[
            MessageHandler(filters.Text(["❌ Отменить", "◀️ Назад"]), cancel),
            CommandHandler("start", cancel),
        ]
    )
