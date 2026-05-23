import asyncio
from typing import Any, Optional
from urllib.parse import parse_qs, urlencode, urlparse

import httpx

from src.application.pagination.cursor_page import CursorPage
from src.application.ports.pokemon_species_gateway import PokemonSpeciesGateway
from src.domain.entities.pokemon_specie import PokemonSpecie
from src.domain.value_objects.base_stats import BaseStats
from src.domain.value_objects.types import Types
from src.infrastructure.settings import get_external_api_url


class PokeApiPokemonSpeciesGateway(PokemonSpeciesGateway):
    DEFAULT_HEADERS = {
        "Accept": "application/json",
        "User-Agent": "poke-team/1.0",
    }

    def __init__(
        self,
        base_url: str | None = None,
        client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        self._base_url = (base_url or get_external_api_url()).rstrip("/")
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(
            headers=self.DEFAULT_HEADERS,
            timeout=10.0,
        )

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def get_by_id(self, id: int) -> Optional[PokemonSpecie]:
        try:
            payload = await self._fetch_json(f"{self._base_url}/pokemon/{id}/")
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                return None
            raise

        return self._map_to_pokemon_specie(payload)

    async def search(
        self,
        name: Optional[str] = None,
        types: Optional[list[Types]] = None,
        limit: int = 10,
        cursor: Optional[str] = None,
    ) -> CursorPage[PokemonSpecie]:
        self._validate_limit(limit)
        normalized_name = name.strip().lower() if name else None
        normalized_types = types or []

        if normalized_name:
            return await self._search_by_exact_name(
                name=normalized_name,
                types=normalized_types,
                cursor=cursor,
            )

        if normalized_types:
            return await self._search_by_types(
                types=normalized_types,
                limit=limit,
                cursor=cursor,
            )

        return await self._search_all(limit=limit, cursor=cursor)

    async def _search_all(
        self,
        limit: int,
        cursor: Optional[str],
    ) -> CursorPage[PokemonSpecie]:
        offset = self._parse_cursor(cursor)
        query = urlencode({"limit": limit, "offset": offset})
        payload = await self._fetch_json(f"{self._base_url}/pokemon/?{query}")
        detail_payloads = await asyncio.gather(
            *(self._fetch_json(item["url"]) for item in payload["results"])
        )
        species = [self._map_to_pokemon_specie(item) for item in detail_payloads]
        return CursorPage(
            items=species,
            next_cursor=self._extract_next_cursor(payload.get("next")),
        )

    async def _search_by_exact_name(
        self,
        name: str,
        types: list[Types],
        cursor: Optional[str],
    ) -> CursorPage[PokemonSpecie]:
        offset = self._parse_cursor(cursor)
        if offset > 0:
            return CursorPage(items=[], next_cursor=None)

        try:
            payload = await self._fetch_json(f"{self._base_url}/pokemon/{name}/")
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                return CursorPage(items=[], next_cursor=None)
            raise

        specie = self._map_to_pokemon_specie(payload)
        if types and not all(specie_type in specie.types for specie_type in types):
            return CursorPage(items=[], next_cursor=None)

        return CursorPage(items=[specie], next_cursor=None)

    async def _search_by_types(
        self,
        types: list[Types],
        limit: int,
        cursor: Optional[str],
    ) -> CursorPage[PokemonSpecie]:
        offset = self._parse_cursor(cursor)
        references = await self._get_pokemon_references_for_types(types)
        page_references = references[offset : offset + limit]
        detail_payloads = await asyncio.gather(
            *(self._fetch_json(reference["url"]) for reference in page_references)
        )
        species = [self._map_to_pokemon_specie(item) for item in detail_payloads]

        next_offset = offset + limit
        next_cursor = str(next_offset) if next_offset < len(references) else None
        return CursorPage(items=species, next_cursor=next_cursor)

    async def _get_pokemon_references_for_types(
        self,
        types: list[Types],
    ) -> list[dict[str, str]]:
        type_entries = await asyncio.gather(
            *(self._fetch_type_entries(pokemon_type) for pokemon_type in types)
        )
        if not type_entries:
            return []

        first_type_entries = type_entries[0]
        if len(type_entries) == 1:
            return first_type_entries

        names_in_all_types = {entry["name"] for entry in first_type_entries}
        for entries in type_entries[1:]:
            names_in_all_types &= {entry["name"] for entry in entries}

        return [
            entry for entry in first_type_entries if entry["name"] in names_in_all_types
        ]

    async def _fetch_type_entries(self, pokemon_type: Types) -> list[dict[str, str]]:
        payload = await self._fetch_json(f"{self._base_url}/type/{pokemon_type.value}/")
        return [
            {
                "name": item["pokemon"]["name"],
                "url": item["pokemon"]["url"],
            }
            for item in payload["pokemon"]
        ]

    def _map_to_pokemon_specie(self, payload: dict[str, Any]) -> PokemonSpecie:
        stats_by_name = {
            item["stat"]["name"]: item["base_stat"] for item in payload["stats"]
        }
        ordered_types = tuple(
            self._map_type(item["type"]["name"])
            for item in sorted(payload["types"], key=lambda item: item["slot"])
        )
        external_id = int(payload["id"])
        front_default = payload["sprites"]["front_default"]

        return PokemonSpecie(
            id=None,
            external_id=external_id,
            name=payload["name"],
            base_stats=BaseStats(
                hp=stats_by_name["hp"],
                attack=stats_by_name["attack"],
                defense=stats_by_name["defense"],
                special_attack=stats_by_name["special-attack"],
                special_defense=stats_by_name["special-defense"],
                speed=stats_by_name["speed"],
            ),
            types=ordered_types,
            front_default_sprite=front_default,
        )

    def _map_type(self, api_type_name: str) -> Types:
        try:
            return Types(api_type_name)
        except ValueError as exc:
            raise ValueError(
                f"Unsupported pokemon type returned by PokeAPI: {api_type_name}"
            ) from exc

    def _parse_cursor(self, cursor: Optional[str]) -> int:
        if cursor is None or cursor == "":
            return 0

        try:
            offset = int(cursor)
        except ValueError as exc:
            raise ValueError("Cursor must be a numeric offset") from exc

        if offset < 0:
            raise ValueError("Cursor must be a non-negative offset")

        return offset

    def _extract_next_cursor(self, next_url: Optional[str]) -> Optional[str]:
        if not next_url:
            return None

        query = parse_qs(urlparse(next_url).query)
        offset_values = query.get("offset")
        if not offset_values:
            return None

        return offset_values[0]

    def _validate_limit(self, limit: int) -> None:
        if limit <= 0:
            raise ValueError("Limit must be greater than zero")

    async def _fetch_json(self, url: str) -> dict[str, Any]:
        response = await self._client.get(url)
        response.raise_for_status()
        return response.json()
