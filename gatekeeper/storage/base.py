from abc import ABC, abstractmethod
from typing import Optional, Any


class Storage(ABC):
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        pass

    @abstractmethod
    def set(self, key: str, value: Any, expiry: Optional[int] = None):
        pass

    @abstractmethod
    def incr(self, key: str, amount: int = 1, expiry: Optional[int] = None) -> int:
        pass

    # For Sliding Window Log (Sorted Sets)
    @abstractmethod
    def add_timestamp(self, key: str, timestamp: float, expiry: Optional[int] = None):
        pass

    @abstractmethod
    def count_timestamps(self, key: str, start: float, end: float) -> int:
        pass

    @abstractmethod
    def remove_timestamps(self, key: str, max_timestamp: float):
        pass

    def execute_lua(self, script: str, keys: list, args: list) -> Any:
        """Execute a Lua script (optional support)"""
        raise NotImplementedError(
            "Lua implementation not supported by this storage backend"
        )
