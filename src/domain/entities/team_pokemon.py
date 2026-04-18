from src.domain.entities.pokemon_specie import PokemonSpecie
from src.domain.value_objects.ivs import IVs


class TeamPokemon:
    def __init__(self, id: int, specie: PokemonSpecie, ivs: IVs):
        if id <= 0:
            raise ValueError("Invalid id")

        if not isinstance(specie, PokemonSpecie):
            raise ValueError("Invalid specie")

        if not isinstance(ivs, IVs):
            raise ValueError("Invalid IVs")

        if len(specie.types) > 2:
            raise ValueError("Specie can have at most 2 types")

        self.id = id
        self.specie = specie
        self.ivs = ivs
        self._moves = set()

    def add_move(self, move: str) -> None:
        if len(self._moves) >= 4:
            raise ValueError("Pokemon can't have more than 4 moves")
        self._moves.add(move)

    @property
    def moves(self):
        return tuple(self._moves)
