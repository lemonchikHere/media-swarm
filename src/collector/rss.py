import asyncio
import hashlib
from typing import AsyncIterator

import feedparser

from src.models import RawPost
from src.collector.base import BaseCollector

# tg.i-c-a.su rate limit: 15 RPM — 4s between requests is safe
TG_PROXY_HOST = "tg.i-c-a.su"
TG_PROXY_DELAY = 5.0


class RSSCollector(BaseCollector):
    async def collect(self, niche: str, source: str) -> AsyncIterator[RawPost]:
        # Respect rate limit for tg.i-c-a.su
        if TG_PROXY_HOST in source:
            await asyncio.sleep(TG_PROXY_DELAY)

        try:
            feed = feedparser.parse(source)
        except Exception as e:
            print(f"[RSS] Failed to parse {source}: {e}")
            return

        if not feed.entries:
            print(f"[RSS] No entries from {source}")
            return

        for entry in feed.entries[:15]:
            text = entry.get("summary", "") or entry.get("description", "")
            title = entry.get("title", "")
            full_text = f"{title}\n\n{text}".strip()
            if len(full_text) < 50:
                continue
            post_id = hashlib.md5(
                f"{source}:{entry.get('id', title)}".encode()
            ).hexdigest()
            yield RawPost(
                id=post_id,
                source=f"rss:{source}",
                niche=niche,
                text=full_text,
                url=entry.get("link"),
            )
