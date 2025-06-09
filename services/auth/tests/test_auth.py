"""
Unit tests for Auth service endpoints.
"""

import pytest
from fastapi import status
from jose import jwt
from datetime import datetime, timedelta

from config import settings


class TestHealthCheck:
    """Test health check endpoint."""
    
    def test_health_check_success(self, client):
        """Test successful health check."""
        response = client.get("/healthz")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "auth"
        assert data["version"] == "1.0.0"
        assert "timestamp" in data


class TestUserRegistration:
    """Test user registration endpoint."""
    
    def test_register_success(self, client, test_user_data):
        """Test successful user registration."""
        response = client.post("/register", json=test_user_data)
        assert response.status_code == status.HTTP_201_CREATED
        
        data = response.json()
        assert data["email"] == test_user_data["email"]
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data
        assert "password" not in data  # Password should not be returned
    
    def test_register_duplicate_email(self, client, test_user_data):
        """Test registration with duplicate email."""
        # Register first user
        client.post("/register", json=test_user_data)
        
        # Try to register same email again
        response = client.post("/register", json=test_user_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Email already registered" in response.json()["detail"]
    
    def test_register_invalid_email(self, client):
        """Test registration with invalid email."""
        invalid_data = {
            "email": "invalid-email",
            "password": "TestPassword123"
        }
        response = client.post("/register", json=invalid_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_register_weak_password(self, client):
        """Test registration with weak password."""
        weak_password_data = {
            "email": "test@example.com",
            "password": "weak"
        }
        response = client.post("/register", json=weak_password_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_register_missing_fields(self, client):
        """Test registration with missing fields."""
        incomplete_data = {"email": "test@example.com"}
        response = client.post("/register", json=incomplete_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestUserLogin:
    """Test user login endpoint."""
    
    def test_login_success(self, client, test_user_data):
        """Test successful user login."""
        # First register a user
        client.post("/register", json=test_user_data)
        
        # Then login
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        response = client.post("/login", json=login_data)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["token_type"] == "bearer"
        assert "access_token" in data
        assert data["expires_in"] == 900  # 15 minutes
        
        # Verify JWT token is valid
        token = data["access_token"]
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        assert payload["sub"] == test_user_data["email"]
    
    def test_login_invalid_email(self, client):
        """Test login with non-existent email."""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "TestPassword123"
        }
        response = client.post("/login", json=login_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Incorrect email or password" in response.json()["detail"]
    
    def test_login_wrong_password(self, client, test_user_data):
        """Test login with wrong password."""
        # Register user
        client.post("/register", json=test_user_data)
        
        # Login with wrong password
        login_data = {
            "email": test_user_data["email"],
            "password": "WrongPassword123"
        }
        response = client.post("/login", json=login_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Incorrect email or password" in response.json()["detail"]
    
    def test_login_invalid_email_format(self, client):
        """Test login with invalid email format."""
        login_data = {
            "email": "invalid-email",
            "password": "TestPassword123"
        }
        response = client.post("/login", json=login_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_login_missing_fields(self, client):
        """Test login with missing fields."""
        incomplete_data = {"email": "test@example.com"}
        response = client.post("/login", json=incomplete_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestProtectedEndpoints:
    """Test protected endpoints that require authentication."""
    
    def test_get_current_user_success(self, client, test_user_data):
        """Test getting current user info with valid token."""
        # Register and login
        client.post("/register", json=test_user_data)
        login_response = client.post("/login", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })
        token = login_response.json()["access_token"]
        
        # Get current user
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/me", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["email"] == test_user_data["email"]
        assert data["is_active"] is True
    
    def test_get_current_user_no_token(self, client):
        """Test getting current user without token."""
        response = client.get("/me")
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_get_current_user_invalid_token(self, client):
        """Test getting current user with invalid token."""
        headers = {"Authorization": "Bearer invalid-token"}
        response = client.get("/me", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_current_user_expired_token(self, client, test_user_data):
        """Test getting current user with expired token."""
        # Create expired token
        expired_payload = {
            "sub": test_user_data["email"],
            "exp": datetime.utcnow() - timedelta(minutes=1)
        }
        expired_token = jwt.encode(expired_payload, settings.JWT_SECRET, algorithm="HS256")
        
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = client.get("/me", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestMetrics:
    """Test metrics endpoint."""
    
    def test_metrics_endpoint(self, client):
        """Test metrics endpoint returns Prometheus format."""
        response = client.get("/metrics")
        assert response.status_code == status.HTTP_200_OK
        assert "text/plain" in response.headers["content-type"]
        
        # Check for basic metrics
        content = response.text
        assert "http_requests_total" in content
        assert "http_request_duration_seconds" in content
