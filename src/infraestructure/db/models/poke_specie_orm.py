from __future__ import annotations

from typing import TYPE_CHECKING, List

from sqlalchemy import (
    CheckConstraint,
    Enum,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.domain.value_objects.types import Types
from src.infraestructure.db.base import Base

if TYPE_CHECKING:
    from src.infraestructure.db.models.movements_orm import PokemonSpecieMovementORM
    from src.infraestructure.db.models.types_orm import PokemonSpecieTypeORM

PokemonTypeEnum = Enum(Types, name="pokemon_type", native_enum=False)


class PokemonSpecieORM(Base):
    __tablename__ = "pokemon_species"
    __table_args__ = (
        CheckConstraint("hp BETWEEN 1 AND 255"),
        CheckConstraint("attack BETWEEN 1 AND 255"),
        CheckConstraint("defense BETWEEN 1 AND 255"),
        CheckConstraint("special_attack BETWEEN 1 AND 255"),
        CheckConstraint("special_defense BETWEEN 1 AND 255"),
        CheckConstraint("speed BETWEEN 1 AND 255"),
        UniqueConstraint("external_id", name="uq_pokemon_species_external_id"),
        UniqueConstraint("name", name="uq_pokemon_species_name"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    external_id: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    hp: Mapped[int] = mapped_column(Integer, nullable=False)
    attack: Mapped[int] = mapped_column(Integer, nullable=False)
    defense: Mapped[int] = mapped_column(Integer, nullable=False)
    special_attack: Mapped[int] = mapped_column(Integer, nullable=False)
    special_defense: Mapped[int] = mapped_column(Integer, nullable=False)
    speed: Mapped[int] = mapped_column(Integer, nullable=False)
    types: Mapped[List["PokemonSpecieTypeORM"]] = relationship(
        back_populates="specie",
        cascade="all, delete-orphan",
        order_by="PokemonSpecieTypeORM.slot",
    )
    movement_links: Mapped[List["PokemonSpecieMovementORM"]] = relationship(
        back_populates="specie",
        cascade="all, delete-orphan",
    )
