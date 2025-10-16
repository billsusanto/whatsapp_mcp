"""
Configuration Utilities

Loads and validates environment variables
"""

import os
from dotenv import load_dotenv
from typing import Optional

# Load .env file
load_dotenv()


class Config:
    """Configuration manager for environment variables"""

    @staticmethod
    def get_anthropic_api_key() -> str:
        """
        Get Anthropic API key

        TODO:
        - Get ANTHROPIC_API_KEY from environment
        - Raise error if not set
        """
        pass

    @staticmethod
    def get_whatsapp_token() -> str:
        """
        Get WhatsApp access token

        TODO:
        - Get WHATSAPP_ACCESS_TOKEN from environment
        - Raise error if not set
        """
        pass

    @staticmethod
    def get_whatsapp_phone_id() -> str:
        """
        Get WhatsApp phone number ID

        TODO:
        - Get WHATSAPP_PHONE_NUMBER_ID from environment
        - Raise error if not set
        """
        pass

    @staticmethod
    def get_verify_token() -> str:
        """
        Get webhook verification token

        TODO:
        - Get WHATSAPP_WEBHOOK_VERIFY_TOKEN from environment
        - Raise error if not set
        """
        pass

    @staticmethod
    def get_system_prompt() -> str:
        """
        Get agent system prompt

        TODO:
        - Get AGENT_SYSTEM_PROMPT from environment
        - Return default if not set
        """
        pass

    @staticmethod
    def validate_all() -> bool:
        """
        Validate that all required env vars are set

        TODO:
        - Check all required variables
        - Print helpful error messages if missing
        - Return True if all valid
        """
        pass
