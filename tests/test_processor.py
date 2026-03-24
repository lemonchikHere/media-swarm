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


@pytest.mark.asyncio
async def test_rewrite_uses_persona_model(rewriter, sample_post):
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="Test content"))]
    
    persona = {"model": "gpt-4o", "humanize": False}
    
    with patch.object(rewriter.client.chat.completions, "create", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_response
        await rewriter.rewrite(sample_post, "style prompt", ["telegram"], persona)
        
        call_kwargs = mock_create.call_args.kwargs
        assert call_kwargs["model"] == "gpt-4o"


@pytest.mark.asyncio
async def test_rewrite_with_persona_humanize(rewriter, sample_post):
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="Humanized content"))]
    
    persona = {"model": "gpt-4o-mini", "humanize": True, "system_prompt": "You are a writer."}
    
    with patch.object(rewriter.client.chat.completions, "create", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_response
        result = await rewriter.rewrite(sample_post, "", ["telegram"], persona)
        
        assert mock_create.call_count == 2


@pytest.mark.asyncio
async def test_rewrite_uses_persona_system_prompt(rewriter, sample_post):
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="Content"))]
    
    persona_system_prompt = "You are a developer advocate."
    
    with patch.object(rewriter.client.chat.completions, "create", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_response
        await rewriter.rewrite(sample_post, "", ["telegram"], {"system_prompt": persona_system_prompt})
        
        call_kwargs = mock_create.call_args.kwargs
        messages = call_kwargs["messages"]
        assert persona_system_prompt in messages[0]["content"]
