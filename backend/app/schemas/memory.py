from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class MemoryRequest(BaseModel):
    title: str
    content: str = ""
    type: str = "TEXT"
    source_url: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    big_tag: Optional[str] = None
    favorite: bool = False
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    privacy_status: Optional[str] = "ANALYZE"


class UpdateMemoryRequest(BaseModel):
    """Partial update — all fields optional."""
    title: Optional[str] = None
    content: Optional[str] = None
    type: Optional[str] = None
    source_url: Optional[str] = None
    tags: Optional[list[str]] = None
    big_tag: Optional[str] = None
    favorite: Optional[bool] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    privacy_status: Optional[str] = None


class MemoryResponse(BaseModel):
    id: str
    title: str
    content: str
    type: str
    source_url: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    sentiment: Optional[str] = None
    sentiment_score: Optional[float] = None
    processing_status: str
    tags: list[str] = Field(default_factory=list)
    big_tag: Optional[str] = None
    favorite: bool = False
    privacy_status: str = "ANALYZE"
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PagedResponse(BaseModel):
    content: list
    page: int
    size: int
    total_elements: int
    total_pages: int
    last: bool
    first: bool
