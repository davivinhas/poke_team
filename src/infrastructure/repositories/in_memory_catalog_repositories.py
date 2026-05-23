from typing import Optional

from src.application.pagination.cursor_page import CursorPage
from src.application.ports.movements_port import MovementsRepositoryPort
from src.application.ports.pokemon_species_port import PokemonSpeciesRepositoryPort
from src.domain.entities.movement import Movement
from src.domain.entities.pokemon_specie import PokemonSpecie
from src.domain.value_objects.types import Types


class InMemoryPokemonSpeciesRepository(PokemonSpeciesRepositoryPort):
    def __init__(self) -> None:
        self._species_by_internal_id: dict[int, PokemonSpecie] = {}
        self._species_by_external_id: dict[int, PokemonSpecie] = {}
        self._next_id = 1

    def get_by_id(self, id: int) -> Optional[PokemonSpecie]:
        pokemon_specie = self._species_by_internal_id.get(id)
        if pokemon_specie is not None:
            return pokemon_specie
        return self._species_by_external_id.get(id)

    def search(
        self,
        name: Optional[str] = None,
        types: Optional[list[Types]] = None,
        limit: int = 10,
        cursor: Optional[str] = None,
    ) -> CursorPage[PokemonSpecie]:
        offset = int(cursor or 0)
        filtered = list(self._species_by_external_id.values())

        if name is not None:
            normalized_name = name.strip().lower()
            filtered = [
                pokemon_specie
                for pokemon_specie in filtered
                if normalized_name in pokemon_specie.name.lower()
            ]

        if types:
            filtered = [
                pokemon_specie
                for pokemon_specie in filtered
                if all(pokemon_type in pokemon_specie.types for pokemon_type in types)
            ]

        items = filtered[offset : offset + limit]
        next_offset = offset + limit
        next_cursor = str(next_offset) if next_offset < len(filtered) else None
        return CursorPage(items=items, next_cursor=next_cursor)

    def save(self, pokemon_specie: PokemonSpecie) -> None:
        existing = self._species_by_external_id.get(pokemon_specie.external_id)
        if existing is not None:
            pokemon_specie.id = existing.id
            self._species_by_internal_id[existing.id] = pokemon_specie
            self._species_by_external_id[pokemon_specie.external_id] = pokemon_specie
            return

        pokemon_specie.id = self._next_id
        self._species_by_internal_id[self._next_id] = pokemon_specie
        self._species_by_external_id[pokemon_specie.external_id] = pokemon_specie
        self._next_id += 1


class InMemoryMovementsRepository(MovementsRepositoryPort):
    def __init__(self) -> None:
        self._movements_by_name: dict[str, Movement] = {}
        self._movement_names_by_specie_id: dict[int, set[str]] = {}

    def search(
        self,
        type: Optional[Types] = None,
        specie_id: Optional[int] = None,
    ) -> Optional[list[Movement]]:
        movements: list[Movement]
        if specie_id is None:
            movements = list(self._movements_by_name.values())
        else:
            movement_names = self._movement_names_by_specie_id.get(specie_id, set())
            movements = [
                movement
                for movement_name, movement in self._movements_by_name.items()
                if movement_name in movement_names
            ]

        if type is not None:
            movements = [movement for movement in movements if movement.type == type]
        return movements

    def save(self, movement: Movement) -> None:
        self._movements_by_name[movement.name] = movement

    def link_to_specie(self, specie_id: int, movement_name: str) -> None:
        movement_names = self._movement_names_by_specie_id.setdefault(specie_id, set())
        movement_names.add(movement_name)
