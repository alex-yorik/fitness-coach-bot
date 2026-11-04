import asyncio

from app.config import DATABASE_PATH
from app.db_utils import get_connection as _create_connection


def get_connection():
    return _create_connection(DATABASE_PATH)


def init_db():
    conn = get_connection()

    conn.execute("""
    CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        name TEXT NOT NULL,
        age INTEGER,
        goal TEXT,
        contact TEXT NOT NULL
    )
    """)

    columns = [row[1] for row in conn.execute("PRAGMA table_info(applications)")]
    if "status" not in columns:
        conn.execute("ALTER TABLE applications ADD COLUMN status TEXT NOT NULL DEFAULT 'new'")

    conn.commit()
    conn.close()


def save_application(answers: dict) -> None:
    """Синхронная запись заявки. Вызывать только из рабочего потока."""
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO applications (name, age, goal, contact) VALUES (?, ?, ?, ?)",
            (answers.get("name"), answers.get("age"), answers.get("goal"), answers.get("contact")),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


async def save_application_async(answers: dict) -> None:
    """Асинхронная обёртка: sqlite3 не блокирует event loop бота."""
    await asyncio.to_thread(save_application, answers)
