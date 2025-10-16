"""
Logging Utilities

Structured logging for the application
"""

import logging
import sys
from datetime import datetime


def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
    """
    Create a configured logger instance

    Args:
        name: Logger name (usually __name__)
        level: Log level (DEBUG, INFO, WARNING, ERROR)

    Returns:
        Configured logger

    TODO:
    - Create logger with name
    - Set level
    - Create formatter with timestamp, level, name, message
    - Add console handler
    - Return logger

    EXAMPLE FORMAT:
    2024-01-15 10:30:45 - INFO - whatsapp.client - Sending message to +1234567890
    """
    pass


def log_webhook_event(event_type: str, phone_number: str, details: dict = None):
    """
    Log a webhook event

    TODO:
    - Log structured data about webhook events
    - Include: timestamp, event_type, phone_number, details
    - Use JSON format for easy parsing
    """
    pass


def log_agent_interaction(phone_number: str, user_message: str, agent_response: str):
    """
    Log an agent interaction

    TODO:
    - Log user message and agent response
    - Truncate long messages for logging
    - Include phone_number and timestamp
    """
    pass
