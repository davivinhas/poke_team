import asyncio
from unittest.mock import AsyncMock, Mock, call

from src.application.use__cases.catalog.search_movements import SearchMovementsUseCase
from src.domain.entities.movement import Movement
from src.domain.value_objects.types import Types


def test_search_movements_uses_gateway_and_persists_results():
    repository = Mock()
    gateway = AsyncMock()
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
    gateway.search.return_value = expected_movements

    use_case = SearchMovementsUseCase(repository, gateway)

    result = asyncio.run(use_case.execute(type=Types.ELECTRIC, specie_name="pikachu"))

    assert result == expected_movements
    gateway.search.assert_awaited_once_with(Types.ELECTRIC, "pikachu")
    repository.save.assert_has_calls([call(expected_movements[0])])


def test_search_movements_returns_empty_list_when_gateway_returns_none():
    repository = Mock()
    gateway = AsyncMock()
    gateway.search.return_value = None

    use_case = SearchMovementsUseCase(repository, gateway)

    result = asyncio.run(use_case.execute(type=Types.ELECTRIC))

    assert result == []
    repository.save.assert_not_called()
