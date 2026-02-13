# SPDX-License-Identifier: CC-BY-SA-4.0

"""Video download handlers."""

import logging
import re
from contextlib import suppress

from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command, CommandStart
from aiogram.types import FSInputFile, Message

from bot.services import (
    DownloadError,
    DownloadResult,
    FileTooLargeError,
    RateLimiter,
    RateLimitExceeded,
    VideoDownloader,
    VideoUnavailableError,
)
from bot.validators import ValidationResult, validate_url

logger = logging.getLogger(__name__)

router = Router(name="video")


@router.message(CommandStart())
async def handle_start(message: Message) -> None:
    """Handle /start command."""
    await message.answer(
        "Welcome to Video Downloader Bot!\n\n"
        "Send me a link from:\n"
        "- YouTube\n"
        "- Instagram (Reels/Posts)\n"
        "- TikTok\n\n"
        "I'll download and send you the video.\n\n"
        "Use /help for more information."
    )


@router.message(Command("help"))
async def handle_help(message: Message) -> None:
    """Handle /help command."""
    await message.answer(
        "How to use this bot:\n\n"
        "1. Copy a video link from YouTube, Instagram, or TikTok\n"
        "2. Send the link to this bot\n"
        "3. Wait for the video to download\n"
        "4. Receive the video file\n\n"
        "Limitations:\n"
        "- Maximum file size: 50MB\n"
        "- Private videos are not supported\n"
        "- Rate limited to prevent abuse\n\n"
        "Supported URL formats:\n"
        "- youtube.com/watch?v=...\n"
        "- youtu.be/...\n"
        "- instagram.com/reel/...\n"
        "- instagram.com/p/...\n"
        "- tiktok.com/@user/video/...\n"
        "- vm.tiktok.com/..."
    )


@router.message(F.text)
async def handle_video_url(
    message: Message,
    downloader: VideoDownloader,
    rate_limiter: RateLimiter,
) -> None:
    """Handle video URL messages."""
    if message.text is None or message.from_user is None:
        return

    user_id = message.from_user.id
    url = message.text.strip()

    # Validate URL
    validation: ValidationResult = validate_url(url)
    if not validation.is_valid:
        await message.answer(f"Invalid URL: {validation.error_message}")
        return

    # Check rate limit
    try:
        rate_limiter.check_rate_limit(user_id)
    except RateLimitExceeded as e:
        await message.answer(
            f"Too many requests. Please wait {e.retry_after} seconds before trying again."
        )
        return

    # Send processing message
    processing_msg = await message.answer(
        f"Downloading video from {validation.platform.value}... Please wait."
    )

    # Download video
    result: DownloadResult | None = None

    try:
        result = await downloader.download(validation.sanitized_url or url)

        # Send video with sanitized filename
        safe_filename = _sanitize_filename(result.title)
        video_file = FSInputFile(result.file_path, filename=f"{safe_filename}.mp4")

        await message.answer_video(
            video=video_file,
            caption=f"{result.title}\n\nDuration: {_format_duration(result.duration)}",
            supports_streaming=True,
        )

        # Delete processing message (ignore errors — video already sent)
        with suppress(TelegramAPIError):
            await processing_msg.delete()

        logger.info(
            "Video sent successfully",
            extra={
                "user_id": user_id,
                "platform": validation.platform.value,
                "file_size": result.file_size,
            },
        )

    except FileTooLargeError as e:
        await processing_msg.edit_text(
            f"Video is too large ({e.file_size // 1024 // 1024}MB). "
            f"Maximum allowed size is {e.max_size // 1024 // 1024}MB."
        )
        logger.warning(
            "File too large",
            extra={"user_id": user_id, "file_size": e.file_size},
        )

    except VideoUnavailableError as e:
        await processing_msg.edit_text(f"Video unavailable: {e}")
        logger.warning(
            "Video unavailable",
            extra={"user_id": user_id, "error": str(e)},
        )

    except DownloadError as e:
        await processing_msg.edit_text(
            "Failed to download video. Please check the URL and try again."
        )
        logger.error(
            "Download error",
            extra={"user_id": user_id, "error": str(e)},
        )

    except Exception:
        await processing_msg.edit_text("An unexpected error occurred. Please try again later.")
        logger.exception(
            "Unexpected error",
            extra={"user_id": user_id},
        )

    finally:
        # Clean up downloaded file
        if result is not None:
            downloader.cleanup_file(result.file_path)


def _sanitize_filename(title: str, max_length: int = 50) -> str:
    """Sanitize title for use as filename."""
    safe_title = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", title)
    safe_title = re.sub(r"[\s_]+", " ", safe_title).strip()
    if len(safe_title) > max_length:
        safe_title = safe_title[:max_length].rsplit(" ", 1)[0]
    return safe_title or "video"


def _format_duration(seconds: int | None) -> str:
    """Format duration in human-readable format."""
    if seconds is None:
        return "Unknown"

    minutes, secs = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)

    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"
