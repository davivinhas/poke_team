from src.domain.entities.team_pokemon import TeamPokemon


class Team:
    def __init__(self, id: int, name: str):
        if id <= 0:
            raise ValueError("Invalid id")

        if not name:
            raise ValueError("Name cannot be empty")

        self.id = id
        self.name = name
        self._pokemons = []

    def add_pokemon(self, pokemon: TeamPokemon) -> None:
        if len(self._pokemons) >= 6:
            raise ValueError("Team can't have more than 6 pokemons")
        self._pokemons.append(pokemon)

    @property
    def pokemons(self):
        return tuple(self._pokemons)

    def rename(self, name: str) -> None:
        self.name = name

    def remove_pokemon(self, pokemon: TeamPokemon) -> None:
        self._pokemons.remove(pokemon)
