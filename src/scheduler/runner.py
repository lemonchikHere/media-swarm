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
