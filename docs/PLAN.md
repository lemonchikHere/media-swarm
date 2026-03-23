# MediaSwarm — Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement task-by-task.
> After EVERY task: commit, push, open PR if feature branch.

**Goal:** Multi-niche automated content aggregation → AI rewrite → multi-platform publishing engine.
**Architecture:** Modular Python pipeline: Collector → Deduplicator → Processor → Scheduler → Publisher. Each module is independent and config-driven.
**Tech Stack:** Python 3.11, Pyrogram, feedparser, OpenAI API (GPT-4o-mini + text-embedding-3-small), Redis (queue + vector cache), SQLite (state), vk_api, docker-compose.

---

## File Structure

```
media-swarm/
├── docker-compose.yml
├── .env.example
├── requirements.txt
├── README.md
├── docs/
│   └── PLAN.md
├── config/
│   ├── niches.yaml          # Niche definitions (realestate, ai_tech)
│   └── publishers.yaml      # Platform credentials mapping
├── src/
│   ├── __init__.py
│   ├── models.py            # Pydantic models: RawPost, ProcessedPost, PublishJob
│   ├── config_loader.py     # Load niches.yaml + publishers.yaml
│   ├── collector/
│   │   ├── __init__.py
│   │   ├── base.py          # BaseCollector ABC
│   │   ├── telegram.py      # TelegramCollector (Pyrogram userbot)
│   │   └── rss.py           # RSSCollector (feedparser)
│   ├── deduplicator/
│   │   ├── __init__.py
│   │   └── embeddings.py    # Semantic dedup via OpenAI embeddings + Redis
│   ├── processor/
│   │   ├── __init__.py
│   │   └── ai_rewriter.py   # GPT-4o-mini rewrite in niche style
│   ├── publisher/
│   │   ├── __init__.py
│   │   ├── base.py          # BasePublisher ABC
│   │   ├── telegram.py      # TelegramPublisher (Bot API)
│   │   └── vk.py            # VKPublisher (vk_api)
│   ├── scheduler/
│   │   ├── __init__.py
│   │   └── runner.py        # APScheduler cron loop
│   └── pipeline.py          # Orchestrates full pipeline per niche
├── tests/
│   ├── test_models.py
│   ├── test_config_loader.py
│   ├── test_deduplicator.py
│   ├── test_processor.py
│   └── test_pipeline.py
└── scripts/
    └── run_once.py          # Manual trigger for testing
```

---

## Task 1: Project scaffold + deps

**Branch:** `feat/scaffold`
**Files:**
- Create: `requirements.txt`
- Create: `docker-compose.yml`
- Create: `.env.example`
- Create: `src/__init__.py`, `src/models.py`

- [ ] Create `requirements.txt`:
```
pyrogram==2.0.106
tgcrypto
feedparser==6.0.11
openai>=1.30.0
redis>=5.0.0
vk-api==11.9.9
apscheduler==3.10.4
pydantic>=2.0.0
pydantic-settings>=2.0.0
python-dotenv==1.0.0
PyYAML>=6.0
pytest>=8.0.0
pytest-asyncio>=0.23.0
httpx>=0.27.0
```

- [ ] Create `docker-compose.yml`:
```yaml
version: '3.9'
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6380:6379"
    volumes:
      - redis_data:/data

  app:
    build: .
    env_file: .env
    depends_on:
      - redis
    volumes:
      - ./:/app
    command: python -m src.scheduler.runner

volumes:
  redis_data:
```

- [ ] Create `.env.example`:
```
OPENAI_API_KEY=sk-...
REDIS_URL=redis://localhost:6380

# Telegram Userbot (collector)
TG_API_ID=
TG_API_HASH=
TG_SESSION_STRING=

# Telegram Bot (publisher)
TG_BOT_TOKEN=

# VK
VK_TOKEN=
```

- [ ] Create `src/models.py` with Pydantic models:
```python
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class RawPost(BaseModel):
    id: str
    source: str        # e.g. "tg:realestate_channel"
    niche: str         # e.g. "realestate"
    text: str
    url: Optional[str] = None
    collected_at: datetime = datetime.utcnow()

class ProcessedPost(BaseModel):
    raw_id: str
    niche: str
    title: str
    body: str
    platform_variants: dict[str, str] = {}  # platform -> text
    created_at: datetime = datetime.utcnow()

class PublishJob(BaseModel):
    post_id: str
    niche: str
    platform: str
    channel_id: str
    status: str = "pending"  # pending | sent | failed
```

- [ ] Write tests in `tests/test_models.py`
- [ ] Run: `pytest tests/test_models.py -v` → should PASS
- [ ] `git commit -m "feat: project scaffold and models"`
- [ ] Push + open PR to main

---

## Task 2: Config loader + niches.yaml

**Branch:** `feat/config`
**Files:**
- Create: `config/niches.yaml`
- Create: `config/publishers.yaml`
- Create: `src/config_loader.py`
- Test: `tests/test_config_loader.py`

