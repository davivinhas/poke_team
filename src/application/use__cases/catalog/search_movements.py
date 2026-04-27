from typing import Optional

from src.application.ports.movements_gateway import MovementsGateway
from src.application.ports.movements_port import MovementsRepositoryPort
from src.application.ports.pokemon_species_gateway import PokemonSpeciesGateway
from src.application.ports.pokemon_species_port import PokemonSpeciesRepositoryPort
from src.domain.entities.movement import Movement
from src.domain.entities.pokemon_specie import PokemonSpecie
from src.domain.value_objects.types import Types


class SearchMovementsUseCase:
    """
    Can search movements by type or specie.
    """

    def __init__(
        self,
        repository: MovementsRepositoryPort,
        gateway: MovementsGateway,
        pokemon_species_repository: PokemonSpeciesRepositoryPort,
        pokemon_species_gateway: PokemonSpeciesGateway,
    ) -> None:
        self._repository = repository
        self._gateway = gateway
        self._pokemon_species_repository = pokemon_species_repository
        self._pokemon_species_gateway = pokemon_species_gateway

    async def execute(
        self, type: Optional[Types] = None, specie_name: Optional[str] = None
    ) -> list[Movement]:
        normalized_specie_name = specie_name.strip().lower() if specie_name else None
        if type is None and normalized_specie_name is None:
            raise ValueError("At least one filter must be informed")

        specie = await self._ensure_local_specie(normalized_specie_name)
        specie_id = specie.id if specie is not None else None

        cached_movements = self._repository.search(type=type, specie_id=specie_id)
        if cached_movements:
            return cached_movements

        movements = await self._gateway.search(type, normalized_specie_name) or []
        for movement in movements:
            self._repository.save(movement)
            if specie_id is not None:
                self._repository.link_to_specie(
                    specie_id=specie_id,
                    movement_name=movement.name,
                )
        return movements

    async def _ensure_local_specie(
        self,
        specie_name: Optional[str],
    ) -> Optional[PokemonSpecie]:
        if specie_name is None:
            return None

        cached_page = self._pokemon_species_repository.search(name=specie_name, limit=1)
        exact_cached_matches = [
            specie
            for specie in cached_page.items
            if specie.name.strip().lower() == specie_name
        ]
        if exact_cached_matches:
            return exact_cached_matches[0]

        gateway_page = await self._pokemon_species_gateway.search(
            name=specie_name, limit=1
        )
        if not gateway_page.items:
            return None

        specie = gateway_page.items[0]
        self._pokemon_species_repository.save(specie)
        return specie
