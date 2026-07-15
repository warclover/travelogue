"""Stable-QH · 典型用户实用试用（persona trial）。

模拟 5 类产品画像在本机 Studio 的真实路径（偏 UI + 必要 API），
补充 scripts/stable_qh_dogfood.py 的契约向覆盖。

Usage:
  TRAVELOGUE_STUDIO_TRUST_LOCAL_ALBUM=1 python scripts/stable_qh_persona_trial.py --base http://127.0.0.1:8768
"""

from __future__ import annotations

import argparse
import json
import secrets
import shutil
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "templates" / "studio" / "assets" / "demo-album"
REPORT: dict[str, dict] = {}


def make_album(tag: str) -> Path:
    slug = f"qhtrial-{tag}-{secrets.token_hex(3)}"
    dest = Path(tempfile.gettempdir()) / slug
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    for img in sorted(DEMO.glob("*.jpg")):
        shutil.copy2(img, dest / img.name)
    assert len(list(dest.glob("*.jpg"))) >= 4
    return dest


def _post_json(base: str, path: str, body: dict) -> tuple[int, dict]:
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        f"{base}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            payload = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            payload = {"raw": raw}
        return exc.code, payload
    except Exception as exc:
        return 0, {"error": "E_CLIENT", "message": str(exc)}


def _get_json(base: str, path: str) -> tuple[int, dict]:
    with urllib.request.urlopen(f"{base}{path}", timeout=30) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))


def record(uid: str, ok: bool, detail: str) -> None:
    REPORT[uid] = {"ok": ok, "detail": detail}
    print(f"[{'PASS' if ok else 'FAIL'}] {uid}: {detail}")


