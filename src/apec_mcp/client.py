"""Thin async HTTP client for the APEC REST API."""
from __future__ import annotations

import os
from typing import Any

import httpx

BASE_URL = "https://www.apec.fr"
_TIMEOUT = 30


def account_id() -> str:
    return os.environ["APEC_ID_COMPTE_CADRE"]


def profile_id() -> str:
    return os.environ["APEC_ID_PROFIL_CADRE"]


def cookies() -> dict[str, str]:
    raw = os.environ.get("APEC_COOKIES", "")
    result: dict[str, str] = {}
    for part in raw.split("; "):
        part = part.strip()
        if "=" in part:
            k, v = part.split("=", 1)
            result[k.strip()] = v.strip()
    return result


def headers() -> dict[str, str]:
    return {
        "accept": "application/json, text/plain, */*",
        "accept-language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
        "content-type": "application/json",
        "origin": BASE_URL,
        "referer": f"{BASE_URL}/candidat/mon-espace/profil.html",
        "user-agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"
        ),
    }


async def get(path: str, params: dict | None = None) -> Any:
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        r = await client.get(
            f"{BASE_URL}{path}", headers=headers(), cookies=cookies(), params=params
        )
        r.raise_for_status()
        return r.json()


async def post(path: str, body: Any, params: dict | None = None) -> Any:
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        r = await client.post(
            f"{BASE_URL}{path}",
            headers=headers(),
            cookies=cookies(),
            json=body,
            params=params,
        )
        r.raise_for_status()
        ct = r.headers.get("content-type", "")
        if "json" in ct:
            return r.json()
        return r.text
