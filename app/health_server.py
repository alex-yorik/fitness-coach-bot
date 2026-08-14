import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from app.database import get_connection
from app.logging_config import get_logger

HEALTH_HOST = os.getenv("HEALTH_HOST", "0.0.0.0")  # nosec B104 - для проверки снаружи
HEALTH_PORT = int(os.getenv("HEALTH_PORT", "8001"))

logger = get_logger(__name__)


def _database_ok() -> bool:
    try:
        conn = get_connection()
        conn.execute("SELECT 1")
        conn.close()
    except Exception:
        return False
    return True


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path != "/healthz":
            self.send_error(404)
            return
        if _database_ok():
            self._send(200, b"ok")
        else:
            self._send(503, b"database unavailable")

    def _send(self, status: int, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:
        logger.info("health_server: %s", format % args)


def start_health_server() -> ThreadingHTTPServer:
    server = ThreadingHTTPServer((HEALTH_HOST, HEALTH_PORT), HealthHandler)
    thread = threading.Thread(target=server.serve_forever, name="health-server", daemon=True)
    thread.start()
    return server
