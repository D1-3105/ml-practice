import asyncio
import json
import os
import pathlib
import time

import httpx
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, UploadFile, File, Form, Path, HTTPException, Body

from src.celery_application.tasks import model_initialize_task, change_server_state
from src.core.container import Container
from src.core.dependencies import get_current_active_user, get_current_super_user
from src.model.models import ClassificationModelORM, InferenceServerORM
from src.schema.classificator_schema import BaseClassificatorSchema
from src.schema.deploy_schema import DeployResponseSchema, DeployResultSchema
from src.schema.inference_schema import ClassificationModelListQuerySchema, \
    ClassificationModelListResponseSchema, InferenceServerInputSchema
from src.schema.prediction_schema import InputPredictionSchema, PredictionResponseSchema, PredictionPaginationSchema, \
    PredictionPaginationSchemaByUser, PredictionListResponseSchema
from src.schema.user_schema import User
from src.services import UserService
from src.services.classificator_service import ClassificatorService
from src.services.inference_service import InferenceService
from src.services.prediction_service import PredictionService
from src.util.date import get_now

router = APIRouter(
    prefix="/inference",
    tags=["inference"],
)


@router.post('/predict/{model_id}')
@inject
async def predict(
        input_tensor: list[list[float]] = Body(embed=True),
        model_id: int = Path(...),
        current_user: User = Depends(get_current_active_user),
        inference_service: InferenceService = Depends(Provide[Container.inference_service]),
        user_service: UserService = Depends(Provide[Container.user_service]),
        prediction_service: PredictionService = Depends(Provide[Container.prediction_service]),
        classificator_service: PredictionService = Depends(Provide[Container.classificator_service])
) -> PredictionResponseSchema:
    creation_time = get_now()
    classificator = classificator_service.get_by_id(model_id)
    input_data = {'input_tensor': input_tensor}
    for retry in range(2):
        try:
            server_id, inference_data = inference_service.infer(
                current_user,
                model=classificator,
                input_data=input_data
            )
            break
        except httpx.ConnectError as e:
            raise HTTPException(status_code=404, detail='No active inference server found!')
    else:
        raise HTTPException(status_code=504)
    prediction_schema = InputPredictionSchema(
        created_at=creation_time,
        predicted_at=get_now(),
        predictor=server_id,
        input_data=input_data,
        output_data=inference_data,
        user_id=current_user.id
    )
    user_service.put_update(current_user.id, current_user)

    new_prediction = prediction_service.add(prediction_schema)
    return {'predictor': new_prediction.predictor, 'output_data': inference_data}


def initialize_server(inference_service, model, cost):
    inference_server_model = inference_service.add(
        InferenceServerInputSchema(
            linked_model_id=model.id,
            cost=cost,
            server_state=InferenceServerORM.ServerState.STARTING
        )
    )
    model_initialize_task.apply_async(
        args=[
            model.model_dump()
        ],
        link=change_server_state.s(server_id=inference_server_model.id)
    )
    return inference_server_model


@router.post('/deploy/{model_id}')
@inject
async def deploy_for_model(
        cost: float,
        model_id: int = Path(...),
        classificator_service: ClassificatorService = Depends(Provide[Container.classificator_service]),
        inference_service: InferenceService = Depends(Provide[Container.inference_service]),
        current_user: User = Depends(get_current_super_user),
) -> DeployResponseSchema:
    model = classificator_service.get_by_id(model_id)
    inference_server_model = initialize_server(inference_service, model, cost)
    return {
        'server_state': inference_server_model.server_state,
        'id': inference_server_model.id,
        'model_id': model.id
    }


@router.post('/deploy/')
@inject
async def deploy(
        model_name: str = Form(),
        cost: float = Form(),
        deploy_file: UploadFile = File(...),
        current_user: User = Depends(get_current_super_user),
        inference_service: InferenceService = Depends(Provide[Container.inference_service]),
        classificator_service: ClassificatorService = Depends(Provide[Container.classificator_service])
) -> DeployResponseSchema:
    path = pathlib.Path(os.getenv('CELERY_MODEL_FILE_ROOT')) / deploy_file.filename
    with open(pathlib.Path(os.getenv('MODEL_FILE_ROOT')) / deploy_file.filename, 'wb+') as f:
        f.write(await deploy_file.read())
    classificator_schema = BaseClassificatorSchema(
        name=model_name,
        cost=cost,
        model_file=str(path.as_posix())
    )
    model: ClassificationModelORM = classificator_service.add(classificator_schema)
    inference_server_model = initialize_server(inference_service, model, cost)
    return {
        'server_state': inference_server_model.server_state,
        'id': inference_server_model.id,
        'model_id': model.id
    }


@router.get('/server/state/{server_id}')
@inject
async def server_state(
        server_id: int,
        current_user: User = Depends(get_current_super_user),
        inference_service: InferenceService = Depends(Provide[Container.inference_service]),
) -> DeployResultSchema:
    return inference_service.get_by_id(server_id)


@router.get('/models/list')
@inject
async def list_classificator_models(
        query_params: ClassificationModelListQuerySchema = Depends(),
        classificator_service: ClassificatorService = Depends(Provide[Container.classificator_service]),
        current_user: User = Depends(get_current_active_user)
) -> ClassificationModelListResponseSchema:
    classificators = classificator_service.get_list(schema=query_params)
    return classificators


@router.get('/predictions/list')
@inject
async def list_predictions(
        query_params: PredictionPaginationSchema = Depends(),
        current_user: User = Depends(get_current_active_user),
        prediction_service: PredictionService = Depends(Provide[Container.prediction_service]),
) -> PredictionListResponseSchema:
    predictions = prediction_service.get_list(
        PredictionPaginationSchemaByUser(**query_params.model_dump(), user_id=current_user.id)
    )
    return predictions
