import asyncio
from unittest.mock import AsyncMock, Mock, call

from src.application.pagination.cursor_page import CursorPage
from src.application.use__cases.catalog.search_pokemon_species import (
    SearchPokemonSpeciesUseCase,
)
from src.domain.entities.pokemon_specie import PokemonSpecie
from src.domain.value_objects.base_stats import BaseStats
from src.domain.value_objects.types import Types


def _build_specie(id: int, external_id: int, name: str) -> PokemonSpecie:
    return PokemonSpecie(
        id=id,
        external_id=external_id,
        name=name,
        base_stats=BaseStats(35, 55, 40, 50, 50, 90),
        types=(Types.ELECTRIC,),
        front_default_sprite=f"https://example.com/{name}.png",
    )


def test_search_pokemon_species_listing_uses_gateway_and_persists_results():
    repository = Mock()
    gateway = AsyncMock()
    pikachu = _build_specie(1, 25, "pikachu")
    raichu = _build_specie(2, 26, "raichu")
    expected_page = CursorPage(
        items=[pikachu, raichu],
        next_cursor="cursor-2",
    )
    gateway.search.return_value = expected_page

    use_case = SearchPokemonSpeciesUseCase(repository, gateway)

    result = asyncio.run(
        use_case.execute(
            types=[Types.ELECTRIC],
            limit=5,
            cursor="1",
        )
    )

    assert result is expected_page
    gateway.search.assert_awaited_once_with(
        name=None,
        types=[Types.ELECTRIC],
        limit=5,
        cursor="1",
    )
    repository.search.assert_not_called()
    repository.save.assert_has_calls([call(pikachu), call(raichu)])


def test_search_pokemon_species_returns_cached_exact_name_without_using_gateway():
    repository = Mock()
    gateway = AsyncMock()
    pikachu = _build_specie(1, 25, "pikachu")
    repository.search.return_value = CursorPage(items=[pikachu], next_cursor=None)

    use_case = SearchPokemonSpeciesUseCase(repository, gateway)

    result = asyncio.run(use_case.execute(name=" Pikachu "))

    assert result.items == [pikachu]
    assert result.next_cursor is None
    repository.search.assert_called_once_with(
        name="pikachu",
        types=None,
        limit=10,
        cursor=None,
    )
    gateway.search.assert_not_awaited()
    repository.save.assert_not_called()


def test_search_pokemon_species_falls_back_to_gateway_when_name_is_not_cached():
    repository = Mock()
    gateway = AsyncMock()
    expected_page = CursorPage(
        items=[_build_specie(1, 6, "charizard")], next_cursor=None
    )
    repository.search.return_value = CursorPage(items=[], next_cursor=None)
    gateway.search.return_value = expected_page

    use_case = SearchPokemonSpeciesUseCase(repository, gateway)

    result = asyncio.run(use_case.execute(name="charizard"))

    assert result is expected_page
    repository.search.assert_called_once_with(
        name="charizard",
        types=None,
        limit=10,
        cursor=None,
    )
    gateway.search.assert_awaited_once_with(
        name="charizard",
        types=None,
        limit=10,
        cursor=None,
    )
    repository.save.assert_called_once_with(expected_page.items[0])
