# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

1. **Do not** open a public GitHub issue
2. Email the maintainer or use [GitHub private vulnerability reporting](https://github.com/danilkiff/yt-downloader-bot/security/advisories/new)
3. Include a description, steps to reproduce, and potential impact

You should receive a response within 48 hours.

## Security Design

This project handles user-provided URLs and downloads external content. Key safeguards:

- **URL whitelist**: Only YouTube, Instagram, and TikTok domains are accepted (regex-based validation)
- **Query parameter sanitization**: Tracking parameters are stripped; only meaningful params are kept
- **Rate limiting**: Per-user sliding window to prevent abuse
- **File size limits**: 50MB cap enforced both in yt-dlp format selection and post-download check
- **Temporary file cleanup**: Downloaded files are removed after sending
- **Non-root Docker**: Container runs as unprivileged user with dropped capabilities
- **Read-only filesystem**: Production container uses read-only root filesystem
