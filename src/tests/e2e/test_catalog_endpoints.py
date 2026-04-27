import asyncio
import os

import httpx
import pytest
from fastapi import HTTPException
from fastapi.routing import APIRoute

from src.domain.entities.pokemon_specie import PokemonSpecie
from src.domain.value_objects.base_stats import BaseStats
from src.domain.value_objects.types import Types
from src.infraestructure.pokeapi.movements_gateway import PokeApiMovementsGateway
from src.infraestructure.pokeapi.pokemon_species_gateway import (
    PokeApiPokemonSpeciesGateway,
)
from src.infraestructure.repositories.in_memory_catalog_repositories import (
    InMemoryMovementsRepository,
    InMemoryPokemonSpeciesRepository,
)
from src.presentation.schemas.catalog import CursorPagePokemonSpeciesResponse

os.environ["EXTERNAL_API_URL"] = "https://example.test/api/v2"

from src.main import create_app


def _get_route_endpoint(app, path: str):
    for route in app.router.routes:
        if isinstance(route, APIRoute) and route.path == path:
            return route.endpoint
    raise AssertionError(f"Route {path} not found")


API_URL = os.environ["EXTERNAL_API_URL"]


class FakeAsyncClient:
    def __init__(self, responses=None, status_codes=None, exception=None):
        self._responses = responses or {}
        self._status_codes = status_codes or {}
        self._exception = exception

    async def get(self, url: str):
        if self._exception is not None:
            raise self._exception

        return httpx.Response(
            self._status_codes.get(url, 200),
            json=self._responses.get(url, {}),
            request=httpx.Request("GET", url),
        )

    async def aclose(self) -> None:
        return None


def _pokemon_payload(
    pokemon_id: int,
    name: str,
    types: list[str],
) -> dict:
    return {
        "id": pokemon_id,
        "name": name,
        "types": [
            {
                "slot": index,
                "type": {"name": pokemon_type},
            }
            for index, pokemon_type in enumerate(types, start=1)
        ],
        "stats": [
            {"base_stat": 35, "stat": {"name": "hp"}},
            {"base_stat": 55, "stat": {"name": "attack"}},
            {"base_stat": 40, "stat": {"name": "defense"}},
            {"base_stat": 50, "stat": {"name": "special-attack"}},
            {"base_stat": 50, "stat": {"name": "special-defense"}},
            {"base_stat": 90, "stat": {"name": "speed"}},
        ],
    }


def _move_payload(
    name: str,
    move_type: str,
) -> dict:
    return {
        "name": name,
        "power": 90,
        "accuracy": 100,
        "pp": 15,
        "type": {"name": move_type},
        "effect_entries": [
            {
                "short_effect": "A strong electric blast crashes down on the target.",
                "effect": "A strong electric blast crashes down on the target.",
                "language": {"name": "en"},
            }
        ],
    }


def _stored_specie(
    external_id: int,
    name: str,
    types: tuple[Types, ...],
    base_stats: BaseStats,
) -> PokemonSpecie:
    return PokemonSpecie(
        id=None,
        external_id=external_id,
        name=name,
        base_stats=base_stats,
        types=types,
    )


def test_search_pokemon_species_endpoint_returns_paginated_response():
    responses = {
        f"{API_URL}/pokemon/?limit=1&offset=0": {
            "count": 1,
            "next": None,
            "previous": None,
            "results": [
                {
                    "name": "pikachu",
                    "url": f"{API_URL}/pokemon/25/",
                }
            ],
        },
        f"{API_URL}/pokemon/25/": _pokemon_payload(
            25,
            "pikachu",
            ["electric"],
        ),
    }

    app = create_app(
        pokemon_species_repository=InMemoryPokemonSpeciesRepository(),
        pokemon_species_gateway=PokeApiPokemonSpeciesGateway(
            base_url=API_URL, client=FakeAsyncClient(responses=responses)
        ),
        movements_repository=InMemoryMovementsRepository(),
        movements_gateway=PokeApiMovementsGateway(
            base_url=API_URL,
            client=FakeAsyncClient(),
        ),
    )
    endpoint = _get_route_endpoint(app, "/pokemon-species")

    response = asyncio.run(endpoint(limit=1))

    assert isinstance(response, CursorPagePokemonSpeciesResponse)
    assert response.model_dump() == {
        "items": [
            {
                "id": 1,
                "external_id": 25,
                "name": "pikachu",
                "base_stats": {
                    "hp": 35,
                    "attack": 55,
                    "defense": 40,
                    "special_attack": 50,
                    "special_defense": 50,
                    "speed": 90,
                },
                "types": ["electric"],
            }
        ],
        "next_cursor": None,
    }


