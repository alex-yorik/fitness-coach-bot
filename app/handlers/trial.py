import logging
import time
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
from app.database import save_application_async
from app.keyboards import back_keyboard, main_keyboard
from app.validators import validate_answer

logger = logging.getLogger(__name__)

NAME, AGE, GOAL, CONTACT = range(4)

RATE_LIMIT_SECONDS = 60.0
_last_submission_at: dict[int, float] = {}
_submitted_users: set[int] = set()


def _user_id(update: Update) -> int | None:
    user = getattr(update, "effective_user", None)
    if user is not None:
        return getattr(user, "id", None)

    message = getattr(update, "message", None)
    from_user = getattr(message, "from_user", None) if message is not None else None
    return getattr(from_user, "id", None) if from_user is not None else None


def _submission_block(user_id: int | None) -> tuple[str, bool] | None:
    """Возвращает текст блокировки и признак завершения диалога."""
    if user_id is None:
        return None

    last_attempt = _last_submission_at.get(user_id)
    if last_attempt is not None and time.monotonic() - last_attempt < RATE_LIMIT_SECONDS:
        return "Подождите минуту перед следующей отправкой", False

    if user_id in _submitted_users:
        return "Вы уже отправляли заявку. Повторная отправка недоступна.", True

    return None


def _answers_summary(answers: dict) -> str:
    fields = [
        ("👤 Имя", "name"),
        ("🎂 Возраст", "age"),
        ("🎯 Цель", "goal"),
        ("📞 Контакт", "contact"),
    ]
    return "\n".join(
        f"{label}: {escape(str(answers.get(key, 'не указано')))}" for label, key in fields
    )


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
    """Сохраняет заявку в рабочем потоке, логирует ошибку и уведомляет администратора."""

    try:
        await save_application_async(answers)
    except Exception as e:
        logger.error("Ошибка при сохранении заявки: %s", e)
        if ADMIN_CHAT_ID:
            await context.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text="❌ Ошибка при сохранении заявки:\n\n"
                f"{escape(str(e))}\n\n"
                f"Данные:\n{_answers_summary(answers)}",
                parse_mode=ParseMode.HTML,
            )
        raise


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
    user_id = _user_id(update)
    block = _submission_block(user_id)
    if block is not None:
        message, terminal = block
        await update.message.reply_text(message, reply_markup=main_keyboard())
        return ConversationHandler.END if terminal else CONTACT

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

    if user_id is not None:
        _last_submission_at[user_id] = time.monotonic()

    try:
        await _save_application(context, context.user_data)
    except Exception:
        context.user_data.clear()
        await update.message.reply_text(
            "Произошла ошибка при сохранении вашей заявки. Пожалуйста, попробуйте еще раз.",
            reply_markup=main_keyboard(),
        )
        return ConversationHandler.END

    if user_id is not None:
        _submitted_users.add(user_id)

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
