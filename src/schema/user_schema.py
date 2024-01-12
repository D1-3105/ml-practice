from typing import List, Optional

from pydantic import BaseModel, Field

from src.schema.base_schema import FindBase, SearchOptions


class User(BaseModel):
    id: int | None = Field(default=None)
    email: str | None
    name: str | None
    balance: float | None = Field(default=None)
    is_active: bool | None = Field(default=True)
    is_superuser: bool | None = Field(default=False)
    password: str | None = Field(default=None)

    class Config:
        orm_mode = True


class BaseUser(BaseModel):
    email: str | None = Field(default=None)
    name: str | None = Field(default=None)
    is_active: bool | None = Field(default=None)
    is_superuser: bool | None = Field(default=None)

    class Config:
        orm_mode = True


class BaseUserWithPassword(BaseUser):
    password: str


class BaseUserWithBalance(BaseUser):
    balance: float


class FindUser(FindBase, BaseUser):
    email__eq: str | None
    ...


class UpsertUser(BaseUser):
    ...


class FindUserResult(BaseModel):
    founds: Optional[List[User]]
    search_options: Optional[SearchOptions]
