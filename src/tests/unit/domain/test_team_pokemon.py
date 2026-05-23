from src.domain.entities.pokemon_specie import PokemonSpecie
from src.domain.entities.team_pokemon import TeamPokemon
from src.domain.value_objects.base_stats import BaseStats
from src.domain.value_objects.ivs import IVs
from src.domain.value_objects.types import Types


def create_pokemon_team():
    return TeamPokemon(
        1,
        PokemonSpecie(
            1,
            25,
            "pikachu",
            BaseStats(35, 55, 40, 50, 50, 90),
            (Types.ELECTRIC,),
            front_default_sprite="https://example.com/pikachu.png",
        ),
        IVs(31, 31, 31, 31, 31, 31),
        [],
    )


def test_create_team_pokemon():
    team_pokemon = create_pokemon_team()
    assert team_pokemon._id == 1
    assert team_pokemon._specie.name == "pikachu"
    assert team_pokemon._ivs == IVs(31, 31, 31, 31, 31, 31)
    assert len(team_pokemon._moves) == 0
    assert team_pokemon._specie.base_stats == BaseStats(35, 55, 40, 50, 50, 90)
    assert team_pokemon._specie.types == (Types.ELECTRIC,)
