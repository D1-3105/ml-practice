from datetime import datetime
from typing import List, Optional, Union

from pydantic import BaseModel, Field


class ModelBaseInfo(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime


class FindBase(BaseModel):
    ordering: Optional[str] = Field(default=None)
    page: Optional[int] = Field(default=None)
    page_size: Optional[Union[int, str]] = Field(default=None)


class SearchOptions(FindBase):
    total_count: Optional[int]


class FindResult(BaseModel):
    founds: Optional[List]
    search_options: Optional[SearchOptions]


class FindDateRange(BaseModel):
    created_at__lt: str
    created_at__lte: str
    created_at__gt: str
    created_at__gte: str


class Blank(BaseModel):
    pass
