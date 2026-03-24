import os
import hashlib
import asyncio
from datetime import datetime
from typing import AsyncIterator
from dotenv import load_dotenv

load_dotenv('.env')

from pyrogram import Client
from src.models import RawPost
from src.collector.base import BaseCollector


class TelegramCollector(BaseCollector):
    def __init__(self):
        self.api_id = int(os.environ['TG_API_ID'])
        self.api_hash = os.environ['TG_API_HASH']
        self.session_string = os.environ['TG_SESSION_STRING']

    async def collect(self, niche: str, source: str) -> AsyncIterator[RawPost]:
        async with Client(
            'tg_collector',
            api_id=self.api_id,
            api_hash=self.api_hash,
            session_string=self.session_string,
            in_memory=True
        ) as app:
            try:
                async for msg in app.get_chat_history(source, limit=20):
                    if not msg.text and not msg.caption:
                        continue
                    text: str = msg.text or msg.caption or ""
                    if len(text) < 50:
                        continue
                    post_id = hashlib.md5(f'tg:{source}:{msg.id}'.encode()).hexdigest()
                    yield RawPost(
                        id=post_id,
                        source=f'tg:{source}',
                        niche=niche,
                        text=text,
                        url=f'https://t.me/{source}/{msg.id}',
                        collected_at=datetime.utcnow(),
                    )
            except Exception as e:
                print(f"Error collecting from {source}: {e}")
