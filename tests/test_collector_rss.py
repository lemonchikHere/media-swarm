import pytest
from unittest.mock import patch, MagicMock
from src.collector.rss import RSSCollector


@pytest.fixture
def rss_collector():
    return RSSCollector()


@pytest.fixture
def mock_feed_entries():
    return [
        {
            "title": "Test Article",
            "summary": "This is a test summary that is long enough to pass the minimum length filter for processing.",
            "link": "https://example.com/article1",
            "id": "article-1",
        },
        {
            "title": "Another Article",
            "description": "Another test description that is long enough to pass the minimum length filter for our posts.",
            "link": "https://example.com/article2",
            "id": "article-2",
        },
    ]


@pytest.mark.asyncio
async def test_rss_collector_yields_raw_posts(rss_collector, mock_feed_entries):
    mock_feed = MagicMock()
    mock_feed.entries = mock_feed_entries

    with patch("feedparser.parse", return_value=mock_feed):
        posts = []
        async for post in rss_collector.collect("realestate", "https://example.com/rss"):
            posts.append(post)

        assert len(posts) == 2
        assert posts[0].niche == "realestate"
        assert "Test Article" in posts[0].text
        assert posts[0].url == "https://example.com/article1"
        assert posts[0].source == "rss:https://example.com/rss"
        assert "Another Article" in posts[1].text


@pytest.mark.asyncio
async def test_rss_collector_skips_empty_text(rss_collector):
    mock_feed = MagicMock()
    mock_feed.entries = [
        {"title": "", "summary": "", "link": None, "id": "empty"},
    ]

    with patch("feedparser.parse", return_value=mock_feed):
        posts = []
        async for post in rss_collector.collect("ai_tech", "https://example.com/rss"):
            posts.append(post)

        assert len(posts) == 0


@pytest.mark.asyncio
async def test_rss_collector_limits_to_20_entries(rss_collector):
    mock_entries = [
        {"title": f"Article {i} with a descriptive title", "summary": f"This is summary number {i} with enough content to pass the minimum length filter.", "link": f"https://ex.com/{i}", "id": str(i)}
        for i in range(30)
    ]
    mock_feed = MagicMock()
    mock_feed.entries = mock_entries

    with patch("feedparser.parse", return_value=mock_feed):
        posts = []
        async for post in rss_collector.collect("realestate", "https://example.com/rss"):
            posts.append(post)

        assert len(posts) == 15
