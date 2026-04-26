import pytest

from src.domain.entities.pokemon_specie import PokemonSpecie
from src.domain.value_objects.base_stats import BaseStats
from src.domain.value_objects.types import Types


def create_pokemon_specie():
    return PokemonSpecie(
        1,
        25,
        "pikachu",
        BaseStats(35, 55, 40, 50, 50, 90),
        (Types.ELECTRIC,),
    )


def test_create_pokemon_specie():
    pokemon_specie = create_pokemon_specie()
    assert pokemon_specie.id == 1
    assert pokemon_specie.external_id == 25
    assert pokemon_specie.name == "pikachu"
    # assert pokemon_specie.base_stats.hp == 35
    # assert pokemon_specie.base_stats.attack == 55
    # assert pokemon_specie.base_stats.defense == 40
    # assert pokemon_specie.base_stats.special_attack == 50
    # assert pokemon_specie.base_stats.special_defense == 50
    # assert pokemon_specie.base_stats.speed == 90
    assert pokemon_specie.base_stats == BaseStats(35, 55, 40, 50, 50, 90)
    assert pokemon_specie.types == (Types.ELECTRIC,)


def test_pokemon_specie_has_types():
    pokemon_specie = create_pokemon_specie()
    assert pokemon_specie.types == (Types.ELECTRIC,)


def test_pokemon_specie_has_two_types():
    pokemon_specie = PokemonSpecie(
        1,
        25,
        "pikachu",
        BaseStats(35, 55, 40, 50, 50, 90),
        (Types.ELECTRIC, Types.FIRE),
    )
    assert pokemon_specie.types == (Types.ELECTRIC, Types.FIRE)


def test_pokemon_specie_with_three_types():
    with pytest.raises(ValueError):
        PokemonSpecie(
            1,
            25,
            "pikachu",
            BaseStats(35, 55, 40, 50, 50, 90),
            (Types.ELECTRIC, Types.FIRE, Types.WATER),
        )


def test_pokemon_specie_with_zero_types():
    with pytest.raises(ValueError):
        PokemonSpecie(
            1,
            25,
            "pikachu",
            BaseStats(35, 55, 40, 50, 50, 90),
            (),
        )


def test_pokemon_specie_with_negative_id():
    with pytest.raises(ValueError):
        PokemonSpecie(
            -1,
            25,
            "pikachu",
            BaseStats(35, 55, 40, 50, 50, 90),
            (Types.ELECTRIC,),
        )


def test_pokemon_specie_with_zero_id():
    with pytest.raises(ValueError):
        PokemonSpecie(
            0,
            25,
            "pikachu",
            BaseStats(35, 55, 40, 50, 50, 90),
            (Types.ELECTRIC,),
        )


def test_pokemon_specie_with_negative_external_id():
    with pytest.raises(ValueError):
        PokemonSpecie(
            1,
            -1,
            "pikachu",
            BaseStats(35, 55, 40, 50, 50, 90),
            (Types.ELECTRIC,),
        )


def test_pokemon_specie_with_zero_external_id():
    with pytest.raises(ValueError):
        PokemonSpecie(
            1,
            0,
            "pikachu",
            BaseStats(35, 55, 40, 50, 50, 90),
            (Types.ELECTRIC,),
        )


def test_pokemon_specie_with_empty_name():
    with pytest.raises(ValueError):
        PokemonSpecie(
            1,
            25,
            "",
            BaseStats(35, 55, 40, 50, 50, 90),
            (Types.ELECTRIC,),
        )


def test_pokemon_specie_with_null_base_stats():
    with pytest.raises(ValueError):
        PokemonSpecie(
            1,
            25,
            "pikachu",
            None,
            (Types.ELECTRIC,),
        )


def test_pokemon_specie_with_null_types():
    with pytest.raises(ValueError):
        PokemonSpecie(
            1,
            25,
            "pikachu",
            BaseStats(35, 55, 40, 50, 50, 90),
            None,
        )


def test_pokemon_specie_with_empty_types():
    with pytest.raises(ValueError):
        PokemonSpecie(
            1,
            25,
            "pikachu",
            BaseStats(35, 55, 40, 50, 50, 90),
            (),
        )


def test_pokemon_specie_with_null_id():
    pokemon_specie = PokemonSpecie(
        None,
        25,
        "pikachu",
        BaseStats(35, 55, 40, 50, 50, 90),
        (Types.ELECTRIC,),
    )

    assert pokemon_specie.id is None


def test_pokemon_specie_with_null_external_id():
    with pytest.raises(ValueError):
        PokemonSpecie(
            1,
            None,
            "pikachu",
            BaseStats(35, 55, 40, 50, 50, 90),
            (Types.ELECTRIC,),
        )
