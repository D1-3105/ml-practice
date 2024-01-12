import enum
from datetime import datetime

from sqlalchemy import Integer, JSON, String, Text
from sqlmodel import Column, DateTime, Field, SQLModel, func


class ClassificationModelORM(SQLModel, table=True):
    id: int = Field(primary_key=True)
    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), default=func.now()))
    updated_at: datetime = Field(sa_column=Column(DateTime(timezone=True), default=func.now(), onupdate=func.now()))
    name: str = Field(unique=True)
    model_file: str = Field(sa_column=Column(String))


class InferenceServerORM(SQLModel, table=True):

    class ServerState(enum.Enum):
        DEAD = 0
        ALIVE = 1
        STARTING = 2

        @classmethod
        def to_str(cls, s):
            return {0: 'Dead', 1: 'Alive', 2: 'Starting'}.get(s.value, 'Undefined')

        @classmethod
        def all(cls):
            return [cls.DEAD, cls.ALIVE, cls.STARTING]

    id: int = Field(primary_key=True)
    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), default=func.now()))
    updated_at: datetime = Field(sa_column=Column(DateTime(timezone=True), default=func.now(), onupdate=func.now()))
    linked_model_id: int = Field(foreign_key=f"{ClassificationModelORM.__tablename__}.id")
    current_port: int | None = Field(nullable=True)
    current_host: str | None = Field(nullable=True)
    cost: float = Field()
    server_state: int = Field(sa_column=Integer, default=ServerState.DEAD)


class User(SQLModel, table=True):
    id: int = Field(primary_key=True)
    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), default=func.now()))
    updated_at: datetime = Field(sa_column=Column(DateTime(timezone=True), default=func.now(), onupdate=func.now()))

    email: str = Field(unique=True)
    password: str = Field()
    balance: float = Field(default=500)
    name: str = Field(default=None, nullable=True)
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)


class Prediction(SQLModel, table=True):
    id: int = Field(primary_key=True)
    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), default=func.now()))
    predicted_at: datetime = Field(sa_column=Column(DateTime(timezone=True)))
    predictor: int = Field(foreign_key=f"{InferenceServerORM.__tablename__}.id")
    user_id: int = Field(foreign_key=f"{User.__tablename__}.id")
    input_data: dict = Field(sa_column=Column(JSON))
    output_data: dict = Field(sa_column=Column(JSON))
