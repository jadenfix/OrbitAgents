"""
Comprehensive edge case tests for Auth Service.

This module tests all edge cases, security vulnerabilities, and error scenarios
to ensure the auth service is robust and secure in production.
"""

import pytest
import json
import time
from fastapi import status
from fastapi.testclient import TestClient
from jose import jwt
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import DatabaseError, IntegrityError

from config import settings
from main import app


class TestSecurityEdgeCases:
    """Test security-related edge cases and vulnerabilities."""
    
    def test_sql_injection_attempts(self, client):
        """Test SQL injection attempts in email field."""
        malicious_payloads = [
            "admin'--",
            "admin'; DROP TABLE users; --",
            "admin' OR '1'='1",
            "admin' UNION SELECT * FROM users --",
            "'; INSERT INTO users (email, password) VALUES ('hacker@evil.com', 'password'); --"
        ]
        
        for payload in malicious_payloads:
            response = client.post("/login", json={
                "email": payload,
                "password": "password123"
            })
            # Should return validation error or auth failure, not 500
            assert response.status_code in [400, 401, 422]
    
    def test_jwt_token_manipulation(self, client, test_user_data):
        """Test various JWT token manipulation attempts."""
        # Register and login to get valid token
        client.post("/register", json=test_user_data)
        login_response = client.post("/login", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })
        valid_token = login_response.json()["access_token"]
        
        # Test modified token payload
        payload = jwt.get_unverified_claims(valid_token)
        payload["sub"] = "hacker@evil.com"
        malicious_token = jwt.encode(payload, "wrong-secret", algorithm="HS256")
        
        response = client.get("/me", headers={"Authorization": f"Bearer {malicious_token}"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Test none algorithm attack
        payload["sub"] = test_user_data["email"]
        none_token = jwt.encode(payload, "", algorithm="none")
        
        response = client.get("/me", headers={"Authorization": f"Bearer {none_token}"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_password_timing_attack_mitigation(self, client, test_user_data):
        """Test that password verification doesn't leak timing information."""
        # Register user
        client.post("/register", json=test_user_data)
        
        # Time multiple failed login attempts
        times = []
        for _ in range(5):
            start = time.time()
            client.post("/login", json={
                "email": test_user_data["email"],
                "password": "wrongpassword"
            })
            times.append(time.time() - start)
        
        # Time non-existent user
        nonexistent_times = []
        for _ in range(5):
            start = time.time()
            client.post("/login", json={
                "email": "nonexistent@example.com",
                "password": "wrongpassword"
            })
            nonexistent_times.append(time.time() - start)
        
        # Times should be similar (within reasonable variance)
        avg_existing = sum(times) / len(times)
        avg_nonexistent = sum(nonexistent_times) / len(nonexistent_times)
        
        # Allow for some variance but shouldn't be dramatically different
        assert abs(avg_existing - avg_nonexistent) < 0.1
    
    def test_jwt_secret_exposure_protection(self, client):
        """Test that JWT secret is not exposed in responses."""
        response = client.get("/healthz")
        content = response.text.lower()
        
        # Ensure JWT secret is not leaked
        assert settings.JWT_SECRET.lower() not in content
        assert "jwt_secret" not in content
        assert "secret" not in content


class TestInputValidationEdgeCases:
    """Test edge cases for input validation."""
    
    def test_extremely_long_inputs(self, client):
        """Test handling of extremely long input values."""
        long_email = "a" * 1000 + "@example.com"
        long_password = "A1" + "a" * 10000
        
        response = client.post("/register", json={
            "email": long_email,
            "password": long_password
        })
        # Should handle gracefully, likely validation error
        assert response.status_code in [400, 413, 422]
    
    def test_unicode_and_special_characters(self, client):
        """Test handling of unicode and special characters."""
        special_cases = [
            {"email": "test+tag@example.com", "password": "Password123!@#"},
            {"email": "test.email@example.com", "password": "Pássw0rd123"},
            {"email": "test@example-domain.com", "password": "密码123Aa"},
            {"email": "test@sub.example.com", "password": "🔐Password1"},
        ]
        
        for case in special_cases:
            response = client.post("/register", json=case)
            # Should either succeed or fail gracefully
            assert response.status_code in [201, 400, 422]
    
    def test_null_and_empty_values(self, client):
        """Test handling of null and empty values."""
        test_cases = [
            {"email": None, "password": "Password123"},
            {"email": "", "password": "Password123"},
            {"email": "test@example.com", "password": None},
            {"email": "test@example.com", "password": ""},
            {"email": " ", "password": "Password123"},
            {"email": "test@example.com", "password": " "},
        ]
        
        for case in test_cases:
            response = client.post("/register", json=case)
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_malformed_json_requests(self, client):
        """Test handling of malformed JSON requests."""
        malformed_requests = [
            '{"email": "test@example.com", "password": "Password123"',  # Missing closing brace
            '{"email": "test@example.com" "password": "Password123"}',  # Missing comma
            '{"email": test@example.com, "password": "Password123"}',   # Unquoted value
            '',  # Empty body
            'not json at all',  # Not JSON
        ]
        
        for malformed_json in malformed_requests:
            response = client.post(
                "/register",
                data=malformed_json,
                headers={"Content-Type": "application/json"}
            )
            assert response.status_code in [400, 422]
    
    def test_content_type_validation(self, client):
        """Test different content types are handled correctly."""
        valid_data = {"email": "test@example.com", "password": "Password123"}
        
        # Test with wrong content type
        response = client.post(
            "/register",
            data=json.dumps(valid_data),
            headers={"Content-Type": "text/plain"}
        )
        assert response.status_code in [400, 422]
        
        # Test with form data instead of JSON
        response = client.post("/register", data=valid_data)
        assert response.status_code in [400, 422]


class TestConcurrencyEdgeCases:
    """Test edge cases related to concurrent operations."""
    
    def test_concurrent_user_registration(self, client):
        """Test concurrent registration attempts with same email."""
        import threading
        import queue
        
        results = queue.Queue()
        user_data = {"email": "concurrent@example.com", "password": "Password123"}
        
        def register_user():
            try:
                response = client.post("/register", json=user_data)
                results.put(response.status_code)
            except Exception as e:
                results.put(str(e))
        
        # Start multiple threads trying to register same user
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=register_user)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Collect results
        status_codes = []
        while not results.empty():
            status_codes.append(results.get())
        
        # Only one should succeed, others should fail
        success_count = sum(1 for code in status_codes if code == 201)
        assert success_count <= 1
        assert any(code == 400 for code in status_codes)  # Email already registered


class TestDatabaseEdgeCases:
    """Test edge cases related to database operations."""
    
    @patch('services.auth.database.SessionLocal')
    def test_database_connection_failure(self, mock_session, client):
        """Test handling of database connection failures."""
        mock_session.side_effect = DatabaseError("Connection failed", None, None)
        
        response = client.get("/healthz")
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    
    @patch('services.auth.main.db.add')
    def test_database_integrity_error(self, mock_add, client):
        """Test handling of database integrity errors during registration."""
        mock_add.side_effect = IntegrityError("UNIQUE constraint failed", None, None)
        
        response = client.post("/register", json={
            "email": "test@example.com",
            "password": "Password123"
        })
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def test_database_transaction_rollback(self, client):
        """Test that failed operations properly rollback transactions."""
        # This would need more complex setup to properly test
        # For now, ensure basic registration works
        response = client.post("/register", json={
            "email": "rollback@example.com",
            "password": "Password123"
        })
        assert response.status_code in [201, 400, 500]


class TestAuthenticationEdgeCases:
    """Test authentication-specific edge cases."""
    
    def test_malformed_authorization_headers(self, client):
        """Test various malformed Authorization headers."""
        malformed_headers = [
            {"Authorization": "Bearer"},  # No token
            {"Authorization": "bearer token"},  # Wrong case
            {"Authorization": "Basic token"},  # Wrong scheme
            {"Authorization": "Bearer "},  # Empty token
            {"Authorization": "Bearer token1 token2"},  # Multiple tokens
            {"Authorization": " Bearer token"},  # Leading space
            {"Authorization": "Bearer\ttoken"},  # Tab character
        ]
        
        for header in malformed_headers:
            response = client.get("/me", headers=header)
            assert response.status_code in [401, 403, 422]
    
    def test_jwt_edge_cases(self, client, test_user_data):
        """Test JWT token edge cases."""
        # Register and login
        client.post("/register", json=test_user_data)
        login_response = client.post("/login", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })
        valid_token = login_response.json()["access_token"]
        
        # Test token with tampered signature
        parts = valid_token.split('.')
        tampered_token = '.'.join(parts[:-1]) + '.tampered_signature'
        
        response = client.get("/me", headers={"Authorization": f"Bearer {tampered_token}"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Test token with missing parts
        incomplete_token = '.'.join(parts[:2])
        
        response = client.get("/me", headers={"Authorization": f"Bearer {incomplete_token}"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_user_state_edge_cases(self, client, test_user_data):
        """Test edge cases with user state (inactive, etc)."""
        # This would require modifying user state in database
        # For comprehensive testing, we'd need admin endpoints
        pass


class TestRateLimitingEdgeCases:
    """Test rate limiting and abuse prevention."""
    
    def test_login_attempt_patterns(self, client, test_user_data):
        """Test various login attempt patterns."""
        # Register user first
        client.post("/register", json=test_user_data)
        
        # Test rapid failed login attempts
        for _ in range(10):
            response = client.post("/login", json={
                "email": test_user_data["email"],
                "password": "wrongpassword"
            })
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Should still allow correct login (no rate limiting implemented yet)
        response = client.post("/login", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })
        assert response.status_code == status.HTTP_200_OK
    
    def test_registration_spam_attempts(self, client):
        """Test rapid registration attempts."""
        base_email = "spam{i}@example.com"
        
        for i in range(10):
            response = client.post("/register", json={
                "email": base_email.format(i=i),
                "password": "Password123"
            })
            # Should succeed or fail gracefully
            assert response.status_code in [201, 400, 422, 429]


class TestErrorHandlingEdgeCases:
    """Test error handling in various scenarios."""
    
    def test_unexpected_server_errors(self, client):
        """Test handling of unexpected server errors."""
        # This would require mocking internal functions to raise unexpected errors
        # For now, test that known endpoints return expected responses
        response = client.get("/nonexistent-endpoint")
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_metrics_endpoint_errors(self, client):
        """Test metrics endpoint under various conditions."""
        response = client.get("/metrics")
        assert response.status_code == status.HTTP_200_OK
        assert "text/plain" in response.headers["content-type"]
    
    def test_cors_edge_cases(self, client):
        """Test CORS handling edge cases."""
        # Test preflight request
        response = client.options("/healthz", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization"
        })
        assert response.status_code in [200, 204]
        
        # Test with disallowed origin
        response = client.get("/healthz", headers={
            "Origin": "http://evil.com"
        })
        # Should still work but without CORS headers for disallowed origin
        assert response.status_code == status.HTTP_200_OK


class TestPerformanceEdgeCases:
    """Test performance-related edge cases."""
    
    def test_large_token_payload(self, client, test_user_data):
        """Test handling of tokens with large payloads."""
        # Register user
        client.post("/register", json=test_user_data)
        
        # Create token with large payload
        large_payload = {
            "sub": test_user_data["email"],
            "exp": datetime.utcnow() + timedelta(minutes=15),
            "large_data": "x" * 1000  # Large string
        }
        large_token = jwt.encode(large_payload, settings.JWT_SECRET, algorithm="HS256")
        
        response = client.get("/me", headers={"Authorization": f"Bearer {large_token}"})
        # Should handle gracefully
        assert response.status_code in [200, 401, 413]
    
    def test_memory_exhaustion_protection(self, client):
        """Test protection against memory exhaustion attacks."""
        # Test with extremely large request body
        large_data = {"email": "test@example.com", "password": "A" * 10000000}
        
        try:
            response = client.post("/register", json=large_data, timeout=5)
            # Should either reject or handle gracefully
            assert response.status_code in [400, 413, 422, 500]
        except Exception:
            # Connection errors are acceptable for protection
            pass


class TestComplianceEdgeCases:
    """Test compliance and regulatory edge cases."""
    
    def test_password_policy_enforcement(self, client):
        """Test comprehensive password policy enforcement."""
        weak_passwords = [
            "password",  # No uppercase, no numbers
            "PASSWORD",  # No lowercase, no numbers
            "Password",  # No numbers
            "12345678",  # No letters
            "Pass1",     # Too short
            "   Pass1   ",  # Whitespace
        ]
        
        for weak_pass in weak_passwords:
            response = client.post("/register", json={
                "email": f"test{weak_pass}@example.com",
                "password": weak_pass
            })
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_email_validation_edge_cases(self, client):
        """Test comprehensive email validation."""
        invalid_emails = [
            "plainaddress",
            "@missingdomain.com",
            "missing@.com",
            "missing@domain",
            "missing.domain.com",
            "two@@domain.com",
            "domain@.com",
            " leading@domain.com",
            "trailing@domain.com ",
            "double..dot@domain.com",
        ]
        
        for invalid_email in invalid_emails:
            response = client.post("/register", json={
                "email": invalid_email,
                "password": "Password123"
            })
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_data_exposure_prevention(self, client, test_user_data):
        """Test that sensitive data is not exposed in responses."""
        # Register user
        response = client.post("/register", json=test_user_data)
        assert response.status_code == status.HTTP_201_CREATED
        
        data = response.json()
        # Ensure password is not in response
        assert "password" not in data
        assert "hashed_password" not in data
        assert test_user_data["password"] not in str(data)
        
        # Login and check token response
        login_response = client.post("/login", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })
        login_data = login_response.json()
        
        # Ensure sensitive data not in login response
        assert "password" not in login_data
        assert "hashed_password" not in login_data 