from datetime import datetime

from pydantic import BaseModel, PrivateAttr, model_validator, Field

from src.schema.base_schema import FindResult, FindBase


class BasePredictionSchema(BaseModel):
    id: int
    created_at: datetime
    predicted_at: datetime
    predictor: int
    input_data: dict
    output_data: dict

    class Config:
        orm_mode = True


class InputPredictionSchema(BaseModel):
    created_at: datetime
    predicted_at: datetime | None
    predictor: int | None
    input_data: dict
    output_data: dict
    user_id: int

    class Config:
        orm_mode = True


class PredictionServerSchema(BaseModel):
    prediction: list[float]

    class Config:
        orm_mode = True


class PredictionResponseSchema(BaseModel):
    predictor: int
    output_data: PredictionServerSchema

    class Config:
        orm_mode = True


class PredictionFullSchema(BaseModel):
    id: int
    created_at: datetime
    predicted_at: datetime
    predictor: int
    input_data: dict
    output_data: dict

    class Config:
        orm_mode = True


class PredictionListResponseSchema(FindResult):
    founds: list[PredictionFullSchema]

    class Config:
        orm_mode = True


class PredictionPaginationSchema(FindBase):
    ...


class PredictionPaginationSchemaByUser(PredictionPaginationSchema):
    user_id: int



class Predicted(BaseModel):
    balance: float
    prediction: PredictionResponseSchema

    class Config:
        orm_mode = True
