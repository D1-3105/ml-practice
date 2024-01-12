from dependency_injector import containers, providers

from src.core.config import configs
from src.core.database import Database
from src.repository import *
from src.repository.classificator_repository import ClassificatorRepository
from src.repository.inference_server_repository import InferenceServerRepository
from src.repository.prediction_repository import PredictionRepository
from src.services import *
from src.services.classificator_service import ClassificatorService
from src.services.inference_service import InferenceService
from src.services.prediction_service import PredictionService


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        modules=[
            "src.api.v1.endpoints.auth",
            "src.api.v1.endpoints.inference",
            "src.core.dependencies",
        ]
    )

    db = providers.Singleton(Database, db_url=configs.DATABASE_URI)

    user_repository = providers.Factory(UserRepository, session_factory=db.provided.session)

    inference_repository = providers.Factory(InferenceServerRepository, session_factory=db.provided.session)

    prediction_repository = providers.Factory(PredictionRepository, session_factory=db.provided.session)

    classificator_repository = providers.Factory(ClassificatorRepository, session_factory=db.provided.session)

    user_service = providers.Factory(UserService, user_repository=user_repository)

    auth_service = providers.Factory(AuthService, user_repository=user_repository)

    inference_service = providers.Factory(InferenceService, inference_repository=inference_repository)

    prediction_service = providers.Factory(PredictionService, prediction_repository=prediction_repository)

    classificator_service = providers.Factory(ClassificatorService, classificator_repository=classificator_repository)

