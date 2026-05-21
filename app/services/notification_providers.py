"""Notification provider interfaces and implementations.

This module contains the base notification provider interface and concrete
implementations for different notification channels (email, SMS, etc.).
"""

import asyncio
import smtplib
import ssl
from abc import ABC, abstractmethod
from email.message import EmailMessage
from functools import partial
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

    async def async_send(
        self,
        recipient: str,
        subject: str,
        message: str,
        **kwargs: Any,
    ) -> bool:
        """Non-blocking async wrapper around send().

        Runs the blocking send() in a thread-pool executor so it does not
        block the asyncio event loop.

        Returns:
            True if the notification was sent successfully, False otherwise
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            partial(self.send, recipient, subject, message, **kwargs),
        )

    async def async_send_batch(
        self,
        messages: list[dict[str, Any]],
    ) -> list[bool]:
        """Send multiple notifications; default falls back to individual sends.

        Subclasses may override to use a more efficient batched transport.
        """
        results = []
        for item in messages:
            ok = await self.async_send(
                item['recipient'],
                item['subject'],
                item['message'],
                **{k: v for k, v in item.items() if k not in ('recipient', 'subject', 'message')},
            )
            results.append(ok)
        return results


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
        smtp_port: int = 465,
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

    @staticmethod
    def _build_message(
        sender: str,
        recipient: str,
        subject: str,
        message: str,
        **kwargs: Any,
    ) -> EmailMessage:
        """Build an EmailMessage object."""
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = recipient

        if cc := kwargs.get('cc'):
            msg['Cc'] = ', '.join(cc) if isinstance(cc, list) else cc
        if bcc := kwargs.get('bcc'):
            msg['Bcc'] = ', '.join(bcc) if isinstance(bcc, list) else bcc

        msg.set_content(message)

        if html_content := kwargs.get('html_content'):
            msg.add_alternative(html_content, subtype='html')

        return msg

    def send(
        self,
        recipient: str,
        subject: str,
        message: str,
        **kwargs: Any,
    ) -> bool:
        """Send an email notification (opens a fresh SMTP connection).

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
            msg = self._build_message(self.sender_email, recipient, subject, message, **kwargs)
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, timeout=10, context=context) as server:
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)

            logger.info(f'Email notification sent to {recipient}')
            return True

        except smtplib.SMTPException as e:
            logger.error(f'SMTP error sending email to {recipient}: {e}')
            return False
        except (TimeoutError, OSError) as e:
            logger.error(f'Connection/timeout error sending email to {recipient}: {e}')
            return False
        except Exception as e:
            logger.error(f'Unexpected error sending email to {recipient}: {e}')
            return False

    def send_batch(
        self,
        messages: list[dict[str, Any]],
    ) -> list[bool]:
        """Send multiple emails over a single SMTP connection.

        Each item in *messages* must have keys:
            recipient, subject, message
        and optional keyword keys (html_content, cc, bcc).

        Opening one connection instead of N separate ones avoids Gmail's
        per-second connection rate limit that silently drops some emails.

        Returns:
            List of bool (True = sent, False = failed) in the same order.
        """
        if not messages:
            return []

        logger.info(f'send_batch called with {len(messages)} messages')
        results: list[bool] = []
        try:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, timeout=10, context=context) as server:
                server.login(self.sender_email, self.sender_password)
                for idx, item in enumerate(messages):
                    recipient = item['recipient']
                    try:
                        msg = self._build_message(
                            self.sender_email,
                            recipient,
                            item['subject'],
                            item['message'],
                            **{k: v for k, v in item.items() if k not in ('recipient', 'subject', 'message')},
                        )
                        server.send_message(msg)
                        logger.info(f'Batch email [{idx + 1}/{len(messages)}] sent to {recipient}')
                        results.append(True)
                    except smtplib.SMTPException as e:
                        logger.error(f'SMTP error in batch send [{idx + 1}/{len(messages)}] to {recipient}: {e}')
                        results.append(False)
        except (smtplib.SMTPException, TimeoutError, OSError) as e:
            logger.error(f'Failed to open SMTP connection for batch send: {e}')
            # Mark all remaining (unsent) as failed
            results.extend([False] * (len(messages) - len(results)))
        except Exception as e:
            logger.error(f'Unexpected error in batch send: {e}')
            results.extend([False] * (len(messages) - len(results)))

        logger.info(f'send_batch finished: {sum(results)}/{len(messages)} sent')
        return results

    async def async_send_batch(
        self,
        messages: list[dict[str, Any]],
    ) -> list[bool]:
        """Non-blocking async wrapper around send_batch().

        Runs the blocking send_batch() in a thread-pool executor.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, partial(self.send_batch, messages))


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
