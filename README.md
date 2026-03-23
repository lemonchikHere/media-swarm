# MediaSwarm

Multi-niche automated content aggregation → AI rewrite → multi-platform publishing engine.

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│   Sources   │────▶│  Collector   │────▶│ Dedup       │────▶│ AI Rewriter  │────▶│ Publishers   │
│ RSS / Telegram│     │ (RSS / TG)  │     │ (embeddings)│     │ (GPT-4o-mini)│     │ TG / VK     │
└─────────────┘     └──────────────┘     └─────────────┘     └─────────────┘     └──────────────┘
       │                                                                    │              │
       ▼                                                                    ▼              ▼
┌─────────────┐     ┌──────────────────────────────────────────────────────────────────────────────┐
│ niches.yaml │     │                              Scheduler (APScheduler)                             │
│ (config)   │     │  Loads niches → schedules per interval → runs pipeline forever                   │
└─────────────┘     └──────────────────────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Clone & install deps

```bash
git clone https://github.com/lemonchikHere/media-swarm.git
cd media-swarm
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure credentials

```bash
cp .env.example .env
# Edit .env with your API keys and tokens
```

### 3. Run with Docker Compose

```bash
docker-compose up -d
```

The app container starts the scheduler which runs each niche on its configured interval (e.g. every 90 minutes for `ai_tech`, every 120 minutes for `realestate`).

### 4. Manual one-shot run (testing)

```bash
source venv/bin/activate
python scripts/run_once.py              # run all niches once
python scripts/run_once.py realestate   # run only realestate niche
```

### 5. Run tests

```bash
source venv/bin/activate
python -m pytest tests/ -v
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | — | OpenAI API key for GPT-4o-mini + embeddings |
| `REDIS_URL` | Yes | `redis://localhost:6380` | Redis connection URL (dedup cache) |
| `TG_API_ID` | For TG collection | — | Telegram API ID (userbot collector) |
| `TG_API_HASH` | For TG collection | — | Telegram API hash |
| `TG_SESSION_STRING` | For TG collection | — | Pyrogram session string |
| `TG_BOT_TOKEN` | For TG publishing | — | Telegram bot token |
| `VK_TOKEN` | For VK publishing | — | VK access token |

## Niches

Configured in `config/niches.yaml`:

| Niche | Interval | Sources | Publishes to |
|-------|----------|---------|-------------|
| `realestate` | 120 min | RBC RSS, Cian RSS | Telegram `@my_realestate`, VK group |
| `ai_tech` | 90 min | Habr AI, TechCrunch RSS | Telegram `@my_aitech`, VK group |

Add more niches in `niches.yaml` following the same structure.

## Pipeline Flow

1. **Collect** — RSS feeds parsed with `feedparser` (Telegram source stub for future)
2. **Deduplicate** — Semantic dedup via OpenAI `text-embedding-3-small` + Redis cache
3. **Rewrite** — GPT-4o-mini rewrites content in niche style, generates platform-specific variants (Telegram markdown vs VK plain text)
4. **Publish** — Telegram bot API + VK wall API post to configured channels

## File Structure

```
media-swarm/
├── Dockerfile              # Container image
├── docker-compose.yml     # Redis + app
├── requirements.txt       # Python deps
├── .env.example           # Env var template
├── config/
│   ├── niches.yaml        # Niche definitions
│   └── publishers.yaml    # Publisher credentials
├── src/
│   ├── config_loader.py   # Load config
│   ├── models.py          # Pydantic models
│   ├── pipeline.py        # Full pipeline orchestrator
│   ├── collector/          # RSS + Telegram collectors
│   ├── deduplicator/      # Semantic dedup
│   ├── processor/          # AI rewriter
│   ├── publisher/          # TG + VK publishers
│   └── scheduler/
│       └── runner.py       # APScheduler cron loop
├── scripts/
│   └── run_once.py         # Manual one-shot trigger
└── tests/                 # Unit tests
```
