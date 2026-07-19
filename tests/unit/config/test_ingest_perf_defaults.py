"""PRD-PIPELINE-PERF-V1 · R1.3 / R1.4 default knobs (E-B rollback via config)."""

from __future__ import annotations

from travelogue.config.ingest import IngestConfig, ingest_from_dict


def test_ingest_perf_defaults() -> None:
    cfg = IngestConfig()
    assert cfg.face_detect_max_edge == 1024
    assert cfg.webp_method == 2


def test_ingest_from_dict_defaults_match() -> None:
    cfg = ingest_from_dict({})
    assert cfg.face_detect_max_edge == 1024
    assert cfg.webp_method == 2


def test_ingest_eb_rollback_via_config() -> None:
    cfg = ingest_from_dict({"face_detect_max_edge": 0, "webp_method": 4})
    assert cfg.face_detect_max_edge == 0
    assert cfg.webp_method == 4
