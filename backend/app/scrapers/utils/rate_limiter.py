"""
Rate limiting utilities for web scraping.
"""
import time
import random
from collections import defaultdict
from typing import Dict


class RateLimiter:
    """Simple rate limiter to avoid overwhelming servers."""

    def __init__(self):
        """Initialize rate limiter."""
        self.last_request_time: Dict[str, float] = defaultdict(float)
        self.request_counts: Dict[str, int] = defaultdict(int)

    def wait_if_needed(
        self,
        source: str,
        min_delay: float = 2.0,
        max_delay: float = 5.0
    ):
        """
        Wait if needed to respect rate limits.

        Args:
            source: Source name (e.g., 'indeed', 'linkedin')
            min_delay: Minimum delay between requests in seconds
            max_delay: Maximum delay between requests in seconds
        """
        current_time = time.time()
        last_time = self.last_request_time[source]

        if last_time > 0:
            elapsed = current_time - last_time
            required_delay = random.uniform(min_delay, max_delay)

            if elapsed < required_delay:
                wait_time = required_delay - elapsed
                time.sleep(wait_time)

        self.last_request_time[source] = time.time()
        self.request_counts[source] += 1

    def get_request_count(self, source: str) -> int:
        """
        Get total number of requests made to a source.

        Args:
            source: Source name

        Returns:
            Request count
        """
        return self.request_counts[source]

    def reset(self, source: str):
        """
        Reset rate limiter for a source.

        Args:
            source: Source name
        """
        self.last_request_time[source] = 0
        self.request_counts[source] = 0


# Global rate limiter instance
rate_limiter = RateLimiter()
