"""ASH M3 · shared helpers for source-text contract assertions.

Prefer field/symbol checks over exact formatting of whole export lines.
Mark intentional literal locks with ``# ASH-CONTRACT`` at the call site.
"""

from __future__ import annotations

import re
from collections.abc import Sequence


def assert_contains_all(
    source: str,
    needles: Sequence[str],
    *,
    where: str,
) -> None:
    """Assert every needle appears in source (with context on failure)."""
    for needle in needles:
        assert needle in source, f"{where}: missing {needle!r}"


def assert_exported_const(
    source: str,
    name: str,
    *,
    where: str,
) -> None:
    """Assert ``export const NAME`` exists (no exact RHS formatting)."""
    assert f"export const {name}" in source, f"{where}: missing export const {name}"


def assert_exported_string_const(
    source: str,
    name: str,
    value: str,
    *,
    where: str,
) -> None:
    """Assert exported string const equals value (allows spacing variance)."""
    assert_exported_const(source, name, where=where)
    pattern = rf'export\s+const\s+{re.escape(name)}\s*=\s*["\']{re.escape(value)}["\']'
    assert re.search(pattern, source), (
        f"{where}: expected {name} == {value!r}"
    )


def assert_exported_array_members(
    source: str,
    name: str,
    members: Sequence[str],
    *,
    where: str,
) -> None:
    """Assert exported array const contains members (order not required)."""
    assert_exported_const(source, name, where=where)
    match = re.search(
        rf"export\s+const\s+{re.escape(name)}\s*=\s*\[([^\]]*)\]",
        source,
        flags=re.S,
    )
    assert match, f"{where}: could not parse array export {name}"
    body = match.group(1)
    for member in members:
        assert f'"{member}"' in body or f"'{member}'" in body, (
            f"{where}: {name} missing member {member!r}"
        )


def assert_js_exports(
    source: str,
    names: Sequence[str],
    *,
    module: str,
) -> None:
    """Assert symbols are exported (function or const)."""
    for name in names:
        as_fn = f"export function {name}"
        as_const = f"export const {name}"
        assert as_fn in source or as_const in source or f"export {{ {name}" in source, (
            f"{module}: missing export for {name!r}"
        )
