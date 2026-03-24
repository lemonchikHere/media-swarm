import os
import hashlib
import asyncio
from datetime import datetime
from typing import AsyncIterator

from pyrogram import Client
from pyrogram.errors import FloodWait
from src.models import RawPost
from src.collector.base import BaseCollector

TG_COLLECT_TIMEOUT = int(os.getenv("TG_COLLECT_TIMEOUT", "30"))


class TelegramCollector(BaseCollector):
    def __init__(self):
        self.api_id = int(os.environ["TG_API_ID"])
        self.api_hash = os.environ["TG_API_HASH"]
        self.session_string = os.environ["TG_SESSION_STRING"]

    async def collect(self, niche: str, source: str) -> AsyncIterator[RawPost]:
        try:
            async with Client(
                "tg_collector",
                api_id=self.api_id,
                api_hash=self.api_hash,
                session_string=self.session_string,
                in_memory=True,
            ) as app:
                async for msg in app.get_chat_history(source, limit=15):
                    try:
                        text: str = msg.text or msg.caption or ""
                        if len(text) < 50:
                            continue
                        post_id = hashlib.md5(
                            f"tg:{source}:{msg.id}".encode()
                        ).hexdigest()
                        yield RawPost(
                            id=post_id,
                            source=f"tg:{source}",
                            niche=niche,
                            text=text,
                            url=f"https://t.me/{source}/{msg.id}",
                            collected_at=datetime.utcnow(),
                        )
                    except Exception:
                        continue
        except FloodWait as e:
            print(f"[TG Collector] FloodWait {e.value}s for {source}")
            await asyncio.sleep(e.value + 2)
        except asyncio.TimeoutError:
            print(f"[TG Collector] Timeout for {source} — skipping")
        except Exception as e:
            print(f"[TG Collector] Error on {source}: {e}")
