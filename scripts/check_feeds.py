#!/usr/bin/env python3
"""Check RSS feeds and validate they work with feedparser."""

import feedparser
import json
from datetime import datetime

# All feeds to check
NICHE_1_REA = [
    "https://realty.rbc.ru/rss/",
    "https://www.cian.ru/rss/",
    "https://www.bn.ru/rss/",
    "https://www.irn.ru/rss/",
    "https://novostroev.ru/rss/",
    "https://metrium.ru/news/rss/",
    "https://realsearch.ru/rss/",
]

NICHE_2_AI_RU = [
    "https://habr.com/ru/rss/hubs/artificial_intelligence/articles/",
    "https://3dnews.ru/rss/all.xml",
    "https://cnews.ru/inc/rss/news.xml",
]

NICHE_2_AI_WEST = [
    "https://feeds.feedburner.com/venturebeat/SZYF",
    "https://techcrunch.com/feed/",
    "https://www.technologyreview.com/feed/",
    "https://www.theverge.com/rss/index.xml",
    "https://feeds.arstechnica.com/arstechnica/index",
    "https://openai.com/news/rss.xml",
    "https://www.artificialintelligence-news.com/feed/",
    "https://syncedreview.com/feed/",
]


def check_feed(url: str) -> dict:
    """Check if a feed URL is valid and returns entry count."""
    try:
        parsed = feedparser.parse(url)
        if parsed.entries:
            first_title = parsed.entries[0].get("title", "No title")[:60]
            return {
                "url": url,
                "status": "OK",
                "entries": len(parsed.entries),
                "title": first_title,
                "feed_title": parsed.feed.get("title", "Unknown"),
            }
        else:
            return {
                "url": url,
                "status": "FAIL",
                "entries": 0,
                "title": "No entries",
                "feed_title": "Unknown",
            }
    except Exception as e:
        return {
            "url": url,
            "status": "FAIL",
            "entries": 0,
            "title": f"Error: {str(e)[:40]}",
            "feed_title": "Unknown",
        }


def print_result(r: dict):
    """Print a single feed result."""
    status_icon = "✓" if r["status"] == "OK" else "✗"
    print(f"{status_icon} {r['url']}")
    print(f"   Status: {r['status']} | Entries: {r['entries']} | Feed: {r['feed_title']}")
    if r["status"] == "OK":
        print(f"   First: {r['title']}")
    print()


def main():
    print("=" * 60)
    print("RSS FEED VALIDATION REPORT")
    print(f"Time: {datetime.now().isoformat()}")
    print("=" * 60)

    all_results = {}

    # Niche 1: Real Estate
    print("\n" + "=" * 60)
    print("NICHE 1: REAL ESTATE (Russian)")
    print("=" * 60)
    realestate_results = []
    for url in NICHE_1_REA:
        r = check_feed(url)
        print_result(r)
        realestate_results.append(r)
    all_results["realestate"] = realestate_results

    # Niche 2: AI Tech - Russian
    print("\n" + "=" * 60)
    print("NICHE 2: AI & TECH - Russian")
    print("=" * 60)
    ai_ru_results = []
    for url in NICHE_2_AI_RU:
        r = check_feed(url)
        print_result(r)
        ai_ru_results.append(r)
    all_results["ai_tech_ru"] = ai_ru_results

    # Niche 2: AI Tech - Western
    print("\n" + "=" * 60)
    print("NICHE 2: AI & TECH - Western")
    print("=" * 60)
    ai_west_results = []
    for url in NICHE_2_AI_WEST:
        r = check_feed(url)
        print_result(r)
        ai_west_results.append(r)
    all_results["ai_tech_west"] = ai_west_results

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for niche, results in all_results.items():
        ok_count = sum(1 for r in results if r["status"] == "OK")
        print(f"{niche}: {ok_count}/{len(results)} feeds working")

    # Save to JSON
    output = {
        "generated": datetime.now().isoformat(),
        "results": all_results,
        "working": {
            "realestate": [r["url"] for r in realestate_results if r["status"] == "OK"],
            "ai_tech_ru": [r["url"] for r in ai_ru_results if r["status"] == "OK"],
            "ai_tech_west": [r["url"] for r in ai_west_results if r["status"] == "OK"],
        }
    }

    with open("config/working_feeds.json", "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nResults saved to config/working_feeds.json")


if __name__ == "__main__":
    main()
