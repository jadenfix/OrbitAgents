"""
Pytest configuration and fixtures for Auth service tests.
"""

import importlib
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set testing environment before importing app modules
os.environ["RATE_LIMIT_ENABLED"] = "false"

app = importlib.import_module("main").app
_database = importlib.import_module("database")
Base = _database.Base
get_db = _database.get_db


@pytest.fixture(scope="function")
def db_session(tmp_path):
    """Isolate each test in its own file database, with separate pooled connections."""
    engine = create_engine(
        f"sqlite:///{tmp_path / 'auth.sqlite'}",
        connect_args={"check_same_thread": False},
    )
    testing_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        with testing_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        with testing_session() as session:
            yield session
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def test_user_data():
    """Sample user data for testing."""
    return {"email": "test@example.com", "password": "SecurePass129"}


@pytest.fixture
def test_user_invalid_data():
    """Invalid user data for testing."""
    return {"email": "invalid-email", "password": "weak"}
