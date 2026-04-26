from typing import List, Optional

from src.application.ports.pokemon_species_gateway import PokemonSpeciesGateway
from src.application.ports.pokemon_species_port import PokemonSpeciesRepositoryPort
from src.domain.value_objects.types import Types


class GetPokemonSpeciesUseCase:
    """
    Can search pokemon species by name or types.
    Supports pagination cursor-based
    """

    def __init__(
        self,
        repository: PokemonSpeciesRepositoryPort,
        external_gateway: PokemonSpeciesGateway,
    ):
        self.repository = repository
        self.external_gateway = external_gateway

    def execute(
        self,
        name: Optional[str] = None,
        types: Optional[List[Types]] = None,
        limit: int = 10,
        cursor: Optional[str] = None,
    ):
        # When cursor is None, it's the first page, the limit is by default 10
        return self.repository.search(name, types, limit, cursor)
