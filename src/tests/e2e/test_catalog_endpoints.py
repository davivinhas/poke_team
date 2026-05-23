import os

import httpx
from fastapi.testclient import TestClient
from src.application.use_cases.catalog.search_movements import SearchMovementsUseCase
from src.application.use_cases.catalog.search_pokemon_species import (
    SearchPokemonSpeciesUseCase,
)

from src.domain.entities.pokemon_specie import PokemonSpecie
from src.domain.value_objects.base_stats import BaseStats
from src.domain.value_objects.types import Types
from src.infrastructure.pokeapi.movements_gateway import PokeApiMovementsGateway
from src.infrastructure.pokeapi.pokemon_species_gateway import (
    PokeApiPokemonSpeciesGateway,
)
from src.infrastructure.repositories.in_memory_catalog_repositories import (
    InMemoryMovementsRepository,
    InMemoryPokemonSpeciesRepository,
)
from src.presentation.dependencies import (
    get_search_movements_use_case,
    get_search_pokemon_species_use_case,
)
from src.presentation.schemas.catalog import CursorPagePokemonSpeciesResponse

os.environ["EXTERNAL_API_URL"] = "https://example.test/api/v2"

from src.main import create_app

API_URL = os.environ["EXTERNAL_API_URL"]


def _build_test_app(
    pokemon_species_repository: InMemoryPokemonSpeciesRepository,
    pokemon_species_gateway: PokeApiPokemonSpeciesGateway,
    movements_repository: InMemoryMovementsRepository,
    movements_gateway: PokeApiMovementsGateway,
):
    app = create_app()

    def _pokemon_species_use_case_override() -> SearchPokemonSpeciesUseCase:
        return SearchPokemonSpeciesUseCase(
            repository=pokemon_species_repository,
            gateway=pokemon_species_gateway,
        )

    def _movements_use_case_override() -> SearchMovementsUseCase:
        return SearchMovementsUseCase(
            repository=movements_repository,
            gateway=movements_gateway,
            pokemon_species_repository=pokemon_species_repository,
            pokemon_species_gateway=pokemon_species_gateway,
        )

    app.dependency_overrides[get_search_pokemon_species_use_case] = (
        _pokemon_species_use_case_override
    )
    app.dependency_overrides[get_search_movements_use_case] = (
        _movements_use_case_override
    )
    return app


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

    app = _build_test_app(
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
    with TestClient(app) as client:
        response = client.get("/pokemon-species", params={"limit": 1})

    assert response.status_code == 200
    payload = response.json()
    assert CursorPagePokemonSpeciesResponse.model_validate(payload).model_dump() == {
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

    app = _build_test_app(
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
    with TestClient(app) as client:
        response = client.get("/pokemon-species", params={"name": "charizard"})

    assert response.status_code == 200
    assert response.json() == {
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

    app = _build_test_app(
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
    with TestClient(app) as client:
        response = client.get("/pokemon-species", params={"limit": 10})

    assert response.status_code == 502
    assert response.json() == {"detail": "Failed to fetch pokemon species from PokeAPI"}


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

    app = _build_test_app(
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
    with TestClient(app) as client:
        response = client.get("/movements", params={"type": Types.ELECTRIC.value})

    assert response.status_code == 200
    assert response.json() == [
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
    app = _build_test_app(
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
    with TestClient(app) as client:
        response = client.get("/movements")

    assert response.status_code == 400
    assert response.json() == {"detail": "At least one filter must be informed"}


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

    app = _build_test_app(
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
    with TestClient(app) as client:
        response = client.get(
            "/movements",
            params={
                "type": "",
                "specie_name": "pikachu",
            },
        )

    assert response.status_code == 200
    assert response.json() == [
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

    app = _build_test_app(
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
    with TestClient(app) as client:
        response = client.get("/movements", params={"specie_name": "pikachu"})

    assert response.status_code == 502
    assert response.json() == {"detail": "Failed to fetch movements from PokeAPI"}
