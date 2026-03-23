import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from src.deduplicator.embeddings import SemanticDeduplicator, SIMILARITY_THRESHOLD


@pytest.fixture
def deduplicator():
    with patch("redis.from_url") as mock_redis, \
         patch("openai.AsyncOpenAI") as mock_client:
        mock_redis.return_value = MagicMock()
        yield SemanticDeduplicator("redis://localhost:6380", "test-api-key")


@pytest.mark.asyncio
async def test_cosine_sim_identical_vectors(deduplicator):
    vec = [1.0, 0.0, 0.0]
    assert deduplicator.cosine_sim(vec, vec) == 1.0


@pytest.mark.asyncio
async def test_cosine_sim_orthogonal_vectors(deduplicator):
    vec1 = [1.0, 0.0, 0.0]
    vec2 = [0.0, 1.0, 0.0]
    assert deduplicator.cosine_sim(vec1, vec2) == 0.0


@pytest.mark.asyncio
async def test_is_duplicate_returns_true_for_similar(deduplicator):
    with patch.object(deduplicator, "get_embedding", new_callable=AsyncMock) as mock_emb:
        mock_emb.return_value = [0.9, 0.1, 0.0]
        mock_redis = deduplicator.redis
        mock_redis.scan_iter.return_value = ["embed:realestate:1"]
        mock_redis.get.return_value = '[0.85, 0.15, 0.0]'
        
        result = await deduplicator.is_duplicate("realestate", "test text")
        assert result is True


@pytest.mark.asyncio
async def test_is_duplicate_returns_false_for_different(deduplicator):
    with patch.object(deduplicator, "get_embedding", new_callable=AsyncMock) as mock_emb:
        mock_emb.return_value = [0.9, 0.1, 0.0]
        mock_redis = deduplicator.redis
        mock_redis.scan_iter.return_value = ["embed:realestate:1"]
        mock_redis.get.return_value = '[0.1, 0.9, 0.0]'
        
        result = await deduplicator.is_duplicate("realestate", "test text")
        assert result is False


@pytest.mark.asyncio
async def test_is_duplicate_returns_false_when_no_stored(deduplicator):
    with patch.object(deduplicator, "get_embedding", new_callable=AsyncMock) as mock_emb:
        mock_emb.return_value = [0.9, 0.1, 0.0]
        mock_redis = deduplicator.redis
        mock_redis.scan_iter.return_value = []
        
        result = await deduplicator.is_duplicate("realestate", "test text")
        assert result is False


@pytest.mark.asyncio
async def test_store_saves_embedding_to_redis(deduplicator):
    with patch.object(deduplicator, "get_embedding", new_callable=AsyncMock) as mock_emb:
        mock_emb.return_value = [0.5, 0.5, 0.0]
        mock_redis = deduplicator.redis
        
        await deduplicator.store("realestate", "post-123", "test text")
        
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert call_args[0][0] == "embed:realestate:post-123"
        assert call_args[0][1] == 7 * 86400
