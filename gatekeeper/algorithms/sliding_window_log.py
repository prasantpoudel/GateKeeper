import time
from typing import Optional
from .base import RateLimiter
from ..storage import Storage


class SlidingWindowLogLimiter(RateLimiter):
    def __init__(
        self, max_requests: int, window_seconds: int, storage: Optional[Storage] = None
    ):
        super().__init__(storage)
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    def allow(self, key: str) -> bool:
        now = time.time()
        window_start = now - self.window_seconds
        storage_key = f"sliding_log:{key}"

        try:
            # Try atomic Lua script if supported (e.g. Redis)
            script = """
             local key = KEYS[1]
             local now = tonumber(ARGV[1])
             local window_start = tonumber(ARGV[2])
             local max_requests = tonumber(ARGV[3])
             local expiry = tonumber(ARGV[4])
             
             redis.call('ZREMRANGEBYSCORE', key, '-inf', window_start)
             local count = redis.call('ZCARD', key)
             
             if count < max_requests then
                 redis.call('ZADD', key, now, now)
                 redis.call('EXPIRE', key, expiry)
                 return 1
             end
             return 0
             """
            # args must be strings or convertible
            result = self.storage.execute_lua(
                script,
                [storage_key],
                [now, window_start, self.max_requests, self.window_seconds],
            )
            return bool(result)

        except NotImplementedError:
            # Fallback for storage that doesn't support Lua (Memory, SQLite)
            # Note: This might have race conditions in distributed non-atomic storage
            # but Memory is locked and SQLite matches this logic.

            self.storage.remove_timestamps(storage_key, window_start)
            count = self.storage.count_timestamps(storage_key, window_start, now)

            if count < self.max_requests:
                # Pass expiry mainly to update TTL if needed
                self.storage.add_timestamp(storage_key, now, self.window_seconds)
                return True
            return False
