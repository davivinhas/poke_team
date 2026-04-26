import asyncio
from typing import Any, Optional

import httpx

from src.application.ports.movements_gateway import MovementsGateway
from src.domain.entities.movement import Movement
from src.domain.value_objects.types import Types


class PokeApiMovementsGateway(MovementsGateway):
    BASE_URL = "https://pokeapi.co/api/v2"
    DEFAULT_HEADERS = {
        "Accept": "application/json",
        "User-Agent": "poke-team/1.0",
    }

    def __init__(
        self,
        base_url: str = BASE_URL,
        client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(
            headers=self.DEFAULT_HEADERS,
            timeout=10.0,
        )

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def search(
        self,
        type: Optional[Types] = None,
        specie_name: Optional[str] = None,
    ) -> Optional[list[Movement]]:
        normalized_specie_name = specie_name.strip().lower() if specie_name else None
        if type is None and normalized_specie_name is None:
            raise ValueError("At least one filter must be informed")

        move_references: list[dict[str, str]] | None = None

        if normalized_specie_name is not None:
            try:
                move_references = await self._fetch_moves_for_specie(
                    normalized_specie_name
                )
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 404:
                    return []
                raise

        if type is not None:
            type_references = await self._fetch_moves_for_type(type)
            if move_references is None:
                move_references = type_references
            else:
                move_names = {reference["name"] for reference in type_references}
                move_references = [
                    reference
                    for reference in move_references
                    if reference["name"] in move_names
                ]

        payloads = await self._fetch_move_payloads(move_references or [])
        return [self._map_to_movement(payload) for payload in payloads]

    async def _fetch_moves_for_specie(self, specie_name: str) -> list[dict[str, str]]:
        payload = await self._fetch_json(f"{self._base_url}/pokemon/{specie_name}/")
        return [
            {
                "name": item["move"]["name"],
                "url": item["move"]["url"],
            }
            for item in payload["moves"]
        ]

    async def _fetch_moves_for_type(self, pokemon_type: Types) -> list[dict[str, str]]:
        payload = await self._fetch_json(f"{self._base_url}/type/{pokemon_type.value}/")
        return [
            {
                "name": item["name"],
                "url": item["url"],
            }
            for item in payload["moves"]
        ]

    async def _fetch_move_payloads(
        self,
        move_references: list[dict[str, str]],
    ) -> list[dict[str, Any]]:
        if not move_references:
            return []

        return await asyncio.gather(
            *(self._fetch_json(reference["url"]) for reference in move_references)
        )

    def _map_to_movement(self, payload: dict[str, Any]) -> Movement:
        return Movement(
            name=payload["name"],
            power=payload["power"] or 0,
            accuracy=payload["accuracy"] or 0,
            description=self._extract_description(payload),
            pp=payload["pp"] or 0,
            type=self._map_type(payload["type"]["name"]),
        )

    def _extract_description(self, payload: dict[str, Any]) -> str:
        for entry in payload.get("effect_entries", []):
            if entry["language"]["name"] == "en":
                return entry.get("short_effect") or entry.get("effect") or ""
        return ""

    def _map_type(self, api_type_name: str) -> Types:
        try:
            return Types(api_type_name)
        except ValueError as exc:
            raise ValueError(
                f"Unsupported move type returned by PokeAPI: {api_type_name}"
            ) from exc

    async def _fetch_json(self, url: str) -> dict[str, Any]:
        response = await self._client.get(url)
        response.raise_for_status()
        return response.json()
