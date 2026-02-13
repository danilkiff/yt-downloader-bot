# SPDX-License-Identifier: CC-BY-SA-4.0

"""Tests for configuration module."""

import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from bot.config import Settings, get_settings


class TestSettings:
    """Test cases for Settings."""

    def test_settings_from_env(self):
        """Test loading settings from environment variables."""
        env_vars = {
            "BOT_TOKEN": "test_token_123",
            "MAX_FILE_SIZE_MB": "30",
            "DOWNLOAD_TIMEOUT": "600",
            "TEMP_DIR": "/custom/temp",
            "RATE_LIMIT_REQUESTS": "10",
            "RATE_LIMIT_WINDOW": "120",
        }

        with patch.dict(os.environ, env_vars, clear=False):
            settings = Settings()

            assert settings.bot_token == "test_token_123"
            assert settings.max_file_size_mb == 30
            assert settings.download_timeout == 600
            assert settings.temp_dir == "/custom/temp"
            assert settings.rate_limit_requests == 10
            assert settings.rate_limit_window == 120

    def test_default_values(self):
        """Test default settings values."""
        env_vars = {"BOT_TOKEN": "test_token"}

        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()

            assert settings.max_file_size_mb == 50
            assert settings.download_timeout == 300
            assert settings.temp_dir == "/tmp/yt-downloader-bot"  # noqa: S108
            assert settings.rate_limit_requests == 5
            assert settings.rate_limit_window == 60

    def test_max_file_size_bytes_property(self):
        """Test max_file_size_bytes property calculation."""
        env_vars = {"BOT_TOKEN": "test_token", "MAX_FILE_SIZE_MB": "50"}

        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()

            assert settings.max_file_size_bytes == 50 * 1024 * 1024

    def test_missing_bot_token_raises_error(self):
        """Test that missing BOT_TOKEN raises validation error."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValidationError):
                Settings(_env_file=None)

    def test_max_file_size_exceeds_telegram_limit(self):
        """Test that max_file_size_mb cannot exceed 50 (Telegram limit)."""
        env_vars = {"BOT_TOKEN": "test_token", "MAX_FILE_SIZE_MB": "100"}

        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ValidationError, match="cannot exceed 50"):
                Settings()

    @pytest.mark.parametrize(
        ("env_var", "value"),
        [
            ("MAX_FILE_SIZE_MB", "0"),
            ("DOWNLOAD_TIMEOUT", "-1"),
            ("RATE_LIMIT_REQUESTS", "0"),
            ("RATE_LIMIT_WINDOW", "-5"),
        ],
    )
    def test_setting_must_be_positive(self, env_var, value):
        env_vars = {"BOT_TOKEN": "test_token", env_var: value}

        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ValidationError, match="must be positive"):
                Settings()


class TestGetSettings:
    """Test cases for get_settings function."""

    def test_get_settings_returns_instance(self):
        """Test that get_settings returns a Settings instance."""
        env_vars = {"BOT_TOKEN": "test_token"}

        with patch.dict(os.environ, env_vars, clear=True):
            settings = get_settings()
            assert isinstance(settings, Settings)
