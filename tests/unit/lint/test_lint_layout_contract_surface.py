"""Tests for scripts/lint_layout_contract_surface.py (P2-C)."""

from __future__ import annotations

from scripts.lint_layout_contract_surface import lint_file, lint_package, main
from tests._repo_root import repo_root

ROOT = repo_root(__file__)


def test_package_is_clean() -> None:
    assert lint_package() == []


def test_main_ok() -> None:
    assert main() == 0


def test_flags_curation_import() -> None:
    rel = "travelogue/layout_contract/_probe_bad.py"
    probe = ROOT / rel
    try:
        probe.write_text(
            "from travelogue.curation.curate import run_curate\n",
            encoding="utf-8",
        )
        viol = lint_file(probe)
        assert len(viol) == 1
        assert "curation" in viol[0]
    finally:
        probe.unlink(missing_ok=True)


def test_allows_util_import() -> None:
    rel = "travelogue/layout_contract/_probe_ok.py"
    probe = ROOT / rel
    try:
        probe.write_text(
            "from travelogue.util.datetime_ import utc_now\n",
            encoding="utf-8",
        )
        assert lint_file(probe) == []
    finally:
        probe.unlink(missing_ok=True)


def test_flags_unknown_travelogue_import() -> None:
    rel = "travelogue/layout_contract/_probe_unknown.py"
    probe = ROOT / rel
    try:
        probe.write_text(
            "from travelogue.services.trip import TripService\n",
            encoding="utf-8",
        )
        viol = lint_file(probe)
        assert len(viol) == 1
        assert "services" in viol[0]
    finally:
        probe.unlink(missing_ok=True)
