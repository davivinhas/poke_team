from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.application.ports.movements_gateway import MovementsGateway
from src.application.ports.movements_port import MovementsRepositoryPort
from src.application.ports.pokemon_species_gateway import PokemonSpeciesGateway
from src.application.ports.pokemon_species_port import PokemonSpeciesRepositoryPort
from src.application.use__cases.catalog.search_movements import SearchMovementsUseCase
from src.application.use__cases.catalog.search_pokemon_species import (
    SearchPokemonSpeciesUseCase,
)
from src.infraestructure.pokeapi import (
    PokeApiMovementsGateway,
    PokeApiPokemonSpeciesGateway,
)
from src.infraestructure.repositories import (
    InMemoryMovementsRepository,
    InMemoryPokemonSpeciesRepository,
)
from src.presentation.routers import create_catalog_router


def create_app(
    pokemon_species_repository: PokemonSpeciesRepositoryPort | None = None,
    pokemon_species_gateway: PokemonSpeciesGateway | None = None,
    movements_repository: MovementsRepositoryPort | None = None,
    movements_gateway: MovementsGateway | None = None,
) -> FastAPI:
    pokemon_species_repository = (
        pokemon_species_repository or InMemoryPokemonSpeciesRepository()
    )
    pokemon_species_gateway = pokemon_species_gateway or PokeApiPokemonSpeciesGateway()
    movements_repository = movements_repository or InMemoryMovementsRepository()
    movements_gateway = movements_gateway or PokeApiMovementsGateway()

    pokemon_species_use_case = SearchPokemonSpeciesUseCase(
        repository=pokemon_species_repository,
        gateway=pokemon_species_gateway,
    )
    movements_use_case = SearchMovementsUseCase(
        repository=movements_repository,
        gateway=movements_gateway,
    )

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        try:
            yield
        finally:
            if hasattr(pokemon_species_gateway, "aclose"):
                await pokemon_species_gateway.aclose()
            if hasattr(movements_gateway, "aclose"):
                await movements_gateway.aclose()

    app = FastAPI(lifespan=lifespan)

    @app.get("/")
    async def read_root() -> dict[str, str]:
        return {"message": "API online"}

    app.include_router(
        create_catalog_router(
            pokemon_species_use_case=pokemon_species_use_case,
            movements_use_case=movements_use_case,
        )
    )
    return app


app = create_app()
