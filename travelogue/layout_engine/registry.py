"""LSE Strategy Pack registry."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from travelogue.layout_engine.policy import LsePolicy, load_policy
from travelogue.layout_engine.validator import validate_strategy_doc

PACKAGE_ROOT = Path(__file__).resolve().parent
DEFAULT_STRATEGIES_DIR = PACKAGE_ROOT / "strategies"

_ACTIVE_STATUSES = frozenset({"experimental", "beta", "ga"})


@dataclass(frozen=True)
class StrategyPack:
    id: str
    version: int
    status: str
    algorithm_version: str
    display_name: str
    content_hash: str
    path: Path
    raw: dict[str, Any]

    def weights_hash(self, profile_id: str = "default") -> str:
        profiles = self.raw.get("scoring_profiles") or {}
        profile = profiles.get(profile_id) or {}
        payload = {
            "strategyId": self.id,
            "strategyVersion": self.version,
            "profileId": profile_id,
            "weights": profile.get("weights") or {},
            "penalties": profile.get("penalties") or {},
        }
        digest = hashlib.sha256(
            json.dumps(payload, sort_keys=True).encode("utf-8")
        ).hexdigest()[:16]
        return f"sha256:{digest}"


def content_hash(doc: dict[str, Any]) -> str:
    raw = json.dumps(doc, sort_keys=True).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()[:16]


def strategy_pack_from_yaml(path: Path, doc: dict[str, Any]) -> StrategyPack:
    return StrategyPack(
        id=str(doc["id"]),
        version=int(doc["version"]),
        status=str(doc["status"]),
        algorithm_version=str(doc["algorithm_version"]),
        display_name=str(doc["displayName"]),
        content_hash=content_hash(doc),
        path=path,
        raw=doc,
    )


def load_strategy_pack(path: Path) -> StrategyPack:
    with path.open(encoding="utf-8") as f:
        doc = yaml.safe_load(f) or {}
    if not isinstance(doc, dict):
        raise ValueError(f"invalid strategy pack: {path}")
    report = validate_strategy_doc(doc)
    if not report.ok:
        msg = "; ".join(f"{i.path}: {i.message}" for i in report.issues[:3])
        raise ValueError(f"strategy pack validation failed ({path}): {msg}")
    return strategy_pack_from_yaml(path, doc)


def list_strategy_files(strategies_dir: Path | None = None) -> list[Path]:
    root = strategies_dir or DEFAULT_STRATEGIES_DIR
    return sorted(p for p in root.glob("*.yaml") if p.is_file())


def list_active_strategies(
    *,
    policy: LsePolicy | None = None,
    strategies_dir: Path | None = None,
) -> list[StrategyPack]:
    pol = policy or load_policy()
    root = strategies_dir or pol.strategies_dir
    packs: list[StrategyPack] = []
    for path in list_strategy_files(root):
        pack = load_strategy_pack(path)
        if pack.status in _ACTIVE_STATUSES:
            packs.append(pack)
    return packs


@lru_cache(maxsize=8)
def get_strategy_pack(strategy_id: str, policy_path: str | None = None) -> StrategyPack:
    pol = load_policy(policy_path)
    for path in list_strategy_files(pol.strategies_dir):
        pack = load_strategy_pack(path)
        if pack.id == strategy_id:
            return pack
    raise KeyError(f"strategy pack not found: {strategy_id}")


def clear_registry_cache() -> None:
    get_strategy_pack.cache_clear()
