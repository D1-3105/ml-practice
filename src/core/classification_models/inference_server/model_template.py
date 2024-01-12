import os
import pickle
import typing

import pydantic
import uvicorn
from fastapi import FastAPI

if typing.TYPE_CHECKING:
    pass


class ModelPipeline:

    def __init__(self, model):
        self.model = model

    def infer(self, input_tensor: typing.Iterable | None = None):
        infer_response = self.model.predict(input_tensor)
        return infer_response


model_pipeline = None


class PredictionResponse(pydantic.BaseModel):
    prediction: list[int]


class ErrorResponse(pydantic.BaseModel):
    error: str
    model_class: str
    message: str


class InferenceRequest(pydantic.BaseModel):
    input_tensor: list[list[float]]


class HealthCheck(pydantic.BaseModel):
    linked_model_id: int


app = FastAPI(debug=True)


@app.post('/api/v2/predict/')
async def predict(inference_request: InferenceRequest) -> PredictionResponse | ErrorResponse:
    try:
        model_response = model_pipeline.infer(inference_request.input_tensor)
        return {'prediction': model_response}
    except Exception as e:
        return {
            'error': e.__class__.__name__,
            "model_class": str(model_pipeline.model.__class__.__name__),
            "message": str(e)
        }


@app.get('/api/v2/healthcheck', status_code=200)
async def health_check() -> HealthCheck:
    return {'linked_model_id': int(os.getenv('LINKED_MODEL_ID', -1))}


if __name__ == '__main__':
    with open(os.getenv('PKL_MODEL_PATH'), 'rb') as f:
        pkl_model = pickle.load(f)
    model_pipeline = ModelPipeline(pkl_model)
    uvicorn.run(app, port=int(os.getenv('PORT')), host=os.getenv('HOST'))
