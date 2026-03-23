import feedparser
import hashlib
from typing import AsyncIterator
from src.models import RawPost
from src.collector.base import BaseCollector


class RSSCollector(BaseCollector):
    async def collect(self, niche: str, source: str) -> AsyncIterator[RawPost]:
        feed = feedparser.parse(source)
        for entry in feed.entries[:20]:
            text = entry.get("summary", "") or entry.get("description", "")
            title = entry.get("title", "")
            full_text = f"{title}\n\n{text}".strip()
            if not full_text:
                continue
            post_id = hashlib.md5(f"{source}:{entry.get('id', title)}".encode()).hexdigest()
            yield RawPost(
                id=post_id,
                source=f"rss:{source}",
                niche=niche,
                text=full_text,
                url=entry.get("link"),
            )
