import asyncio

import httpx
import pytest

from src.application.pagination.cursor_page import CursorPage
from src.domain.value_objects.types import Types
from src.infraestructure.pokeapi.pokemon_species_gateway import (
    PokeApiPokemonSpeciesGateway,
)


def _pokemon_payload(
    pokemon_id: int,
    name: str,
    types: list[str],
    hp: int = 35,
    attack: int = 55,
    defense: int = 40,
    special_attack: int = 50,
    special_defense: int = 50,
    speed: int = 90,
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
            {"base_stat": hp, "stat": {"name": "hp"}},
            {"base_stat": attack, "stat": {"name": "attack"}},
            {"base_stat": defense, "stat": {"name": "defense"}},
            {"base_stat": special_attack, "stat": {"name": "special-attack"}},
            {"base_stat": special_defense, "stat": {"name": "special-defense"}},
            {"base_stat": speed, "stat": {"name": "speed"}},
        ],
    }


def _list_payload(*results: dict, next_url: str | None = None) -> dict:
    return {
        "count": len(results),
        "next": next_url,
        "previous": None,
        "results": list(results),
    }


def _build_gateway_with_responses(
    responses: dict[str, dict],
    requested_urls: list[str],
) -> PokeApiPokemonSpeciesGateway:
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

    return PokeApiPokemonSpeciesGateway(client=FakeAsyncClient())


def test_search_without_filters_hydrates_pokemon_page_from_list_endpoint():
    requested_urls: list[str] = []
    responses = {
        "https://pokeapi.co/api/v2/pokemon/?limit=2&offset=0": _list_payload(
            {
                "name": "pikachu",
                "url": "https://pokeapi.co/api/v2/pokemon/25/",
            },
            {
                "name": "squirtle",
                "url": "https://pokeapi.co/api/v2/pokemon/7/",
            },
            next_url="https://pokeapi.co/api/v2/pokemon/?limit=2&offset=2",
        ),
        "https://pokeapi.co/api/v2/pokemon/25/": _pokemon_payload(
            25,
            "pikachu",
            ["electric"],
        ),
        "https://pokeapi.co/api/v2/pokemon/7/": _pokemon_payload(
            7,
            "squirtle",
            ["water"],
        ),
    }
    gateway = _build_gateway_with_responses(responses, requested_urls)

    result = asyncio.run(gateway.search(limit=2))

    assert isinstance(result, CursorPage)
    assert [specie.id for specie in result.items] == [None, None]
    assert [specie.name for specie in result.items] == ["pikachu", "squirtle"]
    assert [specie.external_id for specie in result.items] == [25, 7]
    assert [specie.types for specie in result.items] == [
        (Types.ELECTRIC,),
        (Types.WATER,),
    ]
    assert result.next_cursor == "2"
    assert requested_urls[0] == "https://pokeapi.co/api/v2/pokemon/?limit=2&offset=0"
    assert set(requested_urls[1:]) == {
        "https://pokeapi.co/api/v2/pokemon/25/",
        "https://pokeapi.co/api/v2/pokemon/7/",
    }


def test_search_by_exact_name_returns_single_result_page():
    requested_urls: list[str] = []
    responses = {
        "https://pokeapi.co/api/v2/pokemon/pikachu/": _pokemon_payload(
            25,
            "pikachu",
            ["electric"],
        )
    }
    gateway = _build_gateway_with_responses(responses, requested_urls)

    result = asyncio.run(gateway.search(name="pikachu"))

    assert [specie.id for specie in result.items] == [None]
    assert [specie.name for specie in result.items] == ["pikachu"]
    assert result.next_cursor is None
    assert requested_urls == ["https://pokeapi.co/api/v2/pokemon/pikachu/"]


def test_search_by_type_uses_type_endpoint_then_hydrates_selected_page():
    requested_urls: list[str] = []
    responses = {
        "https://pokeapi.co/api/v2/type/electric/": {
            "pokemon": [
                {
                    "pokemon": {
                        "name": "pikachu",
                        "url": "https://pokeapi.co/api/v2/pokemon/25/",
                    }
                },
                {
                    "pokemon": {
                        "name": "raichu",
                        "url": "https://pokeapi.co/api/v2/pokemon/26/",
                    }
                },
                {
                    "pokemon": {
                        "name": "magnemite",
                        "url": "https://pokeapi.co/api/v2/pokemon/81/",
                    }
                },
            ]
        },
        "https://pokeapi.co/api/v2/pokemon/26/": _pokemon_payload(
            26,
            "raichu",
            ["electric"],
        ),
        "https://pokeapi.co/api/v2/pokemon/81/": _pokemon_payload(
            81,
            "magnemite",
            ["electric"],
        ),
    }
    gateway = _build_gateway_with_responses(responses, requested_urls)

    result = asyncio.run(gateway.search(types=[Types.ELECTRIC], limit=2, cursor="1"))

    assert [specie.name for specie in result.items] == ["raichu", "magnemite"]
    assert result.next_cursor is None
    assert requested_urls[0] == "https://pokeapi.co/api/v2/type/electric/"
    assert set(requested_urls[1:]) == {
        "https://pokeapi.co/api/v2/pokemon/26/",
        "https://pokeapi.co/api/v2/pokemon/81/",
    }


def test_get_by_id_returns_none_when_pokeapi_returns_404():
    class FakeAsyncClient:
        async def get(self, url: str):
            return httpx.Response(404, request=httpx.Request("GET", url))

        async def aclose(self) -> None:
            return None

    gateway = PokeApiPokemonSpeciesGateway(client=FakeAsyncClient())

    assert asyncio.run(gateway.get_by_id(999999)) is None


def test_search_rejects_invalid_cursor():
    class FakeAsyncClient:
        async def get(self, url: str):
            return httpx.Response(
                200,
                json={},
                request=httpx.Request("GET", url),
            )

        async def aclose(self) -> None:
            return None

    gateway = PokeApiPokemonSpeciesGateway(client=FakeAsyncClient())

    with pytest.raises(ValueError, match="Cursor must be a numeric offset"):
        asyncio.run(gateway.search(cursor="next-page"))
