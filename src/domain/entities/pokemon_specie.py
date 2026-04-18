from domain.value_objects.base_stats import BaseStats
from domain.value_objects.types import Types


class PokemonSpecie:
    def __init__(
        self,
        id: int,
        external_id: int,
        name: str,
        base_stats: BaseStats,
        types: tuple[Types, ...],
    ):
        if id is None or id <= 0:
            raise ValueError("Invalid id")

        if external_id is None or external_id <= 0:
            raise ValueError("Invalid external id")

        if not name:
            raise ValueError("Name cannot be empty")

        if not isinstance(base_stats, BaseStats):
            raise ValueError("Invalid base stats")

        self.id = id
        self.external_id = external_id
        self.name = name
        self.base_stats = base_stats
        self._types = types

    @property
    def types(self):
        return tuple(self._types)
