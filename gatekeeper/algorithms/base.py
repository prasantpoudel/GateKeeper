from abc import ABC, abstractmethod
from typing import Optional
from ..storage import Storage, InMemoryStorage


class RateLimiter(ABC):
    def __init__(self, storage: Optional[Storage] = None):
        self.storage = storage or InMemoryStorage()

    @abstractmethod
    def allow(self, key: str) -> bool:
        """
        Check if the request is allowed for the given key.
        Returns True if allowed, False otherwise.
        """
        pass
