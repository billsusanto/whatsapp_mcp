"""
WhatsApp Webhook Parser

Parses incoming webhook payloads from WhatsApp Business API
"""

from typing import Dict, List, Optional


class WhatsAppWebhookParser:
    """Parser for WhatsApp webhook payloads"""

    @staticmethod
    def parse_message(webhook_data: Dict) -> Optional[Dict]:
        """
        Parse a WhatsApp webhook payload and extract message data

        Args:
            webhook_data: The webhook payload from WhatsApp

        Returns:
            Parsed message dict or None if no valid message
            {
                "from": str,           # Sender's phone number
                "message_id": str,     # WhatsApp message ID
                "timestamp": str,      # Message timestamp
                "type": str,           # Message type (text, image, etc.)
                "text": str,           # Message text (if type is text)
                "media": Dict          # Media info (if type is media)
            }
        """
        try:
            # Navigate nested webhook structure
            entry = webhook_data.get('entry', [])
            if not entry:
                return None

            changes = entry[0].get('changes', [])
            if not changes:
                return None

            value = changes[0].get('value', {})

            # Check if this is a status update (not a message)
            if 'statuses' in value:
                return None  # Ignore status updates

            # Extract messages
            messages = value.get('messages', [])
            if not messages:
                return None

            message = messages[0]

            # Build result dict
            result = {
                "from": message.get('from'),
                "message_id": message.get('id'),
                "timestamp": message.get('timestamp'),
                "type": message.get('type', 'text')
            }

            # Extract content based on message type
            message_type = message.get('type')

            if message_type == 'text':
                text_data = message.get('text', {})
                result["text"] = text_data.get('body', '')

            elif message_type == 'image':
                image_data = message.get('image', {})
                result["media"] = {
                    "id": image_data.get('id'),
                    "mime_type": image_data.get('mime_type'),
                    "sha256": image_data.get('sha256'),
                    "caption": image_data.get('caption', '')
                }

            elif message_type == 'video':
                video_data = message.get('video', {})
                result["media"] = {
                    "id": video_data.get('id'),
                    "mime_type": video_data.get('mime_type'),
                    "sha256": video_data.get('sha256'),
                    "caption": video_data.get('caption', '')
                }

            elif message_type == 'audio':
                audio_data = message.get('audio', {})
                result["media"] = {
                    "id": audio_data.get('id'),
                    "mime_type": audio_data.get('mime_type'),
                    "sha256": audio_data.get('sha256')
                }

            elif message_type == 'document':
                document_data = message.get('document', {})
                result["media"] = {
                    "id": document_data.get('id'),
                    "mime_type": document_data.get('mime_type'),
                    "sha256": document_data.get('sha256'),
                    "filename": document_data.get('filename', ''),
                    "caption": document_data.get('caption', '')
                }

            return result

        except (IndexError, KeyError, TypeError) as e:
            print(f"Error parsing webhook: {str(e)}")
            return None

    @staticmethod
    def is_status_update(webhook_data: Dict) -> bool:
        """
        Check if webhook is a status update (not a message)

        Args:
            webhook_data: The webhook payload

        Returns:
            True if this is a status update
        """
        try:
            entry = webhook_data.get('entry', [])
            if not entry:
                return False

            changes = entry[0].get('changes', [])
            if not changes:
                return False

            value = changes[0].get('value', {})
            return 'statuses' in value

        except (IndexError, KeyError, TypeError):
            return False

    @staticmethod
    def extract_sender(webhook_data: Dict) -> Optional[str]:
        """
        Extract sender's phone number from webhook

        Args:
            webhook_data: The webhook payload

        Returns:
            Sender's phone number or None
        """
        message = WhatsAppWebhookParser.parse_message(webhook_data)
        return message.get('from') if message else None
