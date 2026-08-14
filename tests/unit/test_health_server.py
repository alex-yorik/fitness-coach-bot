import threading
import urllib.error
import urllib.request

from app import health_server as hs


def _request(path: str) -> tuple[int, bytes]:
    server = hs.ThreadingHTTPServer(("127.0.0.1", 0), hs.HealthHandler)
    thread = threading.Thread(target=server.handle_request, daemon=True)
    thread.start()
    try:
        port = server.server_address[1]
        resp = urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=5)
        return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    finally:
        thread.join(timeout=5)
        server.server_close()


class TestHealthHandler:
    def test_healthz_ok(self, monkeypatch):
        monkeypatch.setattr(hs, "_database_ok", lambda: True)
        code, body = _request("/healthz")
        assert code == 200
        assert body == b"ok"

    def test_healthz_db_down(self, monkeypatch):
        monkeypatch.setattr(hs, "_database_ok", lambda: False)
        code, body = _request("/healthz")
        assert code == 503
        assert body == b"database unavailable"

    def test_unknown_path_returns_404(self):
        code, _ = _request("/nope")
        assert code == 404


class TestStartHealthServer:
    def test_starts_and_serves(self, monkeypatch):
        monkeypatch.setattr(hs, "HEALTH_PORT", 0)
        server = hs.start_health_server()
        try:
            port = server.server_address[1]
            resp = urllib.request.urlopen(f"http://127.0.0.1:{port}/healthz", timeout=5)
            assert resp.status == 200
        finally:
            server.shutdown()
            server.server_close()
