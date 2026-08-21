"""MSP · promote-series.py gates (AC-MSP-06 / 25 / 26 / 27)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
import yaml

_REPO = Path(__file__).resolve().parents[3]
_SPEC = importlib.util.spec_from_file_location(
    "promote_series", _REPO / "scripts" / "promote-series.py"
)
assert _SPEC and _SPEC.loader
_mod = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_mod)
GOLD_ID = _mod.GOLD_ID
GateError = _mod.GateError
check_gate10 = _mod.check_gate10
main = _mod.main
promote_one = _mod.promote_one
rewrite_ids = _mod.rewrite_ids

pytestmark = pytest.mark.unit

REPO = Path(__file__).resolve().parents[3]
ATELIER = REPO / "docs" / "templates" / "reserve" / "series"
FACE = REPO / "travelogue" / "layout_templates" / "templates"
APPENDIX_B = REPO / "docs" / "templates" / "ROLE-FACE-MAP.md"
ROLE_MAP = REPO / "docs" / "templates" / "reserve" / "PROMOTE-ROLE-MAP.md"


def _promote(tmp_path: Path, source: Path, **kwargs):
    return promote_one(
        source,
        face_dir=FACE,
        appendix_b=APPENDIX_B,
        role_map=ROLE_MAP,
        dest_dir=tmp_path,
        overwrite=set(kwargs.get("overwrite") or ()),
        confirm_gold=bool(kwargs.get("confirm_gold")),
        dry_run=bool(kwargs.get("dry_run")),
        now="2026-08-21T00:00:00Z",
    )


def test_rewrite_r2_drops_suffix_and_sets_version() -> None:
    dest_id, version = rewrite_ids("folio-28-standard-r2")
    assert dest_id == "magazine-28-standard"
    assert version == 2


def test_gate02_missing_face_does_not_write(tmp_path: Path) -> None:
    source = tmp_path / "folio-8-standard.yaml"
    source.write_text(
        """
id: folio-8-standard
pageCount: 8
density: standard
photo_span: [24, 40]
sequence:
  - { i: 1, role: hero-land, program: hero, faceHint: page-does-not-exist }
  - { i: 2, role: pair-port, program: mosaic, faceHint: page-2-pair-port }
  - { i: 3, role: hero-land, program: hero, faceHint: page-1-hero-land-wide }
  - { i: 4, role: hero-land, program: hero, faceHint: page-1-hero-land-wide }
  - { i: 5, role: hero-land, program: hero, faceHint: page-1-hero-land-wide }
  - { i: 6, role: hero-land, program: hero, faceHint: page-1-hero-land-wide }
  - { i: 7, role: hero-land, program: hero, faceHint: page-1-hero-land-wide }
  - { i: 8, role: hero-land, program: hero, faceHint: page-1-hero-land-wide }
""",
        encoding="utf-8",
    )
    with pytest.raises(GateError, match="GATE-02"):
        _promote(tmp_path / "out", source)
    assert not (tmp_path / "out" / "magazine-8-standard.yaml").exists()


def test_gate11_refuses_existing_without_overwrite(tmp_path: Path) -> None:
    dest = tmp_path / "out"
    dest.mkdir()
    (dest / "magazine-8-standard.yaml").write_text(
        "id: magazine-8-standard\npageCount: 8\n", encoding="utf-8"
    )
    with pytest.raises(GateError, match="GATE-11"):
        _promote(dest, ATELIER / "folio-8-standard.yaml")


def test_gate11_gold_needs_confirm(tmp_path: Path) -> None:
    dest = tmp_path / "out"
    dest.mkdir()
    (dest / f"{GOLD_ID}.yaml").write_text(
        yaml.dump(
            {
                "id": GOLD_ID,
                "pageCount": 16,
                "sequence": [{"patternId": "page-old"}] * 16,
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(GateError, match="GATE-11"):
        _promote(
            dest,
            ATELIER / "folio-16-standard.yaml",
            overwrite={GOLD_ID},
        )


def test_gate10_only_flags_20_to_24() -> None:
    ladder = [
        {"pageCount": 8, "capacity": 27},
        {"pageCount": 12, "capacity": 36},
        {"pageCount": 16, "capacity": 53},
        {"pageCount": 20, "capacity": 72},
        {"pageCount": 24, "capacity": 73},
        {"pageCount": 28, "capacity": 81},
        {"pageCount": 32, "capacity": 116},
        {"pageCount": 36, "capacity": 134},
    ]
    with pytest.raises(GateError, match="GATE-10"):
        check_gate10(ladder)
    without_24 = [row for row in ladder if row["pageCount"] != 24]
    check_gate10(without_24)
    only_neighbors = [
        {"pageCount": 16, "capacity": 53},
        {"pageCount": 20, "capacity": 72},
        {"pageCount": 28, "capacity": 81},
    ]
    check_gate10(only_neighbors)


def test_promote_folio8_writes_capacity(tmp_path: Path) -> None:
    dest_id, dest_path = _promote(tmp_path, ATELIER / "folio-8-standard.yaml")
    assert dest_id == "magazine-8-standard"
    data = yaml.safe_load(dest_path.read_text(encoding="utf-8"))
    assert data["capacity"] == 27
    assert data["version"] == 1
    assert len(data["sequence"]) == 8
    assert data["sequence"][0]["patternId"] == "page-1-hero-land-wide"
    assert data["_promotedFrom"]["atelierId"] == "folio-8-standard"


def test_dry_run_does_not_write(tmp_path: Path) -> None:
    dest_id, dest_path = _promote(
        tmp_path, ATELIER / "folio-8-standard.yaml", dry_run=True
    )
    assert dest_id == "magazine-8-standard"
    assert not dest_path.exists()


def test_cli_repeat_without_overwrite_is_nonzero(tmp_path: Path) -> None:
    dest = tmp_path / "series"
    rc = main(
        [
            "--id",
            "folio-8-standard",
            "--dest-dir",
            str(dest),
            "--dry-run",
        ]
    )
    assert rc == 0
    assert not (dest / "magazine-8-standard.yaml").exists()
    rc = main(["--id", "folio-8-standard", "--dest-dir", str(dest)])
    assert rc == 0
    rc = main(["--id", "folio-8-standard", "--dest-dir", str(dest)])
    assert rc == 1


def test_script_does_not_import_runtime_packages() -> None:
    src = (REPO / "scripts" / "promote-series.py").read_text(encoding="utf-8")
    assert "from travelogue.layout_engine" not in src
    assert "import travelogue.layout_engine" not in src
    assert "from travelogue.layout_templates" not in src
    assert "import travelogue.layout_templates" not in src
