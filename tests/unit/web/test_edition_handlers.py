"""PFM · POST /trips/{id}/edition（BE-PFM-15）。"""

from __future__ import annotations

import copy
import uuid
from dataclasses import replace

import pytest

from travelogue.config import AppConfig, PortfolioPipelineConfig
from travelogue.config.edition import (
    E_PORTFOLIO_PAGE_COUNT,
    E_PORTFOLIO_PAGES_JOURNAL,
    E_PORTFOLIO_UNAVAILABLE,
)
from travelogue.web.studio_handlers.edition_handlers import (
    E_PORTFOLIO_CONFIRM_REQUIRED,
    E_PORTFOLIO_SWITCH_DISABLED,
)


def _cfg(*, enabled: bool = True, allow_refine: bool = True) -> AppConfig:
    base = AppConfig()
    return replace(
        base,
        studio=replace(
            base.studio,
            portfolio_pipeline=PortfolioPipelineConfig(
                enabled=enabled,
                allow_refine_switch=allow_refine,
            ),
        ),
    )


class _H:
    def __init__(self, body: dict) -> None:
        self._payload = body
        self.status = None
        self.body = None

    def _read_json_body(self):
        return self._payload

    def _json_response(self, status, body):
        self.status = status
        self.body = body


def test_edition_switch_requires_literal_true(tmp_path, monkeypatch) -> None:
    from travelogue.web.studio_handlers import edition_handlers as mod

    trip_dir = tmp_path / "t"
    trip_dir.mkdir()
    (trip_dir / "trip.json").write_text("{}", encoding="utf-8")

    h = _H({"edition": "portfolio", "confirmed": "true"})
    monkeypatch.setattr(mod, "load_trip_or_404", lambda *_a, **_k: (trip_dir, {}))
    mod.handle_trip_edition(h, "demo")
    assert h.status == 400
    assert h.body["error"] == E_PORTFOLIO_CONFIRM_REQUIRED


def test_edition_switch_flag_off_rejects_portfolio(tmp_path, monkeypatch) -> None:
    from travelogue.web.studio_handlers import edition_handlers as mod

    trip_dir = tmp_path / "t"
    trip_dir.mkdir()
    (trip_dir / "trip.json").write_text("{}", encoding="utf-8")

    class _Ctx:
        cfg = _cfg(enabled=False)

        def trip_service(self):
            raise AssertionError("must not start job")

    monkeypatch.setattr(mod, "load_trip_or_404", lambda *_a, **_k: (trip_dir, {}))
    monkeypatch.setattr(mod, "studio_ctx", lambda *_a, **_k: _Ctx())
    h = _H({"edition": "portfolio", "confirmed": True})
    mod.handle_trip_edition(h, "demo")
    assert h.status == 409
    assert h.body["error"] == E_PORTFOLIO_UNAVAILABLE


def test_edition_switch_disabled_rejects_portfolio(tmp_path, monkeypatch) -> None:
    from travelogue.web.studio_handlers import edition_handlers as mod

    trip_dir = tmp_path / "t"
    trip_dir.mkdir()

    class _Ctx:
        cfg = _cfg(enabled=True, allow_refine=False)

        def trip_service(self):
            raise AssertionError("must not start job")

    monkeypatch.setattr(mod, "load_trip_or_404", lambda *_a, **_k: (trip_dir, {}))
    monkeypatch.setattr(mod, "studio_ctx", lambda *_a, **_k: _Ctx())
    h = _H({"edition": "portfolio", "confirmed": True})
    mod.handle_trip_edition(h, "demo")
    assert h.status == 409
    assert h.body["error"] == E_PORTFOLIO_SWITCH_DISABLED


def test_edition_same_identity_is_unchanged(tmp_path, monkeypatch) -> None:
    from travelogue.web.studio_handlers import edition_handlers as mod

    trip_dir = tmp_path / "t"
    trip_dir.mkdir()
    monkeypatch.setattr(mod, "load_trip_or_404", lambda *_a, **_k: (trip_dir, {}))
    h = _H({"edition": "journal", "confirmed": True})
    mod.handle_trip_edition(h, "demo")
    assert h.status == 200
    assert h.body["unchanged"] is True
    assert h.body["edition"] == "journal"


