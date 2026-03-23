import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from src.publisher.telegram import TelegramPublisher
from src.models import ProcessedPost
from datetime import datetime


@pytest.fixture
def publisher():
    return TelegramPublisher(bot_token="test-bot-token")


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
async def test_publish_calls_telegram_api(publisher, sample_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        result = await publisher.publish(sample_post, "@my_channel")
        
        assert result is True
        mock_client.post.assert_called_once()


@pytest.mark.asyncio
async def test_publish_sends_correct_payload(publisher, sample_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        await publisher.publish(sample_post, "@my_realestate")
        
        call_kwargs = mock_client.post.call_args[1]["json"]
        assert call_kwargs["chat_id"] == "@my_realestate"
        assert call_kwargs["text"] == "**TG Test**\n\nTG body"
        assert call_kwargs["parse_mode"] == "Markdown"


@pytest.mark.asyncio
async def test_publish_returns_false_on_error(publisher, sample_post):
    mock_response = MagicMock()
    mock_response.status_code = 500
    
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        result = await publisher.publish(sample_post, "@my_channel")
        
        assert result is False


@pytest.mark.asyncio
async def test_publish_uses_fallback_body(publisher, sample_post):
    post_without_telegram = ProcessedPost(
        raw_id="post-456",
        niche="realestate",
        title="Test",
        body="Fallback body",
        platform_variants={"vk": "VK only"},
        created_at=datetime.utcnow(),
    )
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        await publisher.publish(post_without_telegram, "@my_channel")
        
        call_kwargs = mock_client.post.call_args[1]["json"]
        assert call_kwargs["text"] == "Fallback body"


@pytest.mark.asyncio
async def test_publish_truncates_long_text(publisher, sample_post):
    long_text = "A" * 5000
    post_long = ProcessedPost(
        raw_id="post-789",
        niche="realestate",
        title="Long",
        body=long_text,
        platform_variants={"telegram": long_text},
        created_at=datetime.utcnow(),
    )
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        await publisher.publish(post_long, "@my_channel")
        
        call_kwargs = mock_client.post.call_args[1]["json"]
        assert len(call_kwargs["text"]) <= 4096
