# SPDX-License-Identifier: CC-BY-SA-4.0

"""URL validation for supported video platforms."""

import re
from dataclasses import dataclass
from enum import Enum
from urllib.parse import parse_qs, urlencode, urlparse


class Platform(Enum):
    """Supported video platforms."""

    YOUTUBE = "youtube"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    UNKNOWN = "unknown"


@dataclass
class ValidationResult:
    """Result of URL validation."""

    is_valid: bool
    platform: Platform
    error_message: str | None = None
    sanitized_url: str | None = None


# Platform patterns — each regex already encodes the allowed domains,
# so a separate domain whitelist is unnecessary.
_PLATFORM_PATTERNS: dict[Platform, list[str]] = {
    Platform.YOUTUBE: [
        r"^https?://(?:www\.|m\.)?youtube\.com/watch\?v=[\w-]+",
        r"^https?://(?:www\.|m\.)?youtube\.com/shorts/[\w-]+",
        r"^https?://(?:www\.)?youtu\.be/[\w-]+",
        r"^https?://(?:www\.|m\.)?youtube\.com/embed/[\w-]+",
    ],
    Platform.INSTAGRAM: [
        r"^https?://(?:www\.|m\.)?instagram\.com/(?:p|reel|reels|tv)/[\w-]+",
    ],
    Platform.TIKTOK: [
        r"^https?://(?:www\.|m\.)?tiktok\.com/@[\w.-]+/video/\d+",
        r"^https?://(?:vm|vt)\.tiktok\.com/[\w]+",
        r"^https?://(?:www\.)?tiktok\.com/t/[\w]+",
    ],
}

# Query params to keep per platform (everything else is stripped)
_ALLOWED_QUERY_PARAMS: dict[Platform, set[str]] = {
    Platform.YOUTUBE: {"v", "t", "list"},
    Platform.INSTAGRAM: set(),
    Platform.TIKTOK: set(),
}


def validate_url(url: str) -> ValidationResult:
    """
    Validate a URL and determine its platform.

    Returns:
        ValidationResult with validation status and details.
    """
    if not url:
        return ValidationResult(
            is_valid=False,
            platform=Platform.UNKNOWN,
            error_message="URL is empty or invalid",
        )

    url = url.strip()

    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return ValidationResult(
            is_valid=False,
            platform=Platform.UNKNOWN,
            error_message="Invalid URL format",
        )

    if parsed.scheme not in ("http", "https"):
        return ValidationResult(
            is_valid=False,
            platform=Platform.UNKNOWN,
            error_message="Only HTTP/HTTPS URLs are allowed",
        )

    # Match against platform patterns (domain check is embedded in regex)
    for platform, patterns in _PLATFORM_PATTERNS.items():
        if any(re.match(p, url, re.IGNORECASE) for p in patterns):
            sanitized = _strip_tracking_params(url, platform)
            return ValidationResult(
                is_valid=True,
                platform=platform,
                sanitized_url=sanitized,
            )

    return ValidationResult(
        is_valid=False,
        platform=Platform.UNKNOWN,
        error_message="Unsupported platform. Use YouTube, Instagram, or TikTok URLs",
    )


def _strip_tracking_params(url: str, platform: Platform) -> str:
    """Strip tracking/analytics query params, keeping only meaningful ones."""
    parsed = urlparse(url)
    allowed = _ALLOWED_QUERY_PARAMS.get(platform, set())
    query_params = parse_qs(parsed.query)
    filtered = {k: v for k, v in query_params.items() if k in allowed}
    clean_query = urlencode(filtered, doseq=True)
    return parsed._replace(query=clean_query, fragment="").geturl()
