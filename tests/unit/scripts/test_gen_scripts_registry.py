"""M-C3 · scripts registry generator."""

from __future__ import annotations

import importlib.util
import sys

from tests._repo_root import repo_root

ROOT = repo_root(__file__)


def _load_registry_main():
    path = ROOT / "scripts" / "gen_scripts_registry.py"
    spec = importlib.util.spec_from_file_location("gen_scripts_registry_test", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["gen_scripts_registry_test"] = mod
    spec.loader.exec_module(mod)
    return mod.main


def test_gen_scripts_registry_writes_and_check_passes() -> None:
    main = _load_registry_main()
    assert main([]) == 0

    readme = ROOT / "scripts" / "README.md"
    candidates = ROOT / "docs" / "archive" / "ARCHIVE-CANDIDATES.md"
    assert readme.is_file()
    assert candidates.is_file()
    assert "Scripts Registry" in readme.read_text(encoding="utf-8")
    assert "archive candidates" in candidates.read_text(encoding="utf-8").lower()
    assert "gen_scripts_registry.py" in readme.read_text(encoding="utf-8")

    assert main(["--check"]) == 0