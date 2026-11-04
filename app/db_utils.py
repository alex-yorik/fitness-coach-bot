import os
import sqlite3


def get_connection(db_path: str) -> sqlite3.Connection:
    """Создаёт соединение SQLite с общими PRAGMA."""
    directory = os.path.dirname(db_path)
    if directory:
        os.makedirs(directory, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn
