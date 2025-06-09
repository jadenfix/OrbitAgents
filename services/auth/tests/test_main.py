"""
Basic integration tests for the auth service main application.
"""

import pytest
from fastapi.testclient import TestClient
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
        response = client.options("/healthz", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET"
        })
        # CORS preflight should be handled
        assert response.status_code in [200, 204] 