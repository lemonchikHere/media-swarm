import pytest
from datetime import datetime
from src.models import RawPost, ProcessedPost, PublishJob


def test_raw_post_creation():
    post = RawPost(
        id="test123",
        source="tg:test_channel",
        niche="realestate",
        text="Test post content",
        url="https://example.com"
    )
    assert post.id == "test123"
    assert post.source == "tg:test_channel"
    assert post.niche == "realestate"
    assert post.text == "Test post content"
    assert post.url == "https://example.com"
    assert isinstance(post.collected_at, datetime)


def test_raw_post_without_url():
    post = RawPost(
        id="test456",
        source="rss:test_feed",
        niche="ai_tech",
        text="Another post"
    )
    assert post.url is None
    assert post.collected_at is not None


def test_processed_post_creation():
    post = ProcessedPost(
        raw_id="raw123",
        niche="realestate",
        title="Test Title",
        body="Test body content",
        platform_variants={"telegram": "TG variant", "vk": "VK variant"}
    )
    assert post.raw_id == "raw123"
    assert post.niche == "realestate"
    assert post.title == "Test Title"
    assert post.body == "Test body content"
    assert len(post.platform_variants) == 2


def test_processed_post_empty_variants():
    post = ProcessedPost(
        raw_id="raw456",
        niche="ai_tech",
        title="AI Post",
        body="AI content"
    )
    assert post.platform_variants == {}


def test_publish_job_defaults():
    job = PublishJob(
        post_id="post123",
        niche="realestate",
        platform="telegram",
        channel_id="@my_channel"
    )
    assert job.status == "pending"
    assert job.post_id == "post123"


def test_publish_job_status_values():
    job = PublishJob(
        post_id="post456",
        niche="ai_tech",
        platform="vk",
        channel_id="123456789",
        status="sent"
    )
    assert job.status == "sent"
