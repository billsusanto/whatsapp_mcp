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

    def _format_phone_number(self, phone: str) -> str:
        """
        Ensure phone number is in proper format for WhatsApp API

        Args:
            phone: Phone number (with or without +)

        Returns:
            Formatted phone number
        """
        # Remove any whitespace or special characters except +
        phone = ''.join(c for c in phone if c.isdigit() or c == '+')

        # Ensure it doesn't start with + if it's already there
        # WhatsApp API accepts numbers without + prefix
        if phone.startswith('+'):
            phone = phone[1:]

        return phone

    def send_message(self, to: str, text: str) -> Dict:
        """
        Send a text message to a WhatsApp user

        Args:
            to: Phone number in international format (e.g., "+1234567890" or "1234567890")
            text: Message text to send

        Returns:
            API response dict
        """
        # Format phone number
        to = self._format_phone_number(to)

        # Validate message text
        if not text or not text.strip():
            raise ValueError("Message text cannot be empty")

        # WhatsApp has a character limit
        if len(text) > 4096:
            raise ValueError(f"Message text too long ({len(text)} chars). Maximum is 4096 characters")

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
            print(f"DEBUG - Payload: {payload}")
            response = requests.post(self.messages_url, json=payload, headers=headers)
            response.raise_for_status()

            result = response.json()
            print(f"✅ Message sent successfully to {to}")
            return result

        except requests.exceptions.HTTPError as e:
            # Extract detailed error information
            error_details = {
                'status_code': e.response.status_code if e.response else 'Unknown',
                'response_body': e.response.text if e.response else 'No response',
                'url': str(e.request.url) if e.request else 'Unknown',
            }

            error_msg = f"WhatsApp API error: {str(e)}"
            print(f"❌ {error_msg}")
            print(f"❌ Status Code: {error_details['status_code']}")
            print(f"❌ Response Body: {error_details['response_body']}")
            print(f"❌ Request URL: {error_details['url']}")
            print(f"❌ Payload sent: {payload}")

            raise Exception(f"{error_msg}\nDetails: {error_details['response_body']}")

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
