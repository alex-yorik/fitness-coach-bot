from functools import partial

from telegram.ext import Application, CommandHandler, MessageHandler, filters

from app.config import BOT_TOKEN
from app.content_loader import load_content
from app.database import init_db
from app.handlers.pages import show_content_page, show_main_menu  # Импортируем новую функцию
from app.handlers.start import start
from app.handlers.trial import get_trial_handler
from app.health_server import start_health_server
from app.logging_config import get_logger, setup_logging

logger = get_logger(__name__)


def main():
    setup_logging()
    init_db()

    if not BOT_TOKEN:
        logger.error("BOT_TOKEN не найден в .env")
        return

    start_health_server()

    data = load_content()
    trial_button = data["trial"]["button"]

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(get_trial_handler(trial_button))

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("exit", show_main_menu))  # /exit теперь ведет на главное меню

    # Регистрация обработчиков для статических страниц
    page_sections = {
        "about": data["about"]["title"],
        "formats": data["formats"]["title"],
        "gallery": data["gallery"]["title"],
    }
    if "parents" in data and "title" in data["parents"]:
        page_sections["parents"] = data["parents"]["title"]

    for section_key, button_text in page_sections.items():
        app.add_handler(
            MessageHandler(
                filters.Text([button_text]), partial(show_content_page, section_key=section_key)
            )
        )

    # Обработчики для кнопок "Назад" и "Отменить"
    app.add_handler(MessageHandler(filters.Text(["◀️ Назад"]), show_main_menu))
    app.add_handler(MessageHandler(filters.Text(["❌ Отменить"]), show_main_menu))
    app.add_handler(
        CommandHandler("menu", show_main_menu)
    )  # Добавляем команду /menu для главного меню

    logger.info("FitnessCoach запущен")
    app.run_polling()


if __name__ == "__main__":
    main()