def wait_idle(base: str, timeout: float = 120.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        st, body = _post_json(base, "/__travelogue/import", {"albumPath": "__idle__", "title": "x"})
        if body.get("error") == "E_STUDIO_JOB_BUSY" or st == 409:
            time.sleep(0.4)
            continue
        if st != 0:
            return
        time.sleep(0.4)


def wait_job(base: str, job_id: str, timeout: float = 360.0) -> dict:
    deadline = time.time() + timeout
    last: dict = {}
    while time.time() < deadline:
        _, last = _get_json(base, f"/__travelogue/status?jobId={job_id}")
        if last.get("status") in ("succeeded", "failed", "cancelled"):
            time.sleep(0.5)
            return last
        time.sleep(0.5)
    return last


def import_album(
    base: str,
    album: Path,
    *,
    title: str,
    place: str = "旅途",
    force_stub: bool = True,
    keep_dupes: bool = True,
) -> dict:
    wait_idle(base)
    st, body = _post_json(
        base,
        "/__travelogue/import",
        {
            "albumPath": str(album),
            "title": title,
            "place": place,
            "placeUserSet": True,
            "force": True,
            "forceStub": force_stub,
            "photoCullEnabled": False,
            "keepNearDuplicates": keep_dupes,
        },
    )
    if st != 202 or not body.get("jobId"):
        return {"ok": False, "start": body, "status": st}
    job = wait_job(base, body["jobId"])
    trip = (job.get("result") or {}).get("tripId") or job.get("tripId")
    return {"ok": job.get("status") == "succeeded", "job": job, "tripId": trip}


def write_report(base: str, out: Path) -> None:
    order = [
        "SETUP",
        "P1-traveler",
        "P2-curious",
        "P3-fine-craft",
        "P4-trust-cancel",
        "P5-returning",
    ]
    lines = [
        "# Stable-QH · 典型用户实用试用（2026-07-15）",
        "",
        "| 属性 | 内容 |",
        "|------|------|",
        f"| **Studio** | `{base}` |",
        "| **方式** | Playwright UI + Import API（模拟 5 类典型用户） |",
        f"| **样片** | `{DEMO}` |",
        "",
        "## 画像与结果",
        "",
        "| 画像 | 结果 | 细节 |",
        "|------|------|------|",
    ]
    labels = {
        "SETUP": "环境",
        "P1-traveler": "P1 首次旅行者 · 无 Key 主路径",
        "P2-curious": "P2 好奇试用者 · 示例转化",
        "P3-fine-craft": "P3 旁路精细偏好",
        "P4-trust-cancel": "P4 信任 · 取消与再导入",
        "P5-returning": "P5 回访 · 书架与词表",
    }
    for uid in order:
        row = REPORT.get(uid)
        if not row:
            lines.append(f"| {labels.get(uid, uid)} | ☐ 未跑 | — |")
            continue
        mark = "✅ PASS" if row["ok"] else "❌ FAIL"
        detail = str(row["detail"]).replace("|", "/")
        lines.append(f"| {labels.get(uid, uid)} | {mark} | {detail} |")
    lines.extend(
        [
            "",
            "## 剧本说明",
            "",
            "1. **P1** 导入→预览卷轴→确认「长图」操作入口（不强制 PNG 落盘）。",
            "2. **P2** 首页示例转化 CTA / Wizard 打开；上传小文件夹成册。",
            "3. **P3** 精细 + 手动模板 + 自定义标题，成册后核对 trip.json。",
            "4. **P4** 导入中取消→书架无空壳→同夹再导入成功。",
            "5. **P5** 回访首页书架有册；无「长图待更新」；设置含「实验选项」。",
            "",
            "## 残留（真人补签）",
            "",
            "- 系统「选文件夹」对话框与微信发出长图 PNG：需真人。",
            "- 大相册 ≥30s Importing 慢安抚墙钟目视：可选。",
            "- 真 LLM Key 文案气质：本轮 forceStub，不评文案质量。",
            "- 长图工程补签：见本文件「残留」表（`/__travelogue/longshot` → moments PNG）。",
            "",
        ]
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nWrote {out}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8768")
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "docs" / "acceptance-records" / "stable-qh-persona-trial-2026-07-15.md",
    )
    args = parser.parse_args()
    base = args.base.rstrip("/")
    try:
        return _run(base)
    finally:
        write_report(base, args.out)


def _run(base: str) -> int:
    from playwright.sync_api import sync_playwright

    if not DEMO.is_dir():
        record("SETUP", False, f"demo missing: {DEMO}")
        return 1
    try:
        with urllib.request.urlopen(f"{base}/", timeout=10) as resp:
            if resp.status != 200:
                record("SETUP", False, f"Studio HTTP {resp.status}")
                return 1
    except Exception as exc:
        record("SETUP", False, f"Studio unreachable: {exc}")
        return 1
    record("SETUP", True, f"Studio {base}; demo photos={len(list(DEMO.glob('*.jpg')))}")

    album_p1 = make_album("p1")
    album_p3 = make_album("p3")
    album_p4 = make_album("p4")

    # ── P1 首次旅行者 ──
    r1 = import_album(base, album_p1, title="试用·周末短途", place="京都")
    if not r1.get("ok"):
        record("P1-traveler", False, f"import failed {r1}")
    else:
        trip = r1["tripId"]
        longshot_ui = False
        preview_ok = False
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1280, "height": 800})
            page.goto(f"{base}/{trip}/index.html", wait_until="domcontentloaded")
            page.wait_for_timeout(1500)
            html = page.content() or ""
            preview_ok = len(html) > 800 and "碎片拼成" not in html
            page.wait_for_selector(".preview-toolbar", state="attached", timeout=20000)
            longshot_ui = "长图" in html or page.get_by_text("长图").count() > 0
            browser.close()
        record(
            "P1-traveler",
            bool(preview_ok and longshot_ui),
            f"trip={trip}; preview={preview_ok}; longshot_ui={longshot_ui}",
        )

    # ── P2 好奇试用者 · UI 转化入口 + 上传成册 ──
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.goto(f"{base}/", wait_until="networkidle")
        page.wait_for_timeout(800)
        convert = page.locator("#v2-bench-demo-convert")
        has_convert = convert.count() > 0
        opened = False
        if has_convert:
            try:
                convert.first.click(timeout=3000)
                opened = True
            except Exception:
                pass
        if not opened:
            for sel in ("#v2-cta-primary", "text=制作我的游记", "text=开始制作"):
                loc = page.locator(sel).first
                if loc.count():
                    try:
                        loc.click(timeout=3000)
                        opened = True
                        break
                    except Exception:
                        pass
        page.wait_for_timeout(600)
        wizard_visible = page.locator("#v2-wizard-root, #v2-import-wizard").count() > 0
        browser.close()

    # 上传小文件夹（模拟「试用自己的照片」）
    wait_idle(base)
    boundary = "----PersonaTrialBoundary"
    fields = {
        "title": "试用·上传转化",
        "place": "奈良",
        "placeUserSet": "true",
        "mode": "quick_share",
        "force": "true",
        "forceStub": "true",
        "photoCullEnabled": "false",
        "keepNearDuplicates": "true",
    }
    parts: list[bytes] = []
    for k, v in fields.items():
        parts.append(
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode()
        )
    for img in sorted(DEMO.glob("*.jpg"))[:5]:
        parts.append(
            (
                f"--{boundary}\r\nContent-Disposition: form-data; name=\"files[]\"; "
                f'filename="{img.name}"\r\nContent-Type: image/jpeg\r\n\r\n'
            ).encode()
            + img.read_bytes()
            + b"\r\n"
        )
    parts.append(f"--{boundary}--\r\n".encode())
    req = urllib.request.Request(
        f"{base}/__travelogue/import",
        data=b"".join(parts),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            up = json.loads(resp.read().decode("utf-8"))
            code = resp.status
    except urllib.error.HTTPError as exc:
        code = exc.code
        try:
            up = json.loads(exc.read().decode("utf-8"))
        except Exception:
            up = {}
    p2_ok = False
    p2_trip = None
    if code == 202 and up.get("jobId"):
        job = wait_job(base, up["jobId"])
        p2_trip = (job.get("result") or {}).get("tripId") or job.get("tripId")
        p2_ok = job.get("status") == "succeeded" and bool(p2_trip)
        detail = f"convert_cta={has_convert}; wizard_open={opened or wizard_visible}; upload={job.get('status')}; trip={p2_trip}"
    else:
        detail = f"convert_cta={has_convert}; wizard_open={opened}; upload_start={code}/{up}"
    record("P2-curious", p2_ok and (has_convert or opened or wizard_visible), detail)

    # ── P3 旁路精细 ──
    wait_idle(base)
    boundary = "----PersonaFineBoundary"
    fields = {
        "title": "试用·精细手作标题",
        "place": "冲绳",
        "placeUserSet": "true",
        "mode": "fine_craft",
        "layoutDensity": "hero_first",
        "template_mode": "manual",
        "template_id": "visual-journal",
        "userNotes": "persona trial notes",
        "force": "true",
        "forceStub": "true",
        "photoCullEnabled": "false",
        "keepNearDuplicates": "true",
    }
    parts = []
    for k, v in fields.items():
        parts.append(
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode()
        )
    for img in sorted(album_p3.glob("*.jpg"))[:5]:
        parts.append(
            (
                f"--{boundary}\r\nContent-Disposition: form-data; name=\"files[]\"; "
                f'filename="{img.name}"\r\nContent-Type: image/jpeg\r\n\r\n'
            ).encode()
            + img.read_bytes()
            + b"\r\n"
        )
    parts.append(f"--{boundary}--\r\n".encode())
    req = urllib.request.Request(
        f"{base}/__travelogue/import",
        data=b"".join(parts),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            up = json.loads(resp.read().decode("utf-8"))
            code = resp.status
    except urllib.error.HTTPError as exc:
        code = exc.code
        try:
            up = json.loads(exc.read().decode("utf-8"))
        except Exception:
            up = {}
    if code != 202 or not up.get("jobId"):
        record("P3-fine-craft", False, f"upload start {code} {up}")
    else:
        job = wait_job(base, up["jobId"])
        tid = (job.get("result") or {}).get("tripId") or job.get("tripId")
        title_ok = place_ok = tpl_ok = False
        if job.get("status") == "succeeded" and tid:
            trip_path = ROOT / "trips" / tid / "trip.json"
            if trip_path.is_file():
                trip = json.loads(trip_path.read_text(encoding="utf-8"))
                meta = trip.get("meta") or {}
                intent = trip.get("intent") or {}
                title_ok = meta.get("title") == "试用·精细手作标题"
                places = " ".join(str(x) for x in (meta.get("places") or intent.get("places") or []))
                place_ok = "冲绳" in places
                sel = trip.get("templateSelection") or {}
                tpl_ok = sel.get("resolvedTemplateId") == "visual-journal" or sel.get("mode") == "manual"
        record(
            "P3-fine-craft",
            title_ok and place_ok,
            f"trip={tid}; title_ok={title_ok}; place_ok={place_ok}; tpl_ok={tpl_ok}",
        )

    # ── P4 信任取消 ──
    wait_idle(base)
    st, body = _post_json(
        base,
        "/__travelogue/import",
        {
            "albumPath": str(album_p4),
            "title": "试用·取消测",
            "place": "测试",
            "force": True,
            "forceStub": True,
            "photoCullEnabled": False,
            "keepNearDuplicates": True,
        },
    )
    if st != 202 or not body.get("jobId"):
        record("P4-trust-cancel", False, f"import start {st} {body}")
    else:
        jid = body["jobId"]
        time.sleep(1.0)
        cst, cbody = _post_json(base, "/__travelogue/cancel", {"jobId": jid})
        job = wait_job(base, jid, timeout=120)
        wait_idle(base)
        shells = []
        trips_dir = ROOT / "trips"
        if trips_dir.is_dir():
            for d in trips_dir.iterdir():
                if not d.is_dir() or d.name.startswith("_"):
                    continue
                if not d.name.startswith("qhtrial-p4"):
                    continue
                if not (d / "index.html").is_file():
                    shells.append(d.name)
        confirm = "取消后将删除未完成的草稿" in (
            ROOT / "templates" / "studio" / "homepage-v2" / "import-run.js"
        ).read_text(encoding="utf-8")
        r2 = import_album(base, album_p4, title="试用·取消后再导", place="测试")
        ok = (
            job.get("status") == "cancelled"
            and not shells
            and cbody.get("purged") is True
            and confirm
            and r2.get("ok")
        )
        record(
            "P4-trust-cancel",
            bool(ok),
            f"cancel={cst}/purged={cbody.get('purged')}; shells={shells}; reimport={r2.get('ok')}; confirm={confirm}",
        )

    # ── P5 回访 ──
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.goto(f"{base}/", wait_until="networkidle")
        page.wait_for_timeout(1000)
        shelf = page.locator(".v2-shelf__book, .v2-shelf [data-trip-id], .v2-bento__card")
        shelf_n = shelf.count()
        bad_vocab = page.get_by_text("长图待更新").count()
        # settings experimental
        for sel in ("#v2-settings-toggle", "button[aria-label*='设置']", "text=设置"):
            loc = page.locator(sel).first
            if loc.count():
                try:
                    loc.click(timeout=2000)
                    page.wait_for_timeout(400)
                    break
                except Exception:
                    pass
        exp = page.locator("#v2-settings-experimental, summary:has-text('实验选项')")
        exp_ok = exp.count() > 0
        # open a known trip from P1 if present
        trip_open = False
        p1 = REPORT.get("P1-traveler", {})
        detail_p1 = str(p1.get("detail") or "")
        trip_id = None
        if "trip=" in detail_p1:
            trip_id = detail_p1.split("trip=")[1].split(";")[0].strip()
        if trip_id:
            page.goto(f"{base}/{trip_id}/index.html", wait_until="domcontentloaded")
            page.wait_for_timeout(800)
            trip_open = "长图" in (page.content() or "")
        browser.close()
    record(
        "P5-returning",
        shelf_n > 0 and bad_vocab == 0 and exp_ok,
        f"shelf_cards≈{shelf_n}; bad_vocab={bad_vocab}; experimental={exp_ok}; reopen_longshot={trip_open}",
    )

    failed = [k for k, v in REPORT.items() if k != "SETUP" and not v["ok"]]
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
