"""Studio homepage v2 gate · unit tests (M20-j)."""

from __future__ import annotations

import json
from io import StringIO
from pathlib import Path

import pytest
import yaml

from travelogue.web.studio_homepage_gate import (
    bucket_in_treatment,
    decide_root_variant,
    query_variant_override,
    resolve_mode,
    resolve_percent,
    should_redirect_root_to_v2,
    stable_bucket,
)


def test_resolve_mode(monkeypatch) -> None:
    monkeypatch.delenv("TRAVELOGUE_STUDIO_HOMEPAGE_V2", raising=False)
    assert resolve_mode("off") == "off"
    assert resolve_mode("on") == "on"
    assert resolve_mode("auto") == "auto"
    assert resolve_mode("1") == "on"
    assert resolve_mode(None) == "off"  # default when env unset in test


def test_resolve_percent_env_and_yaml(monkeypatch) -> None:
    monkeypatch.delenv("TRAVELOGUE_STUDIO_HOMEPAGE_V2_PERCENT", raising=False)
    cfg = {"studio": {"homepage": {"v2_bento": {"percent": 25}}}}
    assert resolve_percent(cfg) == 25.0
    assert resolve_percent({}) == 0.0
    camel = {"studio": {"homepage": {"v2Bento": {"percent": 12}}}}
    assert resolve_percent(camel) == 12.0


def test_resolve_percent_env_override(monkeypatch) -> None:
    monkeypatch.setenv("TRAVELOGUE_STUDIO_HOMEPAGE_V2_PERCENT", "15")
    assert resolve_percent({"studio": {"homepage": {"v2_bento": {"percent": 99}}}}) == 15.0


def test_stable_bucket_deterministic() -> None:
    a = stable_bucket("Mozilla/Test")
    b = stable_bucket("Mozilla/Test")
    assert a == b
    assert 0 <= a <= 99


def test_bucket_in_treatment() -> None:
    assert bucket_in_treatment(5, 10) is True
    assert bucket_in_treatment(10, 10) is False
    assert bucket_in_treatment(0, 100) is True
    assert bucket_in_treatment(50, 0) is False


def test_decide_root_variant_modes() -> None:
    assert decide_root_variant(mode="off", percent=0, bucket=0) == "v3"
    assert decide_root_variant(mode="on", percent=0, bucket=99) == "v2"
    assert decide_root_variant(mode="auto", percent=10, bucket=5) == "v2"
    assert decide_root_variant(mode="auto", percent=10, bucket=50) == "v3"


def test_query_override() -> None:
    assert query_variant_override({"homepageVariant": ["v2"]}) == "v2"
    assert decide_root_variant(
        mode="off", percent=0, bucket=0, query={"homepageVariant": ["v2"]}
    ) == "v2"


def test_should_redirect_only_auto() -> None:
    assert should_redirect_root_to_v2(mode="auto", variant="v2") is True
    assert should_redirect_root_to_v2(mode="on", variant="v2") is False
    assert should_redirect_root_to_v2(mode="auto", variant="v3") is False


def test_stable_bucket_sha256_contract() -> None:
    """与 bucket.js / 服务端 cookie 分桶公式一致。"""
    import hashlib

    def expected(ua: str) -> int:
        digest = hashlib.sha256(f"travelogue-studio-homepage-v2:{ua}".encode()).hexdigest()
        return int(digest[:8], 16) % 100

    for ua in ("Mozilla/Test", "M20jTest/5", "M20jTest/1"):
        assert stable_bucket(ua) == expected(ua)
    assert stable_bucket("") == expected("unknown")
    assert stable_bucket("Mozilla/Test", existing=42) == 42


def test_read_or_assign_bucket_cookie(monkeypatch) -> None:
    """read_or_assign_bucket 复用 cookie 分桶。"""

    class _Hdr:
        def __init__(self, cookie: str | None, ua: str = "Test") -> None:
            self.headers = {"Cookie": cookie or "", "User-Agent": ua}

    from travelogue.web.studio_homepage_gate import read_or_assign_bucket

    h = _Hdr("travelogue.studio.hp_bucket=55; other=1")
    b, is_new = read_or_assign_bucket(h)
    assert b == 55
    assert is_new is False

    h2 = _Hdr(None, "M20jTest/5")
    b2, is_new2 = read_or_assign_bucket(h2)
    assert b2 == stable_bucket("M20jTest/5")
    assert is_new2 is True


def test_gate_status_script(monkeypatch) -> None:
    import importlib.util
    from pathlib import Path

    monkeypatch.delenv("TRAVELOGUE_STUDIO_HOMEPAGE_V2", raising=False)
    monkeypatch.delenv("TRAVELOGUE_STUDIO_HOMEPAGE_V2_PERCENT", raising=False)
    script = Path(__file__).resolve().parents[1] / "scripts" / "studio_homepage_gate_status.py"
    spec = importlib.util.spec_from_file_location("gate_status", script)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)

    assert mod.main(["--ua", "M20jTest/5", "--json"]) == 0
    monkeypatch.setenv("TRAVELOGUE_STUDIO_HOMEPAGE_V2", "auto")
    monkeypatch.setenv("TRAVELOGUE_STUDIO_HOMEPAGE_V2_PERCENT", "10")
    assert mod.main(["--ua", "M20jTest/5", "--json"]) == 0


def test_gate_status_reads_yaml_percent(tmp_path: Path, monkeypatch) -> None:
    import importlib.util

    script = Path(__file__).resolve().parents[1] / "scripts" / "studio_homepage_gate_status.py"
    spec = importlib.util.spec_from_file_location("gate_status_cfg", script)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)

    monkeypatch.delenv("TRAVELOGUE_STUDIO_HOMEPAGE_V2_PERCENT", raising=False)
    monkeypatch.setenv("TRAVELOGUE_STUDIO_HOMEPAGE_V2", "auto")
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        yaml.safe_dump({"studio": {"homepage": {"v2_bento": {"percent": 25}}}}),
        encoding="utf-8",
    )

    buf = StringIO()
    monkeypatch.setattr("sys.stdout", buf)
    assert mod.main(["--config", str(cfg), "--ua", "M20jTest/5", "--json"]) == 0
    payload = json.loads(buf.getvalue())
    assert payload["percent"] == 25.0
    assert payload["config_path"] == str(cfg.resolve())
    assert payload["root_variant"] == "v2"
