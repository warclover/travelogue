"""Optional reverse geocode for EXIF GPS (city-level only)."""

from __future__ import annotations

import json
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

_NOMINATIM_MIN_INTERVAL_S = 1.1
_geocode_lock = threading.Lock()
_last_geocode_at = 0.0


def _throttle_nominatim() -> None:
    global _last_geocode_at
    with _geocode_lock:
        now = time.monotonic()
        wait = _NOMINATIM_MIN_INTERVAL_S - (now - _last_geocode_at)
        if wait > 0:
            time.sleep(wait)
        _last_geocode_at = time.monotonic()


def _cache_key(lat: float, lon: float) -> str:
    return f"{lat:.4f},{lon:.4f}"


def _load_cache(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _save_cache(path: Path, cache: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


def reverse_geocode_city(
    lat: float,
    lon: float,
    *,
    cache_path: Path,
    enabled: bool = True,
    user_agent: str = "Travelogue/0.2",
) -> str | None:
    """
    Return city-level name via Nominatim when enabled.

    Results are cached locally; failures return None (no network throw).
    """
    if not enabled:
        return None

    key = _cache_key(lat, lon)
    cache = _load_cache(cache_path)
    if key in cache:
        return cache[key] or None

    params = urllib.parse.urlencode(
        {
            "format": "json",
            "lat": f"{lat:.6f}",
            "lon": f"{lon:.6f}",
            "zoom": 10,
            "addressdetails": 1,
        }
    )
    url = f"https://nominatim.openstreetmap.org/reverse?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": user_agent})
    city: str | None = None
    try:
        _throttle_nominatim()
        with urllib.request.urlopen(req, timeout=8) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        address = payload.get("address") if isinstance(payload, dict) else {}
        if isinstance(address, dict):
            for field in ("city", "town", "village", "county", "state"):
                val = address.get(field)
                if isinstance(val, str) and val.strip():
                    city = val.strip()[:32]
                    break
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        city = None

    cache[key] = city or ""
    _save_cache(cache_path, cache)
    return city
