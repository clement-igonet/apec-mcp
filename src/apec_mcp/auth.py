"""APEC session management — auto-login and cookie persistence."""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import httpx

_BASE_URL = "https://www.apec.fr"
_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"
)
_MAX_AGE_SECONDS = 20 * 3600  # re-login after 20 h (cookies last ~24 h)

_cached: dict[str, str] | None = None


def _session_file() -> Path:
    return Path(os.environ.get("APEC_SESSION_FILE", str(Path.home() / ".apec_session.json")))


def _load_from_file() -> dict[str, str] | None:
    f = _session_file()
    if not f.exists():
        return None
    try:
        data = json.loads(f.read_text())
        if time.time() - data.get("saved_at", 0) > _MAX_AGE_SECONDS:
            return None
        return data.get("cookies")
    except Exception:
        return None


def _save_to_file(cookies: dict[str, str]) -> None:
    try:
        f = _session_file()
        f.write_text(json.dumps({"saved_at": time.time(), "cookies": cookies}))
        f.chmod(0o600)
    except Exception:
        pass


async def login() -> dict[str, str]:
    """POST credentials to APEC and return the resulting session cookies."""
    email = os.environ["APEC_EMAIL"]
    password = os.environ["APEC_PASSWORD"]

    async with httpx.AsyncClient(follow_redirects=True) as client:
        # Visit the landing page first to initialise a session (JSESSIONID, srv_id, …)
        await client.get(
            f"{_BASE_URL}/candidat.html",
            headers={
                "accept": "text/html,application/xhtml+xml,*/*;q=0.8",
                "accept-language": "fr-FR,fr;q=0.9",
                "user-agent": _USER_AGENT,
            },
        )

        r = await client.post(
            f"{_BASE_URL}/.apec-login.do",
            data={
                "source": "loginApec",
                "username": email,
                "password": password,
            },
            headers={
                "accept": "application/json",
                "accept-language": "fr-FR,fr;q=0.9",
                "content-type": "application/x-www-form-urlencoded",
                "origin": _BASE_URL,
                "referer": f"{_BASE_URL}/candidat.html",
                "user-agent": _USER_AGENT,
                "x-requested-with": "XMLHttpRequest",
            },
        )
        r.raise_for_status()
        cookies = dict(client.cookies)

    _save_to_file(cookies)
    global _cached
    _cached = cookies
    return cookies


async def get_cookies() -> dict[str, str]:
    """Return valid session cookies, logging in automatically when needed."""
    global _cached

    if _cached is not None:
        return _cached

    # Backward-compat: manual cookie string takes precedence
    raw = os.environ.get("APEC_COOKIES", "")
    if raw:
        result: dict[str, str] = {}
        for part in raw.split("; "):
            part = part.strip()
            if "=" in part:
                k, v = part.split("=", 1)
                result[k.strip()] = v.strip()
        _cached = result
        return _cached

    # Try cached session on disk
    from_file = _load_from_file()
    if from_file:
        _cached = from_file
        return _cached

    # Auto-login
    return await login()


def invalidate() -> None:
    """Force re-authentication on the next API call."""
    global _cached
    _cached = None
    try:
        _session_file().unlink(missing_ok=True)
    except Exception:
        pass