def test_edition_journal_allowed_when_flag_off(tmp_path, monkeypatch) -> None:
    from travelogue.web.studio_handlers import edition_handlers as mod
    from travelogue.web.studio_jobs import get_job_store

    store = get_job_store()
    store.finish_g1()
    store.finish_import()
    trip_id = f"ed-j-{uuid.uuid4().hex[:8]}"
    trip_dir = tmp_path / trip_id
    trip_dir.mkdir()
    (trip_dir / "trip.json").write_text("{}", encoding="utf-8")
    curate_kwargs: dict = {}

    class _Svc:
        def load(self, *_a, **_k):
            return {
                "studio": {
                    "edition": "portfolio",
                    "portfolio": {"pageCount": 16},
                }
            }

        def update(self, _path, mutator, **_k):
            trip = {
                "studio": {
                    "edition": "portfolio",
                    "portfolio": {"pageCount": 16},
                }
            }
            mutator(trip)
            return None

    class _Ctx:
        cfg = _cfg(enabled=False)

        def trip_service(self):
            return _Svc()

    def _curate(trip, **kwargs):
        curate_kwargs.update(kwargs)
        trip.setdefault("studio", {}).pop("edition", None)

    monkeypatch.setattr(mod, "load_trip_or_404", lambda *_a, **_k: (trip_dir, {
        "studio": {"edition": "portfolio", "portfolio": {"pageCount": 16}}
    }))
    monkeypatch.setattr(mod, "studio_ctx", lambda *_a, **_k: _Ctx())
    monkeypatch.setattr("travelogue.curation.curate.run_curate", _curate)
    monkeypatch.setattr(
        "travelogue.domain.pipeline_view.unlock_structure_for_replan",
        lambda trip: None,
    )
    monkeypatch.setattr("travelogue.render.engine.render_trip_surfaces", lambda *a, **k: None)

    class _ImmediateThread:
        def __init__(self, target=None, daemon=None):
            self._target = target

        def start(self) -> None:
            assert self._target is not None
            self._target()

    monkeypatch.setattr(mod.threading, "Thread", _ImmediateThread)
    h = _H({"edition": "journal", "confirmed": True})
    try:
        mod.handle_trip_edition(h, trip_id)
        assert h.status == 202
        assert curate_kwargs.get("refresh_algorithms") is False
        assert curate_kwargs.get("apply_layout") is True
    finally:
        for job in list(store._jobs.values()):
            if job.trip_id == trip_id:
                store.finalize(job, status="cancelled")
        store.finish_g1()


def test_edition_runner_stamps_portfolio_without_refresh(tmp_path, monkeypatch) -> None:
    from travelogue.web.studio_handlers import edition_handlers as mod
    from travelogue.web.studio_jobs import get_job_store

    store = get_job_store()
    store.finish_g1()
    store.finish_import()
    trip_id = f"ed-p-{uuid.uuid4().hex[:8]}"
    trip_dir = tmp_path / trip_id
    trip_dir.mkdir()
    (trip_dir / "trip.json").write_text("{}", encoding="utf-8")
    written: dict = {}
    curate_kwargs: dict = {}

    class _Svc:
        def load(self, *_a, **_k):
            return {"studio": {}, "chapters": [], "curation": {}, "pipeline": {}}

        def update(self, _path, mutator, **_k):
            trip = {"studio": {}, "chapters": [], "curation": {}, "pipeline": {}}
            mutator(trip)
            written.clear()
            written.update(trip)
            return None

    class _Ctx:
        cfg = _cfg(enabled=True)

        def trip_service(self):
            return _Svc()

    def _curate(trip, **kwargs):
        curate_kwargs.update(kwargs)
        folio = trip.setdefault("studio", {}).setdefault("portfolio", {})
        folio["pageCount"] = 16

    monkeypatch.setattr(mod, "load_trip_or_404", lambda *_a, **_k: (trip_dir, {}))
    monkeypatch.setattr(mod, "studio_ctx", lambda *_a, **_k: _Ctx())
    monkeypatch.setattr("travelogue.curation.curate.run_curate", _curate)
    monkeypatch.setattr(
        "travelogue.domain.pipeline_view.unlock_structure_for_replan",
        lambda trip: None,
    )
    render_kwargs: dict = {}

    def _render(*_a, **kwargs):
        render_kwargs.update(kwargs)

    monkeypatch.setattr("travelogue.render.engine.render_trip_surfaces", _render)

    class _ImmediateThread:
        def __init__(self, target=None, daemon=None):
            self._target = target

        def start(self) -> None:
            assert self._target is not None
            self._target()

    monkeypatch.setattr(mod.threading, "Thread", _ImmediateThread)
    h = _H({"edition": "portfolio", "confirmed": True})
    try:
        mod.handle_trip_edition(h, trip_id)
        assert h.status == 202
        assert curate_kwargs.get("refresh_algorithms") is False
        assert written.get("studio", {}).get("edition") == "portfolio"
        assert written.get("studio", {}).get("portfolio", {}).get("pageCount") == 16
        assert render_kwargs.get("stamp_render_bundle") is True
        assert render_kwargs.get("update_pipeline") is False
    finally:
        for job in list(store._jobs.values()):
            if job.trip_id == trip_id:
                store.finalize(job, status="cancelled")
        store.finish_g1()


