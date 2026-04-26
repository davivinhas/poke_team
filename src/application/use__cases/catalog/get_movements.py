from typing import Optional

from src.application.ports.movements_port import MovementsRepositoryPort
from src.domain.entities.movement import Movement
from src.domain.value_objects.types import Types


class SearchMovementsUseCase:
    """ "
    Can search movements by type or specie
    """

    def __init__(self, repository: MovementsRepositoryPort):
        self.repository = repository

    def execute(
        self, type: Optional[Types] = None, specie_name: Optional[str] = None
    ) -> Optional[list[Movement]]:
        return self.repository.search(type, specie_name)
