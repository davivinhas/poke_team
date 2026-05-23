from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.domain.value_objects.types import Types
from src.infrastructure.db.base import Base
from src.infrastructure.db.models.poke_specie_orm import PokemonTypeEnum

if TYPE_CHECKING:
    from src.infrastructure.db.models.poke_specie_orm import PokemonSpecieORM


class MovementORM(Base):
    __tablename__ = "movements"
    __table_args__ = (
        UniqueConstraint("name", name="uq_movements_name"),
        CheckConstraint("power >= 0"),
        CheckConstraint("accuracy >= 0"),
        CheckConstraint("pp >= 0"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    power: Mapped[int] = mapped_column(Integer, nullable=False)
    accuracy: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(1000), nullable=False, default="")
    pp: Mapped[int] = mapped_column(Integer, nullable=False)
    type: Mapped[Types] = mapped_column(PokemonTypeEnum, nullable=False)

    specie_links: Mapped[list["PokemonSpecieMovementORM"]] = relationship(
        back_populates="movement",
        cascade="all, delete-orphan",
    )


class PokemonSpecieMovementORM(Base):
    __tablename__ = "pokemon_specie_movements"
    __table_args__ = (
        UniqueConstraint("specie_id", "movement_id", name="uq_specie_movement"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    specie_id: Mapped[int] = mapped_column(
        ForeignKey("pokemon_species.id", ondelete="CASCADE"), nullable=False, index=True
    )
    movement_id: Mapped[int] = mapped_column(
        ForeignKey("movements.id", ondelete="CASCADE"), nullable=False, index=True
    )

    specie: Mapped["PokemonSpecieORM"] = relationship(back_populates="movement_links")
    movement: Mapped["MovementORM"] = relationship(back_populates="specie_links")
