from datetime import datetime, timezone
from typing import List, Union, Optional
from pydantic import BaseModel, Field, field_validator, model_validator

class Location(BaseModel):
    uule: str
    name: str

class LocationCreateRequest(BaseModel):
    uule: str
    name: str

class LocationUpdateRequest(BaseModel):
    uule: Optional[str] = None
    name: Optional[str] = None

class CrawlRun(BaseModel):
    run_id: str
    status: str = "pending"
    total_keywords: int = 0
    processed_keywords: int = 0
    devices: List[str] = []
    profiles: List[str] = []
    locations: List[str] = []
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error: Optional[str] = None


class AdResult(BaseModel):
    run_id: str
    keyword: str
    device: str
    profile_name: str
    location_uule: Optional[str] = None   # mã UULE (None = không giả lập vị trí)
    location_name: Optional[str] = None   # tên địa điểm để hiển thị
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
    keywords: Union[str, List[str]]
    devices: Union[str, List[str]] = "desktop"
    profiles: Union[str, List[str]] = "Default"
    locations: Union[str, List[str]] = []

    @field_validator('keywords', 'devices', 'profiles', 'locations', mode='before')
    @classmethod
    def convert_to_list(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            return [v] if v else []
        if isinstance(v, list):
            return v
        raise ValueError('Must be string or list of strings')

    @model_validator(mode='after')
    def normalize_lists(self):
        if isinstance(self.keywords, str):
            self.keywords = [self.keywords]
        if isinstance(self.devices, str):
            self.devices = [self.devices]
        if isinstance(self.profiles, str):
            self.profiles = [self.profiles]
        if isinstance(self.locations, str):
            self.locations = [self.locations] if self.locations else []
        return self