def test_page_count_on_journal_is_rejected(tmp_path, monkeypatch) -> None:
    from travelogue.web.studio_handlers import edition_handlers as mod

    trip_dir = tmp_path / "t"
    trip_dir.mkdir()
    monkeypatch.setattr(mod, "load_trip_or_404", lambda *_a, **_k: (trip_dir, {}))
    h = _H({"pageCount": 16})
    mod.handle_trip_edition(h, "demo")
    assert h.status == 400
    assert h.body["error"] == E_PORTFOLIO_PAGES_JOURNAL


def test_page_count_invalid_is_rejected(tmp_path, monkeypatch) -> None:
    from travelogue.web.studio_handlers import edition_handlers as mod

    trip_dir = tmp_path / "t"
    trip_dir.mkdir()
    monkeypatch.setattr(
        mod,
        "load_trip_or_404",
        lambda *_a, **_k: (trip_dir, {"studio": {"edition": "portfolio"}}),
    )
    h = _H({"pageCount": "eighteen"})
    mod.handle_trip_edition(h, "demo")
    assert h.status == 400
    assert h.body["error"] == E_PORTFOLIO_PAGE_COUNT


def test_page_count_only_skips_confirm_and_recomposes(tmp_path, monkeypatch) -> None:
    from travelogue.web.studio_handlers import edition_handlers as mod
    from travelogue.web.studio_jobs import get_job_store

    store = get_job_store()
    store.finish_g1()
    store.finish_import()
    trip_id = f"ed-pg-{uuid.uuid4().hex[:8]}"
    trip_dir = tmp_path / trip_id
    trip_dir.mkdir()
    (trip_dir / "trip.json").write_text("{}", encoding="utf-8")
    written: dict = {}
    curate_kwargs: dict = {}

    class _Svc:
        def load(self, *_a, **_k):
            return {"studio": {"edition": "portfolio", "portfolio": {"pageCountSource": "auto"}}}

        def update(self, _path, mutator, **_k):
            trip = {"studio": {"edition": "portfolio", "portfolio": {"pageCountSource": "auto"}}}
            mutator(trip)
            written.clear()
            written.update(trip)

    class _Ctx:
        cfg = _cfg(enabled=True)

        def trip_service(self):
            return _Svc()

    def _curate(trip, **kwargs):
        curate_kwargs.update(kwargs)

    monkeypatch.setattr(
        mod,
        "load_trip_or_404",
        lambda *_a, **_k: (
            trip_dir,
            {"studio": {"edition": "portfolio", "portfolio": {"pageCountSource": "auto"}}},
        ),
    )
    monkeypatch.setattr(mod, "studio_ctx", lambda *_a, **_k: _Ctx())
    monkeypatch.setattr("travelogue.curation.curate.run_curate", _curate)
    monkeypatch.setattr(
        "travelogue.domain.pipeline_view.unlock_structure_for_replan",
        lambda trip: None,
    )
    monkeypatch.setattr("travelogue.render.engine.render_trip_surfaces", lambda *a, **k: None)

    class _ImmediateThread:
        def __init__(self, target=None, daemon=None):
            self._target = target

        def start(self) -> None:
            assert self._target is not None
            self._target()

    monkeypatch.setattr(mod.threading, "Thread", _ImmediateThread)
    h = _H({"pageCount": 16})
    try:
        mod.handle_trip_edition(h, trip_id)
        assert h.status == 202
        assert curate_kwargs.get("refresh_algorithms") is False
        assert written.get("studio", {}).get("portfolio", {}).get("pageCount") == 16
        assert written.get("studio", {}).get("portfolio", {}).get("pageCountSource") == "user"
    finally:
        for job in list(store._jobs.values()):
            if job.trip_id == trip_id:
                store.finalize(job, status="cancelled")
        store.finish_g1()


