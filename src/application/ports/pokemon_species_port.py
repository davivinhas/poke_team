import abc
from typing import List, Optional

from src.application.pagination.cursor_page import CursorPage
from src.domain.entities.pokemon_specie import PokemonSpecie
from src.domain.value_objects.types import Types


class PokemonSpeciesRepositoryPort(abc.ABC):
    @abc.abstractmethod
    def get_by_id(self, id: int) -> Optional[PokemonSpecie]:
        raise NotImplementedError

    @abc.abstractmethod
    def search(
        self,
        name: Optional[str] = None,
        types: Optional[List[Types]] = None,
        limit: int = 10,
        cursor: Optional[str] = None,
    ) -> CursorPage[PokemonSpecie]:
        raise NotImplementedError

    @abc.abstractmethod
    def save(self, pokemon_specie: PokemonSpecie) -> None:
        raise NotImplementedError