- [ ] Create `config/niches.yaml`:
```yaml
niches:
  realestate:
    name: "Недвижимость"
    style_prompt: |
      Ты редактор телеграм-канала о недвижимости. Перепиши пост в нашем стиле:
      - Короткий цепляющий заголовок с эмодзи
      - 2-3 абзаца, факты и цифры выделяй жирным
      - В конце призыв к действию или вопрос аудитории
      - Тон: экспертный но дружелюбный
    sources:
      telegram:
        - realty_channel_1
        - realty_rbc
      rss:
        - https://realty.rbc.ru/rss/
        - https://www.cian.ru/rss/news/
    publish_to:
      telegram:
        - channel_id: "@my_realestate"
      vk:
        - group_id: "123456789"
    post_interval_minutes: 120
    max_posts_per_day: 8

  ai_tech:
    name: "AI и технологии"
    style_prompt: |
      Ты редактор телеграм-канала об ИИ и технологиях. Перепиши пост в нашем стиле:
      - Заголовок с 🤖 или ⚡ или 🔥
      - Объяснение простым языком (для не-технарей)
      - Почему это важно прямо сейчас
      - Мнение: что это значит для будущего
      - Тон: энтузиаст, немного футурист
    sources:
      telegram:
        - ai_news_ru
        - openai_news
      rss:
        - https://habr.com/ru/rss/hubs/artificial_intelligence/articles/
        - https://techcrunch.com/feed/
    publish_to:
      telegram:
        - channel_id: "@my_aitech"
      vk:
        - group_id: "987654321"
    post_interval_minutes: 90
    max_posts_per_day: 10
```

- [ ] Create `src/config_loader.py`:
```python
import yaml
from pathlib import Path
from dataclasses import dataclass

CONFIG_DIR = Path(__file__).parent.parent / "config"

def load_niches() -> dict:
    with open(CONFIG_DIR / "niches.yaml") as f:
        return yaml.safe_load(f)["niches"]

def get_niche_config(niche: str) -> dict:
    niches = load_niches()
    if niche not in niches:
        raise ValueError(f"Unknown niche: {niche}")
    return niches[niche]
```

- [ ] Tests: `tests/test_config_loader.py` — assert niches load, get_niche_config works, unknown niche raises
- [ ] `pytest tests/test_config_loader.py -v` → PASS
- [ ] `git commit -m "feat: config loader and niches yaml"`
- [ ] Push + PR

---

## Task 3: RSS Collector

**Branch:** `feat/rss-collector`
**Files:**
- Create: `src/collector/base.py`
- Create: `src/collector/rss.py`
- Test: `tests/test_collector_rss.py`

- [ ] `src/collector/base.py`:
```python
from abc import ABC, abstractmethod
from typing import AsyncIterator
from src.models import RawPost

class BaseCollector(ABC):
    @abstractmethod
    async def collect(self, niche: str, source: str) -> AsyncIterator[RawPost]:
        ...
```

- [ ] `src/collector/rss.py`:
```python
import feedparser
import hashlib
from datetime import datetime
from src.models import RawPost
from src.collector.base import BaseCollector

class RSSCollector(BaseCollector):
    async def collect(self, niche: str, source_url: str):
        feed = feedparser.parse(source_url)
        for entry in feed.entries[:20]:
            text = entry.get("summary", "") or entry.get("description", "")
            title = entry.get("title", "")
            full_text = f"{title}\n\n{text}".strip()
            if not full_text:
                continue
            post_id = hashlib.md5(f"{source_url}:{entry.get('id', title)}".encode()).hexdigest()
            yield RawPost(
                id=post_id,
                source=f"rss:{source_url}",
                niche=niche,
                text=full_text,
                url=entry.get("link"),
            )
```

- [ ] Tests: mock feedparser, assert RawPost fields populated correctly
- [ ] `pytest tests/test_collector_rss.py -v` → PASS
- [ ] Commit + PR

---

## Task 4: Deduplicator

**Branch:** `feat/deduplicator`
**Files:**
- Create: `src/deduplicator/embeddings.py`
- Test: `tests/test_deduplicator.py`

- [ ] `src/deduplicator/embeddings.py`:
```python
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
```

- [ ] Tests: mock OpenAI, mock Redis — test duplicate detection works
- [ ] Commit + PR

---

## Task 5: AI Processor (rewriter)

**Branch:** `feat/processor`
**Files:**
- Create: `src/processor/ai_rewriter.py`
- Test: `tests/test_processor.py`

