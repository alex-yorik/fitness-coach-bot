from html import escape

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from app.config import ADMIN_CHAT_ID
from app.content_loader import load_content
from app.database import get_connection
from app.keyboards import back_keyboard, main_keyboard
from app.validators import validate_answer

NAME, AGE, GOAL, CONTACT = range(4)


def _trial_data():
    return load_content()["trial"]


def _trial_step(index: int) -> dict:
    return _trial_data()["steps"][index]


STEP_STATES = [NAME, AGE, GOAL, CONTACT]
STEP_KEYS = ["name", "age", "goal", "contact"]


def _step_text(index: int, answers=None) -> str:
    step = _trial_step(index)
    message = f"Шаг {index + 1} из {len(STEP_STATES)}\n\n{step['question']}"

    if answers:
        saved_answer = answers.get(STEP_KEYS[index])
        if saved_answer:
            message += (
                f"\n\nТекущий ответ: {saved_answer}\nВведите новый ответ, чтобы изменить его."
            )

    return message


async def trial_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    trial = _trial_data()

    await update.message.reply_text(
        f"<b>{trial['title']}</b>\n\n{_step_text(0)}",
        parse_mode=ParseMode.HTML,
        reply_markup=back_keyboard(),
    )
    return NAME


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    step = _trial_step(0)
    ok, _ = validate_answer(step.get("validation", "text"), update.message.text)
    if not ok:
        await update.message.reply_text(
            step.get("error", "⚠️ Некорректный ответ, попробуйте ещё раз."),
            reply_markup=back_keyboard(),
        )
        return NAME

    context.user_data["name"] = update.message.text
    context.user_data["trial_step"] = 1
    await update.message.reply_text(_step_text(1, context.user_data), reply_markup=back_keyboard())
    return AGE


async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    step = _trial_step(1)
    ok, _ = validate_answer(step.get("validation", "age"), update.message.text)
    if not ok:
        await update.message.reply_text(
            step.get("error", "⚠️ Некорректный ответ, попробуйте ещё раз."),
            reply_markup=back_keyboard(),
        )
        return AGE

    context.user_data["age"] = update.message.text
    context.user_data["trial_step"] = 2
    await update.message.reply_text(_step_text(2, context.user_data), reply_markup=back_keyboard())
    return GOAL


async def get_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    step = _trial_step(2)
    ok, _ = validate_answer(step.get("validation", "text"), update.message.text)
    if not ok:
        await update.message.reply_text(
            step.get("error", "⚠️ Некорректный ответ, попробуйте ещё раз."),
            reply_markup=back_keyboard(),
        )
        return GOAL

    context.user_data["goal"] = update.message.text
    context.user_data["trial_step"] = 3
    await update.message.reply_text(_step_text(3, context.user_data), reply_markup=back_keyboard())
    return CONTACT


async def _save_application(context: ContextTypes.DEFAULT_TYPE, answers: dict) -> None:
    """Сохраняет заявку в БД, логирует ошибку и уведомляет администратора."""

    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO applications (name, age, goal, contact) VALUES (?, ?, ?, ?)",
            (answers.get("name"), answers.get("age"), answers.get("goal"), answers.get("contact")),
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Ошибка при сохранении заявки: {e}")
        if ADMIN_CHAT_ID:
            await context.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=f"❌ Ошибка при сохранении заявки:\n\n{escape(str(e))}\n\n"
                f"Данные: {escape(str(answers))}",
                parse_mode=ParseMode.HTML,
            )
        raise
    finally:
        conn.close()


async def _success_reply(update: Update, answers: dict) -> None:
    """Отправляет пользователю сообщение об успешном сохранении заявки."""

    success_text = (
        f"{_trial_data()['success']}\n\n"
        f"👤 Имя: {escape(answers.get('name', 'не указано'))}\n"
        f"🎂 Возраст: {escape(answers.get('age', 'не указано'))}\n"
        f"🎯 Цель: {escape(answers.get('goal', 'не указано'))}\n"
        f"📞 Контакт: {escape(answers.get('contact', 'не указано'))}"
    )
    await update.message.reply_text(
        success_text, parse_mode=ParseMode.HTML, reply_markup=main_keyboard()
    )


async def get_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    step = _trial_step(3)
    ok, _ = validate_answer(step.get("validation", "contact"), update.message.text)
    if not ok:
        await update.message.reply_text(
            step.get("error", "⚠️ Некорректный ответ, попробуйте ещё раз."),
            reply_markup=back_keyboard(),
        )
        return CONTACT

    context.user_data["contact"] = update.message.text
    context.user_data["trial_step"] = 3

    try:
        await _save_application(context, context.user_data)
    except Exception:
        context.user_data.clear()
        await update.message.reply_text(
            "Произошла ошибка при сохранении вашей заявки. Пожалуйста, попробуйте еще раз.",
            reply_markup=main_keyboard(),
        )
        return ConversationHandler.END

    await _success_reply(update, context.user_data)
    context.user_data.clear()
    return ConversationHandler.END


async def back_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    current_step = context.user_data.get("trial_step", 0)
    if current_step == 0:
        await update.message.reply_text("Вы уже на первом шаге.", reply_markup=back_keyboard())
        return STEP_STATES[current_step]

    previous_step = current_step - 1
    context.user_data["trial_step"] = previous_step

    await update.message.reply_text(
        _step_text(previous_step, context.user_data), reply_markup=back_keyboard()
    )
    return STEP_STATES[previous_step]


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(_trial_data()["cancelled"], reply_markup=main_keyboard())
    return ConversationHandler.END


def get_trial_handler(trial_button: str):
    normalized_button = trial_button.strip()
    button_variants = {trial_button, normalized_button}
    if normalized_button:
        button_variants.add(f"🔥 {normalized_button}")

    return ConversationHandler(
        entry_points=[MessageHandler(filters.Text(list(button_variants)), trial_start)],
        states={
            NAME: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND & ~filters.Text(["❌ Отменить", "◀️ Назад"]),
                    get_name,
                )
            ],
            AGE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND & ~filters.Text(["❌ Отменить", "◀️ Назад"]),
                    get_age,
                )
            ],
            GOAL: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND & ~filters.Text(["❌ Отменить", "◀️ Назад"]),
                    get_goal,
                )
            ],
            CONTACT: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND & ~filters.Text(["❌ Отменить", "◀️ Назад"]),
                    get_contact,
                )
            ],
        },
        fallbacks=[
            MessageHandler(filters.Text(["❌ Отменить"]), cancel),
            MessageHandler(filters.Text(["◀️ Назад"]), back_step),
            CommandHandler("start", cancel),
        ],
    )
