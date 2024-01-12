import logging

from . import celery_app
from src.core.container import Container
from src.model.models import ClassificationModelORM, InferenceServerORM
from src.schema.deploy_schema import DeployResultSchema
from ..schema.inference_schema import InferenceServerActiveSchema
from ..services.inference_service import InferenceException

logger = celery_app.log.get_default_logger()


@celery_app.task(
    queue='cold_start_q',
    name='model_initialize_task',
)
def model_initialize_task(model_serialized: dict):
    model = ClassificationModelORM.model_validate(model_serialized)
    deployment_result: DeployResultSchema = Container.inference_service().cold_start(model)
    logger.info(deployment_result.model_dump())
    return deployment_result.model_dump()


@celery_app.task(
    queue='health_check_q',
    name='change_server_state'
)
def change_server_state(initializing_result, server_id: int):
    Container.inference_service().put_update(server_id, DeployResultSchema(**initializing_result))


@celery_app.task(
    queue='health_check_q',
    name='health_check'
)
def health_check_models():
    logger.info('Health check started!')
    inference_service = Container.inference_service()
    inference_servers: list[InferenceServerORM] = inference_service.get_list(
        InferenceServerActiveSchema(**{'server_state': InferenceServerORM.ServerState.ALIVE})
    )['founds']
    for server in inference_servers:
        try:
            linked_id = inference_service.do_health_check(server)
            inference_service.patch_attr(server.id, 'linked_model_id', linked_id)
        except InferenceException:
            inference_service.patch_attr(
                server.id,
                'server_state',
                InferenceServerORM.ServerState.DEAD.value
            )
