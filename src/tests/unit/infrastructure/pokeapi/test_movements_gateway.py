import asyncio

import httpx
import pytest

from src.domain.value_objects.types import Types
from src.infrastructure.pokeapi.movements_gateway import PokeApiMovementsGateway

API_URL = "https://example.test/api/v2"


def _move_payload(
    name: str,
    move_type: str,
    power: int | None = 90,
    accuracy: int | None = 100,
    pp: int = 15,
    description: str = "A strong electric blast crashes down on the target.",
) -> dict:
    return {
        "name": name,
        "power": power,
        "accuracy": accuracy,
        "pp": pp,
        "type": {"name": move_type},
        "effect_entries": [
            {
                "short_effect": description,
                "effect": description,
                "language": {"name": "en"},
            }
        ],
    }


def _build_gateway_with_responses(
    responses: dict[str, dict],
    requested_urls: list[str],
) -> PokeApiMovementsGateway:
    class FakeAsyncClient:
        async def get(self, url: str):
            requested_urls.append(url)
            return httpx.Response(
                200,
                json=responses[url],
                request=httpx.Request("GET", url),
            )

        async def aclose(self) -> None:
            return None

    return PokeApiMovementsGateway(client=FakeAsyncClient())


def test_search_by_type_hydrates_moves_from_type_endpoint():
    requested_urls: list[str] = []
    responses = {
        f"{API_URL}/type/electric/": {
            "moves": [
                {
                    "name": "thunderbolt",
                    "url": f"{API_URL}/move/85/",
                },
                {
                    "name": "thunder",
                    "url": f"{API_URL}/move/87/",
                },
            ]
        },
        f"{API_URL}/move/85/": _move_payload(
            "thunderbolt",
            "electric",
        ),
        f"{API_URL}/move/87/": _move_payload(
            "thunder",
            "electric",
            power=110,
            accuracy=70,
            pp=10,
        ),
    }
    gateway = _build_gateway_with_responses(responses, requested_urls)
    gateway._base_url = API_URL

    result = asyncio.run(gateway.search(type=Types.ELECTRIC))

    assert [movement.name for movement in result] == ["thunderbolt", "thunder"]
    assert [movement.type for movement in result] == [
        Types.ELECTRIC,
        Types.ELECTRIC,
    ]
    assert requested_urls[0] == f"{API_URL}/type/electric/"
    assert set(requested_urls[1:]) == {
        f"{API_URL}/move/85/",
        f"{API_URL}/move/87/",
    }


def test_search_by_specie_hydrates_moves_from_pokemon_endpoint():
    requested_urls: list[str] = []
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
    gateway = _build_gateway_with_responses(responses, requested_urls)
    gateway._base_url = API_URL

    result = asyncio.run(gateway.search(specie_name="pikachu"))

    assert [movement.name for movement in result] == ["thunderbolt"]
    assert requested_urls == [
        f"{API_URL}/pokemon/pikachu/",
        f"{API_URL}/move/85/",
    ]


def test_search_with_type_and_specie_intersects_move_references():
    requested_urls: list[str] = []
    responses = {
        f"{API_URL}/pokemon/pikachu/": {
            "moves": [
                {
                    "move": {
                        "name": "thunderbolt",
                        "url": f"{API_URL}/move/85/",
                    }
                },
                {
                    "move": {
                        "name": "quick-attack",
                        "url": f"{API_URL}/move/98/",
                    }
                },
            ]
        },
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
    gateway = _build_gateway_with_responses(responses, requested_urls)
    gateway._base_url = API_URL

    result = asyncio.run(gateway.search(type=Types.ELECTRIC, specie_name="pikachu"))

    assert [movement.name for movement in result] == ["thunderbolt"]


def test_search_returns_empty_list_when_specie_is_not_found():
    class FakeAsyncClient:
        async def get(self, url: str):
            return httpx.Response(404, request=httpx.Request("GET", url))

        async def aclose(self) -> None:
            return None

    gateway = PokeApiMovementsGateway(base_url=API_URL, client=FakeAsyncClient())

    assert asyncio.run(gateway.search(specie_name="missing")) == []


def test_search_requires_at_least_one_filter():
    class FakeAsyncClient:
        async def get(self, url: str):
            return httpx.Response(
                200,
                json={},
                request=httpx.Request("GET", url),
            )

        async def aclose(self) -> None:
            return None

    gateway = PokeApiMovementsGateway(base_url=API_URL, client=FakeAsyncClient())

    with pytest.raises(ValueError, match="At least one filter must be informed"):
        asyncio.run(gateway.search())
