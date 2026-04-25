"""Notification provider interfaces and implementations.

This module contains the base notification provider interface and concrete
implementations for different notification channels (email, SMS, etc.).
"""

import smtplib
from abc import ABC, abstractmethod
from email.message import EmailMessage
from typing import Any

import structlog

logger = structlog.getLogger(__name__)


class NotificationProvider(ABC):
    """Abstract base class for all notification providers.

    Subclasses must implement the send method to deliver notifications
    through their specific channel (email, SMS, push, etc.).
    """

    @abstractmethod
    def send(
        self,
        recipient: str,
        subject: str,
        message: str,
        **kwargs: Any,
    ) -> bool:
        """Send a notification to the specified recipient.

        Args:
            recipient: The recipient's address (email, phone, user ID, etc.)
            subject: The notification subject/title
            message: The notification message body
            **kwargs: Additional provider-specific parameters

        Returns:
            True if the notification was sent successfully, False otherwise
        """


class EmailNotificationProvider(NotificationProvider):
    """Email notification provider using SMTP.

    This provider uses Python's smtplib to send email notifications via
    a configured SMTP server (Gmail by default).
    """

    def __init__(
        self,
        sender_email: str,
        sender_password: str,
        smtp_server: str = 'smtp.gmail.com',
        smtp_port: int = 587,
    ) -> None:
        """Initialize the email notification provider.

        Args:
            sender_email: Email address to send from
            sender_password: Authentication password (app password for Gmail)
            smtp_server: SMTP server hostname (default: Gmail)
            smtp_port: SMTP server port (default: 587 for TLS)
        """
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port

    def send(
        self,
        recipient: str,
        subject: str,
        message: str,
        **kwargs: Any,
    ) -> bool:
        """Send an email notification.

        Args:
            recipient: Recipient's email address
            subject: Email subject line
            message: Email body (plain text)
            **kwargs: Additional email-specific parameters:
                - html_content (str): HTML version of the message
                - cc (list[str]): CC recipients
                - bcc (list[str]): BCC recipients

        Returns:
            True if email was sent successfully, False otherwise
        """
        try:
            msg = EmailMessage()
            msg['Subject'] = subject
            msg['From'] = self.sender_email
            msg['To'] = recipient

            # Add CC and BCC if provided
            if cc := kwargs.get('cc'):
                msg['Cc'] = ', '.join(cc) if isinstance(cc, list) else cc
            if bcc := kwargs.get('bcc'):
                msg['Bcc'] = ', '.join(bcc) if isinstance(bcc, list) else bcc

            # Set message content
            msg.set_content(message)

            # Add HTML alternative if provided
            if html_content := kwargs.get('html_content'):
                msg.add_alternative(html_content, subtype='html')

            # Connect to SMTP server and send
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)

            logger.info(f'Email notification sent to {recipient}')
            return True

        except smtplib.SMTPException as e:
            logger.error(f'SMTP error sending email to {recipient}: {e}')
            return False
        except Exception as e:
            logger.error(f'Unexpected error sending email to {recipient}: {e}')
            return False


class TelegramNotificationProvider(NotificationProvider):
    """Telegram notification provider.

    This is a placeholder implementation that can be extended in the future
    to send notifications via Telegram Bot API.
    """

    def __init__(self, bot_token: str) -> None:
        """Initialize the Telegram notification provider.

        Args:
            bot_token: Telegram Bot API token
        """
        self.bot_token = bot_token

    def send(
        self,
        recipient: str,
        subject: str,
        message: str,
        **kwargs: Any,
    ) -> bool:
        """Send a Telegram notification.

        Args:
            recipient: Telegram chat ID or username
            subject: Message subject (used as first line or ignored)
            message: Message content
            **kwargs: Additional Telegram-specific parameters

        Returns:
            True if message was sent successfully, False otherwise
        """
        # TODO: Implement Telegram Bot API integration
        logger.warning('Telegram notifications not yet implemented')
        return False
