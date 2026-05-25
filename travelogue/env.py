"""Load local .env into os.environ (does not override existing vars)."""

from __future__ import annotations

import os
import re
from pathlib import Path

from travelogue.paths import ROOT

_ENV_LOADED = False


def _parse_env_line(line: str) -> tuple[str, str] | None:
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    if line.startswith("export "):
        line = line[7:].strip()
    if "=" not in line:
        return None
    key, _, value = line.partition("=")
    key = key.strip()
    if not key or not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", key):
        return None
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        value = value[1:-1]
    return key, value


def load_dotenv_files() -> list[Path]:
    """Load project .env files; return paths that were read."""
    global _ENV_LOADED
    if _ENV_LOADED:
        return []
    _ENV_LOADED = True

    loaded: list[Path] = []
    seen: set[Path] = set()
    for candidate in (ROOT / ".env", Path.cwd() / ".env"):
        path = candidate.resolve()
        if path in seen or not path.is_file():
            continue
        seen.add(path)
        for raw in path.read_text(encoding="utf-8").splitlines():
            parsed = _parse_env_line(raw)
            if not parsed:
                continue
            key, value = parsed
            if key not in os.environ:
                os.environ[key] = value
        loaded.append(path)
    return loaded
