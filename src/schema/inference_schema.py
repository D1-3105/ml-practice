from typing import ClassVar

from fastapi import Path
from pydantic import BaseModel, Field
from sqlalchemy import Column, String

from src.core.config import configs
from src.schema.base_schema import FindResult, FindBase


class InferenceServerInputSchema(BaseModel):
    linked_model_id: int
    cost: float
    server_state: int


class InferenceServerActiveSchema(BaseModel):
    server_state: int
    page_size: str | int = Field(default='all')


class ClassificationModelListQuerySchema(FindBase):
    ...


class ClassificationModelListResponseSchema(FindResult):
    class FoundResult(BaseModel):
        id: int
        name: str
    founds: list[FoundResult]