- [ ] `src/processor/ai_rewriter.py`:
```python
from openai import AsyncOpenAI
from src.models import RawPost, ProcessedPost
import re

class AIRewriter:
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)

    async def rewrite(self, post: RawPost, style_prompt: str, platforms: list[str]) -> ProcessedPost:
        variants = {}
        for platform in platforms:
            platform_hint = self._platform_hint(platform)
            messages = [
                {"role": "system", "content": style_prompt + f"\n\nПлатформа: {platform_hint}"},
                {"role": "user", "content": f"Исходный материал:\n\n{post.text[:3000]}"}
            ]
            resp = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=800,
                temperature=0.7,
            )
            variants[platform] = resp.choices[0].message.content.strip()

        # Extract title from telegram variant
        first_line = variants.get("telegram", "").split("\n")[0]
        title = re.sub(r"[*_#]", "", first_line).strip()[:100]

        return ProcessedPost(
            raw_id=post.id,
            niche=post.niche,
            title=title,
            body=variants.get("telegram", ""),
            platform_variants=variants,
        )

    def _platform_hint(self, platform: str) -> str:
        hints = {
            "telegram": "Telegram канал. Поддерживает markdown. До 4096 символов.",
            "vk": "ВКонтакте пост. Без markdown. До 15000 символов. Хэштеги в конце.",
        }
        return hints.get(platform, platform)
```

- [ ] Tests: mock OpenAI, assert ProcessedPost populated
- [ ] Commit + PR

---

## Task 6: Telegram Publisher

**Branch:** `feat/publisher-telegram`
**Files:**
- Create: `src/publisher/base.py`
- Create: `src/publisher/telegram.py`
- Test: `tests/test_publisher_telegram.py`

- [ ] `src/publisher/base.py`:
```python
from abc import ABC, abstractmethod
from src.models import ProcessedPost

class BasePublisher(ABC):
    @abstractmethod
    async def publish(self, post: ProcessedPost, channel_id: str) -> bool:
        ...
```

- [ ] `src/publisher/telegram.py`:
```python
import httpx
from src.models import ProcessedPost
from src.publisher.base import BasePublisher

class TelegramPublisher(BasePublisher):
    def __init__(self, bot_token: str):
        self.token = bot_token
        self.base_url = f"https://api.telegram.org/bot{bot_token}"

    async def publish(self, post: ProcessedPost, channel_id: str) -> bool:
        text = post.platform_variants.get("telegram", post.body)
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
```

- [ ] Tests: mock httpx, assert publish called with correct payload
- [ ] Commit + PR

---

## Task 7: VK Publisher

**Branch:** `feat/publisher-vk`
**Files:**
- Create: `src/publisher/vk.py`
- Test: `tests/test_publisher_vk.py`

- [ ] `src/publisher/vk.py`:
```python
import vk_api
from src.models import ProcessedPost
from src.publisher.base import BasePublisher

class VKPublisher(BasePublisher):
    def __init__(self, token: str):
        self.vk = vk_api.VkApi(token=token)
        self.api = self.vk.get_api()

    async def publish(self, post: ProcessedPost, group_id: str) -> bool:
        text = post.platform_variants.get("vk", post.body)
        try:
            self.api.wall.post(
                owner_id=f"-{group_id}",
                message=text[:15000],
                from_group=1,
            )
            return True
        except Exception as e:
            print(f"VK publish error: {e}")
            return False
```

- [ ] Tests + Commit + PR

---

## Task 8: Full Pipeline

**Branch:** `feat/pipeline`
**Files:**
- Create: `src/pipeline.py`
- Test: `tests/test_pipeline.py`

- [ ] `src/pipeline.py`:
```python
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
            processed = await self.rewriter.rewrite(post, self.config["style_prompt"], platforms)

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
```

- [ ] Tests: full integration test with mocks
- [ ] Commit + PR

---

## Task 9: Scheduler

**Branch:** `feat/scheduler`
**Files:**
- Create: `src/scheduler/runner.py`
- Create: `scripts/run_once.py`

- [ ] `src/scheduler/runner.py` with APScheduler:
```python
import asyncio
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from src.config_loader import load_niches
from src.pipeline import Pipeline

def make_job(niche: str):
    async def job():
        print(f"[{niche}] Starting pipeline run...")
        pipeline = Pipeline(niche)
        count = await pipeline.run()
        print(f"[{niche}] Published {count} posts")
    return job

async def main():
    scheduler = AsyncIOScheduler()
    niches = load_niches()
    for niche_id, cfg in niches.items():
        interval = cfg.get("post_interval_minutes", 120)
        scheduler.add_job(
            make_job(niche_id),
            "interval",
            minutes=interval,
            id=niche_id,
        )
        print(f"Scheduled {niche_id} every {interval} minutes")

    scheduler.start()
    print("Scheduler started. Press Ctrl+C to stop.")
    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] `scripts/run_once.py` for manual test run
- [ ] Commit + PR

---

## Task 10: Dockerfile + README

**Branch:** `feat/docker`
**Files:**
- Create: `Dockerfile`
- Update: `README.md`

- [ ] `Dockerfile`:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "-m", "src.scheduler.runner"]
```

- [ ] README: quick start, architecture diagram (ASCII), env vars table
- [ ] Final: `docker-compose up -d` → verify runs
- [ ] Commit + PR → merge all to main

---

## Done when:
- [ ] All 10 PRs merged
- [ ] `pytest` passes
- [ ] `docker-compose up` starts scheduler
- [ ] Niches: realestate + ai_tech configured
- [ ] RSS sources collecting and deduplicating
