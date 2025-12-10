"""Email service for sending verification emails."""

import logging
import os
import smtplib
from abc import ABC, abstractmethod
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

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

    @abstractmethod
    def send_password_reset_email(
        self, to_email: str, full_name: str, reset_token: str
    ) -> bool:
        """Send a password reset email to the user.

        Args:
            to_email: Recipient email address.
            full_name: User's full name for personalization.
            reset_token: Token for password reset link.

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
        print("Subject: Verify your Farm-to-Table Marketplace account")
        print(f"\nHello {full_name},")
        print("\nPlease verify your email by clicking the link below:")
        print(f"\n{verification_link}")
        print("\nThis link will expire in 24 hours.")
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

    def send_password_reset_email(
        self, to_email: str, full_name: str, reset_token: str
    ) -> bool:
        """Mock sending a password reset email.

        Args:
            to_email: Recipient email address.
            full_name: User's full name.
            reset_token: Password reset token.

        Returns:
            Always True for mock implementation.
        """
        reset_link = f"{self.base_url}/reset-password?token={reset_token}"

        email_data = {
            "to": to_email,
            "subject": "Reset your Farm-to-Table Marketplace password",
            "full_name": full_name,
            "reset_link": reset_link,
            "reset_token": reset_token,
            "type": "password_reset",
        }

        self.sent_emails.append(email_data)

        logger.info(
            f"[MOCK EMAIL] Password reset email would be sent to: {to_email}\n"
            f"  Subject: Reset your Farm-to-Table Marketplace password\n"
            f"  Reset Link: {reset_link}"
        )

        print(f"\n{'='*60}")
        print("MOCK EMAIL - Password Reset")
        print(f"{'='*60}")
        print(f"To: {to_email}")
        print("Subject: Reset your Farm-to-Table Marketplace password")
        print(f"\nHello {full_name},")
        print("\nWe received a request to reset your password.")
        print("\nClick the link below to reset your password:")
        print(f"\n{reset_link}")
        print("\nThis link will expire in 1 hour.")
        print("\nIf you didn't request this, you can safely ignore this email.")
        print(f"{'='*60}\n")

        return True


class SMTPEmailService(EmailServiceBase):
    """SMTP email service for sending real emails."""

    def __init__(self, base_url: str = "http://localhost:8000") -> None:
        """Initialize the SMTP email service.

        Args:
            base_url: Base URL for verification links.
        """
        self.base_url = base_url
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("SMTP_FROM_EMAIL", self.smtp_user)
        self.from_name = os.getenv("SMTP_FROM_NAME", "Farm-to-Table Marketplace")

    def send_verification_email(
        self, to_email: str, full_name: str, verification_token: str
    ) -> bool:
        """Send a verification email via SMTP.

        Args:
            to_email: Recipient email address.
            full_name: User's full name.
            verification_token: Verification token.

        Returns:
            True if email was sent successfully, False otherwise.
        """
        verification_link = (
            f"{self.base_url}/api/v1/auth/verify-email?token={verification_token}"
        )

        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Verify your Farm-to-Table Marketplace account"
        msg["From"] = f"{self.from_name} <{self.from_email}>"
        msg["To"] = to_email

        # Plain text version
        text_content = f"""
Hello {full_name},

Welcome to Farm-to-Table Marketplace!

Please verify your email address by clicking the link below:

{verification_link}

This link will expire in 24 hours.

If you didn't create an account, you can safely ignore this email.

Best regards,
The Farm-to-Table Marketplace Team
        """.strip()

        # HTML version
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #2e7d32; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f9f9f9; }}
        .button {{ display: inline-block; padding: 12px 24px; background-color: #2e7d32; color: white; text-decoration: none; border-radius: 4px; margin: 20px 0; }}
        .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Farm-to-Table Marketplace</h1>
        </div>
        <div class="content">
            <h2>Hello {full_name},</h2>
            <p>Welcome to Farm-to-Table Marketplace!</p>
            <p>Please verify your email address by clicking the button below:</p>
            <p style="text-align: center;">
                <a href="{verification_link}" class="button">Verify Email Address</a>
            </p>
            <p>Or copy and paste this link into your browser:</p>
            <p style="word-break: break-all; font-size: 12px;">{verification_link}</p>
            <p><strong>This link will expire in 24 hours.</strong></p>
            <p>If you didn't create an account, you can safely ignore this email.</p>
        </div>
        <div class="footer">
            <p>Best regards,<br>The Farm-to-Table Marketplace Team</p>
        </div>
    </div>
</body>
</html>
        """.strip()

        msg.attach(MIMEText(text_content, "plain"))
        msg.attach(MIMEText(html_content, "html"))

        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.from_email, to_email, msg.as_string())

            logger.info(f"Verification email sent successfully to: {to_email}")
            return True

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed: {e}")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending email to {to_email}: {e}")
            return False

    def send_password_reset_email(
        self, to_email: str, full_name: str, reset_token: str
    ) -> bool:
        """Send a password reset email via SMTP.

        Args:
            to_email: Recipient email address.
            full_name: User's full name.
            reset_token: Password reset token.

        Returns:
            True if email was sent successfully, False otherwise.
        """
        reset_link = f"{self.base_url}/reset-password?token={reset_token}"

        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Reset your Farm-to-Table Marketplace password"
        msg["From"] = f"{self.from_name} <{self.from_email}>"
        msg["To"] = to_email

        text_content = f"""
Hello {full_name},

We received a request to reset your password.

Click the link below to reset your password:

{reset_link}

This link will expire in 1 hour.

If you didn't request this, you can safely ignore this email.

Best regards,
The Farm-to-Table Marketplace Team
        """.strip()

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #2e7d32; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f9f9f9; }}
        .button {{ display: inline-block; padding: 12px 24px; background-color: #e74c3c; color: white; text-decoration: none; border-radius: 4px; margin: 20px 0; }}
        .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Farm-to-Table Marketplace</h1>
        </div>
        <div class="content">
            <h2>Hello {full_name},</h2>
            <p>We received a request to reset your password.</p>
            <p>Click the button below to reset your password:</p>
            <p style="text-align: center;">
                <a href="{reset_link}" class="button">Reset Password</a>
            </p>
            <p>Or copy and paste this link into your browser:</p>
            <p style="word-break: break-all; font-size: 12px;">{reset_link}</p>
            <p><strong>This link will expire in 1 hour.</strong></p>
            <p>If you didn't request this, you can safely ignore this email.</p>
        </div>
        <div class="footer">
            <p>Best regards,<br>The Farm-to-Table Marketplace Team</p>
        </div>
    </div>
</body>
</html>
        """.strip()

        msg.attach(MIMEText(text_content, "plain"))
        msg.attach(MIMEText(html_content, "html"))

        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.from_email, to_email, msg.as_string())

            logger.info(f"Password reset email sent successfully to: {to_email}")
            return True

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed: {e}")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending email to {to_email}: {e}")
            return False


# Factory function to get email service based on configuration
def get_email_service(base_url: str = "http://localhost:8000") -> EmailServiceBase:
    """Get the appropriate email service based on configuration.

    Returns SMTPEmailService if SMTP credentials are configured, otherwise MockEmailService.

    Args:
        base_url: Base URL for verification links.

    Returns:
        An email service implementation.
    """
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")

    if smtp_user and smtp_password:
        logger.info("Using SMTP email service")
        return SMTPEmailService(base_url)
    else:
        logger.info("SMTP not configured, using mock email service")
        return MockEmailService(base_url)


# Singleton instance for dependency injection
EmailService = SMTPEmailService if os.getenv("SMTP_USER") else MockEmailService
