import asyncio
import os
from src.config_loader import get_niche_config, get_persona
from src.collector.rss import RSSCollector
from src.collector.telegram import TelegramCollector
from src.deduplicator.embeddings import SemanticDeduplicator
from src.processor.ai_rewriter import AIRewriter
from src.publisher.telegram import TelegramPublisher
from src.publisher.vk import VKPublisher
from src.state import is_seen, mark_seen


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
        self.tg_collector = TelegramCollector()
        self.publishers = {"telegram": TelegramPublisher(os.environ["TG_BOT_TOKEN"])}
        if os.getenv("VK_TOKEN"):
            self.publishers["vk"] = VKPublisher(os.environ["VK_TOKEN"])

    async def run(self, max_posts: int = 3):
        """Run one cycle: collect → dedup → rewrite → publish."""
        collected = []

        # Collect from RSS sources
        for url in self.config["sources"].get("rss", []):
            async for post in self.rss_collector.collect(self.niche, url):
                collected.append(post)

        # Collect from Telegram sources
        for channel in self.config["sources"].get("telegram", []):
            try:
                async for post in self.tg_collector.collect(self.niche, channel):
                    collected.append(post)
            except Exception as e:
                print(f"Error collecting from Telegram channel {channel}: {e}")

        published = 0
        for post in collected:
            if published >= max_posts:
                break

            # Fast SQLite check before expensive embedding dedup
            if is_seen(post.id):
                continue

            if await self.dedup.is_duplicate(self.niche, post.text):
                mark_seen(post.id, self.niche)
                continue

            platforms = list(self.config["publish_to"].keys())
            persona = self.config.get("_persona")
            processed = await self.rewriter.rewrite(
                post, self.config["style_prompt"], platforms, persona
            )

            for platform, channels in self.config["publish_to"].items():
                publisher = self.publishers.get(platform)
                if not publisher:
                    continue
                for ch in channels:
                    channel_id = ch.get("channel_id") or ch.get("group_id")
                    await publisher.publish(processed, channel_id)

            await self.dedup.store(self.niche, post.id, post.text)
            mark_seen(post.id, self.niche)
            published += 1

        return published
