# SPDX-License-Identifier: CC-BY-SA-4.0

"""Tests for URL validator."""

import pytest

from bot.validators.url import Platform, validate_url


class TestValidateUrl:
    """Test cases for validate_url."""

    # Valid YouTube URLs
    @pytest.mark.parametrize(
        "url",
        [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
            "https://www.youtube.com/shorts/abc123xyz",
            "https://m.youtube.com/watch?v=dQw4w9WgXcQ",
            "http://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://www.youtube.com/embed/dQw4w9WgXcQ",
        ],
    )
    def test_valid_youtube_urls(self, url: str):
        result = validate_url(url)
        assert result.is_valid is True
        assert result.platform == Platform.YOUTUBE
        assert result.error_message is None
        assert result.sanitized_url is not None

    # Valid Instagram URLs
    @pytest.mark.parametrize(
        "url",
        [
            "https://www.instagram.com/reel/ABC123xyz/",
            "https://instagram.com/reel/ABC123xyz/",
            "https://www.instagram.com/p/ABC123xyz/",
            "https://www.instagram.com/reels/ABC123xyz/",
            "https://www.instagram.com/tv/ABC123xyz/",
            "https://m.instagram.com/reel/ABC123xyz/",
        ],
    )
    def test_valid_instagram_urls(self, url: str):
        result = validate_url(url)
        assert result.is_valid is True
        assert result.platform == Platform.INSTAGRAM
        assert result.error_message is None

    # Valid TikTok URLs
    @pytest.mark.parametrize(
        "url",
        [
            "https://www.tiktok.com/@username/video/1234567890123456789",
            "https://tiktok.com/@user.name/video/1234567890123456789",
            "https://vm.tiktok.com/ZMxxxxxx/",
            "https://vt.tiktok.com/ZSxxxxxx/",
            "https://m.tiktok.com/@username/video/1234567890123456789",
            "https://www.tiktok.com/t/ZTxxxxxx/",
        ],
    )
    def test_valid_tiktok_urls(self, url: str):
        result = validate_url(url)
        assert result.is_valid is True
        assert result.platform == Platform.TIKTOK
        assert result.error_message is None

    # Invalid URLs - empty/null
    @pytest.mark.parametrize(
        "url",
        [
            "",
            "   ",
            None,
        ],
    )
    def test_empty_urls(self, url):
        result = validate_url(url)
        assert result.is_valid is False
        assert result.platform == Platform.UNKNOWN
        assert result.error_message is not None

    # Invalid URLs - wrong format
    @pytest.mark.parametrize(
        "url",
        [
            "not a url",
            "ftp://youtube.com/watch?v=abc",
            "javascript:alert(1)",
            "file:///etc/passwd",
            "data:text/html,<script>alert(1)</script>",
        ],
    )
    def test_invalid_url_formats(self, url: str):
        result = validate_url(url)
        assert result.is_valid is False

    # Invalid URLs - unsupported platforms
    @pytest.mark.parametrize(
        "url",
        [
            "https://www.facebook.com/video/123",
            "https://twitter.com/user/status/123",
            "https://www.vimeo.com/123456",
            "https://dailymotion.com/video/abc",
            "https://example.com/video.mp4",
        ],
    )
    def test_unsupported_platforms(self, url: str):
        result = validate_url(url)
        assert result.is_valid is False
        assert result.platform == Platform.UNKNOWN
        assert "Unsupported platform" in result.error_message

    # Invalid YouTube URLs (wrong patterns)
    @pytest.mark.parametrize(
        "url",
        [
            "https://www.youtube.com/channel/UCabc",
            "https://www.youtube.com/playlist?list=abc",
            "https://www.youtube.com/",
            "https://www.youtube.com/results?search_query=test",
        ],
    )
    def test_invalid_youtube_patterns(self, url: str):
        result = validate_url(url)
        assert result.is_valid is False

    def test_sanitizes_tracking_params(self):
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&feature=share&utm_source=test"
        result = validate_url(url)
        assert result.is_valid is True
        assert result.sanitized_url == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    def test_preserves_video_id_only(self):
        url = "https://www.youtube.com/watch?v=abc123&index=5&utm_source=test"
        result = validate_url(url)
        assert result.is_valid is True
        assert "index=" not in result.sanitized_url
        assert "utm_source=" not in result.sanitized_url
        assert "v=abc123" in result.sanitized_url

    def test_handles_url_with_whitespace(self):
        url = "  https://www.youtube.com/watch?v=dQw4w9WgXcQ  "
        result = validate_url(url)
        assert result.is_valid is True

    def test_case_insensitive_domain(self):
        url = "https://WWW.YOUTUBE.COM/watch?v=dQw4w9WgXcQ"
        result = validate_url(url)
        assert result.is_valid is True
        assert result.platform == Platform.YOUTUBE

    # Sanitization tests for Instagram
    def test_instagram_strips_tracking_params(self):
        url = "https://www.instagram.com/reel/ABC123xyz/?igsh=abc123&utm_source=test"
        result = validate_url(url)
        assert result.is_valid is True
        assert "igsh=" not in result.sanitized_url
        assert "utm_source=" not in result.sanitized_url

    # Sanitization tests for TikTok
    def test_tiktok_strips_tracking_params(self):
        url = "https://www.tiktok.com/@username/video/1234567890123456789?is_from_webapp=1&sender_device=pc"
        result = validate_url(url)
        assert result.is_valid is True
        assert "is_from_webapp=" not in result.sanitized_url
        assert "sender_device=" not in result.sanitized_url
