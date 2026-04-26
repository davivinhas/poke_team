import pytest

from src.domain.entities.pokemon_specie import PokemonSpecie
from src.domain.entities.team import Team
from src.domain.entities.team_pokemon import TeamPokemon
from src.domain.value_objects.base_stats import BaseStats
from src.domain.value_objects.ivs import IVs
from src.domain.value_objects.types import Types


def _build_team_pokemon() -> TeamPokemon:
    specie = PokemonSpecie(
        1,
        25,
        "pikachu",
        BaseStats(35, 55, 40, 50, 50, 90),
        (Types.ELECTRIC,),
    )
    ivs = IVs(31, 31, 31, 31, 31, 31)
    return TeamPokemon(1, specie, ivs, [])


def test_add_pokemon_to_team():
    team = Team(1, "Team 1")
    pokemon = _build_team_pokemon()
    team.add_pokemon(pokemon)
    assert pokemon in team.pokemons


def test_remove_pokemon_from_team():
    team = Team(1, "Team 1")
    pokemon = _build_team_pokemon()
    team._pokemons.append(pokemon)
    team.remove_pokemon(pokemon)
    assert pokemon not in team.pokemons


def test_can_rename_team():
    team = Team(1, "Team 1")
    team.rename("Team 2")
    assert team.name == "Team 2"


def test_more_than_6_pokemons_in_team():
    team = Team(1, "Team 1")
    team.add_pokemon(_build_team_pokemon())
    team.add_pokemon(_build_team_pokemon())
    team.add_pokemon(_build_team_pokemon())
    team.add_pokemon(_build_team_pokemon())
    team.add_pokemon(_build_team_pokemon())
    team.add_pokemon(_build_team_pokemon())

    with pytest.raises(ValueError):
        team.add_pokemon(_build_team_pokemon())
