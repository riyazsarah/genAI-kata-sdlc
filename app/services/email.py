"""Email service for sending verification emails."""

import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class EmailServiceBase(ABC):
    """Abstract base class for email services."""

    @abstractmethod
    def send_verification_email(
        self, to_email: str, full_name: str, verification_token: str
    ) -> bool:
        """Send a verification email to the user.

        Args:
            to_email: Recipient email address.
            full_name: User's full name for personalization.
            verification_token: Token for email verification link.

        Returns:
            True if email was sent successfully, False otherwise.
        """
        pass


class MockEmailService(EmailServiceBase):
    """Mock email service for development and testing."""

    def __init__(self, base_url: str = "http://localhost:8000") -> None:
        """Initialize the mock email service.

        Args:
            base_url: Base URL for verification links.
        """
        self.base_url = base_url
        self.sent_emails: list[dict] = []

    def send_verification_email(
        self, to_email: str, full_name: str, verification_token: str
    ) -> bool:
        """Mock sending a verification email.

        Logs the email details instead of actually sending.

        Args:
            to_email: Recipient email address.
            full_name: User's full name.
            verification_token: Verification token.

        Returns:
            Always True for mock implementation.
        """
        verification_link = (
            f"{self.base_url}/api/v1/auth/verify-email?token={verification_token}"
        )

        email_data = {
            "to": to_email,
            "subject": "Verify your Farm-to-Table Marketplace account",
            "full_name": full_name,
            "verification_link": verification_link,
            "verification_token": verification_token,
        }

        self.sent_emails.append(email_data)

        logger.info(
            f"[MOCK EMAIL] Verification email would be sent to: {to_email}\n"
            f"  Subject: Verify your Farm-to-Table Marketplace account\n"
            f"  Verification Link: {verification_link}"
        )

        print(f"\n{'='*60}")
        print("MOCK EMAIL - Verification Email")
        print(f"{'='*60}")
        print(f"To: {to_email}")
        print(f"Subject: Verify your Farm-to-Table Marketplace account")
        print(f"\nHello {full_name},")
        print("\nPlease verify your email by clicking the link below:")
        print(f"\n{verification_link}")
        print(f"\nThis link will expire in 24 hours.")
        print(f"{'='*60}\n")

        return True

    def get_last_verification_token(self) -> str | None:
        """Get the last verification token sent (for testing).

        Returns:
            The last verification token or None if no emails sent.
        """
        if self.sent_emails:
            return self.sent_emails[-1].get("verification_token")
        return None


# Factory function to get email service based on configuration
def get_email_service(base_url: str = "http://localhost:8000") -> EmailServiceBase:
    """Get the appropriate email service based on configuration.

    Currently returns MockEmailService. Will be updated when SMTP is configured.

    Args:
        base_url: Base URL for verification links.

    Returns:
        An email service implementation.
    """
    # TODO: Add SMTP email service when Google SMTP credentials are provided
    return MockEmailService(base_url)


# Singleton instance for dependency injection
EmailService = MockEmailService
