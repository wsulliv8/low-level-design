import threading
import time
from typing import List


class Bucket:
    """An atomic data container representing a 1-second chunk of time."""

    def __init__(self):
        self.timestamp: int = 0  # Epoch second this bucket currently represents
        self.count: int = 0
        self._lock = threading.Lock()  # Fine-grained lock per second

    def increment(self, current_second: int) -> None:
        """Increments the click count, resetting if the bucket has expired."""
        with self._lock:
            if self.timestamp != current_second:
                # This bucket belongs to a previous window cycle (e.g., 5 mins ago).
                # Wipe the old historical counts and claim it for the current second.
                self.timestamp = current_second
                self.count = 1
            else:
                self.count += 1

    def get_count_if_valid(self, current_second: int, duration_seconds: int) -> int:
        """Returns count only if the bucket falls within the active tracking window."""
        with self._lock:
            # If the bucket's data is newer than the total window cutoff, it's valid
            if (
                current_second - self.timestamp < duration_seconds
                and self.timestamp > 0
            ):
                return self.count
            return 0


class CircularBucketArray:
    """A fixed-size Ring Buffer wrapping indices via modulo arithmetic."""

    def __init__(self, capacity: int):
        self.capacity = capacity
        self.buckets: List[Bucket] = [Bucket() for _ in range(capacity)]

    def get_bucket(self, current_second: int) -> Bucket:
        # Modulo arithmetic wraps the index cleanly within bounds [0, capacity-1]
        index = current_second % self.capacity
        return self.buckets[index]


class ClickTracker:
    """The central state machine managing metric collections."""

    def __init__(self, window_duration_seconds: int = 300):
        self.window_duration = window_duration_seconds
        self.buffer = CircularBucketArray(capacity=window_duration_seconds)

        # Track historical cumulative total for "whole duration" metrics
        self.total_lifetime_clicks = 0
        self._lifetime_lock = threading.Lock()

    def click(self) -> None:
        """Registers a click event concurrently at the current system time."""
        current_second = int(time.time())

        # 1. Update rolling window metric (Fine-grained lock)
        bucket = self.buffer.get_bucket(current_second)
        bucket.increment(current_second)

        # 2. Update whole-duration metric
        with self._lifetime_lock:
            self.total_lifetime_clicks += 1

    def get_clicks_in_duration(self, custom_duration: int = None) -> int:
        """
        Calculates total clicks within the specified past duration window.
        Defaults to the maximum window configuration (e.g., 300s).
        """
        current_second = int(time.time())
        duration = custom_duration if custom_duration else self.window_duration

        # Enforce boundary limits
        if duration > self.window_duration:
            raise ValueError(
                f"Cannot query duration beyond configured buffer limit of {self.window_duration}s"
            )

        total_clicks = 0

        # Collect metric data by summing valid buckets
        # Note: We do not lock the entire array, allowing clicks to continue concurrently
        for bucket in self.buffer.buckets:
            total_clicks += bucket.get_count_if_valid(current_second, duration)

        return total_clicks

    def get_total_lifetime_clicks(self) -> int:
        """Requirement: Get clicks received during whole duration."""
        with self._lifetime_lock:
            return self.total_lifetime_clicks
