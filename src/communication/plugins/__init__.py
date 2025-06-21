"""
Communication Plugins
"""

from .telegram_communication import TelegramCommunication
from .email_communication import EmailCommunication
from .webhook_communication import WebhookCommunication

__all__ = [
    'TelegramCommunication',
    'EmailCommunication',
    'WebhookCommunication'
]