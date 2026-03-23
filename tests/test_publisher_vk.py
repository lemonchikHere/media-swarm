import pytest
from unittest.mock import patch, MagicMock
from src.publisher.vk import VKPublisher
from src.models import ProcessedPost
from datetime import datetime, timezone


def make_publisher(mock_api):
    mock_instance = MagicMock()
    mock_instance.get_api.return_value = mock_api
    with patch("src.publisher.vk.vk_api.VkApi", return_value=mock_instance):
        publisher = VKPublisher(token="test-token")
    return publisher


@pytest.fixture
def mock_api():
    return MagicMock()


@pytest.fixture
def publisher(mock_api):
    return make_publisher(mock_api)


@pytest.fixture
def sample_post():
    return ProcessedPost(
        raw_id="post-123",
        niche="ai_tech",
        title="AI Breakthrough",
        body="General body text",
        platform_variants={"vk": "VK-specific body text"},
        created_at=datetime.now(timezone.utc),
    )


def test_publish_calls_vk_wall_post(publisher, mock_api, sample_post):
    import asyncio
    result = asyncio.get_event_loop().run_until_complete(
        publisher.publish(sample_post, "123456789")
    )
    assert result is True
    mock_api.wall.post.assert_called_once()


def test_publish_uses_vk_variant(publisher, mock_api, sample_post):
    import asyncio
    asyncio.get_event_loop().run_until_complete(
        publisher.publish(sample_post, "123456789")
    )
    call_kwargs = mock_api.wall.post.call_args[1]
    assert call_kwargs["owner_id"] == "-123456789"
    assert call_kwargs["message"] == "VK-specific body text"
    assert call_kwargs["from_group"] == 1


def test_publish_uses_fallback_body(mock_api):
    post = ProcessedPost(
        raw_id="post-456",
        niche="realestate",
        title="Test",
        body="Fallback body",
        platform_variants={},
        created_at=datetime.now(timezone.utc),
    )
    publisher = make_publisher(mock_api)
    import asyncio
    asyncio.get_event_loop().run_until_complete(publisher.publish(post, "999"))
    call_kwargs = mock_api.wall.post.call_args[1]
    assert call_kwargs["message"] == "Fallback body"


def test_publish_truncates_to_15000_chars(mock_api):
    long_text = "X" * 20000
    post = ProcessedPost(
        raw_id="post-long",
        niche="ai_tech",
        title="Long",
        body=long_text,
        platform_variants={"vk": long_text},
        created_at=datetime.now(timezone.utc),
    )
    publisher = make_publisher(mock_api)
    import asyncio
    asyncio.get_event_loop().run_until_complete(publisher.publish(post, "1"))
    call_kwargs = mock_api.wall.post.call_args[1]
    assert len(call_kwargs["message"]) == 15000


def test_publish_returns_false_on_exception(mock_api, sample_post):
    mock_api.wall.post.side_effect = Exception("Network error")
    publisher = make_publisher(mock_api)
    import asyncio
    result = asyncio.get_event_loop().run_until_complete(
        publisher.publish(sample_post, "1")
    )
    assert result is False
