from pydantic import BaseModel


class BaseClassificatorSchema(BaseModel):
    name: str
    cost: float
    model_file: str
