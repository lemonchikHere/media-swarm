import os
import httpx
from src.models import ProcessedPost
from src.publisher.base import BasePublisher


class TelegramPublisher(BasePublisher):
    """Publishes via Telegram Bot API."""

    def __init__(self, bot_token: str):
        self.token = bot_token
        self.base_url = f"https://api.telegram.org/bot{bot_token}"

    async def publish(self, post: ProcessedPost, channel_id: str) -> bool:
        text = post.platform_variants.get("telegram", post.body)
        if os.getenv("DRY_RUN", "").lower() in ("1", "true", "yes"):
            print(f"[DRY_RUN][Telegram] → {channel_id}:\n{text[:200]}...\n")
            return True
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/sendMessage",
                json={
                    "chat_id": channel_id,
                    "text": text[:4096],
                    "parse_mode": "Markdown",
                },
                timeout=30,
            )
        return resp.status_code == 200
