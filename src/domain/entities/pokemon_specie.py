from src.domain.value_objects.base_stats import BaseStats
from src.domain.value_objects.types import Types


class PokemonSpecie:
    def __init__(
        self,
        id: int | None,
        external_id: int,
        name: str,
        base_stats: BaseStats,
        types: tuple[Types, ...],
    ):
        if id is not None and id <= 0:
            raise ValueError("Invalid id")

        if external_id is None or external_id <= 0:
            raise ValueError("Invalid external id")

        if not name:
            raise ValueError("Name cannot be empty")

        if not isinstance(base_stats, BaseStats):
            raise ValueError("Invalid base stats")

        if not types:
            raise ValueError("Types cannot be empty")

        if not isinstance(types, tuple):
            raise ValueError("Types must be a tuple")

        if not all(isinstance(t, Types) for t in types):
            raise ValueError("Invalid types")

        if len(types) > 2 or len(types) <= 0:
            raise ValueError("Specie need to have at least 1 and at most 2 types")

        self.id = id
        self.external_id = external_id
        self.name = name
        self.base_stats = base_stats
        self._types = types

    @property
    def types(self):
        return tuple(self._types)
