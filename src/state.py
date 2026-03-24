"""SQLite-based state tracking to avoid re-processing seen posts."""
import sqlite3
import os
from pathlib import Path

DB_PATH = Path(os.getenv("STATE_DB", "data/state.db"))


def init_db():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS seen_posts "
        "(id TEXT PRIMARY KEY, niche TEXT, seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
    )
    conn.commit()
    conn.close()


def is_seen(post_id: str) -> bool:
    if not DB_PATH.exists():
        return False
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute("SELECT 1 FROM seen_posts WHERE id=?", (post_id,))
    result = cur.fetchone() is not None
    conn.close()
    return result


def mark_seen(post_id: str, niche: str):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT OR IGNORE INTO seen_posts VALUES (?,?,CURRENT_TIMESTAMP)",
        (post_id, niche),
    )
    conn.commit()
    conn.close()
