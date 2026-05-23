from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends

from src.application.ports.movements_gateway import MovementsGateway
from src.application.ports.movements_port import MovementsRepositoryPort
from src.application.ports.pokemon_species_gateway import PokemonSpeciesGateway
from src.application.ports.pokemon_species_port import PokemonSpeciesRepositoryPort
from src.application.use__cases.catalog.search_movements import SearchMovementsUseCase
from src.application.use__cases.catalog.search_pokemon_species import (
    SearchPokemonSpeciesUseCase,
)
from src.infrastructure.pokeapi import (
    PokeApiMovementsGateway,
    PokeApiPokemonSpeciesGateway,
)
from src.infrastructure.repositories import (
    SQLAlchemyMovementsRepository,
    SQLAlchemyPokemonSpeciesRepository,
)


def get_pokemon_species_repository() -> PokemonSpeciesRepositoryPort:
    return SQLAlchemyPokemonSpeciesRepository()


def get_movements_repository() -> MovementsRepositoryPort:
    return SQLAlchemyMovementsRepository()


async def get_pokemon_species_gateway() -> AsyncGenerator[PokemonSpeciesGateway, None]:
    gateway = PokeApiPokemonSpeciesGateway()
    try:
        yield gateway
    finally:
        if hasattr(gateway, "aclose"):
            await gateway.aclose()


async def get_movements_gateway() -> AsyncGenerator[MovementsGateway, None]:
    gateway = PokeApiMovementsGateway()
    try:
        yield gateway
    finally:
        if hasattr(gateway, "aclose"):
            await gateway.aclose()


def get_search_pokemon_species_use_case(
    repository: Annotated[
        PokemonSpeciesRepositoryPort,
        Depends(get_pokemon_species_repository),
    ],
    gateway: Annotated[
        PokemonSpeciesGateway,
        Depends(get_pokemon_species_gateway),
    ],
) -> SearchPokemonSpeciesUseCase:
    return SearchPokemonSpeciesUseCase(
        repository=repository,
        gateway=gateway,
    )


def get_search_movements_use_case(
    repository: Annotated[
        MovementsRepositoryPort,
        Depends(get_movements_repository),
    ],
    gateway: Annotated[
        MovementsGateway,
        Depends(get_movements_gateway),
    ],
    pokemon_species_repository: Annotated[
        PokemonSpeciesRepositoryPort,
        Depends(get_pokemon_species_repository),
    ],
    pokemon_species_gateway: Annotated[
        PokemonSpeciesGateway,
        Depends(get_pokemon_species_gateway),
    ],
) -> SearchMovementsUseCase:
    return SearchMovementsUseCase(
        repository=repository,
        gateway=gateway,
        pokemon_species_repository=pokemon_species_repository,
        pokemon_species_gateway=pokemon_species_gateway,
    )
