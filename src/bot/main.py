# SPDX-License-Identifier: CC-BY-SA-4.0

"""Main entry point for the Telegram bot."""

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from pydantic import ValidationError

from bot.config import get_settings
from bot.handlers import video_router
from bot.services import RateLimiter, VideoDownloader


def setup_logging() -> None:
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


async def main() -> None:
    """Run the bot."""
    setup_logging()
    logger = logging.getLogger(__name__)

    # Load settings
    try:
        settings = get_settings()
    except ValidationError as e:
        logger.error("Failed to load settings: %s", e)
        logger.error("Make sure BOT_TOKEN is set in environment or .env file")
        sys.exit(1)

    # Create services
    downloader = VideoDownloader(
        temp_dir=settings.temp_dir,
        max_file_size=settings.max_file_size_bytes,
        timeout=settings.download_timeout,
        cookies_file=settings.cookies_file,
    )
    rate_limiter = RateLimiter(
        max_requests=settings.rate_limit_requests,
        window_seconds=settings.rate_limit_window,
    )

    # Initialize bot
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    # Initialize dispatcher with dependencies via workflow_data
    dp = Dispatcher()
    dp["downloader"] = downloader
    dp["rate_limiter"] = rate_limiter
    dp.include_router(video_router)

    logger.info("Starting bot...")

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


def run() -> None:
    """Entry point for the bot."""
    asyncio.run(main())


if __name__ == "__main__":
    run()
