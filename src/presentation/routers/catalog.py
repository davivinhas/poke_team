from typing import Annotated

import httpx
from fastapi import APIRouter, HTTPException, Query

from src.application.use__cases.catalog.search_movements import SearchMovementsUseCase
from src.application.use__cases.catalog.search_pokemon_species import (
    SearchPokemonSpeciesUseCase,
)
from src.domain.value_objects.types import Types
from src.presentation.schemas.catalog import (
    BaseStatsResponse,
    CursorPagePokemonSpeciesResponse,
    MovementResponse,
    PokemonSpecieResponse,
)


def create_catalog_router(
    pokemon_species_use_case: SearchPokemonSpeciesUseCase,
    movements_use_case: SearchMovementsUseCase,
) -> APIRouter:
    router = APIRouter(tags=["catalog"])

    def _parse_optional_type(raw_type: str | Types | None) -> Types | None:
        if raw_type is None:
            return None

        if isinstance(raw_type, Types):
            return raw_type

        normalized_type = raw_type.strip().lower()
        if normalized_type == "":
            return None

        try:
            return Types(normalized_type)
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid movement type: {raw_type}",
            ) from exc

    @router.get(
        "/pokemon-species",
        response_model=CursorPagePokemonSpeciesResponse,
    )
    async def search_pokemon_species(
        name: str | None = None,
        types: Annotated[list[Types] | None, Query()] = None,
        limit: Annotated[int, Query(gt=0)] = 10,
        cursor: str | None = None,
    ) -> CursorPagePokemonSpeciesResponse:
        try:
            page = await pokemon_species_use_case.execute(
                name=name,
                types=types,
                limit=limit,
                cursor=cursor,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=502,
                detail="Failed to fetch pokemon species from PokeAPI",
            ) from exc

        return CursorPagePokemonSpeciesResponse(
            items=[
                PokemonSpecieResponse(
                    id=specie.id,
                    external_id=specie.external_id,
                    name=specie.name,
                    base_stats=BaseStatsResponse(
                        hp=specie.base_stats.hp,
                        attack=specie.base_stats.attack,
                        defense=specie.base_stats.defense,
                        special_attack=specie.base_stats.special_attack,
                        special_defense=specie.base_stats.special_defense,
                        speed=specie.base_stats.speed,
                    ),
                    types=[pokemon_type.value for pokemon_type in specie.types],
                )
                for specie in page.items
            ],
            next_cursor=page.next_cursor,
        )

    @router.get(
        "/movements",
        response_model=list[MovementResponse],
    )
    async def search_movements(
        type: str | None = None,
        specie_name: str | None = None,
    ) -> list[MovementResponse]:
        try:
            movements = await movements_use_case.execute(
                type=_parse_optional_type(type),
                specie_name=specie_name,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=502,
                detail="Failed to fetch movements from PokeAPI",
            ) from exc

        return [
            MovementResponse(
                name=movement.name,
                power=movement.power,
                accuracy=movement.accuracy,
                description=movement.description,
                pp=movement.pp,
                type=movement.type.value,
            )
            for movement in movements
        ]

    return router
