#!/usr/bin/env python3
"""AC-TPC-07 / AC-GCS-09 · flag GPL in the *runtime dependency closure*.

Default scope is the transitive runtime closure: starting from the names the
project declares (requirements*.txt / pyproject), we recursively expand every
installed dependency via ``importlib.metadata.requires`` and compare each
distribution's license against GPL. Optional ``extra`` requirements are skipped
(they are not part of the default runtime install). A small allowlist covers
known build-only tools (PyInstaller) that are packaged but never shipped.

Usage:
  python scripts/license_gpl_scan.py                # runtime closure (default)
  python scripts/license_gpl_scan.py --direct-only  # only declared names
  python scripts/license_gpl_scan.py --all-installed # every installed dist (noisy)
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


def _requirement_name(req: str) -> str | None:
    """Distribution name from a requirement string, skipping ``extra`` deps.

    ``importlib.metadata.requires`` yields entries like ``numpy>=1.2`` or
    ``mip; extra == "solver"``. Optional (extras) requirements are not installed
    in the default runtime, so we drop them; other markers (python_version, os)
    are treated permissively — the closure only needs candidate names to look up.
    """
    head, _, marker = req.partition(";")
    if "extra" in marker:
        return None
    name = re.split(r"[<>=!~ \[(;]", head, maxsplit=1)[0].strip()
    if not name:
        return None
    return name.lower().replace("_", "-")


def _runtime_closure(declared: set[str]) -> set[str]:
    """Transitive runtime dependency closure of ``declared`` (installed only)."""
    seen: set[str] = set()
    stack = list(declared)
    while stack:
        name = stack.pop()
        if name in seen:
            continue
        seen.add(name)
        try:
            reqs = metadata.requires(name) or []
        except metadata.PackageNotFoundError:
            # Declared but not installed — nothing to expand.
            continue
        for req in reqs:
            dep = _requirement_name(req)
            if dep and dep not in seen:
                stack.append(dep)
    return seen


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
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--all-installed",
        action="store_true",
        help="Scan every installed dist (noisy; superset of the runtime closure)",
    )
    group.add_argument(
        "--direct-only",
        action="store_true",
        help="Scan only directly declared names (legacy behavior; no transitive deps)",
    )
    args = parser.parse_args()

    declared = _declared_runtime_names()
    if args.all_installed:
        scope_names: set[str] | None = None
        scope = "all installed"
    elif args.direct_only:
        scope_names = set(declared)
        scope = "declared requirements (direct-only)"
    else:
        scope_names = _runtime_closure(set(declared))
        scope = "runtime dependency closure"

    hits: list[tuple[str, str]] = []
    for dist in metadata.distributions():
        name = (dist.metadata.get("Name") or "?").lower().replace("_", "-")
        if name in ALLOWLIST:
            continue
        if scope_names is not None and scope_names and name not in scope_names:
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

    count = len(scope_names) if scope_names is not None else 0
    if not hits:
        if scope_names is not None:
            print(f"OK: no GPL licenses in {scope} ({count} names, {len(declared)} declared)")
        else:
            print(f"OK: no GPL licenses in {scope}")
        return 0

    print(f"FAIL: GPL licenses in {scope}:", file=sys.stderr)
    for name, line in sorted(hits):
        print(f"  - {name}: {line}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
