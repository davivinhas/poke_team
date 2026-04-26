from abc import ABC, abstractmethod
from typing import Optional

from src.domain.entities.movement import Movement
from src.domain.value_objects.types import Types


class MovementsRepositoryPort(ABC):
    @abstractmethod
    def search(
        self,
        type: Optional[Types] = None,
        specie_name: Optional[str] = None,
    ) -> Optional[list[Movement]]:
        raise NotImplementedError

    @abstractmethod
    def save(self, movement: Movement) -> None:
        raise NotImplementedError
