# Contributing

Thank you for your interest in contributing!

## Development setup

```bash
git clone https://github.com/danilkiff/yt-downloader-bot.git
cd yt-downloader-bot
make dev              # Install all dependencies
cp .env.example .env  # Configure BOT_TOKEN
```

## Workflow

1. Fork the repository
2. Create a feature branch from `master`
3. Make your changes
4. Run all checks: `make check`
5. Open a Pull Request

## Code standards

- **Formatting & linting**: `ruff` — run `make format` before committing
- **Type checking**: `mypy` with `disallow_untyped_defs` — all functions must have type hints
- **Tests**: `pytest` — minimum 80% coverage, run `make cov` to verify
- **All checks at once**: `make check` (lint + typecheck + test)

## Commit messages

Use concise, imperative messages:

```
Add TikTok short URL support
Fix rate limiter window expiration
Remove unused validator parameter
```

## Pull requests

- Keep PRs focused on a single change
- Include tests for new functionality
- Ensure `make check` passes before requesting review
- Describe *what* and *why* in the PR description

## AI-assisted contributions

We explicitly welcome contributions made with the help of AI tools, including autonomous coding agents (Claude Code, Cursor, Copilot Workspace, etc.). Unlike some projects that restrict AI-generated contributions, we care about the **result**, not the method.

Rules:

- **A human is always accountable.** Every PR must be submitted by a person who takes responsibility for the changes — reviews them, can explain the reasoning, and will address feedback.
- **Mark AI involvement.** Add a `Co-Authored-By` trailer (e.g., `Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>`) or note it in the PR description.
- **Quality bar is the same.** AI-assisted PRs must pass `make check`, include tests, and follow all the same standards as any other contribution. Low-effort "prompt-and-paste" PRs will be rejected just like any other low-quality submission.

## Reporting issues

- Use GitHub Issues
- Include steps to reproduce for bugs
- For security vulnerabilities, see [SECURITY.md](SECURITY.md)