def test_edition_switch_orphans_user_caption(tmp_path, monkeypatch) -> None:
    from travelogue.web.studio_handlers import edition_handlers as mod
    from travelogue.web.studio_jobs import get_job_store

    store = get_job_store()
    store.finish_g1()
    store.finish_import()
    trip_id = f"ed-copy-{uuid.uuid4().hex[:8]}"
    trip_dir = tmp_path / trip_id
    trip_dir.mkdir()
    (trip_dir / "trip.json").write_text("{}", encoding="utf-8")
    written: dict = {}

    src = {
        "studio": {},
        "pipeline": {"status": "copy_locked", "locks": {"copy": True, "structure": True}},
        "chapters": [
            {
                "id": "ch-01",
                "title": "手改章名",
                "titleOrigin": "user",
                "items": [
                    {
                        "type": "media-card",
                        "assetId": "a1",
                        "caption": "手改图注",
                        "captionOrigin": "user",
                    }
                ],
                "screens": [{"screenId": "s1", "slots": [{"assetId": "a1"}]}],
            }
        ],
    }

    class _Svc:
        def load(self, *_a, **_k):
            return copy.deepcopy(src)

        def update(self, _path, mutator, **_k):
            trip = copy.deepcopy(src)
            mutator(trip)
            written.clear()
            written.update(trip)

    class _Ctx:
        cfg = _cfg(enabled=True)

        def trip_service(self):
            return _Svc()

    def _curate(trip, **_k):
        trip["chapters"][0]["items"] = [{"type": "media-card", "assetId": "a1"}]
        trip["chapters"][0]["screens"] = [
            {"screenId": "ch-01-sc-01", "slots": [{"assetId": "a1"}]}
        ]

    monkeypatch.setattr(mod, "load_trip_or_404", lambda *_a, **_k: (trip_dir, {}))
    monkeypatch.setattr(mod, "studio_ctx", lambda *_a, **_k: _Ctx())
    monkeypatch.setattr("travelogue.curation.curate.run_curate", _curate)
    monkeypatch.setattr("travelogue.render.engine.render_trip_surfaces", lambda *a, **k: None)

    class _ImmediateThread:
        def __init__(self, target=None, daemon=None):
            self._target = target

        def start(self) -> None:
            assert self._target is not None
            self._target()

    monkeypatch.setattr(mod.threading, "Thread", _ImmediateThread)
    h = _H({"edition": "portfolio", "confirmed": True})
    try:
        mod.handle_trip_edition(h, trip_id)
        assert h.status == 202
        orphans = written.get("studio", {}).get("copyOrphans") or []
        assert any(row.get("text") == "手改图注" for row in orphans)
        assert written["chapters"][0]["title"] == "手改章名"
        assert (written.get("pipeline") or {}).get("locks", {}).get("copy") is False
    finally:
        for job in list(store._jobs.values()):
            if job.trip_id == trip_id:
                store.finalize(job, status="cancelled")
        store.finish_g1()
