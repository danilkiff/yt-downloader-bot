# SPDX-License-Identifier: CC-BY-SA-4.0

"""Tests for main module."""

import os
from unittest.mock import patch

import pytest

from bot.main import main


class TestMain:
    """Test cases for main function."""

    @pytest.mark.asyncio
    async def test_main_missing_bot_token(self):
        from bot.config import get_settings

        get_settings.cache_clear()
        with (
            patch.dict(os.environ, {}, clear=True),
            patch(
                "bot.config.Settings.model_config",
                {"env_file": None, "env_file_encoding": "utf-8", "case_sensitive": False},
            ),
        ):
            with pytest.raises(SystemExit) as exc_info:
                await main()
            assert exc_info.value.code == 1
