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


def _trial_data():
    return load_content()["trial"]


def _trial_step(index: int) -> dict:
    return _trial_data()["steps"][index]


def _step_text(index: int) -> str:
    step = _trial_step(index)
    return f"Шаг {index + 1} из 3\n\n{step['question']}"


async def trial_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    trial = _trial_data()

    await update.message.reply_text(
        f"<b>{trial['title']}</b>\n\n"
        f"{_step_text(0)}",
        parse_mode=ParseMode.HTML,
        reply_markup=back_keyboard()
    )
    return NAME


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text(
        _step_text(1),
        reply_markup=back_keyboard()
    )
    return AGE


async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["age"] = update.message.text
    await update.message.reply_text(
        _step_text(2),
        reply_markup=back_keyboard()
    )
    return GOAL


async def get_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["goal"] = update.message.text
    await update.message.reply_text(
        _step_text(3),
        reply_markup=back_keyboard()
    )
    return CONTACT


async def get_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["contact"] = update.message.text
    trial = _trial_data()

    name = context.user_data.get("name")
    age = context.user_data.get("age")
    goal = context.user_data.get("goal")
    contact = context.user_data.get("contact")

    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO applications (name, age, goal, contact) VALUES (?, ?, ?, ?)",
            (name, age, goal, contact)
        )
        conn.commit()
        conn.close()

        await update.message.reply_text(
            trial["success"] + "\n\n"
            f"👤 Имя: {name}\n"
            f"🎂 Возраст: {age}\n"
            f"🎯 Цель: {goal}\n"
            f"📞 Контакт: {contact}\n\n"
            "Тренер свяжется с вами в ближайшее время для согласования времени пробной тренировки.",
            parse_mode=ParseMode.HTML,
            reply_markup=main_keyboard()
        )

    except Exception as e:
        conn.rollback()
        conn.close()
        await update.message.reply_text(
            "Произошла ошибка при сохранении вашей заявки. Пожалуйста, попробуйте еще раз.",
            reply_markup=main_keyboard()
        )
        print(f"Ошибка при сохранении заявки: {e}") # Логирование ошибки для отладки
        if ADMIN_CHAT_ID:
            await context.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=f"❌ Ошибка при сохранении заявки:\n\n{e}\n\nДанные: {context.user_data}",
                parse_mode=ParseMode.HTML
            )
        return ConversationHandler.END # Завершаем диалог при ошибке

    if ADMIN_CHAT_ID:
        user = update.effective_user
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=(
                f"{trial['admin_notify']}\n\n"
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
        _trial_data()["cancelled"],
        reply_markup=main_keyboard()
    )
    return ConversationHandler.END


def get_trial_handler(trial_button: str):
    normalized_button = trial_button.strip()
    button_variants = {trial_button, normalized_button}
    if normalized_button:
        button_variants.add(f"🔥 {normalized_button}")

    return ConversationHandler(
        entry_points=[
            MessageHandler(filters.Text(list(button_variants)), trial_start)
        ],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Text(["❌ Отменить", "◀️ Назад"]), get_name)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Text(["❌ Отменить", "◀️ Назад"]), get_age)],
            GOAL: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Text(["❌ Отменить", "◀️ Назад"]), get_goal)],
            CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Text(["❌ Отменить", "◀️ Назад"]), get_contact)],
        },
        fallbacks=[
            MessageHandler(filters.Text(["❌ Отменить"]), cancel),
            MessageHandler(filters.Text(["◀️ Назад"]), cancel),
            CommandHandler("start", cancel),
        ]
    )
