"""Real loopback HTTP proves transport, not a live MLS/provider deployment."""

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from api.index import app


class Upstream(BaseHTTPRequestHandler):
    calls = []

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        self.calls.append((self.path, body, self.headers.get("Authorization")))
        if body.get("q") == "reject":
            self.send_response(429)
            data = {"detail": "private upstream diagnostics"}
        elif body.get("q") == "redirect":
            self.send_response(307)
            self.send_header("Location", "http://127.0.0.1:9/leak")
            data = {}
        else:
            self.send_response(200)
            data = {"query": body.get("q"), "listings": [], "total": 0}
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def log_message(self, *args):
        pass


@pytest.fixture
def upstream(monkeypatch):
    Upstream.calls.clear()
    server = ThreadingHTTPServer(("127.0.0.1", 0), Upstream)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setenv("QUERY_SERVICE_URL", f"http://127.0.0.1:{server.server_port}")
    yield server
    server.shutdown()
    server.server_close()
    thread.join()


def test_no_config_never_returns_fake_credentials_results_or_progress(monkeypatch):
    monkeypatch.delenv("QUERY_SERVICE_URL", raising=False)
    monkeypatch.delenv("AUTH_SERVICE_URL", raising=False)
    with app.test_client() as client:
        assert (
            client.post("/api/query/search_pipeline", json={"q": "Denver"}).status_code
            == 503
        )
        assert (
            client.post(
                "/api/auth/login", json={"username": "demo", "password": "demo"}
            ).status_code
            == 503
        )
        assert (
            client.post("/api/auth/register", json={"password": "secret"}).status_code
            == 503
        )
        assert (
            client.post(
                "/api/browser-agent/execute", json={"workflow_id": 1}
            ).status_code
            == 503
        )
        assert client.get("/api/browser-agent/status/nonexistent").status_code == 404
        assert client.post("/api/search", json={"query": "Denver"}).status_code == 410


def test_real_http_forwards_exact_query_and_bearer(upstream):
    with app.test_client() as client:
        response = client.post(
            "/api/query/search_pipeline",
            json={"q": "Denver", "limit": 20},
            headers={"Authorization": "Bearer fixture-only"},
        )
    assert response.status_code == 200
    assert response.json["total"] == 0
    assert Upstream.calls == [
        ("/search_pipeline", {"q": "Denver", "limit": 20}, "Bearer fixture-only")
    ]


def test_provider_rejection_is_preserved_without_leaking_diagnostics(upstream):
    with app.test_client() as client:
        response = client.post("/api/query/search_pipeline", json={"q": "reject"})
    assert response.status_code == 429
    assert "private" not in response.get_data(as_text=True)


def test_no_redirect_replays_credentials(upstream):
    with app.test_client() as client:
        response = client.post(
            "/api/query/search_pipeline",
            json={"q": "redirect"},
            headers={"Authorization": "Bearer fixture-only"},
        )
    assert response.status_code == 502
    assert len(Upstream.calls) == 1


@pytest.mark.parametrize(
    "url",
    [
        "http://example.org",
        "https://name:password@example.org",
        "https://example.org?key=secret",
        "",
    ],
)
def test_invalid_service_config_fails_closed(monkeypatch, url):
    monkeypatch.setenv("QUERY_SERVICE_URL", url)
    with app.test_client() as client:
        assert (
            client.post("/api/query/search_pipeline", json={"q": "Denver"}).status_code
            == 503
        )


def test_unknown_paths_do_not_contact_service(upstream):
    with app.test_client() as client:
        assert client.post("/api/query/delete-index", json={}).status_code == 404
        assert client.post("/api/auth/me", json={}).status_code == 404
    assert not Upstream.calls