def test_search_pokemon_species_endpoint_uses_cached_name_match_before_gateway():
    repository = InMemoryPokemonSpeciesRepository()
    repository.save(
        _stored_specie(
            external_id=6,
            name="charizard",
            base_stats=BaseStats(78, 84, 78, 109, 85, 100),
            types=(Types.FIRE, Types.FLYING),
        )
    )
    request = httpx.Request("GET", f"{API_URL}/pokemon/charizard/")
    response = httpx.Response(502, request=request)

    app = create_app(
        pokemon_species_repository=repository,
        pokemon_species_gateway=PokeApiPokemonSpeciesGateway(
            base_url=API_URL,
            client=FakeAsyncClient(
                exception=httpx.HTTPStatusError(
                    "Bad Gateway",
                    request=request,
                    response=response,
                )
            ),
        ),
        movements_repository=InMemoryMovementsRepository(),
        movements_gateway=PokeApiMovementsGateway(
            base_url=API_URL,
            client=FakeAsyncClient(),
        ),
    )
    endpoint = _get_route_endpoint(app, "/pokemon-species")

    result = asyncio.run(endpoint(name="charizard"))

    assert result.model_dump() == {
        "items": [
            {
                "id": 1,
                "external_id": 6,
                "name": "charizard",
                "base_stats": {
                    "hp": 78,
                    "attack": 84,
                    "defense": 78,
                    "special_attack": 109,
                    "special_defense": 85,
                    "speed": 100,
                },
                "types": ["fire", "flying"],
            }
        ],
        "next_cursor": None,
    }


def test_search_pokemon_species_endpoint_returns_502_for_listing_when_gateway_fails():
    request = httpx.Request("GET", f"{API_URL}/pokemon/?limit=10&offset=0")
    response = httpx.Response(502, request=request)

    app = create_app(
        pokemon_species_repository=InMemoryPokemonSpeciesRepository(),
        pokemon_species_gateway=PokeApiPokemonSpeciesGateway(
            base_url=API_URL,
            client=FakeAsyncClient(
                exception=httpx.HTTPStatusError(
                    "Bad Gateway",
                    request=request,
                    response=response,
                )
            ),
        ),
        movements_repository=InMemoryMovementsRepository(),
        movements_gateway=PokeApiMovementsGateway(
            base_url=API_URL,
            client=FakeAsyncClient(),
        ),
    )
    endpoint = _get_route_endpoint(app, "/pokemon-species")

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(endpoint(limit=10))

    assert exc_info.value.status_code == 502
    assert exc_info.value.detail == "Failed to fetch pokemon species from PokeAPI"


