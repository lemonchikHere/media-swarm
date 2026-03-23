import asyncio
import os
from src.config_loader import get_niche_config
from src.collector.rss import RSSCollector
from src.deduplicator.embeddings import SemanticDeduplicator
from src.processor.ai_rewriter import AIRewriter
from src.publisher.telegram import TelegramPublisher
from src.publisher.vk import VKPublisher


class Pipeline:
    def __init__(self, niche: str):
        self.niche = niche
        self.config = get_niche_config(niche)
        self.dedup = SemanticDeduplicator(
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6380"),
            openai_api_key=os.environ["OPENAI_API_KEY"],
        )
        self.rewriter = AIRewriter(api_key=os.environ["OPENAI_API_KEY"])
        self.rss_collector = RSSCollector()
        self.publishers = {
            "telegram": TelegramPublisher(os.environ["TG_BOT_TOKEN"]),
            "vk": VKPublisher(os.environ["VK_TOKEN"]),
        }

    async def run(self, max_posts: int = 3):
        """Run one cycle: collect → dedup → rewrite → publish."""
        collected = []
        for url in self.config["sources"].get("rss", []):
            async for post in self.rss_collector.collect(self.niche, url):
                collected.append(post)

        published = 0
        for post in collected:
            if published >= max_posts:
                break

            if await self.dedup.is_duplicate(self.niche, post.text):
                continue

            platforms = list(self.config["publish_to"].keys())
            processed = await self.rewriter.rewrite(
                post, self.config["style_prompt"], platforms
            )

            for platform, channels in self.config["publish_to"].items():
                publisher = self.publishers.get(platform)
                if not publisher:
                    continue
                for ch in channels:
                    channel_id = ch.get("channel_id") or ch.get("group_id")
                    await publisher.publish(processed, channel_id)

            await self.dedup.store(self.niche, post.id, post.text)
            published += 1

        return published
