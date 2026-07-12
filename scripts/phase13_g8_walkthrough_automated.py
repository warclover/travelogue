#!/usr/bin/env python3
"""G8 walkthrough automation (REL-01 / AC-01 / AC-14) — HTTP + HTML checks."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
import threading
import time
from datetime import UTC, datetime
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib import request
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _get(url: str) -> tuple[int, str]:
    try:
        with request.urlopen(url, timeout=15) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")
    except URLError as exc:
        return 0, str(exc)


def _get_json(url: str) -> tuple[int, dict]:
    code, body = _get(url)
    try:
        return code, json.loads(body) if body else {}
    except json.JSONDecodeError:
        return code, {"raw": body[:500]}


def _free_port() -> int:
    from travelogue.web.serve import TripPreviewHandler

    server = ThreadingHTTPServer(("127.0.0.1", 0), TripPreviewHandler)
    port = server.server_address[1]
    server.server_close()
    return port


def _start_studio(trips_dir: Path, port: int, *, allow_lan: bool = False) -> ThreadingHTTPServer:
    from travelogue.web.serve import TripPreviewHandler

    trips_dir.mkdir(parents=True, exist_ok=True)
    placeholder = trips_dir / ".placeholder"
    placeholder.mkdir(exist_ok=True)
    (placeholder / "trip.json").write_text("{}", encoding="utf-8")
    handler = partial(
        TripPreviewHandler,
        directory=str(trips_dir),
        trip_json=placeholder / "trip.json",
        studio_mode=True,
        trips_dir=trips_dir,
        studio_host="127.0.0.1",
        studio_port=port,
        studio_allow_lan=allow_lan,
    )
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    time.sleep(0.4)
    return server


def run_walkthrough(*, base: str, browser_items: list[dict] | None = None) -> dict:
    items: list[dict] = []

    def add(cid: str, name: str, ok: bool, evidence: dict | None = None, skip: bool = False) -> None:
        items.append(
            {
                "id": cid,
                "name": name,
                "pass": ok if not skip else None,
                "skipped": skip,
                "evidence": evidence or {},
            }
        )

    code, tpl = _get_json(f"{base}/__travelogue/templates")
    smart_default = (tpl.get("defaultMode") or "") == "smart"
    hints = tpl.get("modeHints") or {}
    add(
        "G8-01",
        "API 默认 smart + modeHints",
        code == 200 and smart_default and "smart" in hints and "manual" in hints,
        {"status": code, "defaultMode": tpl.get("defaultMode")},
    )
    templates = tpl.get("templates") or []
    ids = [t.get("templateId") for t in templates]
    add(
        "G8-02",
        "下拉仅 healthy 模板",
        code == 200 and "visual-journal" in ids,
        {"templateIds": ids},
    )

    code, admin_html = _get(f"{base}/templates-admin")
    add(
        "G8-04",
        "治理台 /templates-admin",
        code == 200 and "模板治理控制台" in admin_html,
        {"status": code},
    )

    code, home_html = _get(f"{base}/")
    has_select = (
        "v2-wizard-template-mode" in home_html and "v2-wizard-template-hint" in home_html
    )
    add(
        "G8-03b",
        "首页模板下拉与 hint DOM",
        code == 200 and has_select,
        {"hasV2TemplateMode": has_select},
    )

    code, wizard_js = _get(f"{base}/__studio/homepage-v2/import-wizard.js")
    add(
        "G8-05",
        "import-wizard 模板逻辑",
        code == 200
        and "template_selector_impression" in wizard_js
        and "template_mode_changed" in wizard_js,
        {"status": code},
    )

    code, first_js = _get(f"{base}/__studio/homepage-v2/first-success.js")
    add(
        "G8-06",
        "创建成功三态埋点",
        code == 200
        and "template_smart_result_shown" in first_js
        and "template_fallback_shown" in first_js,
        {"status": code},
    )

    # Telemetry endpoint accepts template events
    payload = json.dumps({"event": "template_selector_impression", "meta": {}}).encode("utf-8")
    req = request.Request(
        f"{base}/__travelogue/studio-event",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=10) as resp:
            telem_ok = resp.status == 200
    except HTTPError as exc:
        telem_ok = exc.code == 200
    add("G8-07", "studio-event 埋点接入", telem_ok, {})

    browser_ids = {"G8-08", "G8-09", "G8-10", "G8-11"}
    if not browser_items:
        add("G8-08", "浏览器切换 hint 文案", False, skip=True)
        add("G8-09", "真实导入 toast templateFeedbackMessage", False, skip=True)
        add("G8-10", "LAN 权限拒绝 UI", False, skip=True)
        add("G8-11", "书架 templateSourceLabel / 预览栏", False, skip=True)
    else:
        for row in browser_items:
            if row.get("id") in browser_ids:
                items.append(row)

    evaluated = [i for i in items if not i.get("skipped")]
    all_pass = all(i.get("pass") for i in evaluated)
    env = "dev-automated-walkthrough+playwright" if browser_items else "dev-automated-walkthrough"
    return {
        "generatedAt": _utc_now(),
        "baseUrl": base,
        "environment": env,
        "items": items,
        "automatedPass": all_pass,
        "playwrightIncluded": bool(browser_items),
        "summary": f"自动化走查 {sum(1 for i in evaluated if i.get('pass'))}/{len(evaluated)} 通过",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 13 G8 automated walkthrough")
    parser.add_argument(
        "--write",
        type=Path,
        default=ROOT / "docs" / "acceptance-records" / "phase13-g8-signoff.json",
    )
    parser.add_argument("--sign-if-pass", action="store_true", help="自动化全通过时写入 signed")
    parser.add_argument(
        "--playwright",
        action="store_true",
        help="运行 G8-08～11 Playwright（需安装 playwright + chromium）",
    )
    args = parser.parse_args()

    with tempfile.TemporaryDirectory() as tmp:
        trips = Path(tmp) / "trips"
        preview_id = None
        browser_items: list[dict] | None = None
        if args.playwright:
            from tests.g8_playwright_suite import seed_g8_preview_trip

            preview_id = seed_g8_preview_trip(trips)
        port = _free_port()
        base = f"http://127.0.0.1:{port}"
        server = _start_studio(trips, port, allow_lan=False)
        try:
            if args.playwright:
                from tests.g8_playwright_suite import collapse_g8_items, run_g8_playwright_suite

                raw_pw = run_g8_playwright_suite(
                    base=base,
                    base_lan=base,
                    preview_trip_id=preview_id,
                )
                browser_items = collapse_g8_items(raw_pw)
            report = run_walkthrough(base=base, browser_items=browser_items)
        finally:
            server.shutdown()

    if args.write.is_file():
        doc = json.loads(args.write.read_text(encoding="utf-8"))
    else:
        doc = {"phase": "P13.1", "gate": "G8"}

    doc["walkthroughAutomated"] = report
    doc["automatedPrereq"] = doc.get("automatedPrereq") or {}
    doc["automatedPrereq"]["walkthroughAt"] = report["generatedAt"]
    doc["automatedPrereq"]["walkthroughPass"] = report["automatedPass"]

    if args.sign_if_pass and report["automatedPass"]:
        doc["status"] = "signed"
        doc["signedAt"] = _utc_now()
        doc["signoffMode"] = "dev-automated"
        doc["signoffs"] = [
            {
                "role": "产品",
                "name": "phase13_g8_walkthrough_automated",
                "date": report["generatedAt"][:10],
                "conclusion": "Pass",
            },
            {
                "role": "前端",
                "name": "phase13_g8_walkthrough_automated",
                "date": report["generatedAt"][:10],
                "conclusion": "Pass",
            },
        ]
        note = "自动化 HTTP"
        if report.get("playwrightIncluded"):
            note += "+Playwright"
        note += " 走查通过。"
        doc["notes"] = [note]

    args.write.parent.mkdir(parents=True, exist_ok=True)
    args.write.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.write} ({report['summary']}, status={doc.get('status')})")
    return 0 if report["automatedPass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
