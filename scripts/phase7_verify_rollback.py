"""Phase 7 rollback verification CLI (AC-P7-08 drill).

Usage:
  python scripts/phase7_verify_rollback.py --dry-run
  python scripts/phase7_verify_rollback.py --apply
  python scripts/phase7_verify_rollback.py --apply --run-equivalence --strict-equivalence
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config.yaml"
EQUIVALENCE_SCRIPT = ROOT / "scripts" / "phase7_equivalence_check.py"


def rollback_patch() -> dict[str, Any]:
    """Return Phase 7 -> P6 rollback patch."""
    return {
        "vision": {
            "batch_size": 0,
            "prefer_web_derivative": False,
        },
        "pipeline": {
            "parallel_embed": False,
        },
        "ingest": {
            "webp_method": 6,
        },
        "layout_scoring": {
            "incremental": False,
        },
    }


def _deep_set(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    for key, value in patch.items():
        if isinstance(value, dict):
            child = base.get(key)
            if not isinstance(child, dict):
                child = {}
                base[key] = child
            _deep_set(child, value)
        else:
            base[key] = value
    return base


def _deep_get(base: dict[str, Any], path: list[str]) -> Any:
    cur: Any = base
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return None
        cur = cur[key]
    return cur


def _verify_patch_applied(config_data: dict[str, Any], patch: dict[str, Any]) -> list[str]:
    mismatches: list[str] = []

    def walk(node: dict[str, Any], path: list[str]) -> None:
        for key, value in node.items():
            next_path = path + [key]
            if isinstance(value, dict):
                walk(value, next_path)
                continue
            got = _deep_get(config_data, next_path)
            if got != value:
                dotted = ".".join(next_path)
                mismatches.append(f"{dotted}: expected={value!r} got={got!r}")

    walk(patch, [])
    return mismatches


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("PyYAML is required to read config.yaml") from exc

    if not path.is_file():
        raise FileNotFoundError(f"config file not found: {path}")
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ValueError(f"config root must be object: {path}")
    return raw


def _save_yaml(path: Path, data: dict[str, Any]) -> None:
    try:
        import yaml  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("PyYAML is required to write config.yaml") from exc

    dumped = yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
    path.write_text(dumped, encoding="utf-8")


def _run_equivalence(strict: bool) -> tuple[bool, str]:
    if not EQUIVALENCE_SCRIPT.is_file():
        msg = f"equivalence script missing: {EQUIVALENCE_SCRIPT}"
        return (False, msg) if strict else (True, msg)

    cmd = [sys.executable, str(EQUIVALENCE_SCRIPT)]
    proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    ok = proc.returncode == 0
    tail = (proc.stdout or proc.stderr or "").strip()
    if len(tail) > 800:
        tail = tail[-800:]
    if ok:
        return True, "phase7_equivalence_check passed"
    return False, f"phase7_equivalence_check failed (code={proc.returncode}): {tail}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply and verify Phase 7 rollback patch")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG, help="path to config.yaml")
    parser.add_argument("--dry-run", action="store_true", help="print rollback patch and exit")
    parser.add_argument("--apply", action="store_true", help="apply rollback patch to config.yaml")
    parser.add_argument(
        "--run-equivalence",
        action="store_true",
        help="run scripts/phase7_equivalence_check.py after verification",
    )
    parser.add_argument(
        "--strict-equivalence",
        action="store_true",
        help="treat missing/failing equivalence script as failure",
    )
    parser.add_argument("--write-backup", action="store_true", help="write .bak before apply")
    args = parser.parse_args()

    patch = rollback_patch()
    if args.dry_run:
        print(json.dumps({"patch": patch}, indent=2, ensure_ascii=False))
        return 0

    cfg_path = args.config.resolve()
    try:
        data = _load_yaml(cfg_path)
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2

    summary: dict[str, Any] = {"config": str(cfg_path), "patch": patch}
    if args.apply:
        if args.write_backup:
            backup = cfg_path.with_suffix(cfg_path.suffix + ".bak")
            backup.write_text(cfg_path.read_text(encoding="utf-8"), encoding="utf-8")
            summary["backup"] = str(backup)
        _deep_set(data, patch)
        _save_yaml(cfg_path, data)
        summary["applied"] = True
    else:
        summary["applied"] = False

    reloaded = _load_yaml(cfg_path)
    mismatches = _verify_patch_applied(reloaded, patch)
    summary["mismatches"] = mismatches
    summary["verified"] = not mismatches

    if args.run_equivalence:
        ok, msg = _run_equivalence(strict=args.strict_equivalence)
        summary["equivalenceCheck"] = {"ok": ok, "message": msg}
        if not ok:
            print(json.dumps(summary, indent=2, ensure_ascii=False))
            return 3

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if summary["verified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

