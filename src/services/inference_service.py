import dataclasses
import subprocess
import threading

import httpx
from fastapi import HTTPException

from src.core.classification_models.InferenceClient import SyncInferenceClient
from src.core.classification_models.InferenceServer import InferenceServer
from src.model.models import ClassificationModelORM, InferenceServerORM

from src.repository.inference_server_repository import InferenceServerRepository
from src.schema.deploy_schema import DeployResultSchema
from src.schema.inference_schema import InferenceServerInputSchema
from src.schema.user_schema import User
from src.services.base_service import BaseService


class InferenceException(HTTPException):
    ...


class ServerStartError(Exception):
    ...


@dataclasses.dataclass
class ProcessWrapper:
    process: subprocess.Popen
    is_alive: bool = dataclasses.field(default=False)


def process_correct_monitor(process_wrapper: ProcessWrapper):
    while True:
        output = process_wrapper.process.stdout.readline()
        if output.startswith(b'Application startup complete'):
            process_wrapper.is_alive = True
            break


class InferenceService(BaseService):

    def __init__(self, inference_repository: InferenceServerRepository):
        self.inference_repository = inference_repository
        super().__init__(inference_repository)

    @staticmethod
    def cold_start(model: ClassificationModelORM):
        server_pilot = InferenceServer.from_generated(model.model_file)
        server_process = ProcessWrapper(
            process=server_pilot.run_inference_server(dict(LINKED_MODEL_ID=str(model.id)))
        )
        stderr_thread = threading.Thread(target=process_correct_monitor, args=[server_process])
        stderr_thread.start()
        stderr_thread.join(60)
        if server_process.process.poll():
            server_state = InferenceServerORM.ServerState.DEAD
        else:
            server_state = InferenceServerORM.ServerState.ALIVE

        return DeployResultSchema(
            current_port=server_pilot.port,
            current_host=server_pilot.host,
            server_state=server_state
        )

    @staticmethod
    def do_health_check(inference_server: InferenceServerORM):
        client = SyncInferenceClient(
            inference_server.current_host,
            inference_server.current_port
        )
        try:
            response = client.health_check()
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise InferenceException(detail=str(e), status_code=504)
        except Exception as e:
            raise InferenceException(detail=str(e), status_code=502)
        return response.json()['linked_model_id']

    def infer(self, user: User, model: ClassificationModelORM, input_data: dict):
        inference_server = self.inference_repository.get_by_linked_model_id(model_id=model.id)
        if not inference_server:
            raise InferenceException(detail='No inference servers available!', status_code=404)
        if not user.balance >= inference_server.cost:
            raise InferenceException(detail='Not enough money!', status_code=429)

        client = SyncInferenceClient(
            inference_server.current_host,
            inference_server.current_port
        )

        try:
            response = client.predict(input_data)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise InferenceException(detail=str(e), status_code=504)
        except Exception as e:
            raise InferenceException(detail=str(e), status_code=502)
        user.balance -= inference_server.cost
        return inference_server.id, response.json()
