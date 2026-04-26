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
    )


def test_search_pokemon_species_uses_gateway_and_persists_results():
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
            name="pikachu",
            types=[Types.ELECTRIC],
            limit=5,
            cursor="cursor-1",
        )
    )

    assert result is expected_page
    gateway.search.assert_awaited_once_with(
        name="pikachu",
        types=[Types.ELECTRIC],
        limit=5,
        cursor="cursor-1",
    )
    repository.save.assert_has_calls([call(pikachu), call(raichu)])


def test_search_pokemon_species_returns_empty_page_without_persisting():
    repository = Mock()
    gateway = AsyncMock()
    expected_page = CursorPage(items=[], next_cursor=None)
    gateway.search.return_value = expected_page

    use_case = SearchPokemonSpeciesUseCase(repository, gateway)

    result = asyncio.run(use_case.execute(name="missing"))

    assert result is expected_page
    gateway.search.assert_awaited_once_with(
        name="missing",
        types=None,
        limit=10,
        cursor=None,
    )
    repository.save.assert_not_called()
