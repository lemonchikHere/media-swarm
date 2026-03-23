import hashlib
import json
import redis
import numpy as np
from openai import AsyncOpenAI

SIMILARITY_THRESHOLD = 0.85
EMBED_DIM = 1536
TTL_DAYS = 7


class SemanticDeduplicator:
    def __init__(self, redis_url: str, openai_api_key: str):
        self.redis = redis.from_url(redis_url)
        self.client = AsyncOpenAI(api_key=openai_api_key)

    async def get_embedding(self, text: str) -> list[float]:
        resp = await self.client.embeddings.create(
            input=text[:2000],
            model="text-embedding-3-small"
        )
        return resp.data[0].embedding

    def cosine_sim(self, a: list, b: list) -> float:
        a, b = np.array(a), np.array(b)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    async def is_duplicate(self, niche: str, text: str) -> bool:
        """Returns True if semantically similar post already exists."""
        embedding = await self.get_embedding(text)
        key_pattern = f"embed:{niche}:*"
        for key in self.redis.scan_iter(key_pattern):
            stored = json.loads(self.redis.get(key))
            if self.cosine_sim(embedding, stored) > SIMILARITY_THRESHOLD:
                return True
        return False

    async def store(self, niche: str, post_id: str, text: str):
        embedding = await self.get_embedding(text)
        key = f"embed:{niche}:{post_id}"
        self.redis.setex(key, TTL_DAYS * 86400, json.dumps(embedding))
