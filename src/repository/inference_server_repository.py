from contextlib import AbstractContextManager
from typing import Callable

from sqlalchemy.orm import Session

from src.model.models import InferenceServerORM
from src.repository.base_repository import BaseRepository


class InferenceServerRepository(BaseRepository):

    def __init__(self, session_factory: Callable[..., AbstractContextManager[Session]]):
        self.session_factory = session_factory
        super().__init__(session_factory, InferenceServerORM)

    def get_by_linked_model_id(self, model_id) -> InferenceServerORM:
        with self.session_factory() as session:
            query = session.query(self.model).filter(
                self.model.linked_model_id == model_id,
                self.model.server_state == int(self.model.ServerState.ALIVE.value)
            )
            return query.first()
