import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from src.processor.ai_rewriter import AIRewriter
from src.models import RawPost
from datetime import datetime


@pytest.fixture
def rewriter():
    return AIRewriter(api_key="test-api-key")


@pytest.fixture
def sample_post():
    return RawPost(
        id="post-123",
        source="rss:https://example.com/rss",
        niche="realestate",
        text="Test real estate post about a new apartment building.",
        url="https://example.com/post-123",
        collected_at=datetime.utcnow(),
    )


@pytest.mark.asyncio
async def test_rewrite_calls_openai_for_each_platform(rewriter, sample_post):
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="**New Building**\n\nTest content."))]
    
    with patch.object(rewriter.client.chat.completions, "create", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_response
        result = await rewriter.rewrite(sample_post, "style prompt", ["telegram", "vk"])
        
        assert mock_create.call_count == 2
        assert "telegram" in result.platform_variants
        assert "vk" in result.platform_variants


@pytest.mark.asyncio
async def test_rewrite_extracts_title_from_first_line(rewriter, sample_post):
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="**New Apartment**\n\nThis is the body."))]
    
    with patch.object(rewriter.client.chat.completions, "create", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_response
        result = await rewriter.rewrite(sample_post, "style prompt", ["telegram"])
        
        assert result.title == "New Apartment"
        assert result.niche == "realestate"
        assert result.raw_id == "post-123"


@pytest.mark.asyncio
async def test_rewrite_sets_body_to_telegram_variant(rewriter, sample_post):
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="**Title**\n\nBody content."))]
    
    with patch.object(rewriter.client.chat.completions, "create", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_response
        result = await rewriter.rewrite(sample_post, "style prompt", ["telegram", "vk"])
        
        assert result.body == "**Title**\n\nBody content."


@pytest.mark.asyncio
async def test_rewrite_uses_persona_model_when_provided(rewriter, sample_post):
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="Test content"))]
    
    persona = {
        "name": "Test Author",
        "model": "anthropic/claude-haiku-3-5",
        "system_prompt": "You are a test persona."
    }
    
    with patch.object(rewriter.client.chat.completions, "create", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_response
        result = await rewriter.rewrite(sample_post, "style prompt", ["telegram"], persona)
        
        first_call = mock_create.call_args_list[0]
        assert first_call.kwargs["model"] == "anthropic/claude-haiku-3-5"


@pytest.mark.asyncio
async def test_rewrite_uses_default_model_without_persona(rewriter, sample_post):
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="Test content"))]
    
    with patch.object(rewriter.client.chat.completions, "create", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_response
        result = await rewriter.rewrite(sample_post, "style prompt", ["telegram"], None)
        
        call_args = mock_create.call_args
        assert call_args.kwargs["model"] == "gpt-4o-mini"


@pytest.mark.asyncio
async def test_rewrite_adds_humanizer_pass_when_persona_provided(rewriter, sample_post):
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="Test content"))]
    
    persona = {
        "name": "Test Author",
        "model": "gpt-4o-mini",
        "system_prompt": "You are a test persona."
    }
    
    with patch.object(rewriter.client.chat.completions, "create", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_response
        result = await rewriter.rewrite(sample_post, "style prompt", ["telegram"], persona)
        
        assert mock_create.call_count == 2


def test_platform_hint_telegram():
    rewriter = AIRewriter("test-key")
    hint = rewriter._platform_hint("telegram")
    assert "Telegram" in hint
    assert "markdown" in hint


def test_platform_hint_vk():
    rewriter = AIRewriter("test-key")
    hint = rewriter._platform_hint("vk")
    assert "ВКонтакте" in hint
    assert "без markdown" in hint.lower()


def test_platform_hint_unknown():
    rewriter = AIRewriter("test-key")
    hint = rewriter._platform_hint("unknown")
    assert hint == "unknown"
