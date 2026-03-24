import os
from pyrogram import Client
from pyrogram.errors import FloodWait
from src.models import ProcessedPost
from src.publisher.base import BasePublisher
import asyncio

class TelegramPublisher(BasePublisher):
    """Publishes via Pyrogram userbot — no bot token needed."""

    def __init__(self):
        self.api_id = int(os.environ["TG_API_ID"])
        self.api_hash = os.environ["TG_API_HASH"]
        self.session_string = os.environ["TG_SESSION_STRING"]

    async def publish(self, post: ProcessedPost, channel_id: str) -> bool:
        text = post.platform_variants.get("telegram", post.body)
        if os.getenv("DRY_RUN", "").lower() in ("1", "true", "yes"):
            print(f"[DRY_RUN][Telegram] → {channel_id}:\n{text[:200]}...\n")
            return True
        try:
            async with Client(
                "publisher",
                api_id=self.api_id,
                api_hash=self.api_hash,
                session_string=self.session_string,
                in_memory=True,
            ) as app:
                await app.send_message(channel_id, text[:4096])
            return True
        except FloodWait as e:
            print(f"[Telegram] FloodWait {e.value}s for {channel_id}")
            await asyncio.sleep(e.value + 2)
            return False
        except Exception as e:
            print(f"[Telegram] Error posting to {channel_id}: {e}")
            return False
