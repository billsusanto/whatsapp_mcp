"""
WhatsApp Business API Client

This module handles all interactions with the WhatsApp Business API.
"""

import os
import requests
from typing import Dict, List, Optional


class WhatsAppClient:
    """Client for interacting with WhatsApp Business Cloud API"""

    def __init__(self):
        """Initialize the WhatsApp client with credentials from environment"""
        self.access_token = os.getenv('WHATSAPP_ACCESS_TOKEN')
        self.phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')

        if not self.access_token or not self.phone_number_id:
            raise ValueError(
                "WhatsApp credentials not configured. Set WHATSAPP_ACCESS_TOKEN and WHATSAPP_PHONE_NUMBER_ID"
            )

        self.api_version = "v18.0"
        self.base_url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}"
        self.messages_url = f"{self.base_url}/messages"

        print(f"WhatsApp client initialized for phone ID: {self.phone_number_id}")

    def send_message(self, to: str, text: str) -> Dict:
        """
        Send a text message to a WhatsApp user

        Args:
            to: Phone number in international format (e.g., "+1234567890")
            text: Message text to send

        Returns:
            API response dict
        """
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": text}
        }

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        try:
            print(f"Sending message to {to}: {text[:50]}...")
            response = requests.post(self.messages_url, json=payload, headers=headers)
            response.raise_for_status()

            result = response.json()
            print(f"✅ Message sent successfully to {to}")
            return result

        except requests.exceptions.HTTPError as e:
            error_msg = f"WhatsApp API error: {e.response.text if e.response else str(e)}"
            print(f"❌ {error_msg}")
            raise Exception(error_msg)

        except Exception as e:
            print(f"❌ Error sending message: {str(e)}")
            raise

    def mark_as_read(self, message_id: str) -> Dict:
        """
        Mark a message as read

        Args:
            message_id: The WhatsApp message ID to mark as read

        Returns:
            API response dict
        """
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(self.messages_url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()

        except Exception as e:
            print(f"Error marking message as read: {str(e)}")
            raise

    def get_media(self, media_id: str) -> Dict:
        """
        Get media file information (for images, videos, etc.)

        Args:
            media_id: The WhatsApp media ID

        Returns:
            Media information dict with URL and metadata
        """
        media_url = f"https://graph.facebook.com/{self.api_version}/{media_id}"
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }

        try:
            response = requests.get(media_url, headers=headers)
            response.raise_for_status()
            return response.json()

        except Exception as e:
            print(f"Error fetching media: {str(e)}")
            raise

    def download_media(self, media_url: str) -> bytes:
        """
        Download media file from WhatsApp

        Args:
            media_url: The media URL from get_media()

        Returns:
            Media file bytes
        """
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }

        try:
            response = requests.get(media_url, headers=headers)
            response.raise_for_status()
            return response.content

        except Exception as e:
            print(f"Error downloading media: {str(e)}")
            raise
