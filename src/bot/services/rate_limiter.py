"""Rate limiting service for anti-abuse protection."""

import time


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded."""

    def __init__(self, retry_after: int):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after} seconds.")


class RateLimiter:
    """
    In-memory rate limiter using sliding window algorithm.

    Includes automatic cleanup of stale user records to prevent memory leaks.
    """

    _CLEANUP_THRESHOLD_WINDOWS = 10

    def __init__(self, max_requests: int, window_seconds: int):
        if max_requests <= 0:
            raise ValueError("max_requests must be positive")
        if window_seconds <= 0:
            raise ValueError("window_seconds must be positive")

        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._user_logs: dict[int, list[float]] = {}
        self._last_cleanup = time.time()

    @property
    def max_requests(self) -> int:
        return self._max_requests

    @property
    def window_seconds(self) -> int:
        return self._window_seconds

    def check_rate_limit(self, user_id: int) -> None:
        """
        Check if user has exceeded rate limit and record the request.

        Raises:
            RateLimitExceeded: If rate limit is exceeded.
        """
        current_time = time.time()

        self._maybe_cleanup(current_time)

        if user_id not in self._user_logs:
            self._user_logs[user_id] = []
        timestamps = self._user_logs[user_id]

        # Sliding window: keep only timestamps within the window
        cutoff_time = current_time - self._window_seconds
        timestamps[:] = [ts for ts in timestamps if ts > cutoff_time]

        if len(timestamps) >= self._max_requests:
            oldest_timestamp = timestamps[0]
            retry_after = int(oldest_timestamp + self._window_seconds - current_time) + 1
            raise RateLimitExceeded(retry_after=max(1, retry_after))

        timestamps.append(current_time)

    def _maybe_cleanup(self, current_time: float) -> None:
        """Remove users with no recent activity to prevent memory leaks."""
        cleanup_interval = self._window_seconds * self._CLEANUP_THRESHOLD_WINDOWS
        if current_time - self._last_cleanup < cleanup_interval:
            return

        self._last_cleanup = current_time
        cutoff_time = current_time - cleanup_interval

        users_to_remove = [
            user_id
            for user_id, timestamps in self._user_logs.items()
            if not timestamps or max(timestamps) < cutoff_time
        ]
        for user_id in users_to_remove:
            del self._user_logs[user_id]
