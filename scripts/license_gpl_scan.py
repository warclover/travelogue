#!/usr/bin/env python3
"""AC-TPC-07 / AC-GCS-09 · flag GPL in *runtime* dependency closure.

Scans packages declared by the project (requirements*.txt / pyproject) that are
installed, plus a small allowlist for known build-only tools (PyInstaller).

Usage:
  python scripts/license_gpl_scan.py
"""

from __future__ import annotations

import argparse
import re
import sys
from importlib import metadata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

GPL_RE = re.compile(
    r"(?:^|[^A-Za-z])GPL(?:-[123](?:\.0)?)?\b|GNU General Public License",
    re.I,
)
# Build / packaging tools that may be GPL but are not shipped in app runtime.
ALLOWLIST = frozenset(
    {
        "pyinstaller",
        "pyinstaller-hooks-contrib",
        "altgraph",  # pyinstaller dep
    }
)


def _declared_runtime_names() -> set[str]:
    names: set[str] = set()
    for path in (
        ROOT / "requirements.txt",
        ROOT / "requirements-dev.txt",
        ROOT / "pyproject.toml",
    ):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if path.suffix == ".toml":
            for m in re.finditer(
                r'^\s*["\']([A-Za-z0-9_.-]+)["\']\s*[>=<~!]',
                text,
                re.M,
            ):
                names.add(m.group(1).lower().replace("_", "-"))
            for m in re.finditer(
                r'^\s*["\']([A-Za-z0-9_.-]+)[\[>=<~!]',
                text,
                re.M,
            ):
                names.add(m.group(1).lower().replace("_", "-"))
        else:
            for line in text.splitlines():
                line = line.strip()
                if not line or line.startswith("#") or line.startswith("-"):
                    continue
                name = re.split(r"[<>=!~;\[]", line, maxsplit=1)[0].strip()
                if name:
                    names.add(name.lower().replace("_", "-"))
    return names


def _license_blob(dist: metadata.Distribution) -> str:
    parts: list[str] = []
    try:
        meta = dist.metadata
    except Exception:
        return ""
    for key in ("License-Expression", "License"):
        v = meta.get(key)
        if v:
            parts.append(str(v))
    classifiers = meta.get_all("Classifier") if hasattr(meta, "get_all") else None
    if classifiers:
        parts.extend(str(c) for c in classifiers if "License ::" in str(c))
    return "\n".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--all-installed",
        action="store_true",
        help="Scan every installed dist (noisy; default = project requirements only)",
    )
    args = parser.parse_args()

    declared = _declared_runtime_names()
    hits: list[tuple[str, str]] = []
    for dist in metadata.distributions():
        name = (dist.metadata.get("Name") or "?").lower().replace("_", "-")
        if name in ALLOWLIST:
            continue
        if not args.all_installed and declared and name not in declared:
            continue
        blob = _license_blob(dist)
        if not blob:
            continue
        # Skip LGPL-only
        if re.search(r"\bLGPL\b|Lesser General Public", blob, re.I) and not re.search(
            r"(?<!Lesser )GNU General Public License|(?<![A-Z])GPL-[123]", blob, re.I
        ):
            continue
        if GPL_RE.search(blob):
            hits.append((name, blob.splitlines()[0][:140]))

    scope = "all installed" if args.all_installed else "project requirements"
    if not hits:
        print(f"OK: no GPL licenses in {scope} ({len(declared)} declared names)")
        return 0

    print(f"FAIL: GPL licenses in {scope}:", file=sys.stderr)
    for name, line in sorted(hits):
        print(f"  - {name}: {line}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
