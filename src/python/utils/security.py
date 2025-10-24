"""
Security utilities for WhatsApp MCP System

Provides:
- Input validation and sanitization
- Rate limiting
- Secret management
- Security headers
"""

import os
import re
import hashlib
import secrets
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio


class SecretManager:
    """
    Secure secret management with validation

    Validates that all required secrets are present and non-empty
    """

    REQUIRED_SECRETS = [
        "ANTHROPIC_API_KEY",
        "WHATSAPP_ACCESS_TOKEN",
        "WHATSAPP_WEBHOOK_VERIFY_TOKEN",
        "GITHUB_WEBHOOK_SECRET",
    ]

    OPTIONAL_SECRETS = [
        "GITHUB_PERSONAL_ACCESS_TOKEN",
        "NETLIFY_PERSONAL_ACCESS_TOKEN",
        "DATABASE_URL",
        "REDIS_URL",
        "LOGFIRE_TOKEN",
    ]

    @classmethod
    def validate_secrets(cls) -> tuple[bool, list[str]]:
        """
        Validate that all required secrets are present

        Returns:
            (is_valid, missing_secrets)
        """
        missing = []

        for secret_name in cls.REQUIRED_SECRETS:
            value = os.getenv(secret_name)
            if not value or value.strip() == "":
                missing.append(secret_name)

        is_valid = len(missing) == 0
        return is_valid, missing

    @classmethod
    def get_secret(cls, name: str, required: bool = True) -> Optional[str]:
        """
        Safely get a secret with validation

        Args:
            name: Environment variable name
            required: Whether this secret is required

        Returns:
            Secret value or None

        Raises:
            ValueError: If required secret is missing
        """
        value = os.getenv(name)

        if not value or value.strip() == "":
            if required:
                raise ValueError(f"Required secret '{name}' is not configured")
            return None

        return value.strip()

    @classmethod
    def mask_secret(cls, secret: str, show_chars: int = 4) -> str:
        """
        Mask a secret for logging

        Args:
            secret: Secret to mask
            show_chars: Number of chars to show at start/end

        Returns:
            Masked secret (e.g., "sk-a...xyz")
        """
        if not secret or len(secret) <= show_chars * 2:
            return "***"

        return f"{secret[:show_chars]}...{secret[-show_chars:]}"


class InputValidator:
    """
    Input validation and sanitization

    Prevents injection attacks and malicious input
    """

    # Regex patterns for validation
    PHONE_PATTERN = re.compile(r'^\+?[1-9]\d{1,14}$')  # E.164 format
    GITHUB_REPO_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+/[a-zA-Z0-9_.-]+$')
    URL_PATTERN = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE
    )

    # Maximum lengths to prevent DoS
    MAX_MESSAGE_LENGTH = 10000
    MAX_PROMPT_LENGTH = 5000
    MAX_USERNAME_LENGTH = 100

    # Dangerous patterns to block
    DANGEROUS_PATTERNS = [
        r'<script[\s\S]*?>[\s\S]*?</script>',  # XSS
        r'javascript:',  # JavaScript protocol
        r'on\w+\s*=',  # Event handlers
        r'<iframe',  # Iframes
        r'eval\s*\(',  # Code execution
        r'exec\s*\(',  # Code execution
    ]

    @classmethod
    def validate_phone_number(cls, phone: str) -> tuple[bool, str]:
        """
        Validate phone number format

        Args:
            phone: Phone number to validate

        Returns:
            (is_valid, cleaned_phone)
        """
        if not phone:
            return False, ""

        # Remove whitespace
        cleaned = phone.strip().replace(" ", "").replace("-", "")

        # Check format
        if not cls.PHONE_PATTERN.match(cleaned):
            return False, ""

        return True, cleaned

    @classmethod
    def validate_message(cls, message: str) -> tuple[bool, str, Optional[str]]:
        """
        Validate and sanitize user message

        Args:
            message: User message to validate

        Returns:
            (is_valid, sanitized_message, error_reason)
        """
        if not message:
            return False, "", "Empty message"

        # Check length
        if len(message) > cls.MAX_MESSAGE_LENGTH:
            return False, "", f"Message too long (max {cls.MAX_MESSAGE_LENGTH} chars)"

        # Check for dangerous patterns
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, message, re.IGNORECASE):
                return False, "", "Message contains potentially dangerous content"

        # Sanitize: remove control characters except newlines/tabs
        sanitized = ''.join(
            char for char in message
            if char.isprintable() or char in '\n\t'
        )

        return True, sanitized.strip(), None

    @classmethod
    def validate_github_repo(cls, repo: str) -> tuple[bool, str]:
        """
        Validate GitHub repository name

        Args:
            repo: Repository name (owner/repo)

        Returns:
            (is_valid, error_reason)
        """
        if not repo:
            return False, "Empty repository name"

        if not cls.GITHUB_REPO_PATTERN.match(repo):
            return False, "Invalid repository format (expected: owner/repo)"

        return True, ""

    @classmethod
    def validate_url(cls, url: str) -> tuple[bool, str]:
        """
        Validate URL format and safety

        Args:
            url: URL to validate

        Returns:
            (is_valid, error_reason)
        """
        if not url:
            return False, "Empty URL"

        # Check format
        if not cls.URL_PATTERN.match(url):
            return False, "Invalid URL format"

        # Block non-HTTPS in production
        if os.getenv("ENVIRONMENT") == "production" and not url.startswith("https://"):
            return False, "Only HTTPS URLs allowed in production"

        return True, ""


