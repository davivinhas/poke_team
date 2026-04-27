from typing import List, Optional

from src.application.pagination.cursor_page import CursorPage
from src.application.ports.pokemon_species_gateway import PokemonSpeciesGateway
from src.application.ports.pokemon_species_port import PokemonSpeciesRepositoryPort
from src.domain.entities.pokemon_specie import PokemonSpecie
from src.domain.value_objects.types import Types


class SearchPokemonSpeciesUseCase:
    """
    Uses the local repository for exact-name lookups when cached and delegates
    list-style searches to the external catalog, persisting fetched entries.
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
        normalized_name = name.strip().lower() if name and name.strip() else None

        if normalized_name is not None:
            cached_page = self._repository.search(
                name=normalized_name,
                types=types,
                limit=limit,
                cursor=cursor,
            )
            cached_matches = [
                specie
                for specie in cached_page.items
                if specie.name.strip().lower() == normalized_name
            ]
            if cached_matches or (cursor not in (None, "", "0")):
                return CursorPage(items=cached_matches, next_cursor=None)

        page = await self._gateway.search(
            name=name,
            types=types,
            limit=limit,
            cursor=cursor,
        )

        for specie in page.items:
            self._repository.save(specie)

        return page
