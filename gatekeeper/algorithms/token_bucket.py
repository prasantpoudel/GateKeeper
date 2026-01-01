import time
from typing import Optional
from .base import RateLimiter
from ..storage import Storage


class TokenBucketLimiter(RateLimiter):
    def __init__(
        self, capacity: int, refill_rate: float, storage: Optional[Storage] = None
    ):
        super().__init__(storage)
        self.capacity = capacity
        self.refill_rate = refill_rate  # tokens per second

    def allow(self, key: str) -> bool:
        token_key = f"tb:{key}:tokens"
        ts_key = f"tb:{key}:ts"

        now = time.time()

        try:
            script = """
            local token_key = KEYS[1]
            local ts_key = KEYS[2]
            local capacity = tonumber(ARGV[1])
            local refill_rate = tonumber(ARGV[2])
            local now = tonumber(ARGV[3])
            local requested = 1
            
            local last_tokens = tonumber(redis.call('GET', token_key))
            if last_tokens == nil then
                last_tokens = capacity
            end
            
            local last_ts = tonumber(redis.call('GET', ts_key))
            if last_ts == nil then
                last_ts = now
            end
            
            local delta = math.max(0, now - last_ts)
            local filled_tokens = math.min(capacity, last_tokens + (delta * refill_rate))
            
            if filled_tokens >= requested then
                local new_tokens = filled_tokens - requested
                redis.call('SET', token_key, new_tokens)
                redis.call('SET', ts_key, now)
                -- Optional: Set expiry
                return 1
            end
            
            return 0
            """
            result = self.storage.execute_lua(
                script, [token_key, ts_key], [self.capacity, self.refill_rate, now]
            )
            return bool(result)

        except NotImplementedError:
            last_tokens = self.storage.get(token_key)
            last_ts = self.storage.get(ts_key)

            if last_tokens is None:
                last_tokens = self.capacity
            else:
                last_tokens = float(last_tokens)

            if last_ts is None:
                last_ts = now
            else:
                last_ts = float(last_ts)

            delta = max(0, now - last_ts)
            filled_tokens = min(self.capacity, last_tokens + (delta * self.refill_rate))

            if filled_tokens >= 1:
                new_tokens = filled_tokens - 1
                self.storage.set(token_key, new_tokens)
                self.storage.set(ts_key, now)
                return True
            return False
