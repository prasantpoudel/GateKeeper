import time
from typing import Optional
from .base import RateLimiter
from ..storage import Storage


class LeakyBucketLimiter(RateLimiter):
    def __init__(
        self, capacity: int, leak_rate: float, storage: Optional[Storage] = None
    ):
        super().__init__(storage)
        self.capacity = capacity
        self.leak_rate = leak_rate  # requests per second

    def allow(self, key: str) -> bool:
        level_key = f"lb:{key}:level"
        ts_key = f"lb:{key}:ts"

        now = time.time()

        try:
            script = """
            local level_key = KEYS[1]
            local ts_key = KEYS[2]
            local capacity = tonumber(ARGV[1])
            local leak_rate = tonumber(ARGV[2])
            local now = tonumber(ARGV[3])
            
            local last_level = tonumber(redis.call('GET', level_key) or "0")
            local last_ts = tonumber(redis.call('GET', ts_key) or now)
            
            local delta = math.max(0, now - last_ts)
            local leaked = delta * leak_rate
            
            local current_level = math.max(0, last_level - leaked)
            
            if current_level + 1 <= capacity then
                redis.call('SET', level_key, current_level + 1)
                redis.call('SET', ts_key, now)
                return 1
            end
            
            -- We can optionally update ts for leak calculation even on reject?
            -- Usually "GCRA" does update state to punish arrival rate? 
            -- Simple Leaky Bucket just drops. Keeping state as is (besides leak calc) is fine.
            
            return 0
            """
            result = self.storage.execute_lua(
                script, [level_key, ts_key], [self.capacity, self.leak_rate, now]
            )
            return bool(result)

        except NotImplementedError:
            last_level = self.storage.get(level_key)
            if last_level is None:
                last_level = 0
            else:
                last_level = float(last_level)

            last_ts = self.storage.get(ts_key)
            if last_ts is None:
                last_ts = now
            else:
                last_ts = float(last_ts)

            delta = max(0, now - last_ts)
            leaked = delta * self.leak_rate

            current_level = max(0, last_level - leaked)

            if current_level + 1 <= self.capacity:
                self.storage.set(level_key, current_level + 1)
                self.storage.set(ts_key, now)
                return True
            return False
