import pytest

import app.database as database


@pytest.fixture
def db(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test.db")
    monkeypatch.setattr(database, "DATABASE_PATH", db_path)
    return db_path


class TestInitDb:
    def test_creates_tables(self, db):
        database.init_db()
        conn = database.get_connection()
        columns = [row[1] for row in conn.execute("PRAGMA table_info(applications)")]
        conn.close()
        assert columns == ["id", "created_at", "name", "age", "goal", "contact", "status"]

    def test_status_default_is_new(self, db):
        database.init_db()
        conn = database.get_connection()
        conn.execute(
            "INSERT INTO applications (name, age, goal, contact) VALUES (?, ?, ?, ?)",
            ("Иван", 30, "Цель", "@ivan"),
        )
        row = conn.execute("SELECT status FROM applications WHERE id=1").fetchone()
        conn.close()
        assert row[0] == "new"

    def test_idempotent(self, db):
        database.init_db()
        database.init_db()
        conn = database.get_connection()
        count = conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='applications'"
        ).fetchone()[0]
        conn.close()
        assert count == 1

    def test_migrates_status_column(self, db, monkeypatch):
        conn = database.get_connection()
        conn.execute("""
            CREATE TABLE applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                contact TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()

        database.init_db()

        conn = database.get_connection()
        columns = [row[1] for row in conn.execute("PRAGMA table_info(applications)")]
        conn.close()
        assert "status" in columns

    def test_row_factory(self, db):
        database.init_db()
        conn = database.get_connection()
        conn.execute("INSERT INTO applications (name, contact) VALUES ('Иван', '@ivan')")
        row = conn.execute("SELECT name FROM applications WHERE id=1").fetchone()
        conn.close()
        assert row["name"] == "Иван"


@pytest.mark.parametrize(
    "name,age,goal,contact",
    [
        ("Иван", 30, "Похудение", "@ivan"),
        ("Петр", None, None, "+79991234567"),
        ("Без имени", 0, "", "user@example.com"),
    ],
)
class TestSaveApplication:
    def test_save_and_read(self, db, name, age, goal, contact):
        database.init_db()
        conn = database.get_connection()
        conn.execute(
            "INSERT INTO applications (name, age, goal, contact) VALUES (?, ?, ?, ?)",
            (name, age, goal, contact),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM applications WHERE id=1").fetchone()
        conn.close()

        assert row["name"] == name
        assert row["age"] == age
        assert row["goal"] == goal
        assert row["contact"] == contact
        assert row["status"] == "new"
        assert row["created_at"] is not None
