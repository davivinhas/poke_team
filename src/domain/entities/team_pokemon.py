from src.domain.entities.pokemon_specie import PokemonSpecie
from src.domain.value_objects.ivs import IVs
from src.domain.value_objects.movement_slot import MovementSlot


class TeamPokemon:
    def __init__(
        self, id: int, specie: PokemonSpecie, ivs: IVs, moves: list[MovementSlot]
    ):
        if id <= 0:
            raise ValueError("Invalid id")

        if not isinstance(specie, PokemonSpecie):
            raise ValueError("Invalid specie")

        if not isinstance(ivs, IVs):
            raise ValueError("Invalid IVs")

        self._id = id
        self._specie = specie
        self._ivs = ivs
        self._moves = moves

    def add_move(self, move: str) -> None:
        if len(self._moves) >= 4:
            raise ValueError("Pokemon can't have more than 4 moves")
        self._moves.add(move)

    def remove_move(self, move: str) -> None:
        if move not in self._moves:
            raise ValueError("Move not found")
        self._moves.remove(move)

    @property
    def moves(self):
        return tuple(self._moves)

    def change_ivs(self, ivs: IVs) -> None:
        if not isinstance(ivs, IVs):
            raise ValueError("Invalid IVs")
        self.ivs = ivs