def test_search_movements_endpoint_returns_filtered_moves():
    responses = {
        f"{API_URL}/type/electric/": {
            "moves": [
                {
                    "name": "thunderbolt",
                    "url": f"{API_URL}/move/85/",
                }
            ]
        },
        f"{API_URL}/move/85/": _move_payload(
            "thunderbolt",
            "electric",
        ),
    }

    app = create_app(
        pokemon_species_repository=InMemoryPokemonSpeciesRepository(),
        pokemon_species_gateway=PokeApiPokemonSpeciesGateway(
            base_url=API_URL,
            client=FakeAsyncClient(),
        ),
        movements_repository=InMemoryMovementsRepository(),
        movements_gateway=PokeApiMovementsGateway(
            base_url=API_URL, client=FakeAsyncClient(responses=responses)
        ),
    )
    endpoint = _get_route_endpoint(app, "/movements")

    response = asyncio.run(endpoint(type=Types.ELECTRIC))

    assert [movement.model_dump() for movement in response] == [
        {
            "name": "thunderbolt",
            "power": 90,
            "accuracy": 100,
            "description": "A strong electric blast crashes down on the target.",
            "pp": 15,
            "type": "electric",
        }
    ]


def test_search_movements_endpoint_returns_400_when_no_filters_are_informed():
    app = create_app(
        pokemon_species_repository=InMemoryPokemonSpeciesRepository(),
        pokemon_species_gateway=PokeApiPokemonSpeciesGateway(
            base_url=API_URL,
            client=FakeAsyncClient(),
        ),
        movements_repository=InMemoryMovementsRepository(),
        movements_gateway=PokeApiMovementsGateway(
            base_url=API_URL,
            client=FakeAsyncClient(),
        ),
    )
    endpoint = _get_route_endpoint(app, "/movements")

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(endpoint())

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "At least one filter must be informed"


def test_search_movements_endpoint_accepts_blank_type_when_specie_is_informed():
    species_responses = {
        f"{API_URL}/pokemon/pikachu/": _pokemon_payload(
            25,
            "pikachu",
            ["electric"],
        )
    }
    responses = {
        f"{API_URL}/pokemon/pikachu/": {
            "moves": [
                {
                    "move": {
                        "name": "thunderbolt",
                        "url": f"{API_URL}/move/85/",
                    }
                }
            ]
        },
        f"{API_URL}/move/85/": _move_payload(
            "thunderbolt",
            "electric",
        ),
    }

    app = create_app(
        pokemon_species_repository=InMemoryPokemonSpeciesRepository(),
        pokemon_species_gateway=PokeApiPokemonSpeciesGateway(
            base_url=API_URL,
            client=FakeAsyncClient(responses=species_responses),
        ),
        movements_repository=InMemoryMovementsRepository(),
        movements_gateway=PokeApiMovementsGateway(
            base_url=API_URL, client=FakeAsyncClient(responses=responses)
        ),
    )
    endpoint = _get_route_endpoint(app, "/movements")

    response = asyncio.run(endpoint(type="", specie_name="pikachu"))

    assert [movement.model_dump() for movement in response] == [
        {
            "name": "thunderbolt",
            "power": 90,
            "accuracy": 100,
            "description": "A strong electric blast crashes down on the target.",
            "pp": 15,
            "type": "electric",
        }
    ]


def test_search_movements_endpoint_returns_502_when_gateway_fails():
    request = httpx.Request("GET", f"{API_URL}/pokemon/pikachu/")
    response = httpx.Response(403, request=request)
    species_responses = {
        f"{API_URL}/pokemon/pikachu/": _pokemon_payload(
            25,
            "pikachu",
            ["electric"],
        )
    }

    app = create_app(
        pokemon_species_repository=InMemoryPokemonSpeciesRepository(),
        pokemon_species_gateway=PokeApiPokemonSpeciesGateway(
            base_url=API_URL,
            client=FakeAsyncClient(responses=species_responses),
        ),
        movements_repository=InMemoryMovementsRepository(),
        movements_gateway=PokeApiMovementsGateway(
            base_url=API_URL,
            client=FakeAsyncClient(
                exception=httpx.HTTPStatusError(
                    "Forbidden",
                    request=request,
                    response=response,
                )
            ),
        ),
    )
    endpoint = _get_route_endpoint(app, "/movements")

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(endpoint(specie_name="pikachu"))

    assert exc_info.value.status_code == 502
    assert exc_info.value.detail == "Failed to fetch movements from PokeAPI"
