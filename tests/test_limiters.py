import pytest
import time
from gatekeeper import (
    InMemoryStorage,
    SQLiteStorage,
    RedisStorage,
    FixedWindowLimiter,
    SlidingWindowLogLimiter,
    SlidingWindowCounterLimiter,
    TokenBucketLimiter,
    LeakyBucketLimiter,
)


def get_valid_storages():
    storages = [InMemoryStorage(), SQLiteStorage(":memory:")]
    try:
        import redis

        client = redis.Redis(host="localhost", port=6379, socket_connect_timeout=0.1)
        if client.ping():
            storages.append(RedisStorage(client))
    except Exception:
        pass
    return storages


storages = get_valid_storages()
storage_ids = [s.__class__.__name__ for s in storages]


@pytest.mark.parametrize("storage", storages, ids=storage_ids)
class TestLimiters:
    def test_fixed_window(self, storage):
        key = f"fw_{storage.__class__.__name__}_{time.time()}"
        limiter = FixedWindowLimiter(max_requests=2, window_seconds=1, storage=storage)

        assert limiter.allow(key) is True
        assert limiter.allow(key) is True
        assert limiter.allow(key) is False

        time.sleep(1.1)
        assert limiter.allow(key) is True

    def test_sliding_log(self, storage):
        key = f"sl_{storage.__class__.__name__}_{time.time()}"
        limiter = SlidingWindowLogLimiter(
            max_requests=2, window_seconds=1, storage=storage
        )

        assert limiter.allow(key) is True
        assert limiter.allow(key) is True
        assert limiter.allow(key) is False

        time.sleep(1.1)
        assert limiter.allow(key) is True

    def test_sliding_counter(self, storage):
        key = f"sc_{storage.__class__.__name__}_{time.time()}"
        limiter = SlidingWindowCounterLimiter(
            max_requests=2, window_seconds=1, storage=storage
        )

        assert limiter.allow(key) is True
        assert limiter.allow(key) is True
        # Algorithm: if est < max (2 < 2 is False) -> Deny.
        assert limiter.allow(key) is False

        time.sleep(1.1)
        assert limiter.allow(key) is True

    def test_token_bucket(self, storage):
        key = f"tb_{storage.__class__.__name__}_{time.time()}"
        # Capacity 2, burst 2
        limiter = TokenBucketLimiter(capacity=2, refill_rate=2, storage=storage)

        assert limiter.allow(key) is True
        assert limiter.allow(key) is True
        assert limiter.allow(key) is False

        time.sleep(0.6)
        assert limiter.allow(key) is True

    def test_leaky_bucket(self, storage):
        key = f"lb_{storage.__class__.__name__}_{time.time()}"
        limiter = LeakyBucketLimiter(capacity=2, leak_rate=2, storage=storage)

        assert limiter.allow(key) is True
        assert limiter.allow(key) is True
        assert limiter.allow(key) is False

        time.sleep(0.6)
        assert limiter.allow(key) is True
