"""
WhatsApp Webhook Payload Parser

Parses incoming webhook payloads from WhatsApp Business API
"""

from typing import Dict, Optional, List


class WhatsAppWebhookParser:
    """Parser for WhatsApp webhook payloads"""

    @staticmethod
    def parse_message(webhook_data: Dict) -> Optional[Dict]:
        """
        Extract message details from webhook payload

        Args:
            webhook_data: The raw webhook POST body

        Returns:
            Dict with: {
                "from": sender_phone_number,
                "message_id": whatsapp_message_id,
                "text": message_text,
                "timestamp": message_timestamp,
                "name": sender_name (if available)
            }
            Returns None if not a valid message

        TODO:
        - Navigate webhook structure: entry[0].changes[0].value.messages[0]
        - Extract phone number from "from" field
        - Extract text from text.body or handle other message types
        - Handle edge cases (no messages, status updates, etc.)

        WEBHOOK STRUCTURE:
        {
          "object": "whatsapp_business_account",
          "entry": [{
            "changes": [{
              "value": {
                "messages": [{
                  "from": "1234567890",
                  "id": "wamid.xxx",
                  "timestamp": "1234567890",
                  "text": {"body": "Hello"},
                  "type": "text"
                }],
                "contacts": [{
                  "profile": {"name": "John Doe"}
                }]
              }
            }]
          }]
        }

        DOCS: https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/payload-examples
        """
        pass

    @staticmethod
    def is_status_update(webhook_data: Dict) -> bool:
        """
        Check if webhook is a status update (delivered, read, etc.)

        TODO:
        - Check if "statuses" field exists instead of "messages"
        - Return True if it's a status update (we can ignore these)
        """
        pass
