import asyncio
from unittest.mock import AsyncMock, Mock, call

import pytest

from src.application.pagination.cursor_page import CursorPage
from src.application.use__cases.catalog.search_movements import SearchMovementsUseCase
from src.domain.entities.movement import Movement
from src.domain.entities.pokemon_specie import PokemonSpecie
from src.domain.value_objects.base_stats import BaseStats
from src.domain.value_objects.types import Types


def test_search_movements_uses_gateway_and_persists_results():
    repository = Mock()
    gateway = AsyncMock()
    pokemon_species_repository = Mock()
    pokemon_species_gateway = AsyncMock()

    expected_movements = [
        Movement(
            name="thunderbolt",
            power=90,
            accuracy=100,
            description="A strong electric blast crashes down on the target.",
            pp=15,
            type=Types.ELECTRIC,
        )
    ]
    cached_specie = PokemonSpecie(
        id=1,
        external_id=25,
        name="pikachu",
        base_stats=BaseStats(35, 55, 40, 50, 50, 90),
        types=(Types.ELECTRIC,),
    )

    pokemon_species_repository.search.return_value = CursorPage(
        items=[cached_specie],
        next_cursor=None,
    )
    repository.search.return_value = []
    gateway.search.return_value = expected_movements

    use_case = SearchMovementsUseCase(
        repository,
        gateway,
        pokemon_species_repository,
        pokemon_species_gateway,
    )

    result = asyncio.run(use_case.execute(type=Types.ELECTRIC, specie_name="pikachu"))

    assert result == expected_movements
    gateway.search.assert_awaited_once_with(Types.ELECTRIC, "pikachu")
    repository.search.assert_called_once_with(type=Types.ELECTRIC, specie_id=1)
    repository.save.assert_has_calls([call(expected_movements[0])])
    repository.link_to_specie.assert_has_calls(
        [call(specie_id=1, movement_name="thunderbolt")]
    )


def test_search_movements_returns_empty_list_when_gateway_returns_none():
    repository = Mock()
    gateway = AsyncMock()
    pokemon_species_repository = Mock()
    pokemon_species_gateway = AsyncMock()

    pokemon_species_repository.search.return_value = CursorPage(
        items=[], next_cursor=None
    )
    pokemon_species_gateway.search.return_value = CursorPage(items=[], next_cursor=None)
    repository.search.return_value = []
    gateway.search.return_value = None

    use_case = SearchMovementsUseCase(
        repository,
        gateway,
        pokemon_species_repository,
        pokemon_species_gateway,
    )

    result = asyncio.run(use_case.execute(type=Types.ELECTRIC))

    assert result == []
    repository.save.assert_not_called()


def test_search_movements_uses_cached_results_by_specie_without_gateway_call():
    repository = Mock()
    gateway = AsyncMock()
    pokemon_species_repository = Mock()
    pokemon_species_gateway = AsyncMock()

    cached_specie = PokemonSpecie(
        id=1,
        external_id=25,
        name="pikachu",
        base_stats=BaseStats(35, 55, 40, 50, 50, 90),
        types=(Types.ELECTRIC,),
    )
    cached_movements = [
        Movement(
            name="thunderbolt",
            power=90,
            accuracy=100,
            description="A strong electric blast crashes down on the target.",
            pp=15,
            type=Types.ELECTRIC,
        )
    ]

    pokemon_species_repository.search.return_value = CursorPage(
        items=[cached_specie],
        next_cursor=None,
    )
    repository.search.return_value = cached_movements

    use_case = SearchMovementsUseCase(
        repository,
        gateway,
        pokemon_species_repository,
        pokemon_species_gateway,
    )

    result = asyncio.run(use_case.execute(specie_name="pikachu"))

    assert result == cached_movements
    gateway.search.assert_not_called()


def test_search_movements_requires_at_least_one_filter():
    repository = Mock()
    gateway = AsyncMock()
    pokemon_species_repository = Mock()
    pokemon_species_gateway = AsyncMock()

    use_case = SearchMovementsUseCase(
        repository,
        gateway,
        pokemon_species_repository,
        pokemon_species_gateway,
    )

    with pytest.raises(ValueError, match="At least one filter must be informed"):
        asyncio.run(use_case.execute())
