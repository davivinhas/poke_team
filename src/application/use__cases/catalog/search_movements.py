from typing import Optional

from src.application.ports.movements_gateway import MovementsGateway
from src.application.ports.movements_port import MovementsRepositoryPort
from src.domain.entities.movement import Movement
from src.domain.value_objects.types import Types


class SearchMovementsUseCase:
    """
    Can search movements by type or specie.
    """

    def __init__(
        self,
        repository: MovementsRepositoryPort,
        gateway: MovementsGateway,
    ) -> None:
        self._repository = repository
        self._gateway = gateway

    async def execute(
        self, type: Optional[Types] = None, specie_name: Optional[str] = None
    ) -> list[Movement]:
        movements = await self._gateway.search(type, specie_name) or []
        for movement in movements:
            self._repository.save(movement)
        return movements
