from src.repository.classificator_repository import ClassificatorRepository
from src.services.base_service import BaseService


class ClassificatorService(BaseService):
    def __init__(self, classificator_repository: ClassificatorRepository):
        self.classificator_repository = classificator_repository
        super().__init__(classificator_repository)
