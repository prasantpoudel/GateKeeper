from typing import Optional, Any, List
import redis
from .base import Storage


class RedisStorage(Storage):
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    def get(self, key: str) -> Optional[Any]:
        val = self.redis.get(key)
        if val:
            return val.decode("utf-8")
        return None

    def set(self, key: str, value: Any, expiry: Optional[int] = None):
        self.redis.set(key, value, ex=expiry)

    def incr(self, key: str, amount: int = 1, expiry: Optional[int] = None) -> int:
        pipe = self.redis.pipeline()
        pipe.incrby(key, amount)
        if expiry:
            pipe.expire(key, expiry)
        results = pipe.execute()
        return results[0]

    def add_timestamp(self, key: str, timestamp: float, expiry: Optional[int] = None):
        pipe = self.redis.pipeline()
        pipe.zadd(key, {str(timestamp): timestamp})
        if expiry:
            pipe.expire(key, expiry)
        pipe.execute()

    def count_timestamps(self, key: str, start: float, end: float) -> int:
        return self.redis.zcount(key, start, end)

    def remove_timestamps(self, key: str, max_timestamp: float):
        self.redis.zremrangebyscore(key, "-inf", max_timestamp)

    def execute_lua(self, script: str, keys: List[str], args: List[Any]) -> Any:
        # Register script is efficient but Eval is easier for dynamic.
        # Redis-py handles eval caching usually?
        return self.redis.eval(script, len(keys), *keys, *args)
