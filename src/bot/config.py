# SPDX-License-Identifier: CC-BY-SA-4.0

"""Application configuration using pydantic-settings."""

from functools import lru_cache

from pydantic import ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Telegram Bot
    bot_token: str

    # Download settings
    max_file_size_mb: int = 50
    download_timeout: int = 300  # seconds
    temp_dir: str = "/tmp/yt-downloader-bot"  # noqa: S108

    # Cookies file for platforms requiring authentication (e.g. Instagram)
    cookies_file: str | None = None

    # Rate limiting
    rate_limit_requests: int = 5
    rate_limit_window: int = 60  # seconds

    @field_validator(
        "max_file_size_mb",
        "download_timeout",
        "rate_limit_requests",
        "rate_limit_window",
    )
    @classmethod
    def validate_positive(cls, v: int, info: ValidationInfo) -> int:
        if v <= 0:
            raise ValueError(f"{info.field_name} must be positive")
        return v

    @field_validator("max_file_size_mb")
    @classmethod
    def validate_max_file_size(cls, v: int) -> int:
        if v > 50:
            raise ValueError("max_file_size_mb cannot exceed 50 (Telegram API limit)")
        return v

    @field_validator("download_timeout")
    @classmethod
    def validate_download_timeout(cls, v: int) -> int:
        if v > 600:
            raise ValueError("download_timeout cannot exceed 600 seconds")
        return v

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()  # type: ignore[call-arg]  # pydantic-settings loads from env
