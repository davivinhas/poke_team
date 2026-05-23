from typing import Optional

from sqlalchemy import select

from src.application.ports.movements_port import MovementsRepositoryPort
from src.domain.entities.movement import Movement
from src.domain.value_objects.types import Types
from src.infrastructure.db import models
from src.infrastructure.db import session as db_session


class SQLAlchemyMovementsRepository(MovementsRepositoryPort):
    def search(
        self,
        type: Optional[Types] = None,
        specie_id: Optional[int] = None,
    ) -> Optional[list[Movement]]:
        with db_session.SyncSessionFactory() as session:
            query = select(models.MovementORM)

            if specie_id is not None:
                subquery = select(models.PokemonSpecieMovementORM.movement_id).where(
                    models.PokemonSpecieMovementORM.specie_id == specie_id
                )
                query = query.where(models.MovementORM.id.in_(subquery))

            if type is not None:
                query = query.where(models.MovementORM.type == type.name)

            results = session.execute(query).scalars().all()
            return [self._to_domain(o) for o in results]

    def save(self, movement: Movement) -> None:
        with db_session.SyncSessionFactory() as session:
            existing = (
                session.execute(
                    select(models.MovementORM).where(
                        models.MovementORM.name == movement.name
                    )
                )
                .scalars()
                .first()
            )

            if existing is not None:
                existing.power = movement.power
                existing.accuracy = movement.accuracy
                existing.description = movement.description
                existing.pp = movement.pp
                existing.type = movement.type.name
            else:
                orm = models.MovementORM(
                    name=movement.name,
                    power=movement.power,
                    accuracy=movement.accuracy,
                    description=movement.description,
                    pp=movement.pp,
                    type=movement.type.name,
                )
                session.add(orm)

            session.commit()

    def link_to_specie(self, specie_id: int, movement_name: str) -> None:
        with db_session.SyncSessionFactory() as session:
            movement_orm = (
                session.execute(
                    select(models.MovementORM).where(
                        models.MovementORM.name == movement_name
                    )
                )
                .scalars()
                .first()
            )

            if movement_orm is None:
                return

            existing_link = (
                session.execute(
                    select(models.PokemonSpecieMovementORM).where(
                        models.PokemonSpecieMovementORM.specie_id == specie_id,
                        models.PokemonSpecieMovementORM.movement_id == movement_orm.id,
                    )
                )
                .scalars()
                .first()
            )

            if existing_link is not None:
                return

            link = models.PokemonSpecieMovementORM(
                specie_id=specie_id,
                movement_id=movement_orm.id,
            )
            session.add(link)
            session.commit()

    def _to_domain(self, orm: models.MovementORM) -> Movement:
        return Movement(
            name=orm.name,
            power=orm.power,
            accuracy=orm.accuracy,
            description=orm.description,
            pp=orm.pp,
            type=Types(orm.type),
        )
