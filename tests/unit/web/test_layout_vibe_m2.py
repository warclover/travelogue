"""LVP M2 · layout-vibe Studio API (AC-04/05)."""

from __future__ import annotations

import uuid

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


def test_iso06_lvp_rejects_portfolio_trip(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    """ISO-06 · LVP API 拒作品集 trip，不得改 edition / 重跑游记装配。"""
    from travelogue.web.studio_handlers import layout_vibe_handlers as mod

    trip_dir = tmp_path / "pf-lvp"
    trip_dir.mkdir()
    trip = {
        "studio": {"edition": "portfolio", "layoutVibe": VIBE_MAGAZINE_DEFAULT},
        "chapters": [{"id": "keep-me", "screens": [{"patternId": "page-6-grid-land"}]}],
    }
    (trip_dir / "trip.json").write_text(
        __import__("json").dumps(trip, ensure_ascii=False), encoding="utf-8"
    )

    class _H:
        def __init__(self) -> None:
            self.status = None
            self.body = None

        def _read_json_body(self):
            return {"layoutVibe": VIBE_FIT_PHOTO_EXPERIMENTAL, "confirmed": True}

        def _json_response(self, status, body):
            self.status = status
            self.body = body

    def _apply(*_a, **_k):
        raise AssertionError("LVP must not recompose a portfolio trip")

    monkeypatch.setattr(mod, "load_trip_or_404", lambda *_a, **_k: (trip_dir, trip))
    monkeypatch.setattr("travelogue.services.layout.apply_layout_to_trip", _apply)
    h = _H()
    mod.handle_layout_vibe(h, "pf-lvp")
    assert h.status == 409
    assert h.body["error"] == "E_LVP_PORTFOLIO"
    disk = __import__("json").loads((trip_dir / "trip.json").read_text(encoding="utf-8"))
    assert disk["studio"]["edition"] == "portfolio"
    assert disk["studio"]["layoutVibe"] == VIBE_MAGAZINE_DEFAULT
    assert disk["chapters"][0]["id"] == "keep-me"


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


@pytest.mark.parametrize("bad", ["false", "0", 1, "true", 0])
def test_ac_lvp_05_confirm_rejects_non_bool_true(bad: object) -> None:
    """Only JSON literal true satisfies AC-LVP-05 (not truthy strings/ints)."""
    from travelogue.web.studio_handlers import layout_vibe_handlers as mod

    class _H:
        def __init__(self) -> None:
            self.status = None
            self.body = None

        def _read_json_body(self):
            return {
                "layoutVibe": VIBE_FIT_PHOTO_EXPERIMENTAL,
                "confirmedExperimental": bad,
            }

        def _json_response(self, status, body):
            self.status = status
            self.body = body

    h = _H()
    mod.handle_layout_vibe(h, "demo-lvp")
    assert h.status == 400
    assert h.body["error"] == "E_LVP_CONFIRM_REQUIRED"


def test_lvp_binds_trip_id_before_job_runs(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """Busy gate needs trip_id on the job before the worker thread starts."""
    from travelogue.web.studio_handlers import layout_vibe_handlers as mod
    from travelogue.web.studio_jobs import get_job_store

    store = get_job_store()
    # create_g1_continue_job also refuses when import slot is held — clear both.
    store.finish_g1()
    store.finish_import()
    # Unique trip id · avoid 409 from leftover trip busy / on-demand flags.
    trip_id = f"demo-lvp-busy-{uuid.uuid4().hex[:8]}"
    trip_dir = tmp_path / trip_id
    trip_dir.mkdir()
    (trip_dir / "trip.json").write_text("{}", encoding="utf-8")

    class _H:
        def __init__(self) -> None:
            self.status = None
            self.body = None

        def _read_json_body(self):
            return {"layoutVibe": VIBE_MAGAZINE_DEFAULT}

        def _json_response(self, status, body):
            self.status = status
            self.body = body

    class _Svc:
        def load(self, *_a, **_k):
            raise AssertionError("runner must not start when Thread.start is noop")

        def update(self, *_a, **_k):
            raise AssertionError("runner must not start when Thread.start is noop")

    class _Ctx:
        cfg = None

        def trip_service(self):
            return _Svc()

    monkeypatch.setattr(mod, "load_trip_or_404", lambda *_a, **_k: (trip_dir, {}))
    monkeypatch.setattr(mod, "studio_ctx", lambda *_a, **_k: _Ctx())

    class _NoopThread:
        def __init__(self, *a, **k):
            pass

        def start(self) -> None:
            return None

    monkeypatch.setattr(mod.threading, "Thread", _NoopThread)

    h = _H()
    try:
        mod.handle_layout_vibe(h, trip_id)
        assert h.status == 202
        assert store.is_trip_busy(trip_id)
    finally:
        for job in list(store._jobs.values()):
            if job.trip_id == trip_id:
                store.finalize(job, status="cancelled")
        store.finish_g1()


def test_lvp_runner_preserves_export_layout_auto(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """Screens apply may use web profile, but auto must remain on disk."""
    from travelogue.web.studio_handlers import layout_vibe_handlers as mod
    from travelogue.web.studio_jobs import get_job_store

    store = get_job_store()
    store.finish_g1()
    store.finish_import()
    trip_id = f"demo-auto-{uuid.uuid4().hex[:8]}"
    trip_dir = tmp_path / trip_id
    trip_dir.mkdir()
    (trip_dir / "trip.json").write_text("{}", encoding="utf-8")
    written: dict = {}

    class _H:
        def __init__(self) -> None:
            self.status = None
            self.body = None

        def _read_json_body(self):
            return {"layoutVibe": VIBE_MAGAZINE_DEFAULT}

        def _json_response(self, status, body):
            self.status = status
            self.body = body

    class _Svc:
        def load(self, *_a, **_k):
            return {
                "exportLayout": "auto",
                "layoutEngine": "screens",
                "studio": {},
                "chapters": [{"id": "c1"}],
                "curation": {},
                "pipeline": {},
            }

        def update(self, _path, mutator, **_k):
            trip = {
                "exportLayout": "auto",
                "layoutEngine": "screens",
                "studio": {},
                "chapters": [{"id": "c1"}],
                "curation": {},
                "pipeline": {},
            }
            mutator(trip)
            written.clear()
            written.update(trip)
            return None

    class _Ctx:
        cfg = None

        def trip_service(self):
            return _Svc()

    def _apply(trip, **kwargs):
        trip["exportLayout"] = kwargs.get("export_layout") or "web"
        trip["chapters"] = [{"id": "rebuilt"}]
        trip["layoutEngine"] = "screens"
        trip["layoutEngineVersion"] = "screens-test"

    monkeypatch.setattr(mod, "load_trip_or_404", lambda *_a, **_k: (trip_dir, {}))
    monkeypatch.setattr(mod, "studio_ctx", lambda *_a, **_k: _Ctx())
    monkeypatch.setattr(
        "travelogue.services.layout.apply_layout_to_trip",
        _apply,
    )
    monkeypatch.setattr(
        "travelogue.render.engine.render_trip_surfaces",
        lambda *a, **k: None,
    )
    monkeypatch.setattr(
        "travelogue.layout_engine.api.resolve_layout_engine",
        lambda trip: "screens",
    )

    class _ImmediateThread:
        def __init__(self, target=None, daemon=None):
            self._target = target

        def start(self) -> None:
            assert self._target is not None
            self._target()

    monkeypatch.setattr(mod.threading, "Thread", _ImmediateThread)

    h = _H()
    try:
        mod.handle_layout_vibe(h, trip_id)
        assert h.status == 202
        assert written.get("exportLayout") == "auto"
        assert written.get("chapters") == [{"id": "rebuilt"}]
        assert (written.get("studio") or {}).get("layoutVibe") == VIBE_MAGAZINE_DEFAULT
    finally:
        for job in list(store._jobs.values()):
            if job.trip_id == trip_id:
                store.finalize(job, status="cancelled")
        store.finish_g1()


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
    assert "成册类型" in sheet


def test_help_h8_points_to_docs_not_lse() -> None:
    """SHD-02 · Help H8 (LVP) must not link LSE admin; H7 stays NAS-reserved."""
    text = (ROOT / "templates/studio/js/help-onboarding.js").read_text(encoding="utf-8")
    assert 'id: "H8"' in text
    assert 'id: "H7"' not in text
    assert "成册风格" in text
    assert "lse-flags-admin" not in text.lower()
    features = (ROOT / "templates/studio/preview-toolbar/features.js").read_text(
        encoding="utf-8"
    )
    assert 'itemId: "H8"' in features
    assert "lse-flags-admin" not in features.lower()


def test_shd01_wireframe_exists() -> None:
    wf = ROOT / "docs/wireframes/layout-vibe-picker-f1-wireframe.html"
    assert wf.is_file()
    html = wf.read_text(encoding="utf-8")
    assert "杂志成册" in html
    assert "更贴照片比例" in html
    assert "改用「更贴照片比例」" in html
    for token in ("MTSO", "MEGC", "MSA", "LSE"):
        assert token not in html


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
