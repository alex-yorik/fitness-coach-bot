from telegram.ext import Application, CommandHandler, MessageHandler, filters

from app.config import BOT_TOKEN
from app.database import init_db
from app.handlers.start import start
from app.handlers.pages import show_about, show_formats, show_parents, show_main_menu
from app.handlers.trial import get_trial_handler
from app.content_loader import load_content


def main():
    init_db()

    if not BOT_TOKEN:
        print("❌ BOT_TOKEN не найден в .env")
        return

    data = load_content()
    trial_button = data["trial"]["button"]

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(get_trial_handler(trial_button))

    app.add_handler(CommandHandler("start", start))

    app.add_handler(MessageHandler(
        filters.Text([data["about"]["title"]]), show_about
    ))
    app.add_handler(MessageHandler(
        filters.Text([data["formats"]["title"]]), show_formats
    ))
    app.add_handler(MessageHandler(
        filters.Text([data["parents"]["title"]]), show_parents
    ))
    app.add_handler(MessageHandler(
        filters.Text(["◀️ Назад", "❌ Отменить"]), show_main_menu
    ))

    print("✅ TeacherBot запущен")
    app.run_polling()


if __name__ == "__main__":
    main()
