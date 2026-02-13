# CLAUDE.md

This file provides guidance for Claude Code when working with this repository.

## Project overview

Telegram bot for downloading videos from YouTube, Instagram, and TikTok. Built with Python 3.14, aiogram 3.x, and yt-dlp.

## Commands

```bash
make dev        # Install all dependencies
make run        # Run the bot locally
make test       # Run tests
make cov        # Run tests with coverage
make lint       # Lint + format check + typecheck
make format     # Auto-format code
make check      # Run all checks (lint + test)
make clean      # Remove temporary files
```

## Architecture

```
src/bot/
├── config.py           # Settings (pydantic-settings, loads from .env)
├── main.py             # Entry point, bot initialization
├── handlers/
│   └── video.py        # Message handlers (/start, /help, URL processing)
├── services/
│   ├── downloader.py   # VideoDownloader - yt-dlp wrapper
│   └── rate_limiter.py # RateLimiter - sliding window algorithm
└── validators/
    └── url.py          # URLValidator - whitelist-based URL validation
```

## Key design decisions

- **URL Validation**: Whitelist approach - only specific domains (youtube.com, instagram.com, tiktok.com) are allowed. Tracking parameters are stripped from URLs.
- **Rate Limiting**: In-memory sliding window per user. Default: 5 requests per 60 seconds.
- **File Size**: 50MB limit (Telegram Bot API constraint).
- **Async**: All I/O operations are async. yt-dlp calls run in executor to avoid blocking.
- **Error Handling**: Custom exceptions (`DownloadError`, `FileTooLargeError`, `VideoUnavailableError`, `RateLimitExceeded`) with user-friendly messages.

## Code style

- Comments and documentation in English
- Type hints required for all functions
- Use `ruff` for linting and formatting
- Follow existing patterns in the codebase
- Every new source file must start with `# SPDX-License-Identifier: CC-BY-SA-4.0`

## Testing

- Tests are in `tests/` directory
- Use `pytest` with `pytest-asyncio` for async tests
- Minimum coverage requirement: 80%
- Mock external services (yt-dlp, Telegram API) in tests

## Environment variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `BOT_TOKEN` | Yes | - | Telegram bot token |
| `MAX_FILE_SIZE_MB` | No | 50 | Max video size in MB |
| `DOWNLOAD_TIMEOUT` | No | 300 | Download timeout in seconds |
| `RATE_LIMIT_REQUESTS` | No | 5 | Max requests per window |
| `RATE_LIMIT_WINDOW` | No | 60 | Rate limit window in seconds |
| `TEMP_DIR` | No | /tmp/yt-downloader-bot | Temp directory for downloads |

## Security considerations

When modifying this codebase:

1. **Never** add new domains to the URL whitelist without careful review
2. **Never** disable URL validation or sanitization
3. **Always** clean up temporary files after processing
4. **Never** expose bot token or other secrets in logs
5. **Always** validate user input before processing
