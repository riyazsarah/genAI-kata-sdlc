"""Pytest configuration and fixtures."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def valid_user_data() -> dict:
    """Return valid user registration data."""
    return {
        "full_name": "John Doe",
        "email": "john.doe@example.com",
        "password": "SecurePass123!",
        "phone": "+1234567890",
    }


@pytest.fixture
def weak_password_data() -> dict:
    """Return user data with a weak password."""
    return {
        "full_name": "John Doe",
        "email": "john.weak@example.com",
        "password": "123",
        "phone": "+1234567890",
    }


@pytest.fixture
def invalid_email_data() -> dict:
    """Return user data with an invalid email."""
    return {
        "full_name": "John Doe",
        "email": "invalid-email",
        "password": "SecurePass123!",
        "phone": "+1234567890",
    }
