import pytest
import os
from unittest.mock import patch, MagicMock, AsyncMock
from src.publisher.telegram import TelegramPublisher
from src.models import ProcessedPost
from datetime import datetime


@pytest.fixture(autouse=True)
def tg_env(monkeypatch):
    monkeypatch.setenv("TG_API_ID", "12345")
    monkeypatch.setenv("TG_API_HASH", "testhash")
    monkeypatch.setenv("TG_SESSION_STRING", "teststring")
    monkeypatch.delenv("DRY_RUN", raising=False)


@pytest.fixture
def publisher():
    return TelegramPublisher()


@pytest.fixture
def sample_post():
    return ProcessedPost(
        raw_id="post-123",
        niche="realestate",
        title="New Building",
        body="**Test**\n\nBody content",
        platform_variants={"telegram": "**TG Test**\n\nTG body", "vk": "VK Test\n\nVK body"},
        created_at=datetime.utcnow(),
    )


@pytest.mark.asyncio
async def test_publish_calls_send_message(publisher, sample_post):
    mock_app = AsyncMock()
    mock_app.__aenter__ = AsyncMock(return_value=mock_app)
    mock_app.__aexit__ = AsyncMock(return_value=None)
    mock_app.send_message = AsyncMock()

    with patch("src.publisher.telegram.Client", return_value=mock_app):
        result = await publisher.publish(sample_post, "@test_channel")

    assert result is True
    mock_app.send_message.assert_called_once_with("@test_channel", "**TG Test**\n\nTG body")


@pytest.mark.asyncio
async def test_publish_uses_fallback_body(publisher):
    post = ProcessedPost(
        raw_id="post-456",
        niche="ai_tech",
        title="Test",
        body="Fallback body content here",
        platform_variants={},
        created_at=datetime.utcnow(),
    )
    mock_app = AsyncMock()
    mock_app.__aenter__ = AsyncMock(return_value=mock_app)
    mock_app.__aexit__ = AsyncMock(return_value=None)
    mock_app.send_message = AsyncMock()

    with patch("src.publisher.telegram.Client", return_value=mock_app):
        result = await publisher.publish(post, "@test_channel")

    assert result is True
    mock_app.send_message.assert_called_once_with("@test_channel", "Fallback body content here")


@pytest.mark.asyncio
async def test_publish_truncates_long_text(publisher, sample_post):
    sample_post.platform_variants["telegram"] = "A" * 5000
    mock_app = AsyncMock()
    mock_app.__aenter__ = AsyncMock(return_value=mock_app)
    mock_app.__aexit__ = AsyncMock(return_value=None)
    mock_app.send_message = AsyncMock()

    with patch("src.publisher.telegram.Client", return_value=mock_app):
        await publisher.publish(sample_post, "@test_channel")

    sent_text = mock_app.send_message.call_args[0][1]
    assert len(sent_text) <= 4096


@pytest.mark.asyncio
async def test_publish_returns_false_on_error(publisher, sample_post):
    mock_app = AsyncMock()
    mock_app.__aenter__ = AsyncMock(return_value=mock_app)
    mock_app.__aexit__ = AsyncMock(return_value=None)
    mock_app.send_message = AsyncMock(side_effect=Exception("Connection error"))

    with patch("src.publisher.telegram.Client", return_value=mock_app):
        result = await publisher.publish(sample_post, "@test_channel")

    assert result is False


@pytest.mark.asyncio
async def test_dry_run_skips_publish(publisher, sample_post, monkeypatch):
    monkeypatch.setenv("DRY_RUN", "true")
    with patch("src.publisher.telegram.Client") as mock_client:
        result = await publisher.publish(sample_post, "@test_channel")
    assert result is True
    mock_client.assert_not_called()
