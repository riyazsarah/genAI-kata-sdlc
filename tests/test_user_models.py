"""Tests for user models."""

import pytest
from pydantic import ValidationError

from app.models.user import UserCreate


class TestUserCreate:
    """Tests for UserCreate model validation."""

    def test_valid_user_create(self):
        """Valid user data should create successfully."""
        user = UserCreate(
            full_name="John Doe",
            email="john.doe@example.com",
            password="SecurePass123!",
            phone="+1234567890",
        )

        assert user.full_name == "John Doe"
        assert user.email == "john.doe@example.com"
        assert user.password == "SecurePass123!"
        assert user.phone == "+1234567890"

    def test_valid_user_without_phone(self):
        """User without phone should be valid."""
        user = UserCreate(
            full_name="John Doe",
            email="john.doe@example.com",
            password="SecurePass123!",
        )

        assert user.phone is None

    def test_invalid_email_format(self):
        """Invalid email format should raise validation error."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                full_name="John Doe",
                email="invalid-email",
                password="SecurePass123!",
            )

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("email",) for error in errors)

    def test_email_missing_domain(self):
        """Email without domain should raise validation error."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                full_name="John Doe",
                email="john@",
                password="SecurePass123!",
            )

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("email",) for error in errors)

    def test_weak_password_too_short(self):
        """Password less than 8 characters should fail."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                full_name="John Doe",
                email="john@example.com",
                password="Abc1!",
            )

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("password",) for error in errors)

    def test_weak_password_no_uppercase(self):
        """Password without uppercase should fail."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                full_name="John Doe",
                email="john@example.com",
                password="securepass123!",
            )

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("password",) for error in errors)

    def test_weak_password_no_special_char(self):
        """Password without special character should fail."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                full_name="John Doe",
                email="john@example.com",
                password="SecurePass123",
            )

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("password",) for error in errors)

    def test_full_name_too_short(self):
        """Full name less than 2 characters should fail."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                full_name="J",
                email="john@example.com",
                password="SecurePass123!",
            )

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("full_name",) for error in errors)

    def test_full_name_whitespace_cleaning(self):
        """Full name with extra whitespace should be cleaned."""
        user = UserCreate(
            full_name="  John   Doe  ",
            email="john@example.com",
            password="SecurePass123!",
        )

        assert user.full_name == "John Doe"

    def test_full_name_only_whitespace(self):
        """Full name with only whitespace should fail."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                full_name="   ",
                email="john@example.com",
                password="SecurePass123!",
            )

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("full_name",) for error in errors)

    def test_phone_max_length(self):
        """Phone number exceeding max length should fail."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                full_name="John Doe",
                email="john@example.com",
                password="SecurePass123!",
                phone="+" + "1" * 25,  # 26 characters
            )

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("phone",) for error in errors)

    def test_valid_international_phone(self):
        """International phone formats should be valid."""
        user = UserCreate(
            full_name="John Doe",
            email="john@example.com",
            password="SecurePass123!",
            phone="+91-9876543210",
        )

        assert user.phone == "+91-9876543210"

    def test_email_domain_is_lowercased_by_pydantic(self):
        """Email domain is lowercased by Pydantic EmailStr validation."""
        user = UserCreate(
            full_name="John Doe",
            email="John.Doe@Example.COM",
            password="SecurePass123!",
        )

        # Pydantic EmailStr lowercases the domain part
        assert user.email == "John.Doe@example.com"
