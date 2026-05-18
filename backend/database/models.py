from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field


class CrawlRun(BaseModel):
    run_id: str
    status: str = "pending"
    total_keywords: int = 0
    processed_keywords: int = 0
    devices: List[str] = []
    profiles: List[str] = []
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error: Optional[str] = None


class AdResult(BaseModel):
    run_id: str
    keyword: str
    device: str
    profile_name: str
    has_ads: bool = False
    ad_position: int = 0
    ad_title: Optional[str] = None
    advertiser: Optional[str] = None
    visible_domain: Optional[str] = None
    raw_url: Optional[str] = None
    final_url: Optional[str] = None
    final_domain: Optional[str] = None
    screenshot_path: Optional[str] = None
    html_path: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CrawlStartRequest(BaseModel):
    keywords: List[str]
    devices: List[str] = ["desktop"]
    profiles: List[str] = ["Default"]