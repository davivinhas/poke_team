from typing import Optional

from sqlalchemy import func, select

from src.application.pagination.cursor_page import CursorPage
from src.application.ports.pokemon_species_port import PokemonSpeciesRepositoryPort
from src.domain.entities.pokemon_specie import PokemonSpecie
from src.domain.value_objects.base_stats import BaseStats
from src.domain.value_objects.types import Types
from src.infrastructure.db import models
from src.infrastructure.db import session as db_session


class SQLAlchemyPokemonSpeciesRepository(PokemonSpeciesRepositoryPort):
    def get_by_id(self, id: int) -> Optional[PokemonSpecie]:
        with db_session.SyncSessionFactory() as session:
            orm = session.get(models.PokemonSpecieORM, id)
            if orm is not None:
                return self._to_domain(orm)

            orm = (
                session.execute(
                    select(models.PokemonSpecieORM).where(
                        models.PokemonSpecieORM.external_id == id
                    )
                )
                .scalars()
                .first()
            )
            if orm is not None:
                return self._to_domain(orm)

            return None

    def search(
        self,
        name: Optional[str] = None,
        types: Optional[list[Types]] = None,
        limit: int = 10,
        cursor: Optional[str] = None,
    ) -> CursorPage[PokemonSpecie]:
        offset = int(cursor or 0)

        with db_session.SyncSessionFactory() as session:
            query = select(models.PokemonSpecieORM)

            if name is not None:
                normalized_name = name.strip().lower()
                query = query.where(
                    func.lower(models.PokemonSpecieORM.name).contains(normalized_name)
                )

            if types:
                type_names = [t.name for t in types]
                subquery = (
                    select(models.PokemonSpecieTypeORM.specie_id)
                    .where(models.PokemonSpecieTypeORM.type.in_(type_names))
                    .group_by(models.PokemonSpecieTypeORM.specie_id)
                    .having(func.count() == len(type_names))
                    .subquery()
                )
                query = query.where(models.PokemonSpecieORM.id.in_(subquery))

            query = query.offset(offset).limit(limit + 1)
            results = session.execute(query).scalars().all()

            has_more = len(results) > limit
            items = results[:limit]

            next_cursor = str(offset + limit) if has_more else None

            return CursorPage(
                items=[self._to_domain(o) for o in items],
                next_cursor=next_cursor,
            )

    def save(self, pokemon_specie: PokemonSpecie) -> None:
        with db_session.SyncSessionFactory() as session:
            existing = (
                session.execute(
                    select(models.PokemonSpecieORM).where(
                        models.PokemonSpecieORM.external_id
                        == pokemon_specie.external_id
                    )
                )
                .scalars()
                .first()
            )

            if existing is not None:
                existing.name = pokemon_specie.name
                existing.hp = pokemon_specie.base_stats.hp
                existing.attack = pokemon_specie.base_stats.attack
                existing.defense = pokemon_specie.base_stats.defense
                existing.special_attack = pokemon_specie.base_stats.special_attack
                existing.special_defense = pokemon_specie.base_stats.special_defense
                existing.speed = pokemon_specie.base_stats.speed
                existing.front_default_sprite = pokemon_specie.front_default_sprite

                existing.types = []
                session.flush()

                existing.types = [
                    models.PokemonSpecieTypeORM(slot=i + 1, type=t.name)
                    for i, t in enumerate(pokemon_specie.types)
                ]

                session.flush()
                pokemon_specie.id = existing.id
            else:
                orm = models.PokemonSpecieORM(
                    external_id=pokemon_specie.external_id,
                    name=pokemon_specie.name,
                    hp=pokemon_specie.base_stats.hp,
                    attack=pokemon_specie.base_stats.attack,
                    defense=pokemon_specie.base_stats.defense,
                    special_attack=pokemon_specie.base_stats.special_attack,
                    special_defense=pokemon_specie.base_stats.special_defense,
                    speed=pokemon_specie.base_stats.speed,
                    front_default_sprite=pokemon_specie.front_default_sprite,
                    types=[
                        models.PokemonSpecieTypeORM(slot=i + 1, type=t.name)
                        for i, t in enumerate(pokemon_specie.types)
                    ],
                )
                session.add(orm)
                session.flush()
                pokemon_specie.id = orm.id

            session.commit()

    def _to_domain(self, orm: models.PokemonSpecieORM) -> PokemonSpecie:
        ordered_types = tuple(
            Types(orm_type.type) for orm_type in sorted(orm.types, key=lambda t: t.slot)
        )
        return PokemonSpecie(
            id=orm.id,
            external_id=orm.external_id,
            name=orm.name,
            base_stats=BaseStats(
                hp=orm.hp,
                attack=orm.attack,
                defense=orm.defense,
                special_attack=orm.special_attack,
                special_defense=orm.special_defense,
                speed=orm.speed,
            ),
            types=ordered_types,
            front_default_sprite=orm.front_default_sprite,
        )
