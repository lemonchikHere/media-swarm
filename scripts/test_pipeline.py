#!/usr/bin/env python3
"""
Dry-run test script for MediaSwarm pipeline.
Usage: DRY_RUN=true python scripts/test_pipeline.py [niche]
"""
import asyncio
import os
import sys
from pathlib import Path

# Ensure DRY_RUN is set
os.environ.setdefault("DRY_RUN", "true")

# Load .env
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline import Pipeline

async def main():
    niche = sys.argv[1] if len(sys.argv) > 1 else "ai_tech"
    max_posts = int(sys.argv[2]) if len(sys.argv) > 2 else 2

    print(f"[DRY_RUN] Testing niche: {niche}, max_posts: {max_posts}")
    print("=" * 60)

    pipeline = Pipeline(niche)
    count = await pipeline.run(max_posts=max_posts)

    print("=" * 60)
    print(f"[DRY_RUN] Done. Would have published {count} post(s).")

if __name__ == "__main__":
    asyncio.run(main())
