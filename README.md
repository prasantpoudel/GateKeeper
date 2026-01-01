# 🚦 GateKeeper — A Complete Rate Limiting Toolkit for Python

**GateKeeper** is a flexible, extensible, and production-ready **rate limiting library for Python**, supporting **multiple rate limiting algorithms** with **In-Memory**, **Redis**, and **SQLite** backing.

It is designed to help developers:

* Protect APIs from abuse
* Control traffic bursts
* Enforce quotas and usage policies
* Learn and experiment with real-world rate limiting strategies

> Inspired by real systems used in API gateways, cloud services, and distributed systems.

---

## ✨ Features

* ✅ **5 Rate Limiting Algorithms**: Fixed Window, Sliding Window Log, Sliding Window Counter, Token Bucket, Leaky Bucket.
* ✅ **Multiple Storage Backends**:
    * **In-Memory**: Thread-safe, fast, single-node.
    * **Redis**: Distributed, high-performance, atomic (using Lua scripts).
    * **SQLite**: Persistent, local file-based storage.
* ✅ **Clean API**: Swap algorithms and storage backends easily.
* ✅ **Thread-Safe**: Designed to work in concurrent environments.

---

## 📚 Supported Rate Limiting Algorithms

| Algorithm | Best Use Case |
| :--- | :--- |
| **Fixed Window Counter** | Simple limits (e.g., 100 req/min). Memory efficient. |
| **Sliding Window Log** | Precise rate control. Tracks every request timestamp. |
| **Sliding Window Counter** | Balance between accuracy & performance. Smoother than Fixed Window. |
| **Token Bucket** | Allows bursts of traffic while maintaining an average rate. |
| **Leaky Bucket** | Enforces a constant flow rate. generic traffic shaping. |

---

## ⚙️ Installation

```bash
pip install gatekeeperpy
```

*Note: You need a running Redis instance to use the Redis backend.*

---

## 🚀 Usage

### 1. Simple In-Memory Usage (Default)

Perfect for single-process applications or testing.

```python
from gatekeeper import FixedWindowLimiter

# Allow 10 requests per minute
limiter = FixedWindowLimiter(max_requests=10, window_seconds=60)

user_id = "user_123"

if limiter.allow(user_id):
    print("Request allowed!")
else:
    print("Rate limit exceeded.")
```

### 2. Distributed Rate Limiting with Redis

Essential for distributed systems where multiple app instances share the limit.

```python
import redis
from gatekeeper import TokenBucketLimiter, RedisStorage

# Connect to Redis
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
storage = RedisStorage(redis_client)

# Capacity 100 tokens, refills 10 tokens/second
limiter = TokenBucketLimiter(capacity=100, refill_rate=10, storage=storage)

if limiter.allow("api_key:xyz"):
    process_request()
```

### 3. Persistent Storage with SQLite

Good for maintaining limits across application restarts without a full database server.

```python
from gatekeeper import SlidingWindowCounterLimiter, SQLiteStorage

storage = SQLiteStorage("limits.db")

limiter = SlidingWindowCounterLimiter(max_requests=500, window_seconds=3600, storage=storage)

if limiter.allow("user_ip:192.168.1.1"):
    pass
```

---

## 🧩 Architecture

GateKeeper separates the **Algorithm** logic from the **Storage** backend. This allows any algorithm to run on any storage.

```
┌─────────────────┐       ┌──────────────────┐
│   RateLimiter   │─────▶│     Storage      │
│   (Algorithm)   │       │   (Interface)    │
└────────┬────────┘       └────────┬─────────┘
         │                         │
   ┌─────┴─────┐           ┌───────┼────────┐
   │           │           │       │        │
FixedWin    TokenBkt    Memory   Redis    SQLite
```

---

## 🧪 Algorithms Explained

### 1️⃣ Fixed Window Counter
Counts requests in fixed time blocks (e.g., 12:00-12:01).
*   **Pros**: Low memory, fast.
*   **Cons**: Can allow double the limit at window boundaries (burst).

### 2️⃣ Sliding Window Log
Stores the timestamp of every request.
*   **Pros**: 100% accurate.
*   **Cons**: High memory usage (stores all timestamps).

### 3️⃣ Sliding Window Counter
Approximates the sliding window using the previous window's weight.
*   **Pros**: Accurate enough, memory efficient.
*   **Cons**: Slight approximation error.

### 4️⃣ Token Bucket
Tokens are added at a fixed rate up to a capacity. Each request consumes a token.
*   **Pros**: Allows bursts (up to capacity).
*   **Cons**: Slightly more complex to tune.

### 5️⃣ Leaky Bucket
Requests act like water entering a bucket. The bucket leaks at a constant rate.
*   **Pros**: Smooths traffic to a constant rate.
*   **Cons**: Bursts are dropped (or queued) strictly.

---

## ⚡ Performance

*   **In-Memory**: Microsecond latency. Fastest.
*   **Redis**: Depends on network (typically <1ms on localhost). Uses **Lua scripts** to perform check-and-set operations atomically, minimizing round-trips.
*   **SQLite**: Slower than Redis/Memory but provides persistence on disk.

---

## 🧪 Testing

The library includes a comprehensive test suite using `pytest`.

```bash
# Run all tests
PYTHONPATH=. pytest

# Run tests with output
PYTHONPATH=. pytest -v
```

---

## 📄 License

MIT License.
