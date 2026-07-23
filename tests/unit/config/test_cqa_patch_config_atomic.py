"""CQA M2 · patch_config_file atomic write (AC-21)."""

from __future__ import annotations

import threading
from pathlib import Path

import yaml

from travelogue.config.loader import patch_config_file


def test_patch_config_file_concurrent_yields_valid_yaml(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text("studio:\n  g1_confirm_structure: false\n", encoding="utf-8")
    errors: list[BaseException] = []

    def worker(flag: bool) -> None:
        try:
            for _ in range(20):
                patch_config_file(path, {"studio": {"g1ConfirmStructure": flag}})
                flag = not flag
        except BaseException as exc:  # noqa: BLE001 — surface in parent
            errors.append(exc)

    threads = [
        threading.Thread(target=worker, args=(True,)),
        threading.Thread(target=worker, args=(False,)),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)
    assert not errors
    text = path.read_text(encoding="utf-8")
    loaded = yaml.safe_load(text)
    assert isinstance(loaded, dict)
    assert "studio" in loaded
    assert isinstance(loaded["studio"].get("g1_confirm_structure"), bool)
