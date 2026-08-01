"""L0 Hardening · resolve stub + bootstrap config + job error payload."""

from __future__ import annotations

from pathlib import Path

import pytest

from travelogue.paths import (
    OWNERSHIP_MARKER_NAME,
    _force_bootstrap_llm_provider_stub,
    _force_bootstrap_vision_disabled,
    ensure_user_data_layout,
)
from travelogue.web.studio_errors import is_llm_auth_recoverable, job_error_payload
from travelogue.web.studio_narrate import (
    resolve_studio_narrate_provider,
    resolve_studio_narrate_provider_if_ready,
)


def test_resolve_studio_narrate_provider_always_stub_for_import() -> None:
    assert resolve_studio_narrate_provider() == "stub"
    assert resolve_studio_narrate_provider(force_stub=True) == "stub"
    assert resolve_studio_narrate_provider(force_stub=False) == "stub"


def test_resolve_studio_narrate_provider_if_ready_without_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "travelogue.web.studio_narrate.studio_llm_status",
        lambda *, cfg=None: {"llmAvailable": False, "llmProvider": "deepseek"},
    )
    assert resolve_studio_narrate_provider_if_ready() == "stub"


def test_resolve_studio_narrate_provider_if_ready_with_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "travelogue.web.studio_narrate.resolve_llm_may_call",
        lambda *, cfg=None: True,
    )
    monkeypatch.setattr(
        "travelogue.web.studio_narrate.studio_llm_status",
        lambda *, cfg=None: {"llmAvailable": True, "llmProvider": "deepseek"},
    )
    assert resolve_studio_narrate_provider_if_ready() == "deepseek"


def test_resolve_studio_narrate_provider_if_ready_blocked_without_may_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "travelogue.web.studio_narrate.resolve_llm_may_call",
        lambda *, cfg=None: False,
    )
    monkeypatch.setattr(
        "travelogue.web.studio_narrate.studio_llm_status",
        lambda *, cfg=None: {"llmAvailable": True, "llmProvider": "deepseek"},
    )
    assert resolve_studio_narrate_provider_if_ready() == "stub"


def test_job_error_payload_marks_llm_auth_recoverable() -> None:
    payload = job_error_payload("E_LLM_AUTH")
    assert payload["code"] == "E_LLM_AUTH"
    assert payload["recoverableWithStub"] is True
    assert is_llm_auth_recoverable("E_LLM_AUTH")
    assert not is_llm_auth_recoverable("E_STUDIO_PIPELINE")
    plain = job_error_payload("E_STUDIO_PIPELINE")
    assert "recoverableWithStub" not in plain


def test_force_bootstrap_llm_provider_stub_rewrites_deepseek(tmp_path: Path) -> None:
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        "trips_dir: ./trips\n\nllm:\n  provider: deepseek\n  model: deepseek-chat\n",
        encoding="utf-8",
    )
    _force_bootstrap_llm_provider_stub(cfg)
    text = cfg.read_text(encoding="utf-8")
    assert "provider: stub" in text
    assert "provider: deepseek" not in text
    assert "model: deepseek-chat" in text


def test_force_bootstrap_vision_disabled(tmp_path: Path) -> None:
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        "trips_dir: ./trips\n\nvision:\n  enabled: true\n  model: foo\n",
        encoding="utf-8",
    )
    _force_bootstrap_vision_disabled(cfg)
    text = cfg.read_text(encoding="utf-8")
    assert "enabled: false" in text
    assert "enabled: true" not in text
    assert "model: foo" in text


def test_ensure_user_data_layout_bootstraps_stub(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import sys

    from travelogue import paths

    monkeypatch.setattr(paths, "is_frozen", lambda: True)
    monkeypatch.setattr(paths, "is_portable_mode", lambda: True)
    monkeypatch.setattr(paths, "exe_dir", lambda: tmp_path)
    monkeypatch.setattr(paths, "user_data_dir", lambda: tmp_path)
    example = tmp_path / "config.yaml.example"
    example.write_text(
        "trips_dir: ./trips\nllm:\n  provider: deepseek\nvision:\n  enabled: true\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(paths, "bundled_config_example", lambda: example)
    monkeypatch.setattr(sys, "frozen", True, raising=False)

    root = ensure_user_data_layout()
    assert root == tmp_path
    assert (tmp_path / OWNERSHIP_MARKER_NAME).is_file()
    cfg_text = (tmp_path / "config.yaml").read_text(encoding="utf-8")
    assert "provider: stub" in cfg_text
    assert "provider: deepseek" not in cfg_text
    assert "enabled: false" in cfg_text
    assert "enabled: true" not in cfg_text


def test_run_studio_llm_narrate_auth_does_not_require_trip_mutation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """BE-07：无凭证时局部 E_LLM_AUTH，不改写 trip。"""
    from travelogue.llm.errors import LlmError
    from travelogue.web.studio_narrate import run_studio_llm_narrate

    trip_dir = tmp_path / "t1"
    trip_dir.mkdir()
    (trip_dir / "trip.json").write_text('{"meta":{"title":"x"}}', encoding="utf-8")
    before = (trip_dir / "trip.json").read_text(encoding="utf-8")
    monkeypatch.setattr(
        "travelogue.web.studio_narrate.resolve_llm_may_call",
        lambda *, cfg=None: True,
    )
    monkeypatch.setattr(
        "travelogue.web.studio_narrate.studio_llm_status",
        lambda *, cfg=None: {"llmAvailable": False, "llmProvider": "stub"},
    )
    with pytest.raises(LlmError) as ei:
        run_studio_llm_narrate(trip_dir)
    assert ei.value.code == "E_LLM_AUTH"
    assert (trip_dir / "trip.json").read_text(encoding="utf-8") == before


def test_config_yaml_example_defaults_to_stub() -> None:
    root = Path(__file__).resolve().parents[3]
    text = (root / "config.yaml.example").read_text(encoding="utf-8")
    llm_block = text.split("llm:", 1)[1].split("\n# ---", 1)[0]
    active = [
        ln
        for ln in llm_block.splitlines()
        if ln.strip().startswith("provider:") and not ln.lstrip().startswith("#")
    ]
    assert active and "stub" in active[0]
