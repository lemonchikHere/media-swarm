import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from src.pipeline import Pipeline
from src.models import RawPost, ProcessedPost
from datetime import datetime, timezone


@pytest.fixture
def mock_collector_posts():
    post1 = RawPost(
        id="post-1",
        source="rss:https://example.com/rss",
        niche="realestate",
        text="Test post 1",
        collected_at=datetime.now(timezone.utc),
    )
    post2 = RawPost(
        id="post-2",
        source="rss:https://example.com/rss",
        niche="realestate",
        text="Test post 2",
        collected_at=datetime.now(timezone.utc),
    )

    async def mock_collect(niche, url):
        for p in [post1, post2]:
            yield p

    mock = MagicMock()
    mock.collect = mock_collect
    return mock


def make_fake_rewrite():
    async def fake_rewrite(post, style_prompt, platforms):
        return ProcessedPost(
            raw_id=post.id,
            niche=post.niche,
            title="Rewritten Title",
            body="Rewritten body",
            platform_variants={"telegram": "TG body", "vk": "VK body"},
            created_at=datetime.now(timezone.utc),
        )
    return fake_rewrite


def make_mock_dedup():
    mock = MagicMock()
    mock.is_duplicate = AsyncMock(return_value=False)
    mock.store = AsyncMock()
    return mock


def make_mock_rewriter():
    mock = MagicMock()
    mock.rewrite = AsyncMock(side_effect=make_fake_rewrite())
    return mock


def make_mock_telegram():
    mock = MagicMock()
    mock.publish = AsyncMock(return_value=True)
    return mock


def make_mock_vk():
    mock = MagicMock()
    mock.publish = AsyncMock(return_value=True)
    return mock


def test_pipeline_run_full_flow(mock_collector_posts):
    mock_dedup = make_mock_dedup()
    mock_rewriter = make_mock_rewriter()
    mock_tg = make_mock_telegram()
    mock_vk = make_mock_vk()

    with (
        patch("src.pipeline.RSSCollector", return_value=mock_collector_posts),
        patch("src.pipeline.SemanticDeduplicator", return_value=mock_dedup),
        patch("src.pipeline.AIRewriter", return_value=mock_rewriter),
        patch("src.pipeline.TelegramPublisher", return_value=mock_tg),
        patch("src.pipeline.VKPublisher", return_value=mock_vk),
        patch.dict("os.environ", {
            "OPENAI_API_KEY": "test-key",
            "TG_BOT_TOKEN": "test-tg",
            "VK_TOKEN": "test-vk",
            "REDIS_URL": "redis://localhost:6380",
        }),
    ):
        pipeline = Pipeline("realestate")
        import asyncio
        result = asyncio.get_event_loop().run_until_complete(pipeline.run(max_posts=2))

        assert result == 2
        assert mock_dedup.is_duplicate.call_count == 2
        assert mock_dedup.store.call_count == 2
        assert mock_tg.publish.call_count == 2
        assert mock_vk.publish.call_count == 2


def test_pipeline_skips_duplicates_when_duplicate(mock_collector_posts):
    mock_dedup = make_mock_dedup()
    mock_dedup.is_duplicate = AsyncMock(return_value=True)
    mock_rewriter = make_mock_rewriter()
    mock_tg = make_mock_telegram()
    mock_vk = make_mock_vk()

    with (
        patch("src.pipeline.RSSCollector", return_value=mock_collector_posts),
        patch("src.pipeline.SemanticDeduplicator", return_value=mock_dedup),
        patch("src.pipeline.AIRewriter", return_value=mock_rewriter),
        patch("src.pipeline.TelegramPublisher", return_value=mock_tg),
        patch("src.pipeline.VKPublisher", return_value=mock_vk),
        patch.dict("os.environ", {
            "OPENAI_API_KEY": "test-key",
            "TG_BOT_TOKEN": "test-tg",
            "VK_TOKEN": "test-vk",
            "REDIS_URL": "redis://localhost:6380",
        }),
    ):
        pipeline = Pipeline("realestate")
        import asyncio
        result = asyncio.get_event_loop().run_until_complete(pipeline.run())

        assert result == 0
        assert mock_rewriter.rewrite.call_count == 0
        assert mock_tg.publish.call_count == 0


def test_pipeline_respects_max_posts(mock_collector_posts):
    mock_dedup = make_mock_dedup()
    mock_rewriter = make_mock_rewriter()
    mock_tg = make_mock_telegram()
    mock_vk = make_mock_vk()

    with (
        patch("src.pipeline.RSSCollector", return_value=mock_collector_posts),
        patch("src.pipeline.SemanticDeduplicator", return_value=mock_dedup),
        patch("src.pipeline.AIRewriter", return_value=mock_rewriter),
        patch("src.pipeline.TelegramPublisher", return_value=mock_tg),
        patch("src.pipeline.VKPublisher", return_value=mock_vk),
        patch.dict("os.environ", {
            "OPENAI_API_KEY": "test-key",
            "TG_BOT_TOKEN": "test-tg",
            "VK_TOKEN": "test-vk",
            "REDIS_URL": "redis://localhost:6380",
        }),
    ):
        pipeline = Pipeline("realestate")
        import asyncio
        result = asyncio.get_event_loop().run_until_complete(pipeline.run(max_posts=1))

        assert result == 1
        assert mock_tg.publish.call_count == 1


def test_pipeline_loads_niche_config():
    mock_dedup = make_mock_dedup()
    mock_rewriter = make_mock_rewriter()
    mock_tg = make_mock_telegram()
    mock_vk = make_mock_vk()

    with (
        patch("src.pipeline.SemanticDeduplicator", return_value=mock_dedup),
        patch("src.pipeline.AIRewriter", return_value=mock_rewriter),
        patch("src.pipeline.TelegramPublisher", return_value=mock_tg),
        patch("src.pipeline.VKPublisher", return_value=mock_vk),
        patch.dict("os.environ", {
            "OPENAI_API_KEY": "test-key",
            "TG_BOT_TOKEN": "test-tg",
            "VK_TOKEN": "test-vk",
            "REDIS_URL": "redis://localhost:6380",
        }),
    ):
        pipeline = Pipeline("realestate")
        assert pipeline.niche == "realestate"
        assert "rss" in pipeline.config["sources"]
        assert "telegram" in pipeline.config["publish_to"]
