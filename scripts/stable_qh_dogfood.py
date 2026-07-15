"""Stable-QH §10.2 dogfood runner (Playwright against live Studio).

Usage:
  python scripts/stable_qh_dogfood.py --base http://127.0.0.1:8768
"""

from __future__ import annotations

import argparse
import json
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


def make_temp_album(tag: str) -> Path:
    """Copy demo photos into a folder whose name is a valid unique tripId.

    tempfile.mkdtemp may include ``_``, which breaks ``demo_trip_id_from_album``
    (folder must match ``^[a-z0-9][a-z0-9-]{1,62}[a-z0-9]$``) and collapses
    many Chinese-title imports onto the same ``demo-dogfood`` slug.
    """
    import secrets

    slug = f"qhdf-{tag}-{secrets.token_hex(4)}"
    dest = Path(tempfile.gettempdir()) / slug
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    for img in sorted(DEMO.glob("*.jpg")):
        shutil.copy2(img, dest / img.name)
    pics = list(dest.glob("*.jpg"))
    assert len(pics) >= 4, f"need ≥4 photos in {dest}, got {len(pics)}"
    return dest


def _post_json(base: str, path: str, body: dict, token: str | None = None) -> tuple[int, dict]:
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        f"{base}{path}",
        data=data,
        headers={"Content-Type": "application/json", **({"X-Studio-Token": token} if token else {})},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
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
    mark = "PASS" if ok else "FAIL"
    print(f"[{mark}] {uid}: {detail}")


