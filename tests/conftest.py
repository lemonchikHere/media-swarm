import pytest

@pytest.fixture(autouse=True)
def clear_dry_run(monkeypatch):
    """Ensure DRY_RUN is not set during tests unless explicitly tested."""
    monkeypatch.delenv("DRY_RUN", raising=False)