class RateLimiter:
    """
    In-memory rate limiter with sliding window

    For production, use Redis-based rate limiting
    """

    def __init__(self, max_requests: int, window_seconds: int):
        """
        Initialize rate limiter

        Args:
            max_requests: Maximum requests per window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list[datetime]] = defaultdict(list)
        self._lock = asyncio.Lock()

        # Start cleanup task
        asyncio.create_task(self._cleanup_old_entries())

    async def check_rate_limit(self, identifier: str) -> tuple[bool, Optional[int]]:
        """
        Check if request is within rate limit

        Args:
            identifier: Unique identifier (user_id, IP, etc.)

        Returns:
            (is_allowed, seconds_until_reset)
        """
        async with self._lock:
            now = datetime.utcnow()
            cutoff = now - timedelta(seconds=self.window_seconds)

            # Remove old requests
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier]
                if req_time > cutoff
            ]

            # Check limit
            request_count = len(self.requests[identifier])

            if request_count >= self.max_requests:
                # Calculate seconds until oldest request expires
                oldest_request = min(self.requests[identifier])
                seconds_until_reset = int(
                    (oldest_request + timedelta(seconds=self.window_seconds) - now).total_seconds()
                )
                return False, seconds_until_reset

            # Add current request
            self.requests[identifier].append(now)
            return True, None

    async def _cleanup_old_entries(self):
        """Periodically clean up old entries to prevent memory leak"""
        while True:
            await asyncio.sleep(300)  # Run every 5 minutes

            async with self._lock:
                now = datetime.utcnow()
                cutoff = now - timedelta(seconds=self.window_seconds * 2)

                # Remove expired entries
                expired_keys = []
                for identifier, requests in self.requests.items():
                    # Remove old requests
                    self.requests[identifier] = [
                        req_time for req_time in requests
                        if req_time > cutoff
                    ]
                    # Mark for deletion if empty
                    if not self.requests[identifier]:
                        expired_keys.append(identifier)

                # Delete empty entries
                for key in expired_keys:
                    del self.requests[key]

                if expired_keys:
                    print(f"🧹 Rate limiter cleanup: removed {len(expired_keys)} expired entries")


class SecurityHeaders:
    """
    Security headers for HTTP responses
    """

    @staticmethod
    def get_security_headers() -> Dict[str, str]:
        """
        Get recommended security headers

        Returns:
            Dictionary of security headers
        """
        return {
            # Prevent clickjacking
            "X-Frame-Options": "DENY",

            # Prevent MIME type sniffing
            "X-Content-Type-Options": "nosniff",

            # Enable XSS protection
            "X-XSS-Protection": "1; mode=block",

            # Enforce HTTPS
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",

            # Content Security Policy
            "Content-Security-Policy": "default-src 'self'; script-src 'self'; object-src 'none'",

            # Referrer policy
            "Referrer-Policy": "strict-origin-when-cross-origin",

            # Permissions policy
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        }


def generate_secure_token(length: int = 32) -> str:
    """
    Generate a cryptographically secure random token

    Args:
        length: Length of token in bytes

    Returns:
        Hexadecimal token string
    """
    return secrets.token_hex(length)


def hash_identifier(identifier: str) -> str:
    """
    Hash an identifier for privacy-preserving storage

    Args:
        identifier: Identifier to hash (phone number, email, etc.)

    Returns:
        SHA256 hash of identifier
    """
    return hashlib.sha256(identifier.encode()).hexdigest()


# Validation functions for common use cases
def validate_and_sanitize_input(
    message: str,
    user_id: str
) -> tuple[bool, str, Optional[str]]:
    """
    Validate and sanitize user input comprehensively

    Args:
        message: User message
        user_id: User identifier

    Returns:
        (is_valid, sanitized_message, error_reason)
    """
    # Validate message
    is_valid, sanitized, error = InputValidator.validate_message(message)
    if not is_valid:
        return False, "", error

    # Additional validation can be added here

    return True, sanitized, None
