import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

FLASK_USERNAME = os.getenv("FLASK_USERNAME")
FLASK_PASSWORD = os.getenv("FLASK_PASSWORD")

DATABASE_PATH = os.getenv(
    "DATABASE_PATH",
    "/app/data/database.db"
)
