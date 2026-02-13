# YT Downloader Bot

Telegram bot for downloading videos from YouTube, Instagram, and TikTok.

## Features

- Download videos from YouTube, Instagram Reels/Posts, and TikTok
- Automatic URL validation and sanitization
- Rate limiting to prevent abuse
- 50MB file size limit (Telegram API constraint)
- Docker support for easy deployment

## Bot commands

- `/start` — Welcome message and supported platforms
- `/help` — Usage instructions and limitations
- Send any video URL — Bot downloads and sends the video

## Requirements

- Python 3.14+
- Poetry 2.0+
- ffmpeg (for video processing)

## Installation

```bash
git clone https://github.com/danilkiff/yt-downloader-bot.git
cd yt-downloader-bot
make dev              # Install all dependencies
cp .env.example .env  # Configure BOT_TOKEN
```

## Usage

```bash
make run              # Run locally
make docker-up        # Or with Docker
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `BOT_TOKEN` | (required) | Telegram bot token from @BotFather |
| `MAX_FILE_SIZE_MB` | 50 | Maximum video file size |
| `DOWNLOAD_TIMEOUT` | 300 | Download timeout in seconds |
| `RATE_LIMIT_REQUESTS` | 5 | Max requests per window |
| `RATE_LIMIT_WINDOW` | 60 | Rate limit window in seconds |

## Development

```bash
make dev        # Install dev dependencies
make test       # Run tests
make cov        # Run tests with coverage
make lint       # Lint + format check + typecheck
make format     # Auto-format code
make check      # Run all checks (lint + test)
make clean      # Remove temporary files
```

## Security

- URL whitelist validation (only YouTube, Instagram, TikTok)
- Tracking parameter sanitization
- Rate limiting per user
- Non-root Docker container
- Read-only filesystem in production

## License

[CC BY-SA 4.0](LICENSE)
