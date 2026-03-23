from abc import ABC, abstractmethod
from typing import AsyncIterator
from src.models import RawPost


class BaseCollector(ABC):
    @abstractmethod
    async def collect(self, niche: str, source: str) -> AsyncIterator[RawPost]:
        ...
