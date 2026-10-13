"""
Basic integration tests for the auth service main application.
"""

from main import app


class TestMainApplication:
    """Test the main FastAPI application setup."""

    def test_app_creation(self):
        """Test that the FastAPI app is created successfully."""
        assert app is not None
        assert app.title == "OrbitAgents Auth Service"
        assert app.version == "1.0.0"

    def test_docs_endpoints(self, client):
        """Test that documentation endpoints are accessible."""
        # Test OpenAPI docs
        response = client.get("/docs")
        assert response.status_code == 200

        # Test ReDoc
        response = client.get("/redoc")
        assert response.status_code == 200

        # Test OpenAPI schema
        response = client.get("/openapi.json")
        assert response.status_code == 200
        assert "openapi" in response.json()

    def test_cors_headers(self, client):
        """Test that CORS headers are properly configured."""
        response = client.options(
            "/healthz",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        # CORS preflight should be handled
        assert response.status_code in [200, 204]


def test_rate_limit_policy_and_window(monkeypatch):
    from config import settings
    from main import is_rate_limited, rate_limit_storage

    monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", True)
    monkeypatch.setenv("TESTING", "true")
    rate_limit_storage.clear()
    monkeypatch.setattr("main.time.time", lambda: 100.0)
    assert not is_rate_limited("policy-fixture", max_requests=1, window_seconds=10)
    assert is_rate_limited("policy-fixture", max_requests=1, window_seconds=10)
    monkeypatch.setattr("main.time.time", lambda: 111.0)
    assert not is_rate_limited("policy-fixture", max_requests=1, window_seconds=10)
    rate_limit_storage.clear()
