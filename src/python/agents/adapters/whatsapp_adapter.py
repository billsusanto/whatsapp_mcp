"""
WhatsApp Notification Adapter

Implements NotificationAdapter for WhatsApp Business API.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from .notification import NotificationAdapter
from whatsapp_mcp.client import WhatsAppClient


class WhatsAppAdapter(NotificationAdapter):
    """
    WhatsApp platform adapter.

    Uses WhatsAppClient to send messages via WhatsApp Business Cloud API.
    """

    def __init__(self, client: WhatsAppClient):
        """
        Initialize WhatsApp adapter.

        Args:
            client: WhatsAppClient instance for sending messages
        """
        self.client = client
        print("✅ WhatsApp notification adapter initialized")

    async def send_message(self, phone_number: str, message: str) -> None:
        """
        Send a WhatsApp message to a phone number.

        Args:
            phone_number: Recipient phone number (e.g., "+1234567890")
            message: Message text to send

        Raises:
            Exception: If WhatsApp API call fails
        """
        try:
            self.client.send_message(phone_number, message)
            print(f"📱 WhatsApp message sent to {phone_number}: {message[:50]}...")
        except Exception as e:
            print(f"❌ Failed to send WhatsApp message to {phone_number}: {e}")
            raise

    async def send_reaction(self, message_id: str, reaction: str) -> None:
        """
        React to a WhatsApp message.

        Note:
            WhatsApp Business API may have limited reaction support.
            This is a placeholder for future implementation.

        Args:
            message_id: WhatsApp message ID
            reaction: Reaction emoji
        """
        # WhatsApp reactions API support is limited
        # Log for now, can be implemented when API supports it
        print(f"⚠️  WhatsApp reactions not fully supported. Message: {message_id}, Reaction: {reaction}")

    def get_platform_name(self) -> str:
        """Get platform identifier."""
        return "whatsapp"
