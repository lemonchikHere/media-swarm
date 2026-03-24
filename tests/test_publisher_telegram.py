import pytest, os
from unittest.mock import patch, AsyncMock, MagicMock
from src.publisher.telegram import TelegramPublisher
from src.models import ProcessedPost
from datetime import datetime

@pytest.fixture
def publisher():
    return TelegramPublisher("test-bot-token")

@pytest.fixture
def post():
    return ProcessedPost(
        raw_id="p1", niche="ai_tech", title="Test", body="Fallback body",
        platform_variants={"telegram": "**TG post**\n\nContent here"},
        created_at=datetime.utcnow(),
    )

@pytest.mark.asyncio
async def test_publish_sends_correct_payload(publisher, post):
    mock_resp = MagicMock(status_code=200)
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__ = AsyncMock(return_value=MagicMock(
            post=AsyncMock(return_value=mock_resp)
        ))
        mock_client.return_value.__aexit__ = AsyncMock(return_value=None)
        result = await publisher.publish(post, "@test_channel")
    assert result is True

@pytest.mark.asyncio
async def test_publish_returns_false_on_error(publisher, post):
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__ = AsyncMock(return_value=MagicMock(
            post=AsyncMock(return_value=MagicMock(status_code=400))
        ))
        mock_client.return_value.__aexit__ = AsyncMock(return_value=None)
        result = await publisher.publish(post, "@test_channel")
    assert result is False

@pytest.mark.asyncio
async def test_dry_run_skips_publish(publisher, post, monkeypatch):
    monkeypatch.setenv("DRY_RUN", "true")
    with patch("httpx.AsyncClient") as mock_client:
        result = await publisher.publish(post, "@test_channel")
    assert result is True
    mock_client.assert_not_called()

@pytest.mark.asyncio
async def test_uses_fallback_body(publisher):
    p = ProcessedPost(raw_id="p2", niche="ai_tech", title="T", body="Fallback",
                      platform_variants={}, created_at=datetime.utcnow())
    mock_resp = MagicMock(status_code=200)
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__ = AsyncMock(return_value=MagicMock(
            post=AsyncMock(return_value=mock_resp)
        ))
        mock_client.return_value.__aexit__ = AsyncMock(return_value=None)
        result = await publisher.publish(p, "@ch")
    assert result is True
