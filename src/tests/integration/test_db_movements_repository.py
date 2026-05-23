from src.domain.entities.movement import Movement
from src.domain.entities.pokemon_specie import PokemonSpecie
from src.domain.value_objects.base_stats import BaseStats
from src.domain.value_objects.types import Types
from src.infrastructure.repositories.db_movements_repository import (
    SQLAlchemyMovementsRepository,
)
from src.infrastructure.repositories.db_pokemon_species_repository import (
    SQLAlchemyPokemonSpeciesRepository,
)


def _make_movement(
    name: str,
    type: Types = Types.ELECTRIC,
) -> Movement:
    return Movement(
        name=name,
        power=90,
        accuracy=100,
        description=f"A {type.value} move.",
        pp=15,
        type=type,
    )


def test_save_and_search():
    repo = SQLAlchemyMovementsRepository()

    repo.save(_make_movement("thunderbolt", Types.ELECTRIC))
    repo.save(_make_movement("flamethrower", Types.FIRE))

    results = repo.search(type=Types.ELECTRIC)
    assert results is not None
    assert len(results) == 1
    assert results[0].name == "thunderbolt"


def test_save_updates_existing_movement():
    repo = SQLAlchemyMovementsRepository()

    repo.save(_make_movement("thunderbolt", Types.ELECTRIC))
    repo.save(
        Movement(
            name="thunderbolt",
            power=120,
            accuracy=100,
            description="Updated thunderbolt",
            pp=10,
            type=Types.ELECTRIC,
        )
    )

    results = repo.search(type=Types.ELECTRIC)
    assert results is not None
    assert len(results) == 1
    assert results[0].power == 120
    assert results[0].description == "Updated thunderbolt"


def test_search_by_specie_id():
    specie_repo = SQLAlchemyPokemonSpeciesRepository()
    movement_repo = SQLAlchemyMovementsRepository()

    specie = PokemonSpecie(
        id=None,
        external_id=25,
        name="pikachu",
        base_stats=BaseStats(35, 55, 40, 50, 50, 90),
        types=(Types.ELECTRIC,),
        front_default_sprite="https://example.com/pikachu.png",
    )
    specie_repo.save(specie)

    movement_repo.save(_make_movement("thunderbolt", Types.ELECTRIC))
    movement_repo.save(_make_movement("flamethrower", Types.FIRE))
    movement_repo.link_to_specie(specie.id, "thunderbolt")

    results = movement_repo.search(specie_id=specie.id)
    assert results is not None
    assert len(results) == 1
    assert results[0].name == "thunderbolt"


def test_search_by_type_and_specie_id():
    specie_repo = SQLAlchemyPokemonSpeciesRepository()
    movement_repo = SQLAlchemyMovementsRepository()

    specie = PokemonSpecie(
        id=None,
        external_id=25,
        name="pikachu",
        base_stats=BaseStats(35, 55, 40, 50, 50, 90),
        types=(Types.ELECTRIC,),
        front_default_sprite="https://example.com/pikachu.png",
    )
    specie_repo.save(specie)

    movement_repo.save(_make_movement("thunderbolt", Types.ELECTRIC))
    movement_repo.save(_make_movement("thunder", Types.ELECTRIC))
    movement_repo.save(_make_movement("flamethrower", Types.FIRE))
    movement_repo.link_to_specie(specie.id, "thunderbolt")
    movement_repo.link_to_specie(specie.id, "flamethrower")

    results = movement_repo.search(type=Types.FIRE, specie_id=specie.id)
    assert results is not None
    assert len(results) == 1
    assert results[0].name == "flamethrower"


def test_search_returns_empty_list_when_no_matches():
    repo = SQLAlchemyMovementsRepository()

    results = repo.search(type=Types.GHOST)
    assert results is not None
    assert results == []


def test_link_to_specie_is_idempotent():
    specie_repo = SQLAlchemyPokemonSpeciesRepository()
    movement_repo = SQLAlchemyMovementsRepository()

    specie = PokemonSpecie(
        id=None,
        external_id=25,
        name="pikachu",
        base_stats=BaseStats(35, 55, 40, 50, 50, 90),
        types=(Types.ELECTRIC,),
        front_default_sprite="https://example.com/pikachu.png",
    )
    specie_repo.save(specie)
    movement_repo.save(_make_movement("thunderbolt", Types.ELECTRIC))

    movement_repo.link_to_specie(specie.id, "thunderbolt")
    movement_repo.link_to_specie(specie.id, "thunderbolt")

    results = movement_repo.search(specie_id=specie.id)
    assert results is not None
    assert len(results) == 1
