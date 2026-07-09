"""P5-12.2 · single-track acceptance documentation hub."""



from __future__ import annotations

from tests._repo_root import repo_root

ROOT = repo_root(__file__)
ACCEPTANCE = ROOT / "docs" / "ACCEPTANCE.md"
RECORDS_README = ROOT / "docs" / "acceptance-records" / "README.md"


def test_acceptance_hub_links_phase5_gate() -> None:
    text = ACCEPTANCE.read_text(encoding="utf-8")
    assert "单轨入口" in text
    assert "ACCEPTANCE-PHASE5.md" in text
    assert "UX-P5-80-01" in text
    assert "phase5-zero-edit.json" in text


def test_acceptance_hub_mvp_crosswalk() -> None:
    text = ACCEPTANCE.read_text(encoding="utf-8")
    assert "MVP → Phase 对照" in text
    assert "附录 A" in text


def test_acceptance_records_readme_index() -> None:
    text = RECORDS_README.read_text(encoding="utf-8")
    assert "phase5-peval.json" in text
    assert "phase4-intent.json" in text
    assert "ACCEPTANCE.md" in text
