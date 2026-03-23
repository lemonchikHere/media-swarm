from abc import ABC, abstractmethod
from src.models import ProcessedPost


class BasePublisher(ABC):
    @abstractmethod
    async def publish(self, post: ProcessedPost, channel_id: str) -> bool:
        ...
