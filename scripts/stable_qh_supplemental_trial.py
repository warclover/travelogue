"""Supplemental trials: stale vocab, large-album slow hint, 2 old-trip regressions.

Usage:
  TRAVELOGUE_STUDIO_TRUST_LOCAL_ALBUM=1 python scripts/stable_qh_supplemental_trial.py --base http://127.0.0.1:8768
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


def record(uid: str, ok: bool, detail: str) -> None:
    REPORT[uid] = {"ok": ok, "detail": detail}
    print(f"[{'PASS' if ok else 'FAIL'}] {uid}: {detail}")


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
    with urllib.request.urlopen(f"{base}{path}", timeout=60) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))


def wait_idle(base: str, timeout: float = 180.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        st, body = _post_json(base, "/__travelogue/import", {"albumPath": "__idle__", "title": "x"})
        if body.get("error") == "E_STUDIO_JOB_BUSY" or st == 409:
            time.sleep(0.5)
            continue
        if st != 0:
            return
        time.sleep(0.5)


def wait_job(base: str, job_id: str, timeout: float = 900.0) -> dict:
    deadline = time.time() + timeout
    last: dict = {}
    while time.time() < deadline:
        _, last = _get_json(base, f"/__travelogue/status?jobId={job_id}")
        if last.get("status") in ("succeeded", "failed", "cancelled"):
            time.sleep(0.4)
            return last
        time.sleep(0.6)
    return last


def write_report(base: str, out: Path) -> None:
    order = [
        "SETUP",
        "STALE-VOCAB",
        "SLOW-HINT",
        "OLD-TRIP-A",
        "OLD-TRIP-B",
    ]
    labels = {
        "SETUP": "环境",
        "STALE-VOCAB": "精修→长图可更新词表",
        "SLOW-HINT": "大相册 Importing ≥30s 慢安抚",
        "OLD-TRIP-A": "老 trip 回归 A",
        "OLD-TRIP-B": "老 trip 回归 B",
    }
    lines = [
        "# Stable-QH · 补充试用（精修 stale / 慢安抚 / 老 trip）（2026-07-15）",
        "",
        "| 属性 | 内容 |",
        "|------|------|",
        f"| **Studio** | `{base}` |",
        "| **范围** | 精修→长图可更新；大相册慢安抚；本机 2 本老 trip |",
        "",
        "## 结果",
        "",
        "| 项 | 结果 | 细节 |",
        "|----|------|------|",
    ]
    for uid in order:
        row = REPORT.get(uid)
        if not row:
            lines.append(f"| {labels.get(uid, uid)} | ☐ 未跑 | — |")
            continue
        mark = "✅ PASS" if row["ok"] else "❌ FAIL"
        lines.append(f"| {labels.get(uid, uid)} | {mark} | {str(row['detail']).replace('|', '/')} |")
    lines.extend(
        [
            "",
            "## 说明",
            "",
            "- **STALE**：先导长图，等待 >0.5s 宽限后再 PATCH 标题 bump `updatedAt`；书架/API 应出现「长图可更新」，且无「长图待更新」。",
            "- **SLOW**：合成 48 张去重后仍唯一的图；Importing 面板在约 ≥30s 出现「比预期久一些，请耐心等待…」（见到后可 cancel）。",
            "- **OLD**：抽 2 本本机已有 index 的 trip，验预览 HTML + 长图入口 + 无禁用词表。",
            "",
        ]
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nWrote {out}")


def pick_old_trips(n: int = 2) -> list[Path]:
    trips = ROOT / "trips"
    cands: list[tuple[int, Path]] = []
    for d in trips.iterdir():
        if not d.is_dir() or d.name.startswith("_") or d.name.startswith("qh"):
            continue
        if d.name.startswith("job-"):
            continue
        if not (d / "index.html").is_file() or not (d / "trip.json").is_file():
            continue
        try:
            t = json.loads((d / "trip.json").read_text(encoding="utf-8"))
            assets = len(t.get("assets") or [])
        except Exception:
            assets = 0
        if assets >= 20:
            cands.append((assets, d))
    cands.sort(reverse=True)
    # Prefer mid-size for speed + one larger
    if len(cands) >= 2:
        return [cands[0][1], cands[min(5, len(cands) - 1)][1]]
    return [c[1] for c in cands[:n]]


def trial_stale_vocab(base: str) -> None:
    """Export longshot then bump trip → longshotStale + UI vocab."""
    # Prefer existing small trial with preview; else import quick
    trip_id = None
    for name in ("qhtrial-p1-eb2232", "qhdf-main-72390808", "qhtrial-p1-589f48"):
        d = ROOT / "trips" / name
        if (d / "index.html").is_file():
            trip_id = name
            break
    if not trip_id:
        record("STALE-VOCAB", False, "no small trial trip with index.html")
        return

    wait_idle(base)
    st, body = _post_json(
        base,
        "/__travelogue/longshot",
        {"tripId": trip_id, "scale": 1, "format": "png", "platform": "wechat_moments"},
    )
    if st == 409:
        wait_idle(base)
        st, body = _post_json(
            base,
            "/__travelogue/longshot",
            {"tripId": trip_id, "scale": 1, "format": "png", "platform": "wechat_moments"},
        )
    if st != 202 or not body.get("jobId"):
        # maybe client fallback
        if body.get("fallback") == "client":
            record("STALE-VOCAB", False, f"longshot client fallback only: {body}")
            return
        record("STALE-VOCAB", False, f"longshot start {st} {body}")
        return
    job = wait_job(base, body["jobId"], timeout=300)
    if job.get("status") != "succeeded":
        record("STALE-VOCAB", False, f"longshot {job.get('status')} err={job.get('error')}")
        return

    # Exceed longshot_outputs_stale 0.5s grace (updatedAt vs latest PNG)
    time.sleep(1.2)

    # Refine bump: PATCH intent title (raises mtime / revision)
    trip_json = ROOT / "trips" / trip_id / "trip.json"
    before = json.loads(trip_json.read_text(encoding="utf-8"))
    rev = int((before.get("meta") or {}).get("revision") or 0)
    patch = {
        "title": f"{(before.get('meta') or {}).get('title') or trip_id}·精修试",
        "expectedRevision": rev,
    }
    # try intent patch endpoints
    pst, pbody = _post_json(base, f"/__travelogue/trips/{trip_id}/intent", patch)
    # Some handlers are PATCH only
    if pst in (0, 404, 405) or pbody.get("error"):
        req = urllib.request.Request(
            f"{base}/__travelogue/trips/{trip_id}/intent",
            data=json.dumps(patch).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="PATCH",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                pst = resp.status
                pbody = json.loads(resp.read().decode("utf-8") or "{}")
        except urllib.error.HTTPError as exc:
            pst = exc.code
            try:
                pbody = json.loads(exc.read().decode("utf-8") or "{}")
            except Exception:
                pbody = {}
        except Exception as exc:
            pst, pbody = 0, {"error": str(exc)}

    # Fallback: touch trip.json mtime after writing a no-op revision bump via file
    if pst not in (200, 204) or pbody.get("ok") is False:
        time.sleep(0.2)
        data = json.loads(trip_json.read_text(encoding="utf-8"))
        meta = data.setdefault("meta", {})
        meta["title"] = str(meta.get("title") or trip_id) + "·精修试"
        meta["revision"] = int(meta.get("revision") or 0) + 1
        from datetime import datetime, timezone

        data["updatedAt"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        trip_json.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        patch_note = f"file_bump; intent_http={pst}/{pbody}"
    else:
        patch_note = f"intent_patch={pst}"

    time.sleep(0.6)
    # API shelf list
    _, trips_payload = _get_json(base, "/__travelogue/trips?limit=50")
    items = trips_payload.get("trips") or trips_payload.get("items") or []
    if isinstance(trips_payload.get("data"), list):
        items = trips_payload["data"]
    # shape varies
    if not items and isinstance(trips_payload, dict):
        for k, v in trips_payload.items():
            if isinstance(v, list) and v and isinstance(v[0], dict) and "tripId" in v[0]:
                items = v
                break

    hit = None
    for it in items:
        if str(it.get("tripId") or it.get("id") or "") == trip_id:
            hit = it
            break

    api_stale = bool(hit and hit.get("longshotStale"))
    # UI check
    from playwright.sync_api import sync_playwright

    ui_ok = False
    bad = 0
    badge = 0
    resume = 0
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.goto(f"{base}/", wait_until="networkidle")
        page.wait_for_timeout(1500)
        bad = page.get_by_text("长图待更新").count()
        badge = page.locator(".v2-shelf__stale-badge", has_text="长图可更新").count()
        resume = page.get_by_text("更新长图").count()
        # also check preview dock
        page.goto(f"{base}/{trip_id}/index.html", wait_until="domcontentloaded")
        page.wait_for_timeout(2000)
        content = page.content() or ""
        dock_ok = "长图可更新" in content or "更新长图" in content or page.locator(".preview-toolbar__longshot--stale").count() > 0
        ui_ok = bad == 0 and (badge > 0 or resume > 0 or dock_ok or api_stale)
        browser.close()

    # Product AC: no「长图待更新」; shelf/API/dock use「长图可更新」
    ok = bad == 0 and (api_stale or badge > 0 or resume > 0 or dock_ok)
    record(
        "STALE-VOCAB",
        ok,
        f"trip={trip_id}; {patch_note}; api_stale={api_stale}; badge={badge}; resume_cta={resume}; bad_vocab={bad}; dock_hint={dock_ok}",
    )


def trial_slow_hint(base: str) -> None:
    """Unique large album + resume Importing UI; assert slow hint after ≥30s."""
    from playwright.sync_api import sync_playwright

    try:
        from PIL import Image, ImageDraw
    except ImportError:
        record("SLOW-HINT", False, "Pillow not available to synthesize unique album")
        return

    slug = f"qhslow-{secrets.token_hex(3)}"
    album = Path(tempfile.gettempdir()) / slug
    if album.exists():
        shutil.rmtree(album)
    album.mkdir()
    # Unique pixels → survive MD5 dedupe; 48 frames keeps wall clock realistic
    for i in range(48):
        im = Image.new("RGB", (640, 480), (i * 3 % 255, 40, 80 + (i * 5) % 150))
        draw = ImageDraw.Draw(im)
        draw.rectangle((20 + i, 20, 200 + i, 180), fill=(255 - i * 2 % 200, 120, 30))
        draw.text((30, 200), f"slow-album-{i}", fill=(255, 255, 255))
        im.save(album / f"shot-{i:03d}.jpg", quality=85)

    wait_idle(base)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.goto(f"{base}/", wait_until="networkidle")
        page.wait_for_timeout(600)

        started = page.evaluate(
            """async (albumPath) => {
              const body = {
                albumPath,
                title: '慢安抚大相册试',
                place: '测试',
                force: true,
                forceStub: true,
                photoCullEnabled: false,
                keepNearDuplicates: true,
              };
              const r = await fetch('/__travelogue/import', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(body),
              });
              const j = await r.json();
              if (!j.jobId) return { error: j, status: r.status };
              const SS = {
                activeJobId: 'travelogue.studio.activeJobId',
                activePending: 'travelogue.studio.activePending',
              };
              // Prefer keys from page if constants expose them
              try {
                sessionStorage.setItem(SS.activeJobId, j.jobId);
                sessionStorage.setItem(SS.activePending, JSON.stringify({
                  albumPath, title: body.title, mode: 'quick_share'
                }));
              } catch (e) {}
              return j;
            }""",
            str(album),
        )
        if not isinstance(started, dict) or not started.get("jobId"):
            # Try alternate SS key prefixes used by v2
            record("SLOW-HINT", False, f"import start failed: {started}")
            browser.close()
            return
        job_id = started["jobId"]

        # Reload → resumeV2ImportIfAny should attach poll + tickSlowHint
        page.goto(f"{base}/", wait_until="domcontentloaded")
        page.wait_for_timeout(2000)

        # Ensure SS keys match product — rewrite from constants if resume missed
        if not (page.locator("#v2-importing").count() and page.locator("#v2-importing").is_visible()):
            page.evaluate(
                """(jobId) => {
                  const keys = [];
                  for (let i = 0; i < sessionStorage.length; i++) keys.push(sessionStorage.key(i));
                  // brute common keys
                  const candidates = [
                    'travelogue.studio.activeJobId',
                    'tl.studio.activeJobId',
                    'activeJobId',
                  ];
                  for (const k of candidates) sessionStorage.setItem(k, jobId);
                }""",
                job_id,
            )
            page.goto(f"{base}/", wait_until="domcontentloaded")
            page.wait_for_timeout(1500)

        hint_seen = False
        hint_text = ""
        t0 = time.time()
        while time.time() - t0 < 100:
            hint = page.locator("#v2-import-slow-hint")
            if hint.count():
                try:
                    visible = hint.is_visible()
                except Exception:
                    visible = False
                text = (hint.text_content() or "").strip()
                if visible and text and ("比预期久" in text or "耐心" in text or "还在" in text):
                    hint_seen = True
                    hint_text = text
                    break
            # job may finish early — still require wall ≥30s for this AC
            _, job = _get_json(base, f"/__travelogue/status?jobId={job_id}")
            if job.get("status") in ("succeeded", "failed", "cancelled") and time.time() - t0 < 30:
                # Finished too fast — fail this criterion honestly
                record(
                    "SLOW-HINT",
                    False,
                    f"job finished early in {time.time()-t0:.1f}s status={job.get('status')}; need ≥30s wall for hint AC",
                )
                browser.close()
                wait_idle(base)
                return
            if job.get("status") in ("succeeded", "failed", "cancelled") and time.time() - t0 >= 30:
                break
            page.wait_for_timeout(1000)

        elapsed = time.time() - t0
        # Cancel if still running
        _, job = _get_json(base, f"/__travelogue/status?jobId={job_id}")
        if job.get("status") in ("queued", "running"):
            _post_json(base, "/__travelogue/cancel", {"jobId": job_id})
            wait_job(base, job_id, timeout=120)
        wait_idle(base)
        browser.close()

        run_src = (ROOT / "templates" / "studio" / "homepage-v2" / "import-run.js").read_text(
            encoding="utf-8"
        )
        src_ok = "tickSlowHint" in run_src and "SLOW_JOB_MS" in run_src
        # Product gate is 30000ms; 1s poll + reload skew → accept first sight ≥28s
        ok = hint_seen and src_ok and elapsed >= 28 and "比预期久一些" in hint_text
        record(
            "SLOW-HINT",
            ok,
            f"job={job_id}; wall_s={elapsed:.1f}; hint_seen={hint_seen}; hint={hint_text!r}; album_n=48; src_ok={src_ok}",
        )


def trial_old_trip(base: str, trip_dir: Path, uid: str) -> None:
    trip_id = trip_dir.name
    trip = json.loads((trip_dir / "trip.json").read_text(encoding="utf-8"))
    title = (trip.get("meta") or {}).get("title") or trip_id
    assets = len(trip.get("assets") or [])

    # preview fetch
    try:
        with urllib.request.urlopen(f"{base}/{trip_id}/index.html", timeout=60) as resp:
            html = resp.read().decode("utf-8", errors="replace")
            preview_ok = resp.status == 200 and len(html) > 500
    except Exception as exc:
        record(uid, False, f"trip={trip_id}; preview fetch failed: {exc}")
        return

    # entry API if present
    entry_ok = True
    try:
        est, ebody = _get_json(base, f"/__travelogue/trips/{trip_id}/entry")
        entry_ok = est == 200 and bool(ebody)
    except Exception:
        entry_ok = False

    from playwright.sync_api import sync_playwright

    longshot_ui = False
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.goto(f"{base}/{trip_id}/index.html", wait_until="domcontentloaded")
        page.wait_for_timeout(2000)
        try:
            page.wait_for_selector(".preview-toolbar", state="attached", timeout=20000)
        except Exception:
            pass
        content = page.content() or ""
        longshot_ui = "长图" in content
        bad = "长图待更新" in content
        browser.close()

    ok = preview_ok and longshot_ui and not bad
    record(
        uid,
        ok,
        f"trip={trip_id}; title={title!r}; assets={assets}; preview={preview_ok}; entry={entry_ok}; longshot_ui={longshot_ui}; bad_vocab={bad}",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8768")
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT
        / "docs"
        / "acceptance-records"
        / "stable-qh-supplemental-trial-2026-07-15.md",
    )
    args = parser.parse_args()
    base = args.base.rstrip("/")
    try:
        return _run(base)
    finally:
        write_report(base, args.out)


def _run(base: str) -> int:
    try:
        with urllib.request.urlopen(f"{base}/", timeout=10) as resp:
            if resp.status != 200:
                record("SETUP", False, f"HTTP {resp.status}")
                return 1
    except Exception as exc:
        record("SETUP", False, f"unreachable: {exc}")
        return 1
    record("SETUP", True, f"Studio {base}")

    trial_stale_vocab(base)
    trial_slow_hint(base)

    olds = pick_old_trips(2)
    if len(olds) < 2:
        record("OLD-TRIP-A", False, f"need ≥2 old trips, found {len(olds)}")
        record("OLD-TRIP-B", False, "blocked")
    else:
        trial_old_trip(base, olds[0], "OLD-TRIP-A")
        trial_old_trip(base, olds[1], "OLD-TRIP-B")

    failed = [k for k, v in REPORT.items() if k != "SETUP" and not v["ok"]]
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
