import time
from typing import Optional
from .base import RateLimiter
from ..storage import Storage


class FixedWindowLimiter(RateLimiter):
    def __init__(
        self, max_requests: int, window_seconds: int, storage: Optional[Storage] = None
    ):
        super().__init__(storage)
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    def allow(self, key: str) -> bool:
        now = int(time.time())
        window_start = now // self.window_seconds
        storage_key = f"fixed:{key}:{window_start}"

        current_count = self.storage.incr(storage_key, 1, self.window_seconds)

        return current_count <= self.max_requests
