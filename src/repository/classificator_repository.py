from contextlib import AbstractContextManager
from typing import Callable

from sqlmodel import Session

from src.model.models import ClassificationModelORM
from src.repository.base_repository import BaseRepository


class ClassificatorRepository(BaseRepository):

    def __init__(self, session_factory: Callable[..., AbstractContextManager[Session]]):
        self.session_factory = session_factory
        super().__init__(session_factory, ClassificationModelORM)
