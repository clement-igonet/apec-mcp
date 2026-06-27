"""Thin async HTTP client for the APEC REST API."""
from __future__ import annotations

import os
from typing import Any

import httpx

from apec_mcp import auth

BASE_URL = "https://www.apec.fr"
_TIMEOUT = 30


def account_id() -> str:
    return os.environ["APEC_ID_COMPTE_CADRE"]


def profile_id() -> str:
    return os.environ["APEC_ID_PROFIL_CADRE"]


def _headers() -> dict[str, str]:
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


async def _request(method: str, path: str, **kwargs: Any) -> Any:
    """Execute a request, retrying once with a fresh login on 401/403."""
    for attempt in range(2):
        cookies = await auth.get_cookies()
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            r = await client.request(
                method,
                f"{BASE_URL}{path}",
                headers=_headers(),
                cookies=cookies,
                **kwargs,
            )
        if r.status_code in (401, 403) and attempt == 0:
            auth.invalidate()
            continue
        r.raise_for_status()
        ct = r.headers.get("content-type", "")
        if "json" in ct:
            return r.json()
        return r.text
    raise RuntimeError("Authentication failed after re-login attempt")


async def get(path: str, params: dict | None = None) -> Any:
    return await _request("GET", path, params=params)


async def post(path: str, body: Any, params: dict | None = None) -> Any:
    return await _request("POST", path, json=body, params=params)
