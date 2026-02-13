"""Tests for message handlers."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.handlers.video import (
    _format_duration,
    _sanitize_filename,
    handle_help,
    handle_start,
    handle_video_url,
)
from bot.services.downloader import (
    DownloadError,
    DownloadResult,
    FileTooLargeError,
    VideoUnavailableError,
)

from .conftest import USER_ID, make_message


class TestFormatDuration:
    """Test cases for duration formatting."""

    @pytest.mark.parametrize(
        ("seconds", "expected"),
        [
            (0, "0:00"),
            (45, "0:45"),
            (125, "2:05"),
            (600, "10:00"),
            (3661, "1:01:01"),
            (7200, "2:00:00"),
            (None, "Unknown"),
        ],
    )
    def test_format_duration(self, seconds, expected):
        assert _format_duration(seconds) == expected


class TestSanitizeFilename:
    """Test cases for filename sanitization."""

    def test_removes_unsafe_characters(self):
        assert _sanitize_filename('test<>:"/\\|?*file') == "testfile"

    def test_truncates_long_names(self):
        long_name = "a" * 100
        result = _sanitize_filename(long_name, max_length=50)
        assert len(result) <= 50

    def test_truncates_at_word_boundary(self):
        result = _sanitize_filename("hello world test name", max_length=15)
        assert result == "hello world"

    def test_returns_fallback_for_empty(self):
        assert _sanitize_filename("???") == "video"

    def test_normalizes_whitespace(self):
        assert _sanitize_filename("hello   world") == "hello world"


class TestStartHandler:
    """Test cases for /start command handler."""

    @pytest.mark.asyncio
    async def test_start_command(self):
        message = AsyncMock()
        message.answer = AsyncMock()

        await handle_start(message)

        message.answer.assert_called_once()
        call_args = message.answer.call_args[0][0]
        assert "Welcome" in call_args
        assert "YouTube" in call_args
        assert "Instagram" in call_args
        assert "TikTok" in call_args


class TestHelpHandler:
    """Test cases for /help command handler."""

    @pytest.mark.asyncio
    async def test_help_command(self):
        message = AsyncMock()
        message.answer = AsyncMock()

        await handle_help(message)

        message.answer.assert_called_once()
        call_args = message.answer.call_args[0][0]
        assert "How to use" in call_args
        assert "50MB" in call_args


class TestVideoUrlHandler:
    """Test cases for video URL handler."""

    @pytest.mark.asyncio
    async def test_invalid_url(self, downloader, rate_limiter):
        message = make_message(text="not a valid url")

        await handle_video_url(message, downloader, rate_limiter)

        message.answer.assert_called_once()
        assert "Invalid URL" in message.answer.call_args[0][0]

    @pytest.mark.asyncio
    async def test_unsupported_platform(self, downloader, rate_limiter):
        message = make_message(text="https://www.vimeo.com/123456")

        await handle_video_url(message, downloader, rate_limiter)

        message.answer.assert_called_once()
        assert "Invalid URL" in message.answer.call_args[0][0]

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self, downloader, rate_limiter):
        message = make_message()

        # Exhaust rate limit
        for _ in range(5):
            rate_limiter.check_rate_limit(USER_ID)

        await handle_video_url(message, downloader, rate_limiter)

        message.answer.assert_called_once()
        assert "Too many requests" in message.answer.call_args[0][0]

    @pytest.mark.asyncio
    async def test_successful_download(self, downloader, rate_limiter, temp_dir):
        fake_video = temp_dir / "video_test1234.mp4"
        fake_video.write_bytes(b"fake video content")

        message = make_message()
        processing_msg = AsyncMock()
        processing_msg.delete = AsyncMock()
        message.answer.return_value = processing_msg

        mock_result = DownloadResult(
            file_path=fake_video,
            title="Test Video",
            duration=120,
            file_size=1024,
        )

        with patch.object(downloader, "download", return_value=mock_result):
            with patch.object(downloader, "cleanup_file", new_callable=MagicMock):
                await handle_video_url(message, downloader, rate_limiter)

        message.answer_video.assert_called_once()
        processing_msg.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_file_too_large(self, downloader, rate_limiter):
        message = make_message()
        processing_msg = AsyncMock()
        processing_msg.edit_text = AsyncMock()
        message.answer.return_value = processing_msg

        with patch.object(
            downloader,
            "download",
            side_effect=FileTooLargeError(60 * 1024 * 1024, 50 * 1024 * 1024),
        ):
            await handle_video_url(message, downloader, rate_limiter)

        processing_msg.edit_text.assert_called_once()
        assert "too large" in processing_msg.edit_text.call_args[0][0]

    @pytest.mark.asyncio
    async def test_video_unavailable(self, downloader, rate_limiter):
        message = make_message()
        processing_msg = AsyncMock()
        processing_msg.edit_text = AsyncMock()
        message.answer.return_value = processing_msg

        with patch.object(
            downloader,
            "download",
            side_effect=VideoUnavailableError("Video is private"),
        ):
            await handle_video_url(message, downloader, rate_limiter)

        processing_msg.edit_text.assert_called_once()
        assert "unavailable" in processing_msg.edit_text.call_args[0][0].lower()

    @pytest.mark.asyncio
    async def test_download_error(self, downloader, rate_limiter):
        message = make_message()
        processing_msg = AsyncMock()
        processing_msg.edit_text = AsyncMock()
        message.answer.return_value = processing_msg

        with patch.object(
            downloader,
            "download",
            side_effect=DownloadError("Network error"),
        ):
            await handle_video_url(message, downloader, rate_limiter)

        processing_msg.edit_text.assert_called_once()
        assert "Failed to download" in processing_msg.edit_text.call_args[0][0]

    @pytest.mark.asyncio
    async def test_empty_message(self, downloader, rate_limiter):
        message = make_message(text=None)

        await handle_video_url(message, downloader, rate_limiter)

        message.answer.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_user(self, downloader, rate_limiter):
        message = make_message(text="https://youtube.com/watch?v=test", has_user=False)

        await handle_video_url(message, downloader, rate_limiter)

        message.answer.assert_not_called()
