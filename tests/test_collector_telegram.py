import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from src.collector.telegram import TelegramCollector
from src.models import RawPost


@pytest.fixture
def mock_env():
    with patch.dict('os.environ', {
        'TG_API_ID': '123456',
        'TG_API_HASH': 'test_hash',
        'TG_SESSION_STRING': 'test_session'
    }):
        yield


@pytest.fixture
def collector(mock_env):
    return TelegramCollector()


class MockMessage:
    def __init__(self, id=1, text="Test message text " * 10, caption=None):
        self.id = id
        self.text = text
        self.caption = caption


class MockChatHistory:
    def __init__(self, messages):
        self._messages = messages
    
    def __aiter__(self):
        return self
    
    async def __anext__(self):
        if self._messages:
            return self._messages.pop(0)
        raise StopAsyncIteration


@pytest.mark.asyncio
async def test_collect_filters_short_messages(collector):
    """Test that messages shorter than 50 chars are filtered out."""
    mock_messages = [
        MockMessage(id=1, text="Short"),  # Less than 50 chars
        MockMessage(id=2, text="This is a longer message " * 10),  # More than 50 chars
    ]
    
    mock_client = MagicMock()
    mock_client.get_chat_history = MagicMock(return_value=MockChatHistory(mock_messages))
    
    mock_async_client = AsyncMock()
    mock_async_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_async_client.__aexit__ = AsyncMock(return_value=None)
    mock_async_client.get_chat_history = mock_client.get_chat_history
    
    with patch('src.collector.telegram.Client', return_value=mock_async_client):
        posts = []
        async for post in collector.collect("test_niche", "test_channel"):
            posts.append(post)
        
        assert len(posts) == 1
        assert "longer message" in posts[0].text


@pytest.mark.asyncio
async def test_collect_generates_correct_id(collector):
    """Test that post IDs are generated correctly."""
    mock_messages = [
        MockMessage(id=123, text="Test message content " * 10),
    ]
    
    mock_client = MagicMock()
    mock_client.get_chat_history = MagicMock(return_value=MockChatHistory(mock_messages))
    
    mock_async_client = AsyncMock()
    mock_async_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_async_client.__aexit__ = AsyncMock(return_value=None)
    mock_async_client.get_chat_history = mock_client.get_chat_history
    
    with patch('src.collector.telegram.Client', return_value=mock_async_client):
        posts = []
        async for post in collector.collect("test_niche", "test_channel"):
            posts.append(post)
        
        assert len(posts) == 1
        assert posts[0].source == "tg:test_channel"
        assert "t.me/test_channel/123" in posts[0].url


@pytest.mark.asyncio
async def test_collect_handles_caption_instead_of_text(collector):
    """Test that captions are used when text is None."""
    mock_messages = [
        MockMessage(id=1, text=None, caption="Caption message " * 10),
    ]
    
    mock_client = MagicMock()
    mock_client.get_chat_history = MagicMock(return_value=MockChatHistory(mock_messages))
    
    mock_async_client = AsyncMock()
    mock_async_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_async_client.__aexit__ = AsyncMock(return_value=None)
    mock_async_client.get_chat_history = mock_client.get_chat_history
    
    with patch('src.collector.telegram.Client', return_value=mock_async_client):
        posts = []
        async for post in collector.collect("test_niche", "test_channel"):
            posts.append(post)
        
        assert len(posts) == 1
        assert "Caption message" in posts[0].text


@pytest.mark.asyncio
async def test_collect_handles_empty_messages(collector):
    """Test that messages without text or caption are skipped."""
    mock_messages = [
        MockMessage(id=1, text=None, caption=None),
        MockMessage(id=2, text="Valid message " * 10),
    ]
    
    mock_client = MagicMock()
    mock_client.get_chat_history = MagicMock(return_value=MockChatHistory(mock_messages))
    
    mock_async_client = AsyncMock()
    mock_async_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_async_client.__aexit__ = AsyncMock(return_value=None)
    mock_async_client.get_chat_history = mock_client.get_chat_history
    
    with patch('src.collector.telegram.Client', return_value=mock_async_client):
        posts = []
        async for post in collector.collect("test_niche", "test_channel"):
            posts.append(post)
        
        assert len(posts) == 1
