"""AC-P17-13 · algorithm_version bump policy for Strategy Pack changes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from travelogue.paths import ROOT

DEFAULT_LOCK_PATH = ROOT / "docs" / "acceptance-records" / "p17-algorithm-version.lock.json"


def load_algorithm_lock(path: str | Path | None = None) -> dict[str, Any]:
    p = Path(path or DEFAULT_LOCK_PATH)
    if not p.is_file():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def pack_fingerprint(pack: Any) -> dict[str, Any]:
    return {
        "strategyId": pack.id,
        "strategyVersion": pack.version,
        "algorithmVersion": pack.algorithm_version,
        "contentHash": pack.content_hash,
    }


def validate_pack_against_lock(
    pack: Any,
    *,
    lock_path: str | Path | None = None,
) -> tuple[bool, str | None]:
    """Require explicit algorithm_version or strategy version bump when content_hash changes."""
    lock = load_algorithm_lock(lock_path)
    if not lock:
        return True, None
    if lock.get("strategyId") and lock["strategyId"] != pack.id:
        return False, "strategyId mismatch vs lock"
    if lock.get("contentHash") == pack.content_hash:
        if lock.get("algorithmVersion") != pack.algorithm_version:
            return False, "algorithm_version changed without content_hash change"
        return True, None
    bumped = (
        lock.get("algorithmVersion") != pack.algorithm_version
        or int(lock.get("strategyVersion") or 0) != int(pack.version)
    )
    if not bumped:
        return False, "content_hash changed but algorithm_version/strategy version not bumped"
    return True, None
