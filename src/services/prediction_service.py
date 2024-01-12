from src.repository.prediction_repository import PredictionRepository
from src.services.base_service import BaseService


class PredictionService(BaseService):

    def __init__(self, prediction_repository: PredictionRepository):
        self.prediction_repository = prediction_repository
        super().__init__(prediction_repository)
