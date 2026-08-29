"""RCL W0 · frontend live-path closure (AC-RCL-03 / BLK-RCL-09)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from scripts.lint_frontend_live_path import (
    INVENTORY,
    LIVE_PATH_ROOTS,
    check_live_path,
    main,
    parse_inventory,
    walk_live_closure,
)

pytestmark = [pytest.mark.unit]


def _write(root: Path, rel: str, body: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def _inventory(*rows: tuple[str, str]) -> str:
    lines = ["| 文件 | 状态 | 被谁 import | 禁止事项 |", "|---|---|---|---|"]
    for path, status in rows:
        lines.append(f"| `{path}` | {status} | test | — |")
    return "\n".join(lines) + "\n"


def test_roots_are_the_two_hardcoded_constants() -> None:
    assert LIVE_PATH_ROOTS == (
        "templates/studio/preview-toolbar.js",
        "templates/studio/homepage-v2/bootstrap.js",
    )


def test_repo_inventory_covers_closure() -> None:
    rows = parse_inventory(INVENTORY.read_text(encoding="utf-8"))
    assert {row.status for row in rows} <= {"LIVE", "READER", "FROZEN", "GENERATED"}
    closure = walk_live_closure()
    registered = {row.path for row in rows}
    assert LIVE_PATH_ROOTS[0] in registered
    assert LIVE_PATH_ROOTS[1] in registered
    assert closure <= registered
    assert any(row.status == "FROZEN" for row in rows)
    assert any(row.path.endswith("visual-journal/longshot.js") for row in rows)
    assert check_live_path() == []


def test_unregistered_import_is_red(tmp_path: Path) -> None:
    _write(tmp_path, LIVE_PATH_ROOTS[0], 'import "./extra.js";\n')
    _write(tmp_path, LIVE_PATH_ROOTS[1], "export {}\n")
    _write(tmp_path, "templates/studio/extra.js", "export {}\n")
    text = _inventory((LIVE_PATH_ROOTS[0], "LIVE"), (LIVE_PATH_ROOTS[1], "LIVE"))
    hits = check_live_path(root=tmp_path, inventory_text=text)
    assert any("unregistered" in row and "extra.js" in row for row in hits)


def test_frozen_imported_by_live_root_is_red(tmp_path: Path) -> None:
    _write(tmp_path, LIVE_PATH_ROOTS[0], 'import "./classic.js";\n')
    _write(tmp_path, LIVE_PATH_ROOTS[1], "export {}\n")
    _write(tmp_path, "templates/studio/classic.js", "export {}\n")
    text = _inventory(
        (LIVE_PATH_ROOTS[0], "LIVE"),
        (LIVE_PATH_ROOTS[1], "LIVE"),
        ("templates/studio/classic.js", "FROZEN"),
    )
    hits = check_live_path(root=tmp_path, inventory_text=text)
    assert any("FROZEN" in row and "classic.js" in row for row in hits)


def test_multiline_from_is_followed(tmp_path: Path) -> None:
    _write(
        tmp_path,
        LIVE_PATH_ROOTS[0],
        'import {\n  init\n} from "./preview-toolbar/init-v3.js";\n',
    )
    _write(tmp_path, LIVE_PATH_ROOTS[1], "export {}\n")
    _write(tmp_path, "templates/studio/preview-toolbar/init-v3.js", "export {}\n")
    text = _inventory(
        (LIVE_PATH_ROOTS[0], "LIVE"),
        (LIVE_PATH_ROOTS[1], "LIVE"),
        ("templates/studio/preview-toolbar/init-v3.js", "LIVE"),
    )
    assert check_live_path(root=tmp_path, inventory_text=text) == []
    assert "templates/studio/preview-toolbar/init-v3.js" in walk_live_closure(tmp_path)


def test_main_green_on_repo() -> None:
    assert main([]) == 0


# AC-RCL-16 · §7.2 required headers (status enum in the file head).
_W3_HEADER_FILES = (
    ("templates/studio/preview-toolbar.js", "LIVE"),
    ("templates/studio/homepage-v2/bootstrap.js", "LIVE"),
    ("templates/studio/preview-toolbar/init-v3.js", "LIVE"),
    ("templates/studio/preview-toolbar/bootstrap.js", "LIVE"),
    ("templates/studio/preview-toolbar/dock.js", "LIVE"),
    ("templates/studio/preview-toolbar-v3-sheet.js", "LIVE"),
    ("templates/studio/preview-toolbar-v3-task-dock.js", "LIVE"),
    ("templates/visual-journal/longshot.js", "READER"),
    ("templates/visual-journal/journal.css", "LIVE"),
    ("templates/visual-journal/journal-screens.css", "LIVE"),
    ("templates/visual-journal/portfolio-pages.css", "LIVE"),
)
_STATUS_RE = re.compile(r"\b(LIVE|READER|FROZEN|GENERATED)\b")


def test_w3_required_files_have_status_headers() -> None:
    from scripts.lint_frontend_live_path import ROOT

    for rel, expected in _W3_HEADER_FILES:
        head = "\n".join((ROOT / rel).read_text(encoding="utf-8").splitlines()[:20])
        found = _STATUS_RE.findall(head)
        assert found, rel
        assert found[0] == expected, rel
