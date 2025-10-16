"""
WhatsApp Business API Client

This module handles all interactions with the WhatsApp Business API.
It will be used by BOTH:
- Next.js webhook handler (via API calls)
- MCP server (directly)
"""

import os
import requests
from typing import Dict, List, Optional


class WhatsAppClient:
    """Client for interacting with WhatsApp Business Cloud API"""

    def __init__(self):
        """
        Initialize the WhatsApp client

        TODO:
        - Load WHATSAPP_ACCESS_TOKEN from environment
        - Load WHATSAPP_PHONE_NUMBER_ID from environment
        - Set up the base API URL: https://graph.facebook.com/v18.0/{phone_number_id}/messages
        """
        pass

    def send_message(self, to: str, text: str) -> Dict:
        """
        Send a text message to a WhatsApp user

        Args:
            to: Phone number in international format (e.g., "+1234567890")
            text: Message text to send

        Returns:
            API response dict

        TODO:
        - Create POST request to WhatsApp API
        - Set headers with Authorization: Bearer {access_token}
        - Send JSON payload:
          {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": text}
          }
        - Handle errors (rate limits, invalid numbers, etc.)
        - Return response

        DOCS: https://developers.facebook.com/docs/whatsapp/cloud-api/guides/send-messages
        """
        pass

    def mark_as_read(self, message_id: str) -> Dict:
        """
        Mark a message as read

        Args:
            message_id: The WhatsApp message ID to mark as read

        TODO:
        - Send POST to /messages endpoint
        - Payload: {"messaging_product": "whatsapp", "status": "read", "message_id": message_id}

        DOCS: https://developers.facebook.com/docs/whatsapp/cloud-api/guides/mark-message-as-read
        """
        pass

    def get_media(self, media_id: str) -> Dict:
        """
        Get media file information (for images, videos, etc.)

        Args:
            media_id: The WhatsApp media ID

        TODO:
        - GET request to https://graph.facebook.com/v18.0/{media_id}
        - Return media URL and metadata

        DOCS: https://developers.facebook.com/docs/whatsapp/cloud-api/reference/media
        """
        pass
