#!/usr/bin/env python3
"""M21 post-deploy route smoke (P1-4 · M21-CUTOVER §2 发布后 0–2h).

HTTP 检查（无需 Playwright）：
  - GET /           → v2 标记（mode=on 时）
  - GET /classic    → legacy-freeze classic
  - GET /v2         → 302 /
  - GET /__travelogue/config → 200 + capabilities

用法：
    # 对已部署实例
    python scripts/m21_deploy_smoke.py --base http://127.0.0.1:8766

    # 本地临时起 Studio（默认 TRAVELOGUE_STUDIO_HOMEPAGE_V2=on）
    python scripts/m21_deploy_smoke.py --spawn

    python scripts/m21_deploy_smoke.py --spawn --json --write docs/acceptance-records/m21-deploy-smoke.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]

V2_ROOT_MARKERS = ('data-homepage-variant="v2"', "studio-home-v2.css")
CLASSIC_MARKERS = (
    'data-studio-v="4"',
    "Classic 首页（Deprecated）",
    "/__studio/legacy-freeze/studio.classic.js",
)


def _fetch(url: str, *, method: str = "GET", follow_redirect: bool = True) -> tuple[int, str, dict]:
    req = urllib.request.Request(url, method=method)
    if not follow_redirect:

        class _NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ARG002
                return None

        opener = urllib.request.build_opener(_NoRedirect)
        try:
            with opener.open(req, timeout=15) as resp:
                body = resp.read().decode("utf-8", errors="replace")
                return resp.status, body, dict(resp.headers)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
            return exc.code, body, dict(exc.headers)

    with urllib.request.urlopen(req, timeout=15) as resp:
        body = resp.read().decode("utf-8", errors="replace")
        return resp.status, body, dict(resp.headers)


def _spawn_base(*, gate_mode: str) -> tuple[object, str]:
    sys.path.insert(0, str(_REPO))
    from tests.test_studio_server import _free_port, _start_studio_server

    prev = os.environ.get("TRAVELOGUE_STUDIO_HOMEPAGE_V2")
    os.environ["TRAVELOGUE_STUDIO_HOMEPAGE_V2"] = gate_mode
    trips_dir = Path(tempfile.mkdtemp(prefix="m21-smoke-")) / "trips"
    trips_dir.mkdir(parents=True)
    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    base = f"http://127.0.0.1:{port}"
    server._m21_smoke_prev_gate = prev  # type: ignore[attr-defined]
    return server, base


def _shutdown_spawn(server: object) -> None:
    prev = getattr(server, "_m21_smoke_prev_gate", None)
    server.shutdown()  # type: ignore[attr-defined]
    server.server_close()  # type: ignore[attr-defined]
    if prev is None:
        os.environ.pop("TRAVELOGUE_STUDIO_HOMEPAGE_V2", None)
    else:
        os.environ["TRAVELOGUE_STUDIO_HOMEPAGE_V2"] = prev


def run_smoke(base: str, *, expect_v2_root: bool = True) -> dict:
    checks: list[dict] = []
    ok = True

    status, html, _ = _fetch(base.rstrip("/") + "/")
    root_v2 = all(m in html for m in V2_ROOT_MARKERS)
    passed = status == 200 and (root_v2 if expect_v2_root else 'data-homepage-variant="classic"' in html or "studio.classic" in html)
    checks.append({"id": "root", "passed": passed, "status": status, "expect_v2": expect_v2_root})
    ok &= passed

    status, html, _ = _fetch(base.rstrip("/") + "/classic")
    classic_ok = status == 200 and all(m in html for m in CLASSIC_MARKERS)
    checks.append({"id": "classic", "passed": classic_ok, "status": status})
    ok &= classic_ok

    status, _, headers = _fetch(base.rstrip("/") + "/v2", follow_redirect=False)
    loc = headers.get("Location") or headers.get("location")
    redirect_ok = status == 302 and loc == "/"
    checks.append({"id": "v2_redirect", "passed": redirect_ok, "status": status, "location": loc})
    ok &= redirect_ok

    status, body, _ = _fetch(base.rstrip("/") + "/__travelogue/config")
    cfg_ok = False
    caps: list[str] = []
    if status == 200:
        try:
            data = json.loads(body)
            caps = list((data.get("capabilities") or {}).keys())
            cfg_ok = "pickFolder" in caps
        except json.JSONDecodeError:
            cfg_ok = False
    checks.append({"id": "config", "passed": cfg_ok, "status": status, "capabilities": caps})
    ok &= cfg_ok

    return {
        "base": base,
        "ok": ok,
        "expect_v2_root": expect_v2_root,
        "checkedAt": datetime.now(UTC).isoformat(),
        "checks": checks,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="M21 deploy route smoke")
    ap.add_argument("--base", help="Studio base URL (omit with --spawn)")
    ap.add_argument("--spawn", action="store_true", help="start ephemeral loopback Studio")
    ap.add_argument(
        "--gate-mode",
        default="on",
        choices=("on", "off", "auto"),
        help="TRAVELOGUE_STUDIO_HOMEPAGE_V2 when --spawn (default on)",
    )
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--write", type=Path, help="write report JSON")
    args = ap.parse_args()

    server = None
    base = args.base
    if args.spawn:
        server, base = _spawn_base(gate_mode=args.gate_mode)
    elif not base:
        ap.error("provide --base or --spawn")

    expect_v2 = args.gate_mode == "on" or (args.gate_mode == "auto" and not args.spawn)
    if args.spawn and args.gate_mode == "off":
        expect_v2 = False

    try:
        report = run_smoke(base, expect_v2_root=expect_v2)
    finally:
        if server is not None:
            _shutdown_spawn(server)

    if args.write:
        args.write.parent.mkdir(parents=True, exist_ok=True)
        args.write.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        label = "PASS" if report["ok"] else "FAIL"
        print(f"=== M21 deploy smoke [{label}] ===")
        print(f"  base: {report['base']}")
        for chk in report["checks"]:
            mark = "ok" if chk["passed"] else "FAIL"
            print(f"  {chk['id']}: {mark}")

    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
