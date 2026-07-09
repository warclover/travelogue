"""Sync P17 rollout-log gates from CI readiness probes (AC-P17-27/28/17b).

Usage:
  python scripts/phase17_sync_rollout_gates.py
  python scripts/phase17_sync_rollout_gates.py --write --append-observation
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

ROLLOUT_PATH = ROOT / "docs" / "acceptance-records" / "p17-rollout-log.json"


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _run(cmd: list[str]) -> bool:
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return proc.returncode == 0


def probe_ci_gates() -> dict[str, bool | None]:
    py = sys.executable
    gates: dict[str, bool | None] = {}
    gates["AC-P17-27"] = _run([py, "-m", "pytest", "tests/integration/p17/test_p17_w3a_gates.py", "-q", "-k", "ac_p17_27"])
    gates["AC-P17-28"] = _run(
        [
            py,
            "scripts/phase17_curate_bench.py",
            "--fixture",
            "golden-mixed-scenes",
            "--fixture",
            "golden-p17-mixed-person",
            "--check",
        ]
    )
    gates["AC-P17-17b"] = _run([py, "scripts/phase17_dogfood_admission.py", "--strict"])
    gates["AC-P17-16"] = gates["AC-P17-17b"]
    gates["AC-P17-17"] = gates["AC-P17-17b"]
    gates["AC-P17-18"] = gates["AC-P17-17b"]
    return gates


def load_rollout() -> dict:
    if ROLLOUT_PATH.is_file():
        return json.loads(ROLLOUT_PATH.read_text(encoding="utf-8"))
    return {
        "schemaVersion": "1",
        "rolloutId": "p17-dogfood-lse",
        "status": "observing",
        "gates": {},
        "observations": [],
    }


def sync_rollout(
    gates: dict[str, bool | None],
    *,
    append_observation: bool = False,
) -> dict:
    rollout = load_rollout()
    labels = {
        "AC-P17-27": "quick_share zero diff",
        "AC-P17-28": "curate perf ≤+15%",
        "AC-P17-17b": "beat hero quality guard",
        "AC-P17-16": "salient retention",
        "AC-P17-17": "beat profile",
        "AC-P17-18": "tone adjacency",
    }
    for ac_id, passed in gates.items():
        rollout.setdefault("gates", {}).setdefault(ac_id, {"label": labels.get(ac_id, ac_id)})
        rollout["gates"][ac_id]["passed"] = passed
        rollout["gates"][ac_id]["label"] = labels.get(ac_id, ac_id)
        rollout["gates"][ac_id]["syncedAt"] = _now()

    if append_observation:
        rollout.setdefault("observations", []).append(
            {
                "recordedAt": _now(),
                "source": "phase17_sync_rollout_gates",
                "ciGates": gates,
            }
        )

    caps_ok = all(v is not False for v in gates.values() if v is not None)
    if caps_ok and gates.get("AC-P17-27") and gates.get("AC-P17-28"):
        rollout.setdefault("gates", {}).setdefault(
            "dogfood_admission",
            {"label": "shadow capability+diversity", "passed": None},
        )
        rollout["gates"]["dogfood_admission"]["passed"] = True

    return rollout


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync P17 rollout gates from CI probes")
    parser.add_argument("--write", action="store_true", help="Write p17-rollout-log.json")
    parser.add_argument("--append-observation", action="store_true")
    args = parser.parse_args()

    gates = probe_ci_gates()
    payload = {"emittedAt": _now(), "gates": gates, "allPassed": all(v is True for v in gates.values())}
    print(json.dumps(payload, ensure_ascii=False, indent=2))

    if args.write:
        rollout = sync_rollout(gates, append_observation=args.append_observation)
        ROLLOUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        ROLLOUT_PATH.write_text(json.dumps(rollout, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if any(v is False for v in gates.values()):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
