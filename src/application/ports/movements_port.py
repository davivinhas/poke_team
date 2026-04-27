from abc import ABC, abstractmethod
from typing import Optional

from src.domain.entities.movement import Movement
from src.domain.value_objects.types import Types


class MovementsRepositoryPort(ABC):
    @abstractmethod
    def search(
        self,
        type: Optional[Types] = None,
        specie_id: Optional[int] = None,
    ) -> Optional[list[Movement]]:
        raise NotImplementedError

    @abstractmethod
    def save(self, movement: Movement) -> None:
        raise NotImplementedError

    @abstractmethod
    def link_to_specie(self, specie_id: int, movement_name: str) -> None:
        raise NotImplementedError
