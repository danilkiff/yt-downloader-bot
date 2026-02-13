# SPDX-License-Identifier: CC-BY-SA-4.0

"""Tests for rate limiter service."""

from unittest.mock import patch

import pytest

from bot.services.rate_limiter import RateLimiter, RateLimitExceeded


class TestRateLimiter:
    """Test cases for RateLimiter."""

    def test_allows_requests_under_limit(self, rate_limiter):
        user_id = 12345
        for _ in range(5):
            rate_limiter.check_rate_limit(user_id)

    def test_blocks_requests_over_limit(self, rate_limiter):
        user_id = 12345
        for _ in range(5):
            rate_limiter.check_rate_limit(user_id)

        with pytest.raises(RateLimitExceeded) as exc_info:
            rate_limiter.check_rate_limit(user_id)

        assert exc_info.value.retry_after > 0

    def test_different_users_have_separate_limits(self, rate_limiter):
        user_1 = 11111
        user_2 = 22222

        for _ in range(5):
            rate_limiter.check_rate_limit(user_1)

        # user_2 should still be able to make requests
        rate_limiter.check_rate_limit(user_2)

    def test_window_expiration(self):
        rate_limiter = RateLimiter(max_requests=2, window_seconds=10)
        user_id = 12345

        with patch("bot.services.rate_limiter.time.time") as mock_time:
            mock_time.return_value = 1000.0

            rate_limiter.check_rate_limit(user_id)
            rate_limiter.check_rate_limit(user_id)

            with pytest.raises(RateLimitExceeded):
                rate_limiter.check_rate_limit(user_id)

            # Advance past window
            mock_time.return_value = 1011.0

            # Should be allowed again
            rate_limiter.check_rate_limit(user_id)

    def test_retry_after_calculation(self):
        rate_limiter = RateLimiter(max_requests=1, window_seconds=10)
        user_id = 12345

        rate_limiter.check_rate_limit(user_id)

        with pytest.raises(RateLimitExceeded) as exc_info:
            rate_limiter.check_rate_limit(user_id)

        assert 1 <= exc_info.value.retry_after <= 11

    @pytest.mark.parametrize("value", [0, -1])
    def test_invalid_max_requests(self, value):
        with pytest.raises(ValueError, match="max_requests must be positive"):
            RateLimiter(max_requests=value, window_seconds=60)

    @pytest.mark.parametrize("value", [0, -1])
    def test_invalid_window_seconds(self, value):
        with pytest.raises(ValueError, match="window_seconds must be positive"):
            RateLimiter(max_requests=5, window_seconds=value)

    def test_properties(self):
        rate_limiter = RateLimiter(max_requests=10, window_seconds=120)
        assert rate_limiter.max_requests == 10
        assert rate_limiter.window_seconds == 120
