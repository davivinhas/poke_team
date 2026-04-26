from pydantic import BaseModel


class BaseStatsResponse(BaseModel):
    hp: int
    attack: int
    defense: int
    special_attack: int
    special_defense: int
    speed: int


class PokemonSpecieResponse(BaseModel):
    id: int | None
    external_id: int
    name: str
    base_stats: BaseStatsResponse
    types: list[str]


class CursorPagePokemonSpeciesResponse(BaseModel):
    items: list[PokemonSpecieResponse]
    next_cursor: str | None


class MovementResponse(BaseModel):
    name: str
    power: int
    accuracy: int
    description: str
    pp: int
    type: str
