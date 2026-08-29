"""
Utility helpers for FreeStack.
"""

import uuid
import re
from typing import Optional


def generate_id() -> str:
    """Generate a random UUID string."""
    return str(uuid.uuid4())


def slugify(text: str, max_length: int = 100) -> str:
    """Convert text to a URL-friendly slug."""
    # Convert to lowercase
    text = text.lower()
    # Replace non-alphanumeric with hyphens
    text = re.sub(r'[^a-z0-9]+', '-', text)
    # Remove leading/trailing hyphens
    text = text.strip('-')
    # Truncate
    if len(text) > max_length:
        text = text[:max_length].rstrip('-')
    return text


def truncate(text: str, length: int, suffix: str = "...") -> str:
    """Truncate text to a maximum length."""
    if len(text) <= length:
        return text
    return text[:length - len(suffix)] + suffix


def mask_secret(secret: str, visible_chars: int = 4) -> str:
    """Mask a secret for logging."""
    if len(secret) <= visible_chars * 2:
        return "*" * len(secret)
    return secret[:visible_chars] + "*" * (len(secret) - visible_chars * 2) + secret[-visible_chars:]


def parse_duration(duration: str) -> int:
    """Parse duration string to seconds (e.g., '1h30m', '5m', '30s')."""
    import re
    pattern = r'(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?'
    match = re.match(pattern, duration)
    if not match:
        raise ValueError(f"Invalid duration format: {duration}")

    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)

    return hours * 3600 + minutes * 60 + seconds


def format_duration(seconds: int) -> str:
    """Format seconds as human-readable duration."""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        remaining = seconds % 60
        if remaining:
            return f"{minutes}m{remaining}s"
        return f"{minutes}m"
    else:
        hours = seconds // 3600
        remaining = seconds % 3600
        minutes = remaining // 60
        if minutes:
            return f"{hours}h{minutes}m"
        return f"{hours}h"