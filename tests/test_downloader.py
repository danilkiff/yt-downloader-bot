# SPDX-License-Identifier: CC-BY-SA-4.0

"""Tests for video downloader service."""

from unittest.mock import MagicMock, patch

import pytest
import yt_dlp

from bot.services.downloader import (
    DownloadError,
    FileTooLargeError,
    VideoDownloader,
    VideoUnavailableError,
)

from .conftest import FAKE_ID


def _mock_ydl_context(mock_ydl_class: MagicMock, side_effect=None, return_value=None):
    """Wire up YoutubeDL mock so `with YoutubeDL(opts) as ydl` works."""
    mock_instance = MagicMock()
    mock_ydl_class.return_value.__enter__ = MagicMock(return_value=mock_instance)
    mock_ydl_class.return_value.__exit__ = MagicMock(return_value=False)
    if side_effect:
        mock_instance.extract_info.side_effect = side_effect
    else:
        mock_instance.extract_info.return_value = return_value
    return mock_instance


class TestVideoDownloader:
    """Test cases for VideoDownloader."""

    def test_initialization(self, temp_dir):
        downloader = VideoDownloader(
            temp_dir=str(temp_dir),
            max_file_size=100 * 1024 * 1024,
            timeout=120,
        )
        assert downloader.temp_dir == temp_dir
        assert downloader.max_file_size == 100 * 1024 * 1024

    def test_creates_temp_directory(self, temp_dir):
        new_dir = temp_dir / "subdir" / "downloads"
        _downloader = VideoDownloader(temp_dir=str(new_dir))  # noqa: F841
        assert new_dir.exists()

    def test_cleanup_file(self, downloader, temp_dir):
        test_file = temp_dir / "test_video.mp4"
        test_file.write_text("test content")
        assert test_file.exists()

        downloader.cleanup_file(test_file)
        assert not test_file.exists()

    def test_cleanup_nonexistent_file(self, downloader, temp_dir):
        nonexistent = temp_dir / "nonexistent.mp4"
        downloader.cleanup_file(nonexistent)


class TestDownload:
    """Test cases for VideoDownloader.download()."""

    @pytest.mark.asyncio
    async def test_successful_download(self, downloader, temp_dir, mock_uuid):
        video_file = temp_dir / f"video_{FAKE_ID}.mp4"
        video_file.write_bytes(b"x" * 1024)

        with patch("yt_dlp.YoutubeDL") as mock_ydl:
            _mock_ydl_context(
                mock_ydl,
                return_value={"title": "Test Video", "duration": 120},
            )

            result = await downloader.download("https://youtube.com/watch?v=test")

        assert result.title == "Test Video"
        assert result.duration == 120
        assert result.file_size == 1024
        assert result.file_path == video_file

    @pytest.mark.asyncio
    async def test_download_fallback_title(self, downloader, temp_dir, mock_uuid):
        video_file = temp_dir / f"video_{FAKE_ID}.mp4"
        video_file.write_bytes(b"x" * 512)

        with patch("yt_dlp.YoutubeDL") as mock_ydl:
            _mock_ydl_context(mock_ydl, return_value={})

            result = await downloader.download("https://youtube.com/watch?v=test")

        assert result.title == "Unknown"
        assert result.duration is None

    @pytest.mark.asyncio
    async def test_download_none_info(self, downloader):
        with patch("yt_dlp.YoutubeDL") as mock_ydl:
            _mock_ydl_context(mock_ydl, return_value=None)

            with pytest.raises(VideoUnavailableError, match="Could not download"):
                await downloader.download("https://youtube.com/watch?v=test")

    @pytest.mark.asyncio
    async def test_download_file_too_large(self, temp_dir, mock_uuid):
        downloader = VideoDownloader(
            temp_dir=str(temp_dir),
            max_file_size=100,
            timeout=60,
        )

        video_file = temp_dir / f"video_{FAKE_ID}.mp4"
        video_file.write_bytes(b"x" * 200)

        with patch("yt_dlp.YoutubeDL") as mock_ydl:
            _mock_ydl_context(mock_ydl, return_value={"title": "Big Video"})

            with pytest.raises(FileTooLargeError) as exc_info:
                await downloader.download("https://youtube.com/watch?v=test")

        assert exc_info.value.file_size == 200
        assert exc_info.value.max_size == 100
        assert not video_file.exists()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("error_msg", ["Video is private", "This video is unavailable"])
    async def test_download_private_or_unavailable(self, downloader, error_msg):
        with patch("yt_dlp.YoutubeDL") as mock_ydl:
            _mock_ydl_context(
                mock_ydl,
                side_effect=yt_dlp.utils.DownloadError(error_msg),
            )

            with pytest.raises(VideoUnavailableError, match="private or unavailable"):
                await downloader.download("https://youtube.com/watch?v=test")

    @pytest.mark.asyncio
    async def test_download_generic_ytdlp_error(self, downloader):
        with patch("yt_dlp.YoutubeDL") as mock_ydl:
            _mock_ydl_context(
                mock_ydl,
                side_effect=yt_dlp.utils.DownloadError("Network error"),
            )

            with pytest.raises(DownloadError, match="Download failed"):
                await downloader.download("https://youtube.com/watch?v=test")

    @pytest.mark.asyncio
    async def test_download_timeout(self, temp_dir):
        import time

        downloader = VideoDownloader(
            temp_dir=str(temp_dir),
            max_file_size=50 * 1024 * 1024,
            timeout=1,
        )

        def slow_extract(*args, **kwargs):
            time.sleep(3)
            return {"title": "Test"}

        with patch("yt_dlp.YoutubeDL") as mock_ydl:
            _mock_ydl_context(mock_ydl, side_effect=slow_extract)

            with pytest.raises(DownloadError, match="timed out"):
                await downloader.download("https://youtube.com/watch?v=test")

    @pytest.mark.asyncio
    async def test_download_unexpected_error(self, downloader):
        with patch("yt_dlp.YoutubeDL") as mock_ydl:
            _mock_ydl_context(
                mock_ydl,
                side_effect=RuntimeError("something broke"),
            )

            with pytest.raises(DownloadError, match="Unexpected error"):
                await downloader.download("https://youtube.com/watch?v=test")
