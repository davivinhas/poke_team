from abc import ABC, abstractmethod
from typing import Optional

from src.domain.value_objects.types import Types


class MovementsGateway(ABC):
    @abstractmethod
    def search(
        self,
        type: Optional[Types] = None,
        specie_name: Optional[str] = None,
    ) -> Optional[str]:
        raise NotImplementedError
