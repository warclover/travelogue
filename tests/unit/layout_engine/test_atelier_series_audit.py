"""AS-PFM-03 · atelier YAML reconcile (tests may read reserve; runtime must not)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

from travelogue.layout_engine.editorial_series.catalog import (
    assert_not_reserve_path,
    load_official_series,
    official_series_dir,
)
from travelogue.paths import ROOT

pytestmark = pytest.mark.unit

ATELIER_SERIES = ROOT / "docs" / "templates" / "reserve" / "series"
LTE_TEMPLATES = ROOT / "travelogue" / "layout_templates" / "templates"
FOLIO_ID_RE = re.compile(r"^folio-(\d+)-")
KNOWN_MISSING_FACES = frozenset({"page-10-grid-port"})


def _atelier_docs() -> list[tuple[Path, dict]]:
    rows: list[tuple[Path, dict]] = []
    for path in sorted(ATELIER_SERIES.glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        assert isinstance(data, dict), path.name
        rows.append((path, data))
    return rows


def test_as_pfm_03_atelier_id_matches_pagecount_and_sequence() -> None:
    docs = _atelier_docs()
    assert docs, "atelier series cabinet is empty"
    for path, data in docs:
        sid = str(data.get("id") or path.stem)
        matched = FOLIO_ID_RE.match(sid)
        assert matched, f"{path.name} id {sid!r} is not folio-{{pages}}-"
        id_pages = int(matched.group(1))
        page_count = int(data.get("pageCount") or 0)
        sequence = data.get("sequence") or []
        assert page_count == id_pages, (
            f"{sid} pageCount {page_count} != id pages {id_pages}"
        )
        assert isinstance(sequence, list) and len(sequence) == page_count, (
            f"{sid} sequence {len(sequence)} != pageCount {page_count}"
        )


def test_as_pfm_03_folio24_is_not_labeled_32() -> None:
    path = ATELIER_SERIES / "folio-24-standard.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert data["id"] == "folio-24-standard"
    assert int(data["pageCount"]) == 24
    assert len(data["sequence"]) == 24


def test_as_pfm_03_folio16_matches_official_p0_faces() -> None:
    atelier = yaml.safe_load(
        (ATELIER_SERIES / "folio-16-standard.yaml").read_text(encoding="utf-8")
    )
    official = load_official_series()
    gold = next(row for row in official if row["id"] == "magazine-16-standard")
    assert gold["id"] == "magazine-16-standard"
    want = [str(page.get("faceHint") or "") for page in atelier["sequence"]]
    got = [
        str(page.get("faceHint") or page.get("patternId") or "")
        for page in gold["sequence"]
    ]
    assert got == want
    assert gold["photo_span"] == atelier["photo_span"] == [48, 80]


def test_as_pfm_03_promote_blockers_stay_honest() -> None:
    lte_ids = {path.stem for path in LTE_TEMPLATES.glob("page-*.yaml")}
    missing: dict[str, set[str]] = {}
    over_max: list[str] = []
    for path, data in _atelier_docs():
        sid = str(data.get("id") or path.stem)
        if int(data.get("pageCount") or 0) > 32:
            over_max.append(sid)
        absent = {
            str(page.get("faceHint") or "")
            for page in (data.get("sequence") or [])
            if str(page.get("faceHint") or "")
            and str(page.get("faceHint")) not in lte_ids
        }
        if absent:
            missing[sid] = absent
    assert missing == {
        "folio-32-standard-r2": set(KNOWN_MISSING_FACES),
        "folio-36-standard": set(KNOWN_MISSING_FACES),
    }
    assert over_max == ["folio-36-standard"]
    assert "page-10-grid-port" not in lte_ids


def test_runtime_catalog_still_refuses_reserve() -> None:
    with pytest.raises(ValueError, match="must not read"):
        assert_not_reserve_path(ATELIER_SERIES)
    with pytest.raises(ValueError, match="must not read"):
        load_official_series(series_dir=ATELIER_SERIES)
    assert official_series_dir().resolve() != ATELIER_SERIES.resolve()
