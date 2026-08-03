"""LVP M2 · layout-vibe Studio API (AC-04/05)."""

from __future__ import annotations

import pytest

from travelogue.config.layout_vibe import (
    VIBE_FIT_PHOTO_EXPERIMENTAL,
    VIBE_MAGAZINE_DEFAULT,
)
from travelogue.paths import ROOT
from travelogue.web.studio_handlers.layout_vibe_handlers import (
    EXPERIMENTAL_CONFIRM_BODY,
    layout_vibe_options,
)


def test_layout_vibe_options_have_no_algorithm_jargon() -> None:
    """AC-LVP-04 · UI options must not expose MTSO/MEGC/MSA/SSG/LSE."""
    banned = ("MTSO", "MEGC", "MSA", "SSG", "LSE", "slot_adaptation", "selection_optimization")
    for opt in layout_vibe_options():
        human = f"{opt['label']} {opt['consequence']} {opt['badge']}"
        for token in banned:
            assert token not in human, human
        assert opt["id"] in (VIBE_MAGAZINE_DEFAULT, VIBE_FIT_PHOTO_EXPERIMENTAL)


def test_ac_lvp_05_experimental_requires_confirm() -> None:
    """AC-LVP-05 · experimental without confirmedExperimental → 400."""
    from travelogue.web.studio_handlers import layout_vibe_handlers as mod

    class _H:
        def __init__(self) -> None:
            self.status = None
            self.body = None

        def _read_json_body(self):
            return {"layoutVibe": VIBE_FIT_PHOTO_EXPERIMENTAL}

        def _json_response(self, status, body):
            self.status = status
            self.body = body

    h = _H()
    mod.handle_layout_vibe(h, "demo-lvp")
    assert h.status == 400
    assert h.body["error"] == "E_LVP_CONFIRM_REQUIRED"
    assert "篇幅" in EXPERIMENTAL_CONFIRM_BODY or "页数" in EXPERIMENTAL_CONFIRM_BODY
    assert "改回" in EXPERIMENTAL_CONFIRM_BODY


def test_ac_lvp_05_magazine_does_not_require_confirm(monkeypatch: pytest.MonkeyPatch) -> None:
    """Recommended vibe may proceed past the confirm gate (busy/404 ok)."""
    from travelogue.web.studio_handlers import layout_vibe_handlers as mod

    class _H:
        def __init__(self) -> None:
            self.status = None
            self.body = None

        def _read_json_body(self):
            return {"layoutVibe": VIBE_MAGAZINE_DEFAULT}

        def _json_response(self, status, body):
            self.status = status
            self.body = body

    monkeypatch.setattr(mod, "load_trip_or_404", lambda *_a, **_k: None)
    h = _H()
    mod.handle_layout_vibe(h, "demo-lvp")
    # load_trip_or_404 stub returns None → handler returns without setting status
    assert h.status is None or h.status != 400 or h.body.get("error") != "E_LVP_CONFIRM_REQUIRED"


def test_ui_source_has_no_algorithm_jargon_in_lvp_copy() -> None:
    """AC-LVP-04 · features.js LVP card copy gate."""
    text = (ROOT / "templates/studio/preview-toolbar/features.js").read_text(encoding="utf-8")
    # slice around mountLayoutVibeControls defaults
    start = text.find("_LVP_DEFAULT_OPTIONS")
    end = text.find("export function mountLayoutVibeControls")
    chunk = text[start:end]
    for token in ("MTSO", "MEGC", "MSA", "SSG", "LSE"):
        assert token not in chunk
    assert "杂志成册" in chunk
    assert "更贴照片比例" in chunk
    next_export = text.find("\nexport function", end + 1)
    fn = text[end : next_export if next_export > 0 else end + 12000]
    assert "toolbarConfirm" in fn
    assert "confirmedExperimental" in fn


def test_sheet_book_panel_hosts_layout_vibe_zone() -> None:
    sheet = (ROOT / "templates/studio/preview-toolbar-v3-sheet.js").read_text(encoding="utf-8")
    assert 'data-book-zone="layout-vibe"' in sheet
    assert "mountLayoutVibeControls" in sheet
    assert "成册风格" in sheet


def test_route_layout_vibe_registered() -> None:
    from travelogue.web.studio_dispatch import studio_route_snapshot

    rows = studio_route_snapshot()
    hit = [
        r
        for r in rows
        if r["path"] == "/__travelogue/trips/{tripId}/layout-vibe" and r["method"] == "POST"
    ]
    assert hit
    assert hit[0]["handler"] == "trip_handlers.handle_layout_vibe"
