"""Pytest configuration and fixtures."""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.config import get_settings
from bot.services import RateLimiter, VideoDownloader

USER_ID = 12345


@pytest.fixture(autouse=True)
def clear_settings_cache():
    """Clear get_settings cache before each test."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def downloader(temp_dir):
    """Create a VideoDownloader instance for tests."""
    return VideoDownloader(
        temp_dir=str(temp_dir),
        max_file_size=50 * 1024 * 1024,
        timeout=60,
    )


@pytest.fixture
def rate_limiter():
    """Create a RateLimiter instance for tests."""
    return RateLimiter(max_requests=5, window_seconds=60)


def make_message(
    text: str | None = "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    user_id: int = USER_ID,
    *,
    has_user: bool = True,
) -> AsyncMock:
    """Create a mock Telegram message for handler tests."""
    message = AsyncMock()
    message.text = text
    message.answer = AsyncMock()
    message.answer_video = AsyncMock()

    if has_user:
        message.from_user = MagicMock()
        message.from_user.id = user_id
    else:
        message.from_user = None

    return message


FAKE_UUID_HEX = "ab" * 16  # uuid4().hex is 32 chars; [:8] → "abababab"
FAKE_ID = FAKE_UUID_HEX[:8]


@pytest.fixture
def mock_uuid():
    """Mock uuid4 to produce a predictable file ID."""
    mock = MagicMock()
    mock.hex = FAKE_UUID_HEX
    with patch("bot.services.downloader.uuid.uuid4", return_value=mock):
        yield
