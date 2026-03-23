from pydantic import BaseModel
from datetime import datetime, timezone
from typing import Optional


class RawPost(BaseModel):
    id: str
    source: str
    niche: str
    text: str
    url: Optional[str] = None
    collected_at: datetime = datetime.now(timezone.utc)

class ProcessedPost(BaseModel):
    raw_id: str
    niche: str
    title: str
    body: str
    platform_variants: dict[str, str] = {}
    created_at: datetime = datetime.now(timezone.utc)


class PublishJob(BaseModel):
    post_id: str
    niche: str
    platform: str
    channel_id: str
    status: str = "pending"
