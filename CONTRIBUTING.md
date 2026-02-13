# Contributing

Thank you for your interest in contributing!

## Development Setup

```bash
git clone https://github.com/danilkiff/yt-downloader-bot.git
cd yt-downloader-bot
make dev              # Install all dependencies
cp .env.example .env  # Configure BOT_TOKEN
```

## Workflow

1. Fork the repository
2. Create a feature branch from `main`
3. Make your changes
4. Run all checks: `make check`
5. Open a Pull Request

## Code Standards

- **Formatting & linting**: `ruff` — run `make format` before committing
- **Type checking**: `mypy` with `disallow_untyped_defs` — all functions must have type hints
- **Tests**: `pytest` — minimum 80% coverage, run `make cov` to verify
- **All checks at once**: `make check` (lint + typecheck + test)

## Commit Messages

Use concise, imperative messages:

```
Add TikTok short URL support
Fix rate limiter window expiration
Remove unused validator parameter
```

## Pull Requests

- Keep PRs focused on a single change
- Include tests for new functionality
- Ensure `make check` passes before requesting review
- Describe *what* and *why* in the PR description

## Reporting Issues

- Use GitHub Issues
- Include steps to reproduce for bugs
- For security vulnerabilities, see [SECURITY.md](SECURITY.md)
