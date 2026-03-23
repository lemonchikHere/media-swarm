#!/usr/bin/env python3
"""Manual one-shot pipeline trigger for testing or ad-hoc runs."""
import asyncio
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config_loader import load_niches
from src.pipeline import Pipeline


async def run_niche(niche_id: str):
    print(f"\n=== Running niche: {niche_id} ===")
    pipeline = Pipeline(niche_id)
    count = await pipeline.run()
    print(f"=== {niche_id}: published {count} posts ===")
    return count


async def main():
    niches = load_niches()

    if len(sys.argv) > 1:
        niche_id = sys.argv[1]
        if niche_id not in niches:
            print(f"Unknown niche: {niche_id}")
            print(f"Available: {list(niches.keys())}")
            sys.exit(1)
        await run_niche(niche_id)
    else:
        total = 0
        for niche_id in niches:
            count = await run_niche(niche_id)
            total += count
        print(f"\n=== TOTAL: published {total} posts across {len(niches)} niches ===")


if __name__ == "__main__":
    asyncio.run(main())
