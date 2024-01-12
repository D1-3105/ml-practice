from datetime import datetime

from pydantic import BaseModel, Field
from src.schema.user_schema import User, BaseUser


class SignIn(BaseModel):
    email__eq: str | None = Field(..., alias='email')
    password: str | None


class SignUp(BaseModel):
    email: str | None
    password: str | None
    name: str | None


class Payload(BaseModel):
    id: int | None
    email: str | None
    name: str | None
    is_superuser: bool | None


class SignInResponse(BaseModel):
    access_token: str | None
    expiration: datetime | None
    user_info: BaseUser | None

    class Config:
        exclude = {'user_info': {'password': True}}
