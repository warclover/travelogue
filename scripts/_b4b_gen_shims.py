#!/usr/bin/env python3
"""Generate curation/ shims for M-B4b moved modules."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHIM_HEADER = '''\
"""Deprecated shim · moved to layout_engine (M-B4b)."""

import warnings

warnings.warn(
    "{message}",
    DeprecationWarning,
    stacklevel=2,
)

'''

PLANNER_MODULES = [
    "screen_planner",
    "screen_planner_stages",
    "screen_planner_attach",
    "layout_search",
]


def write_shim(old_mod: str, new_mod: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    message = f"{old_mod} is deprecated; use {new_mod}"
    body = SHIM_HEADER.format(message=message)
    # Re-export public and private names (legacy_bridge imports _LANDSCAPE_* etc.).
    body += "from importlib import import_module\n"
    body += f"_mod = import_module({new_mod!r})\n"
    body += "for _name, _value in vars(_mod).items():\n"
    body += "    if _name.startswith('__'):\n"
    body += "        continue\n"
    body += "    globals()[_name] = _value\n"
    body += "del _mod, _name, _value\n"
    path.write_text(body, encoding="utf-8")
    print(f"wrote {path.relative_to(ROOT)}")


def main() -> None:
    for name in PLANNER_MODULES:
        write_shim(
            f"travelogue.curation.{name}",
            f"travelogue.layout_engine.planner.{name}",
            ROOT / "travelogue" / "curation" / f"{name}.py",
        )

    mosaic_dir = ROOT / "travelogue" / "layout_engine" / "mosaic"
    shim_root = ROOT / "travelogue" / "curation" / "mosaic"
    shim_root.mkdir(parents=True, exist_ok=True)
    for path in sorted(mosaic_dir.glob("*.py")):
        name = path.stem
        write_shim(
            f"travelogue.curation.mosaic.{name}",
            f"travelogue.layout_engine.mosaic.{name}",
            shim_root / f"{name}.py",
        )

    init = shim_root / "__init__.py"
    write_shim(
        "travelogue.curation.mosaic",
        "travelogue.layout_engine.mosaic",
        init,
    )


if __name__ == "__main__":
    main()
