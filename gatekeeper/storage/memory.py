import time
import threading
from typing import Optional, Any, Dict, List
from .base import Storage


class InMemoryStorage(Storage):
    def __init__(self):
        self._data: Dict[str, Any] = {}
        self._expiry: Dict[str, float] = {}
        self._sorted_sets: Dict[str, List[float]] = {}
        self._lock = threading.Lock()

    def _is_expired(self, key: str) -> bool:
        if key in self._expiry and time.time() > self._expiry[key]:
            self._delete(key)
            return True
        return False

    def _delete(self, key: str):
        self._data.pop(key, None)
        self._expiry.pop(key, None)
        self._sorted_sets.pop(key, None)

    def _set_expiry(self, key: str, expiry: Optional[int]):
        if expiry:
            self._expiry[key] = time.time() + expiry
        else:
            # If no expiry is provided, we might want to clear existing expiry?
            # Or preserve it? Redis preserves TTL on INCR, but SET removes it unless specified.
            # For simplicity, we'll implement overwrite behavior if expiry is passed, else preserve.
            pass

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if self._is_expired(key):
                return None
            return self._data.get(key)

    def set(self, key: str, value: Any, expiry: Optional[int] = None):
        with self._lock:
            self._data[key] = value
            if expiry:
                self._expiry[key] = time.time() + expiry
            elif key in self._expiry:
                del self._expiry[key]

    def incr(self, key: str, amount: int = 1, expiry: Optional[int] = None) -> int:
        with self._lock:
            if self._is_expired(key):
                # Expired means it's gone
                pass

            val = self._data.get(key, 0)
            if not isinstance(val, int):
                val = 0

            new_val = val + amount
            self._data[key] = new_val

            if expiry:
                self._expiry[key] = time.time() + expiry

            return new_val

    def add_timestamp(self, key: str, timestamp: float, expiry: Optional[int] = None):
        with self._lock:
            self._is_expired(key)

            if key not in self._sorted_sets:
                self._sorted_sets[key] = []

            self._sorted_sets[key].append(timestamp)
            # Assuming timestamps are added in order usually, but sort to be safe
            self._sorted_sets[key].sort()

            if expiry:
                self._expiry[key] = time.time() + expiry

    def count_timestamps(self, key: str, start: float, end: float) -> int:
        with self._lock:
            if self._is_expired(key):
                return 0

            timestamps = self._sorted_sets.get(key, [])
            return sum(1 for t in timestamps if start <= t <= end)

    def remove_timestamps(self, key: str, max_timestamp: float):
        with self._lock:
            if self._is_expired(key):
                return

            if key in self._sorted_sets:
                self._sorted_sets[key] = [
                    t for t in self._sorted_sets[key] if t > max_timestamp
                ]
