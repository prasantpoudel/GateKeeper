import time
from typing import Optional
from .base import RateLimiter
from ..storage import Storage


class SlidingWindowCounterLimiter(RateLimiter):
    def __init__(
        self, max_requests: int, window_seconds: int, storage: Optional[Storage] = None
    ):
        super().__init__(storage)
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    def allow(self, key: str) -> bool:
        now = time.time()
        window_size = self.window_seconds

        current_window = int(now // window_size)
        prev_window = current_window - 1

        curr_key = f"swc:{key}:{current_window}"
        prev_key = f"swc:{key}:{prev_window}"

        # Calculate weight of previous window
        # How much of the previous window overlaps with the sliding window?
        # Actually it's: count = curr + prev * (1 - (now - current_window_start) / size)
        # weight = (window_size - (now % window_size)) / window_size
        time_into_window = now % window_size
        weight = (window_size - time_into_window) / window_size

        # Keys for Lua
        keys = [curr_key, prev_key]
        expiry = int(window_size * 2 + 10)  # Keep long enough for next window LOOKUP

        try:
            script = """
            local curr_key = KEYS[1]
            local prev_key = KEYS[2]
            local weight = tonumber(ARGV[1])
            local max_req = tonumber(ARGV[2])
            local expiry = tonumber(ARGV[3])
            
            local curr = tonumber(redis.call('GET', curr_key) or "0")
            local prev = tonumber(redis.call('GET', prev_key) or "0")
            
            local est = curr + (prev * weight)
            
            if est < max_req then
                redis.call('INCR', curr_key)
                redis.call('EXPIRE', curr_key, expiry)
                return 1
            end
            return 0
            """
            result = self.storage.execute_lua(
                script, keys, [weight, self.max_requests, expiry]
            )
            return bool(result)

        except NotImplementedError:
            curr_count = self.storage.get(curr_key)
            if curr_count is None:
                curr_count = 0
            else:
                curr_count = int(curr_count)

            prev_count = self.storage.get(prev_key)
            if prev_count is None:
                prev_count = 0
            else:
                prev_count = int(prev_count)

            estimated_count = curr_count + (prev_count * weight)

            if estimated_count < self.max_requests:
                self.storage.incr(curr_key, 1, expiry)
                return True
            return False
