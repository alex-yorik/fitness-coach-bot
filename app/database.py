import asyncio
import os
import sqlite3

from app.config import DATABASE_PATH


def get_connection():
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row

    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")

    return conn


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
