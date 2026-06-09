"""LSE global policy loader."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

PACKAGE_ROOT = Path(__file__).resolve().parent
DEFAULT_POLICY_PATH = PACKAGE_ROOT / "lse_policy.yaml"


@dataclass(frozen=True)
class LsePolicy:
    policy_version: str
    default_strategy_id: str
    strategies_dir: Path
    raw: dict[str, Any]

    @classmethod
    def from_dict(cls, doc: dict[str, Any], *, base_dir: Path | None = None) -> LsePolicy:
        strategies_rel = str(doc.get("strategies_dir", "travelogue/layout_engine/strategies"))
        strategies_path = Path(strategies_rel)
        if not strategies_path.is_absolute():
            from travelogue.paths import ROOT

            strategies_path = (ROOT / strategies_path).resolve()
        return cls(
            policy_version=str(doc.get("policy_version", "p17-2026-06")),
            default_strategy_id=str(doc.get("default_strategy_id", "lse-default-2026-06")),
            strategies_dir=strategies_path,
            raw=dict(doc),
        )


def load_policy(path: Path | str | None = None) -> LsePolicy:
    policy_path = Path(path) if path else DEFAULT_POLICY_PATH
    if not policy_path.is_absolute():
        from travelogue.paths import ROOT

        policy_path = (ROOT / policy_path).resolve()
    with policy_path.open(encoding="utf-8") as f:
        doc = yaml.safe_load(f) or {}
    if not isinstance(doc, dict):
        raise ValueError(f"invalid LSE policy YAML: {policy_path}")
    return LsePolicy.from_dict(doc)
