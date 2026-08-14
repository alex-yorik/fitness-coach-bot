import hashlib
import hmac
import os
import tempfile

_TEST_SECRET = "test-secret-key-for-unit-tests"
TEST_PASSWORD = "test-admin-password"
TEST_USERNAME = "admin"

os.environ["SECRET_KEY"] = _TEST_SECRET
os.environ["FLASK_USERNAME"] = TEST_USERNAME
os.environ["SESSION_COOKIE_SECURE"] = "False"
os.environ["DATABASE_PATH"] = os.path.join(tempfile.mkdtemp(), "web_test.db")
os.environ["FLASK_PASSWORD_HASH"] = hmac.new(
    _TEST_SECRET.encode(), TEST_PASSWORD.encode(), hashlib.sha256
).hexdigest()

os.environ["LOG_PATH"] = os.path.join(tempfile.mkdtemp(), "bot.log")
os.environ["WEB_LOG_PATH"] = os.path.join(tempfile.mkdtemp(), "web.log")
os.environ["HEALTH_PORT"] = "18001"

CREATE_APPLICATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    name TEXT NOT NULL,
    age INTEGER,
    goal TEXT,
    contact TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'new'
)
"""
