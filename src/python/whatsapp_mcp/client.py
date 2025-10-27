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

    def _split_message(self, text: str, max_length: int = 4096) -> list[str]:
        """
        Split a long message into chunks that fit WhatsApp's character limit.
        Tries to split at natural boundaries (paragraphs, sentences, spaces).

        Args:
            text: The message text to split
            max_length: Maximum characters per chunk (default: 4096)

        Returns:
            List of message chunks
        """
        if len(text) <= max_length:
            return [text]

        chunks = []
        remaining = text

        while len(remaining) > max_length:
            # Try to find a good split point
            chunk = remaining[:max_length]

            # Try to split at paragraph (double newline)
            split_idx = chunk.rfind('\n\n')
            if split_idx > max_length * 0.5:  # Only use if we're past halfway
                split_idx += 2  # Include the newlines
            # Try to split at single newline
            elif (split_idx := chunk.rfind('\n')) > max_length * 0.5:
                split_idx += 1
            # Try to split at sentence end
            elif (split_idx := max(chunk.rfind('. '), chunk.rfind('! '), chunk.rfind('? '))) > max_length * 0.5:
                split_idx += 2  # Include period and space
            # Try to split at space
            elif (split_idx := chunk.rfind(' ')) > max_length * 0.5:
                split_idx += 1
            else:
                # Force split at max_length
                split_idx = max_length

            chunks.append(remaining[:split_idx].strip())
            remaining = remaining[split_idx:].strip()

        # Add remaining text
        if remaining:
            chunks.append(remaining)

        return chunks

    def send_message(self, to: str, text: str, auto_split: bool = True) -> Dict:
        """
        Send a text message to a WhatsApp user.
        Automatically splits messages longer than 4096 characters into multiple messages.

        Args:
            to: Phone number in international format (e.g., "+1234567890" or "1234567890")
            text: Message text to send
            auto_split: If True, automatically split long messages (default: True)

        Returns:
            API response dict (last message sent if split into multiple)
        """
        # Format phone number
        to = self._format_phone_number(to)

        # Validate message text
        if not text or not text.strip():
            raise ValueError("Message text cannot be empty")

        # WhatsApp has a 4096 character limit
        if len(text) > 4096:
            if auto_split:
                print(f"⚠️  Message too long ({len(text)} chars). Splitting into multiple messages...")
                chunks = self._split_message(text)
                print(f"📨 Sending {len(chunks)} messages...")

                last_response = None
                for i, chunk in enumerate(chunks, 1):
                    print(f"📤 Sending part {i}/{len(chunks)} ({len(chunk)} chars)")
                    last_response = self._send_single_message(to, chunk)
                    # Add small delay between messages to avoid rate limiting
                    if i < len(chunks):
                        import time
                        time.sleep(0.5)

                print(f"✅ All {len(chunks)} messages sent successfully")
                return last_response
            else:
                raise ValueError(f"Message text too long ({len(text)} chars). Maximum is 4096 characters")

        return self._send_single_message(to, text)

    def _send_single_message(self, to: str, text: str) -> Dict:
        """
        Send a single message (internal method, assumes text is within limit)

        Args:
            to: Formatted phone number
            text: Message text (must be <= 4096 chars)

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
