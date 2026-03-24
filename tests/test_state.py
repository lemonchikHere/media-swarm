import pytest
import os
import tempfile
from pathlib import Path


@pytest.fixture(autouse=True)
def tmp_db(tmp_path, monkeypatch):
    db = tmp_path / "test_state.db"
    monkeypatch.setenv("STATE_DB", str(db))
    # Force re-import with new path
    import importlib
    import src.state as state_mod
    state_mod.DB_PATH = db
    yield db


def test_is_seen_returns_false_for_new_post():
    from src.state import is_seen
    assert is_seen("new-post-id") is False


def test_mark_seen_and_is_seen():
    from src.state import mark_seen, is_seen
    mark_seen("post-123", "ai_tech")
    assert is_seen("post-123") is True


def test_mark_seen_idempotent():
    from src.state import mark_seen, is_seen
    mark_seen("post-dup", "realestate")
    mark_seen("post-dup", "realestate")  # should not raise
    assert is_seen("post-dup") is True


def test_different_posts_independent():
    from src.state import mark_seen, is_seen
    mark_seen("post-a", "ai_tech")
    assert is_seen("post-a") is True
    assert is_seen("post-b") is False
