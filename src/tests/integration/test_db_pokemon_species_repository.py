from src.domain.entities.pokemon_specie import PokemonSpecie
from src.domain.value_objects.base_stats import BaseStats
from src.domain.value_objects.types import Types
from src.infrastructure.repositories.db_pokemon_species_repository import (
    SQLAlchemyPokemonSpeciesRepository,
)


def _make_specie(
    external_id: int,
    name: str,
    types: tuple[Types, ...],
    id: int | None = None,
) -> PokemonSpecie:
    return PokemonSpecie(
        id=id,
        external_id=external_id,
        name=name,
        base_stats=BaseStats(35, 55, 40, 50, 50, 90),
        types=types,
        front_default_sprite=f"https://example.com/{name}.png",
    )


def test_save_and_get_by_internal_id():
    repo = SQLAlchemyPokemonSpeciesRepository()

    specie = _make_specie(25, "pikachu", (Types.ELECTRIC,))
    repo.save(specie)
    internal_id = specie.id
    assert internal_id is not None

    loaded = repo.get_by_id(internal_id)
    assert loaded is not None
    assert loaded.name == "pikachu"
    assert loaded.external_id == 25
    assert loaded.types == (Types.ELECTRIC,)
    assert loaded.base_stats.hp == 35


def test_get_by_external_id():
    repo = SQLAlchemyPokemonSpeciesRepository()

    specie = _make_specie(6, "charizard", (Types.FIRE, Types.FLYING))
    repo.save(specie)

    loaded = repo.get_by_id(6)
    assert loaded is not None
    assert loaded.name == "charizard"
    assert loaded.external_id == 6


def test_get_by_id_returns_none_when_not_found():
    repo = SQLAlchemyPokemonSpeciesRepository()
    assert repo.get_by_id(999) is None


def test_save_updates_existing_specie():
    repo = SQLAlchemyPokemonSpeciesRepository()

    specie = _make_specie(25, "pikachu", (Types.ELECTRIC,))
    repo.save(specie)
    internal_id = specie.id

    updated = _make_specie(25, "raichu", (Types.ELECTRIC,), id=internal_id)
    repo.save(updated)

    loaded = repo.get_by_id(25)
    assert loaded is not None
    assert loaded.name == "raichu"


def test_search_by_name():
    repo = SQLAlchemyPokemonSpeciesRepository()

    repo.save(_make_specie(25, "pikachu", (Types.ELECTRIC,)))
    repo.save(_make_specie(6, "charizard", (Types.FIRE, Types.FLYING)))
    repo.save(_make_specie(26, "raichu", (Types.ELECTRIC,)))

    result = repo.search(name="pikachu")
    assert len(result.items) == 1
    assert result.items[0].name == "pikachu"


def test_search_by_name_case_insensitive():
    repo = SQLAlchemyPokemonSpeciesRepository()

    repo.save(_make_specie(25, "pikachu", (Types.ELECTRIC,)))

    result = repo.search(name="PIKACHU")
    assert len(result.items) == 1
    assert result.items[0].name == "pikachu"


def test_search_by_type():
    repo = SQLAlchemyPokemonSpeciesRepository()

    repo.save(_make_specie(25, "pikachu", (Types.ELECTRIC,)))
    repo.save(_make_specie(6, "charizard", (Types.FIRE, Types.FLYING)))
    repo.save(_make_specie(26, "raichu", (Types.ELECTRIC,)))

    result = repo.search(types=[Types.ELECTRIC])
    assert len(result.items) == 2
    assert {s.name for s in result.items} == {"pikachu", "raichu"}


def test_search_by_multiple_types_requires_all():
    repo = SQLAlchemyPokemonSpeciesRepository()

    repo.save(_make_specie(25, "pikachu", (Types.ELECTRIC,)))
    repo.save(_make_specie(6, "charizard", (Types.FIRE, Types.FLYING)))
    repo.save(_make_specie(59, "arcanine", (Types.FIRE,)))

    result = repo.search(types=[Types.FIRE, Types.FLYING])
    assert len(result.items) == 1
    assert result.items[0].name == "charizard"


def test_search_pagination():
    repo = SQLAlchemyPokemonSpeciesRepository()

    for i in range(5):
        repo.save(_make_specie(100 + i, f"pokemon-{i}", (Types.NORMAL,)))

    page1 = repo.search(limit=2)
    assert len(page1.items) == 2
    assert page1.next_cursor is not None

    page2 = repo.search(limit=2, cursor=page1.next_cursor)
    assert len(page2.items) == 2
    assert page2.next_cursor is not None

    page3 = repo.search(limit=2, cursor=page2.next_cursor)
    assert len(page3.items) == 1
    assert page3.next_cursor is None


def test_save_assigns_id():
    repo = SQLAlchemyPokemonSpeciesRepository()

    specie = _make_specie(25, "pikachu", (Types.ELECTRIC,))
    assert specie.id is None

    repo.save(specie)
    assert specie.id is not None
    assert specie.id > 0
