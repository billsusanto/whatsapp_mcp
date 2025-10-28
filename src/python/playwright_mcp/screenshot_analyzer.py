"""
Screenshot Analyzer Helper

Utilities for capturing, encoding, and analyzing screenshots from Playwright.
Supports base64 encoding for Claude API compatibility.
"""

import base64
import os
import tempfile
from typing import Optional, Dict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ScreenshotAnalyzer:
    """Helper for screenshot capture and analysis"""

    def __init__(self, temp_dir: Optional[str] = None):
        """
        Initialize screenshot analyzer

        Args:
            temp_dir: Directory to store temporary screenshots (default: system temp)
        """
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self.screenshots: Dict[str, Dict] = {}  # screenshot_id -> metadata
        logger.info(f"📸 ScreenshotAnalyzer initialized (temp_dir: {self.temp_dir})")

    def encode_screenshot_base64(self, image_path: str) -> str:
        """
        Encode screenshot image to base64 for Claude API

        Args:
            image_path: Path to image file

        Returns:
            Base64 encoded string
        """
        with open(image_path, 'rb') as image_file:
            encoded = base64.b64encode(image_file.read()).decode('utf-8')
            logger.info(f"📦 Encoded screenshot: {len(encoded)} bytes")
            return encoded

    def save_screenshot_metadata(
        self,
        screenshot_id: str,
        image_path: str,
        page_url: str,
        selector: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict:
        """
        Save metadata about a screenshot

        Args:
            screenshot_id: Unique identifier for screenshot
            image_path: Path to screenshot file
            page_url: URL of page when screenshot was taken
            selector: CSS selector if element screenshot (optional)
            description: Human-readable description (optional)

        Returns:
            Metadata dictionary
        """
        metadata = {
            'id': screenshot_id,
            'path': image_path,
            'url': page_url,
            'selector': selector,
            'description': description,
            'timestamp': datetime.now().isoformat(),
            'size': os.path.getsize(image_path) if os.path.exists(image_path) else 0
        }

        self.screenshots[screenshot_id] = metadata
        logger.info(f"💾 Saved metadata for screenshot: {screenshot_id}")
        return metadata

    def get_screenshot_for_claude(self, screenshot_id: str) -> Optional[Dict]:
        """
        Get screenshot in Claude API-compatible format

        Args:
            screenshot_id: ID of screenshot to retrieve

        Returns:
            Dictionary with base64 image data and metadata, or None if not found
        """
        if screenshot_id not in self.screenshots:
            logger.warning(f"⚠️ Screenshot not found: {screenshot_id}")
            return None

        metadata = self.screenshots[screenshot_id]
        image_path = metadata['path']

        if not os.path.exists(image_path):
            logger.error(f"❌ Screenshot file missing: {image_path}")
            return None

        # Encode image
        base64_image = self.encode_screenshot_base64(image_path)

        return {
            'id': screenshot_id,
            'image_base64': base64_image,
            'url': metadata['url'],
            'selector': metadata['selector'],
            'description': metadata['description'],
            'timestamp': metadata['timestamp']
        }

    def create_screenshot_path(self, screenshot_id: str) -> str:
        """
        Generate file path for a screenshot

        Args:
            screenshot_id: Unique identifier

        Returns:
            Full file path for screenshot
        """
        filename = f"screenshot_{screenshot_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        return os.path.join(self.temp_dir, filename)

    def cleanup_screenshots(self):
        """Delete all temporary screenshot files"""
        logger.info("🧹 Cleaning up screenshots...")

        for screenshot_id, metadata in self.screenshots.items():
            image_path = metadata['path']
            try:
                if os.path.exists(image_path):
                    os.remove(image_path)
                    logger.info(f"🗑️ Deleted: {image_path}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to delete {image_path}: {e}")

        self.screenshots.clear()
        logger.info("✅ Screenshot cleanup complete")

    def get_all_screenshot_ids(self) -> list:
        """Get list of all screenshot IDs"""
        return list(self.screenshots.keys())

    def get_screenshot_count(self) -> int:
        """Get number of screenshots stored"""
        return len(self.screenshots)


def create_playwright_screenshot_message(
    screenshot_base64: str,
    description: str,
    page_url: str
) -> Dict:
    """
    Create a properly formatted message with screenshot for Claude

    Args:
        screenshot_base64: Base64 encoded image
        description: Description of the screenshot
        page_url: URL where screenshot was taken

    Returns:
        Message dictionary compatible with Claude API
    """
    return {
        "role": "user",
        "content": [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": screenshot_base64
                }
            },
            {
                "type": "text",
                "text": f"Screenshot from {page_url}: {description}"
            }
        ]
    }
