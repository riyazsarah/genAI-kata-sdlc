"""Tests for security utilities."""

from datetime import datetime, timedelta, timezone

import pytest

from app.core.security import (
    PasswordValidator,
    generate_verification_token,
    get_verification_expiry,
    hash_password,
    is_token_expired,
    verify_password,
)


class TestPasswordHashing:
    """Tests for password hashing functions."""

    def test_hash_password_returns_different_hash(self):
        """Password hash should be different from plain password."""
        password = "SecurePass123!"
        hashed = hash_password(password)

        assert hashed != password
        assert len(hashed) > 0

    def test_hash_password_produces_unique_hashes(self):
        """Same password should produce different hashes (due to salt)."""
        password = "SecurePass123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2

    def test_verify_password_correct(self):
        """Correct password should verify successfully."""
        password = "SecurePass123!"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Incorrect password should fail verification."""
        password = "SecurePass123!"
        wrong_password = "WrongPass123!"
        hashed = hash_password(password)

        assert verify_password(wrong_password, hashed) is False

    def test_password_is_stored_securely(self):
        """Password hash should use bcrypt format."""
        password = "SecurePass123!"
        hashed = hash_password(password)

        # Bcrypt hashes start with $2b$ (or $2a$, $2y$)
        assert hashed.startswith("$2")
        # Bcrypt hashes are typically 60 characters
        assert len(hashed) == 60


class TestPasswordValidator:
    """Tests for password validation."""

    def test_valid_password(self):
        """Valid password should pass validation."""
        password = "SecurePass123!"
        is_valid, errors = PasswordValidator.validate(password)

        assert is_valid is True
        assert errors == []

    def test_password_too_short(self):
        """Short password should fail validation."""
        password = "Abc1!"
        is_valid, errors = PasswordValidator.validate(password)

        assert is_valid is False
        assert any("8 characters" in error for error in errors)

    def test_password_missing_uppercase(self):
        """Password without uppercase should fail validation."""
        password = "securepass123!"
        is_valid, errors = PasswordValidator.validate(password)

        assert is_valid is False
        assert any("uppercase" in error for error in errors)

    def test_password_missing_lowercase(self):
        """Password without lowercase should fail validation."""
        password = "SECUREPASS123!"
        is_valid, errors = PasswordValidator.validate(password)

        assert is_valid is False
        assert any("lowercase" in error for error in errors)

    def test_password_missing_digit(self):
        """Password without digit should fail validation."""
        password = "SecurePass!"
        is_valid, errors = PasswordValidator.validate(password)

        assert is_valid is False
        assert any("digit" in error for error in errors)

    def test_password_missing_special_char(self):
        """Password without special character should fail validation."""
        password = "SecurePass123"
        is_valid, errors = PasswordValidator.validate(password)

        assert is_valid is False
        assert any("special character" in error for error in errors)

    def test_password_multiple_errors(self):
        """Password with multiple issues should return all errors."""
        password = "abc"
        is_valid, errors = PasswordValidator.validate(password)

        assert is_valid is False
        assert len(errors) >= 3  # Too short, missing uppercase, digit, special

    def test_get_requirements_message(self):
        """Requirements message should include all requirements."""
        message = PasswordValidator.get_requirements_message()

        assert "8 characters" in message
        assert "uppercase" in message
        assert "lowercase" in message
        assert "digit" in message
        assert "special" in message


class TestVerificationToken:
    """Tests for verification token generation and expiry."""

    def test_generate_verification_token_is_uuid(self):
        """Generated token should be a valid UUID string."""
        token = generate_verification_token()

        # UUID format: 8-4-4-4-12 characters
        assert len(token) == 36
        assert token.count("-") == 4

    def test_generate_verification_token_is_unique(self):
        """Each generated token should be unique."""
        tokens = [generate_verification_token() for _ in range(100)]

        assert len(set(tokens)) == 100

    def test_get_verification_expiry_default(self):
        """Default expiry should be 24 hours from now."""
        before = datetime.now(timezone.utc)
        expiry = get_verification_expiry()
        after = datetime.now(timezone.utc)

        expected_min = before + timedelta(hours=24)
        expected_max = after + timedelta(hours=24)

        assert expected_min <= expiry <= expected_max

    def test_get_verification_expiry_custom_hours(self):
        """Custom hours parameter should work."""
        before = datetime.now(timezone.utc)
        expiry = get_verification_expiry(hours=48)
        after = datetime.now(timezone.utc)

        expected_min = before + timedelta(hours=48)
        expected_max = after + timedelta(hours=48)

        assert expected_min <= expiry <= expected_max

    def test_is_token_expired_none(self):
        """None expiry should be considered expired."""
        assert is_token_expired(None) is True

    def test_is_token_expired_past(self):
        """Past datetime should be expired."""
        past = datetime.now(timezone.utc) - timedelta(hours=1)
        assert is_token_expired(past) is True

    def test_is_token_expired_future(self):
        """Future datetime should not be expired."""
        future = datetime.now(timezone.utc) + timedelta(hours=1)
        assert is_token_expired(future) is False

    def test_is_token_expired_naive_datetime(self):
        """Naive datetime should be handled correctly."""
        # Create a naive datetime in the future
        future = datetime.now() + timedelta(hours=1)
        assert is_token_expired(future) is False

        # Create a naive datetime in the past
        past = datetime.now() - timedelta(hours=1)
        assert is_token_expired(past) is True
