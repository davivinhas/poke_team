from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.domain.value_objects.types import Types
from src.infraestructure.db.base import Base
from src.infraestructure.db.models.poke_specie_orm import PokemonTypeEnum

if TYPE_CHECKING:
    from src.infraestructure.db.models.poke_specie_orm import PokemonSpecieORM


class PokemonSpecieTypeORM(Base):
    __tablename__ = "pokemon_specie_types"
    __table_args__ = (
        UniqueConstraint("specie_id", "slot", name="uq_specie_type_slot"),
        UniqueConstraint("specie_id", "type", name="uq_specie_type_value"),
        CheckConstraint("slot IN (1, 2)"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    specie_id: Mapped[int] = mapped_column(
        ForeignKey("pokemon_species.id", ondelete="CASCADE"), nullable=False
    )
    slot: Mapped[int] = mapped_column(Integer, nullable=False)
    type: Mapped[Types] = mapped_column(PokemonTypeEnum, nullable=False)
    specie: Mapped["PokemonSpecieORM"] = relationship(back_populates="types")