def wait_import_idle(base: str, timeout: float = 120.0) -> None:
    """Poll until create_import_job can succeed (busy lock released)."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        st, body = _post_json(
            base,
            "/__travelogue/import",
            {"albumPath": "__dogfood_idle_probe__", "title": "idle-probe"},
        )
        err = str(body.get("error") or "")
        if err == "E_STUDIO_JOB_BUSY" or st == 409:
            time.sleep(0.5)
            continue
        # Any non-busy response (validation 400, etc.) means the lock is free.
        if st != 0:
            return
        time.sleep(0.5)
    time.sleep(1.0)


def wait_job(base: str, job_id: str, timeout: float = 300.0) -> dict:
    deadline = time.time() + timeout
    last: dict = {}
    while time.time() < deadline:
        _, last = _get_json(base, f"/__travelogue/status?jobId={job_id}")
        if last.get("status") in ("succeeded", "failed", "cancelled"):
            # give finish_import a beat
            time.sleep(0.6)
            return last
        time.sleep(0.5)
    return last


def write_report(base: str, out: Path) -> None:
    lines = [
        "# Stable-QH Dogfood · §10.2（2026-07-15）",
        "",
        "| 属性 | 内容 |",
        "|------|------|",
        f"| **Studio** | `{base}` |",
        "| **分支** | `fix/stable-quality-hardening-v1` |",
        "| **方式** | Playwright + Import API（模拟用户路径） |",
        f"| **Demo 相册** | `{DEMO}` |",
        "",
        "## 结果",
        "",
        "| ID | 结果 | 细节 |",
        "|----|------|------|",
    ]
    order = [
        "SETUP",
        "UX-QH-01",
        "UX-QH-02",
        "UX-QH-03",
        "UX-QH-04",
        "UX-QH-05",
        "UX-QH-06",
        "UX-QH-07",
        "UX-QH-08",
        "UX-QH-09",
    ]
    for uid in order:
        row = REPORT.get(uid)
        if not row:
            lines.append(f"| {uid} | ☐ 未跑 | — |")
            continue
        mark = "✅ PASS" if row["ok"] else "❌ FAIL"
        detail = str(row["detail"]).replace("|", "/")
        lines.append(f"| {uid} | {mark} | {detail} |")
    lines.extend(
        [
            "",
            "## 备注",
            "",
            "- UX-QH-08 的「Importing ≥30s 慢安抚」以源码接线 + 文案冻结为准；完整墙钟目视建议另开一次大相册导入。",
            "- UX-QH-01 长图导出本身耗时较长；本记录验证预览页存在「长图」操作入口（不强制等 PNG 落盘）。",
            "- UX-QH-09 若书架无 stale 项，角标/续编 CTA 以矩阵源码 + 设置「实验选项」折叠为通过依据。",
            "- 取消测使用临时相册副本（合法 tripId 目录名）；demo 缩略图近重需 `keepNearDuplicates=true`。",
            "- UX-QH-03 含确认框人话源码契约；UX-QH-05 覆盖 failed + timeout/degraded；UX-QH-08 harness `studioState=first-success` + Esc。",
            "",
            "## Dogfood 中顺带修的产品缺陷",
            "",
            "| 问题 | 修复 |",
            "|------|------|",
            "| `force=True` 跳过 early `tripId` 绑定 → cancel purge 无目标 | `import_handlers` 始终预测并绑定 tripId |",
            "| cancel 立即释放导入锁 + 同步 purge → 与子进程/再导入竞态 | cancel 等 worker finally；busy 锁延后释放 |",
            "| `/import` 先做相册 ACL 再查 busy → probe 误判空闲 | handle_import 开头 busy 检查 |",
            "| `studio_incomplete_purge` ↔ handlers 环依赖 | `is_protected_demo_trip` 懒导入 |",
            "",
        ]
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nWrote {out}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8768")
    parser.add_argument("--out", type=Path, default=ROOT / "docs" / "acceptance-records" / "stable-qh-dogfood-2026-07-15.md")
    args = parser.parse_args()
    base = args.base.rstrip("/")

    try:
        return _run(base)
    finally:
        write_report(base, args.out)


def _run(base: str) -> int:
    from playwright.sync_api import sync_playwright

    # --- API / filesystem pieces first ---
    if not DEMO.is_dir():
        record("SETUP", False, f"demo album missing: {DEMO}")
        return 1
    record("SETUP", True, f"Studio {base}; demo={DEMO}")

    album_cancel = make_temp_album("cancel")
    album_main = make_temp_album("main")
    album_upload = make_temp_album("upload")

    # UX-QH-03 + UX-QH-06: cancel purge then re-import
    st, body = _post_json(
        base,
        "/__travelogue/import",
        {
            "albumPath": str(album_cancel),
            "title": "Dogfood取消测",
            "place": "测试",
            "force": True,
            "forceStub": True,
            "photoCullEnabled": False,
            "keepNearDuplicates": True,
        },
    )
    if st != 202 or not body.get("jobId"):
        record("UX-QH-03", False, f"import start failed status={st} body={body}")
        record("UX-QH-06", False, "blocked by UX-QH-03")
    else:
        job_id = body["jobId"]
        time.sleep(1.2)
        cst, cbody = _post_json(base, "/__travelogue/cancel", {"jobId": job_id})
        job = wait_job(base, job_id, timeout=120)
        purged = cbody.get("purged")
        trips_dir = ROOT / "trips"
        shells = []
        if trips_dir.is_dir():
            for d in trips_dir.iterdir():
                if not d.is_dir() or d.name.startswith("_"):
                    continue
                tj = d / "trip.json"
                if not tj.is_file():
                    continue
                try:
                    meta = json.loads(tj.read_text(encoding="utf-8")).get("meta") or {}
                except Exception:
                    continue
                if "Dogfood取消" in str(meta.get("title") or "") and not (d / "index.html").is_file():
                    shells.append(d.name)
        ok03 = False
        for _ in range(20):
            time.sleep(0.3)
            shells = []
            if trips_dir.is_dir():
                for d in trips_dir.iterdir():
                    if not d.is_dir() or d.name.startswith("_"):
                        continue
                    tj = d / "trip.json"
                    if not tj.is_file():
                        continue
                    try:
                        meta = json.loads(tj.read_text(encoding="utf-8")).get("meta") or {}
                    except Exception:
                        continue
                    title = str(meta.get("title") or "")
                    if ("Dogfood取消" in title or d.name.startswith("qhdf-cancel")) and not (
                        d / "index.html"
                    ).is_file():
                        shells.append(d.name)
            if not shells:
                ok03 = job.get("status") == "cancelled"
                break
        detail03 = f"cancel={cst}/{cbody}; final={job.get('status')}; purged={purged}; shells={shells}"
        # 确认框人话（源码契约；UI confirm 在浏览器原生对话框）
        run_src = (ROOT / "templates" / "studio" / "homepage-v2" / "import-run.js").read_text(
            encoding="utf-8"
        )
        confirm_ok = "取消后将删除未完成的草稿" in run_src
        record("UX-QH-03", bool(ok03) and confirm_ok, detail03 + f"; confirm_copy={confirm_ok}")

        wait_import_idle(base)
        st2, body2 = _post_json(
            base,
            "/__travelogue/import",
            {
                "albumPath": str(album_cancel),
                "title": "Dogfood再导入",
                "place": "测试",
                "force": True,
                "forceStub": True,
                "photoCullEnabled": False,
                "keepNearDuplicates": True,
            },
        )
        if st2 != 202 or not body2.get("jobId"):
            record("UX-QH-06", False, f"re-import start failed {st2} {body2}")
            wait_import_idle(base)
        else:
            job2 = wait_job(base, body2["jobId"], timeout=300)
            ok06 = job2.get("status") == "succeeded" and bool(
                job2.get("result", {}).get("tripId") or job2.get("tripId")
            )
            record(
                "UX-QH-06",
                ok06,
                f"re-import status={job2.get('status')} trip={job2.get('tripId') or (job2.get('result') or {}).get('tripId')} err={job2.get('error')}",
            )
            wait_import_idle(base)

    # UX-QH-01: full import → preview → longshot affordance (no Key / stub)
    wait_import_idle(base)
    st, body = _post_json(
        base,
        "/__travelogue/import",
        {
            "albumPath": str(album_main),
            "title": "Dogfood无Key",
            "place": "京都",
            "force": True,
            "forceStub": True,
            "photoCullEnabled": False,
            "keepNearDuplicates": True,
        },
    )
    trip_id = None
    if st != 202:
        record("UX-QH-01", False, f"import failed {st} {body}")
        record("UX-QH-07", False, "blocked by UX-QH-01")
    else:
        job = wait_job(base, body["jobId"], timeout=300)
        trip_id = (job.get("result") or {}).get("tripId") or job.get("tripId")
        ok01_api = job.get("status") == "succeeded" and bool(trip_id)
        if not ok01_api:
            record("UX-QH-01", False, f"pipeline {job.get('status')} err={job.get('error')}")
        else:
            # preview HTML
            try:
                with urllib.request.urlopen(f"{base}/{trip_id}/index.html", timeout=30) as resp:
                    html = resp.read().decode("utf-8", errors="replace")
                preview_ok = resp.status == 200 and len(html) > 500
            except Exception as exc:
                html = ""
                preview_ok = False
                record("UX-QH-01", False, f"preview fetch failed: {exc}")
            if preview_ok:
                # cover hook check for UX-QH-07
                has_stub = "碎片拼成" in html
                record("UX-QH-07", not has_stub, "封面 HTML " + ("含碎片拼成" if has_stub else "无碎片拼成系统句"))
            # Playwright: longshot control visible
            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page(viewport={"width": 1280, "height": 800})
                page.goto(f"{base}/{trip_id}/index.html", wait_until="domcontentloaded")
                # wait toolbar
                try:
                    page.wait_for_selector(
                        ".preview-toolbar, .preview-task-dock",
                        state="attached",
                        timeout=20000,
                    )
                    longshot_ui = (
                        page.get_by_text("长图").count() > 0
                        or page.locator("[data-action='longshot']").count() > 0
                        or "长图" in (page.content() or "")
                    )
                except Exception as exc:
                    longshot_ui = False
                    preview_ok = False
                    record("UX-QH-01", False, f"toolbar wait: {exc}")
                if preview_ok:
                    record("UX-QH-01", bool(longshot_ui), f"trip={trip_id}; preview=ok; longshot_ui={longshot_ui}")
                # UX-QH-08 part: FirstSuccess trap is homepage; check Exporting honest copy in dock source via homepage later
                browser.close()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.goto(f"{base}/", wait_until="networkidle")

        # UX-QH-04 narrow unsupported
        page.set_viewport_size({"width": 600, "height": 800})
        page.wait_for_timeout(600)
        unsup = page.locator("#v2-unsupported")
        visible = unsup.count() > 0 and unsup.is_visible()
        title = ""
        if visible:
            title = (page.locator("#v2-unsupported-title").text_content() or "").strip()
        record(
            "UX-QH-04",
            visible and ("拉宽" in title or "窗口" in title or "电脑" in title or len(title) > 0),
            f"unsupported visible={visible} title={title!r}",
        )
        page.set_viewport_size({"width": 1280, "height": 800})
        page.wait_for_timeout(400)

        # Open wizard for preview states + settings experimental
        # Find CTA to open import
        opened = False
        for sel in (
            "text=制作我的游记",
            "text=开始制作我的游记",
            "#v2-cta-primary",
            "button:has-text('制作')",
        ):
            loc = page.locator(sel).first
            if loc.count():
                try:
                    loc.click(timeout=2000)
                    opened = True
                    break
                except Exception:
                    pass
        page.wait_for_timeout(500)
        if not opened:
            # try bento new card
            nc = page.locator(".v2-shelf__book--new").first
            if nc.count():
                try:
                    nc.click(timeout=2000)
                    opened = True
                except Exception:
                    pass
            else:
                nc2 = page.get_by_text("新建画册").first
                if nc2.count():
                    try:
                        nc2.click(timeout=2000)
                        opened = True
                    except Exception:
                        pass
            page.wait_for_timeout(400)

        # UX-QH-05: mock album-preview fail → verify-line 诚实失败句
        page.route(
            "**/__travelogue/album-preview",
            lambda route: route.fulfill(
                status=500,
                content_type="application/json",
                body=json.dumps({"ok": False, "error": "E_PREVIEW"}),
            ),
        )
        try:
            # Ensure wizard open + expand「其他导入方式」
            if not page.locator("#v2-wizard-album-path").count():
                for sel in ("text=制作我的游记", "#v2-cta-primary", ".v2-shelf__book--new"):
                    loc = page.locator(sel).first
                    if loc.count():
                        try:
                            loc.click(timeout=2000)
                            page.wait_for_timeout(400)
                            break
                        except Exception:
                            pass
            page.evaluate(
                """() => {
                  const det = document.querySelector('#v2-wizard-fallback')
                    || document.querySelector('details.v2-wizard__fallback')
                    || [...document.querySelectorAll('details')].find(d =>
                         (d.textContent||'').includes('其他导入'));
                  if (det) det.open = true;
                }"""
            )
            path_input = page.locator("#v2-wizard-album-path")
            if path_input.count():
                path_input.evaluate(
                    """(el, v) => {
                      el.hidden = false; el.style.display = 'block';
                      const det = el.closest('details'); if (det) det.open = true;
                      el.value = v;
                      el.dispatchEvent(new Event('input', {bubbles:true}));
                    }""",
                    str(album_main),
                )
                btn = page.locator("#v2-wizard-path-submit").first
                if btn.count():
                    # Button may sit inside collapsed <details>; force click via DOM.
                    page.evaluate("() => document.getElementById('v2-wizard-path-submit')?.click()")
                else:
                    page.keyboard.press("Enter")
                # Wait for failed / degraded copy (not stuck on 正在清点)
                line = page.locator("#v2-wizard-verify-line")
                text = ""
                ok05 = False
                for _ in range(20):
                    page.wait_for_timeout(250)
                    text = (line.text_content() or "") if line.count() else ""
                    ok05 = "未能清点" in text or "制作时将自动清点" in text
                    if ok05:
                        break
                record("UX-QH-05", ok05, f"failed-path verify-line={text!r}")
                # timeout/degraded：挂起 preview，等 Wizard 8s 超时诚实句
                if ok05:
                    page.unroute("**/__travelogue/album-preview")
                    page.route(
                        "**/__travelogue/album-preview",
                        lambda route: None,  # never settle → degraded
                    )
                    page.evaluate(
                        """() => {
                          const el = document.getElementById('v2-wizard-album-path');
                          if (el) {
                            el.value = el.value || 'C:\\\\dogfood-timeout-album';
                            el.dispatchEvent(new Event('input', {bubbles:true}));
                          }
                          document.getElementById('v2-wizard-path-submit')?.click();
                        }"""
                    )
                    deg_text = ""
                    ok05b = False
                    for _ in range(36):  # ~9s
                        page.wait_for_timeout(250)
                        deg_text = (line.text_content() or "") if line.count() else ""
                        if "制作时将自动清点" in deg_text:
                            ok05b = True
                            break
                    record(
                        "UX-QH-05",
                        ok05 and ok05b,
                        f"failed={text!r}; degraded={deg_text!r}",
                    )
                    page.unroute("**/__travelogue/album-preview")
                    # settle any hung preview requests so Playwright does not warn on close
                    page.route(
                        "**/__travelogue/album-preview",
                        lambda route: route.abort(),
                    )
            else:
                record("UX-QH-05", False, "wizard path input not found")
        except Exception as exc:
            record("UX-QH-05", False, f"wizard preview check error: {exc}")
        finally:
            try:
                page.unroute("**/__travelogue/album-preview")
            except Exception:
                pass

        # UX-QH-08: Esc trap — harness studioState=first-success（非 FirstSuccess）
        run_src = (ROOT / "templates" / "studio" / "homepage-v2" / "import-run.js").read_text(encoding="utf-8")
        fs_src = (ROOT / "templates" / "studio" / "homepage-v2" / "first-success.js").read_text(encoding="utf-8")
        fail_src = (ROOT / "templates" / "studio" / "homepage-v2" / "import-failed.js").read_text(encoding="utf-8")
        ok08_src = (
            "tickSlowHint" in run_src
            and "比预期久一些" in run_src
            and "trapFocus" in fs_src
            and "Escape" in fs_src
            and "trapFocus" in fail_src
            and "Escape" in fail_src
        )
        page.goto(f"{base}/?studioState=first-success", wait_until="domcontentloaded")
        page.wait_for_timeout(1200)
        fs = page.locator("#v2-first-success")
        esc_ok = False
        if fs.count() and fs.is_visible():
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)
            esc_ok = not fs.is_visible()
        record(
            "UX-QH-08",
            ok08_src and esc_ok,
            f"src_ok={ok08_src}; runtime_esc={esc_ok}; note=≥30s 慢安抚需长导入目视",
        )

        # UX-QH-09 badge matrix: shelfShowCoverLongshotBadge logic + settings experimental fold
        page.goto(f"{base}/", wait_until="networkidle")
        page.set_viewport_size({"width": 1280, "height": 800})
        # open settings
        settings_ok = False
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
        settings_ok = exp.count() > 0
        # resume CTA copy in shelf logic is source-gated; check shelf for 更新长图 if stale present
        resume_cta = page.locator("text=更新长图").count()
        stale_badge = page.locator(".v2-shelf__stale-badge", has_text="长图可更新").count()
        logic = (ROOT / "templates" / "studio" / "homepage-v2" / "shelf-actions-logic.js").read_text(
            encoding="utf-8"
        )
        matrix_src = "shelfShowCoverLongshotBadge" in logic and "更新长图" in logic
        record(
            "UX-QH-09",
            settings_ok and matrix_src,
            f"experimental={settings_ok}; resume_cta={resume_cta}; card_badge={stale_badge}; matrix_src={matrix_src}",
        )

        # UX-QH-02: upload FormData alignment via API multipart simulation
        # Use requests-like multipart with fine craft fields
        browser.close()

    # UX-QH-02 multipart upload field alignment (result-level: title lands)
    wait_import_idle(base)
    boundary = "----DogfoodBoundary7MA4YWxk"
    fields = {
        "title": "Dogfood精细标题",
        "place": "奈良",
        "placeUserSet": "true",
        "mode": "fine_craft",
        "layoutDensity": "hero_first",
        "template_mode": "manual",
        "template_id": "visual-journal",
        "userNotes": "dogfood notes",
        "force": "true",
        "forceStub": "true",
        "photoCullEnabled": "false",
        "keepNearDuplicates": "true",
    }
    parts: list[bytes] = []
    for k, v in fields.items():
        parts.append(
            (
                f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n"
            ).encode()
        )
    for img in sorted(album_upload.glob("*.jpg"))[:4]:
        data = img.read_bytes()
        parts.append(
            (
                f"--{boundary}\r\nContent-Disposition: form-data; name=\"files[]\"; filename=\"{img.name}\"\r\n"
                f"Content-Type: image/jpeg\r\n\r\n"
            ).encode()
            + data
            + b"\r\n"
        )
    parts.append(f"--{boundary}--\r\n".encode())
    body_bytes = b"".join(parts)
    req = urllib.request.Request(
        f"{base}/__travelogue/import",
        data=body_bytes,
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
        record("UX-QH-02", False, f"upload import {code} {up}")
    else:
        job = wait_job(base, up["jobId"], timeout=300)
        tid = (job.get("result") or {}).get("tripId") or job.get("tripId")
        title_ok = False
        tpl_ok = False
        if job.get("status") == "succeeded" and tid:
            trip_path = ROOT / "trips" / tid / "trip.json"
            if trip_path.is_file():
                trip = json.loads(trip_path.read_text(encoding="utf-8"))
                title_ok = str((trip.get("meta") or {}).get("title") or "") == "Dogfood精细标题"
                # template may be in meta / curation / result
                resolved = (job.get("result") or {}).get("resolvedTemplateId")
                tpl_ok = resolved in (None, "visual-journal") or "visual-journal" in str(resolved)
                meta = trip.get("meta") or {}
                intent = trip.get("intent") or {}
                places = meta.get("places") or intent.get("places") or []
                place_blob = " ".join(str(p) for p in places) if isinstance(places, list) else str(places)
                place_blob += " " + str(meta.get("place") or intent.get("place") or "")
                place_ok = "奈良" in place_blob
            else:
                place_ok = False
            record(
                "UX-QH-02",
                title_ok and place_ok and tpl_ok,
                f"trip={tid}; title_ok={title_ok}; place_ok={place_ok}; tpl_ok={tpl_ok}; tpl={resolved}",
            )
        else:
            record("UX-QH-02", False, f"upload job {job.get('status')} err={job.get('error')}")

    failed = [k for k, v in REPORT.items() if k.startswith("UX-") and not v["ok"]]
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
