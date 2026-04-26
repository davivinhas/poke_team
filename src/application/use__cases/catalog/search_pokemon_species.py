from typing import List, Optional

from src.application.pagination.cursor_page import CursorPage
from src.application.ports.pokemon_species_gateway import PokemonSpeciesGateway
from src.application.ports.pokemon_species_port import PokemonSpeciesRepositoryPort
from src.domain.entities.pokemon_specie import PokemonSpecie
from src.domain.value_objects.types import Types


class SearchPokemonSpeciesUseCase:
    """
    Searches pokemon species using the external catalog as the paginated source
    of truth, while persisting returned entries locally as durable cache.
    """

    def __init__(
        self,
        repository: PokemonSpeciesRepositoryPort,
        gateway: PokemonSpeciesGateway,
    ) -> None:
        self._repository = repository
        self._gateway = gateway

    async def execute(
        self,
        name: Optional[str] = None,
        types: Optional[List[Types]] = None,
        limit: int = 10,
        cursor: Optional[str] = None,
    ) -> CursorPage[PokemonSpecie]:
        page = await self._gateway.search(
            name=name,
            types=types,
            limit=limit,
            cursor=cursor,
        )

        for specie in page.items:
            self._repository.save(specie)

        return page
