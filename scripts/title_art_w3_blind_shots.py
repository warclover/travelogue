"""W3 盲评样本出图（PRD-COVER-CALLIGRAPHY-TITLE-V1 · AC-CAL-BLIND）。

对每条真实 trip 生成同构图成对截图：
- ``*-css.png``：titleArt 关闭（现网 HTML/CSS 标题）
- ``*-art.png``：titleArt 开启（路线 B 贴纸）

并写出：
- ``manifest.json`` / ``manifest.csv``：样本元数据 + 左右随机打乱密钥
- ``scores.csv``：评委打分空表
- ``review.html``：本地预览成对对比（含打乱后的左右标签，不含正确答案）

用法：

    python scripts/title_art_w3_blind_shots.py
    python scripts/title_art_w3_blind_shots.py --limit 4   # 冒烟

注意：会对 trip.json 做临时改动，但每条样本结束都会从 ``.bak`` 完整还原。
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import shutil
import sys
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
except (AttributeError, ValueError):
    pass

from travelogue.cover_engine.title_art import resolve_title_art  # noqa: E402
from travelogue.media.source_resolve import resolve_source_path  # noqa: E402
from travelogue.web.rerender import rerender_draft_trip  # noqa: E402

OUT_DIR = (
    ROOT
    / "docs"
    / "acceptance-records"
    / "attachments"
    / "cover-calligraphy-title-v1-w3-blind-2026-08-08"
)
TRIPS = ROOT / "trips"
VIEWPORT = {"width": 1280, "height": 900}

#: (trip_id, style_override|None) —— None 表示保持 trip 现有 coverOpeningStyle
#: 覆盖 4 款白名单各 ≥2，合计 12。
SAMPLE_PLAN: list[tuple[str, str | None]] = [
    ("demo-0ebda73294", "band-cut"),  # 显式覆盖，避免 trip 被其它样本改风格后串样
    ("demo-2019", None),  # band-cut
    ("demo-1b67b06546", None),  # band-cut（可能需生成）
    ("demo-49551086fe", None),  # band-cut
    ("demo-1547c68851", None),  # veil-footer
    ("demo-3ee2727aea", None),  # veil-footer
    ("demo-20ecc928d6", None),  # veil-footer
    # demo-65db8fd377 焦点落在下半标题区会 focal_conflict；换同构图可用 trip 临时改风格
    ("demo-0ebda73294", "veil-footer"),
    ("demo-album", "contact-stamp"),
    ("demo-e52494839a", "contact-stamp"),
    ("demo-d6697c8dca", "folio-overlap"),
    ("demo-ef0cef1d1d", "folio-overlap"),
]

#: 与 SAMPLE_PLAN 一一对应的预期风格（过滤 --styles 用；override 优先）
_PLAN_STYLE_LABELS = [
    "band-cut",
    "band-cut",
    "band-cut",
    "band-cut",
    "veil-footer",
    "veil-footer",
    "veil-footer",
    "veil-footer",
    "contact-stamp",
    "contact-stamp",
    "folio-overlap",
    "folio-overlap",
]


def _plan_style_label(idx: int) -> str:
    return _PLAN_STYLE_LABELS[idx - 1]


def _load_trip(trip_dir: Path) -> dict:
    return json.loads((trip_dir / "trip.json").read_text(encoding="utf-8"))


def _save_trip(trip_dir: Path, trip: dict) -> None:
    (trip_dir / "trip.json").write_text(
        json.dumps(trip, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _ensure_title_art(trip_dir: Path, trip: dict, *, force: bool) -> dict | None:
    art_dir = trip_dir / "trip-derived" / "title-art"

    def _resolve_asset_path(asset: dict) -> Path | None:
        return resolve_source_path(asset, trip_dir)

    def _write_png(data: bytes) -> str:
        art_dir.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha1(data).hexdigest()[:12]
        out_path = art_dir / f"{digest}.png"
        out_path.write_bytes(data)
        return str(art_dir.relative_to(trip_dir) / out_path.name).replace("\\", "/")

    result = resolve_title_art(
        trip,
        resolve_asset_path=_resolve_asset_path,
        write_png=_write_png,
        route_c_enabled=False,
        force=force,
    )
    _save_trip(trip_dir, trip)
    meta = trip.get("meta") if isinstance(trip.get("meta"), dict) else {}
    title_art = meta.get("titleArt") if isinstance(meta.get("titleArt"), dict) else None
    if result is not None:
        return result.to_meta_dict()
    if title_art and title_art.get("enabled") and not title_art.get("stale"):
        return title_art
    return None


def _set_enabled(trip: dict, enabled: bool) -> None:
    meta = trip.setdefault("meta", {})
    title_art = meta.get("titleArt")
    if not isinstance(title_art, dict):
        return
    title_art["enabled"] = enabled
    title_art["stale"] = False


def _free_port() -> int:
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return


def _start_server(directory: Path, port: int) -> ThreadingHTTPServer:
    root = str(directory)

    class Handler(_QuietHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=root, **kwargs)

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def _shot_cover(page, url: str, out_path: Path) -> None:
    resp = page.goto(url, wait_until="load", timeout=90_000)
    if resp is not None and resp.status >= 400:
        raise RuntimeError(f"HTTP {resp.status} for {url}")
    try:
        page.wait_for_selector(".cover-opening", timeout=30_000)
    except Exception:
        title = page.title()
        body = page.locator("body").inner_text()[:400]
        raise RuntimeError(f"missing .cover-opening at {url} title={title!r} body={body!r}") from None
    # 直出 trips HTML 时没有 Studio shell.css，folio-plate-meta 会露出来；一并藏掉草稿栏
    page.evaluate(
        """() => {
          const root = document.documentElement;
          root.removeAttribute('data-debug');
          if (root.getAttribute('data-folio') === 'lite' || root.getAttribute('data-folio') === 'full') {
            root.setAttribute('data-folio', 'off');
          }
        }"""
    )
    page.add_style_tag(
        content="""
        .screenplay-toolbar,
        .longshot-toolbar,
        .share-toolbar,
        [data-block="screenplay-toolbar"],
        [data-block="share-toolbar"],
        .longshot-file-banner,
        .longshot-export-sheet,
        .footer-cta,
        .surface-nav,
        .golden-banner,
        .folio-plate-meta {
          display: none !important;
          visibility: hidden !important;
          pointer-events: none !important;
        }
        """
    )
    page.wait_for_timeout(300)
    loc = page.locator(".cover-opening").first
    box = loc.bounding_box()
    if not box or box["width"] < 10 or box["height"] < 10:
        raise RuntimeError(f"invalid .cover-opening box at {url}: {box!r}")
    # element screenshot：只截封面节点，避免 page clip 把下一屏叠进来的像素带上
    loc.screenshot(path=str(out_path))


def _display_title(meta: dict) -> str:
    from travelogue.domain.title_humanize import resolve_display_title

    return resolve_display_title(meta)


def process_sample(
    *,
    pair_id: str,
    trip_id: str,
    style_override: str | None,
    page,
    base_url: str,
    rng: random.Random,
    force: bool = False,
) -> dict | None:
    trip_dir = TRIPS / trip_id
    trip_json = trip_dir / "trip.json"
    if not trip_json.is_file():
        print(f"SKIP {trip_id}: missing trip.json")
        return None

    bak = trip_dir / "trip.json.w3blind.bak"
    shutil.copy2(trip_json, bak)
    try:
        trip = _load_trip(trip_dir)
        meta = trip.setdefault("meta", {})
        native_style = str(meta.get("coverOpeningStyle") or "")
        target_style = style_override or native_style
        if style_override:
            meta["coverOpeningStyle"] = style_override
            _save_trip(trip_dir, trip)

        need_force = force or bool(style_override) or not (
            isinstance(meta.get("titleArt"), dict)
            and meta["titleArt"].get("enabled")
            and not meta["titleArt"].get("stale")
            and str(meta["titleArt"].get("openingStyleId") or "") == target_style
        )
        title_art = _ensure_title_art(trip_dir, trip, force=need_force)
        if not title_art:
            print(f"SKIP {trip_id}: title-art fail-open (style={target_style})")
            return None

        engine = str(title_art.get("engine") or "")
        if engine != "clean-pipeline-v1":
            print(f"SKIP {trip_id}: engine={engine} (本轮只要路线 B)")
            return None

        # ON
        trip = _load_trip(trip_dir)
        _set_enabled(trip, True)
        _save_trip(trip_dir, trip)
        rerender_draft_trip(trip_dir / "trip.json")
        art_path = OUT_DIR / f"{pair_id}-art.png"
        _shot_cover(page, f"{base_url}/{trip_id}/index.html", art_path)

        # OFF
        trip = _load_trip(trip_dir)
        _set_enabled(trip, False)
        _save_trip(trip_dir, trip)
        rerender_draft_trip(trip_dir / "trip.json")
        css_path = OUT_DIR / f"{pair_id}-css.png"
        _shot_cover(page, f"{base_url}/{trip_id}/index.html", css_path)

        trip = _load_trip(trip_dir)
        meta = trip.get("meta") if isinstance(trip.get("meta"), dict) else {}
        title = _display_title(meta)
        # 左右随机：True = 艺术字在左
        art_on_left = rng.random() < 0.5
        left_file = f"{pair_id}-art.png" if art_on_left else f"{pair_id}-css.png"
        right_file = f"{pair_id}-css.png" if art_on_left else f"{pair_id}-art.png"
        left_kind = "art" if art_on_left else "css"
        right_kind = "css" if art_on_left else "art"

        row = {
            "pairId": pair_id,
            "tripId": trip_id,
            "style": target_style,
            "nativeStyle": native_style,
            "styleOverride": style_override or "",
            "title": title,
            "engine": engine,
            "assetPath": str(title_art.get("assetPath") or ""),
            "artFile": art_path.name,
            "cssFile": css_path.name,
            "leftFile": left_file,
            "rightFile": right_file,
            "leftKind": left_kind,
            "rightKind": right_kind,
            "artOnLeft": art_on_left,
        }
        print(
            f"OK {pair_id} · {trip_id} · {target_style} · title={title!r} · "
            f"left={left_kind}"
        )
        return row
    finally:
        if bak.is_file():
            shutil.move(str(bak), str(trip_json))
            try:
                rerender_draft_trip(trip_dir / "trip.json")
            except Exception as exc:  # noqa: BLE001
                print(f"WARN restore rerender {trip_id}: {exc}")


def _write_manifest(rows: list[dict]) -> None:
    (OUT_DIR / "manifest.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    fields = [
        "pairId",
        "tripId",
        "style",
        "title",
        "leftFile",
        "rightFile",
        "leftKind",
        "rightKind",
        "artOnLeft",
        "engine",
        "assetPath",
        "styleOverride",
    ]
    with (OUT_DIR / "manifest.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    # 评委可见表：不含 leftKind/rightKind/artOnLeft 答案
    with (OUT_DIR / "scores.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            [
                "pairId",
                "tripId",
                "style",
                "title",
                "leftFile",
                "rightFile",
                "choice",  # left | right | tie
                "raterId",
                "notes",
            ]
        )
        for row in rows:
            writer.writerow(
                [
                    row["pairId"],
                    row["tripId"],
                    row["style"],
                    row["title"],
                    row["leftFile"],
                    row["rightFile"],
                    "",
                    "",
                    "",
                ]
            )

    # 答案钥（评委不应看到）
    with (OUT_DIR / "answer-key.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["pairId", "artSide", "cssSide", "artOnLeft"])
        for row in rows:
            writer.writerow(
                [
                    row["pairId"],
                    "left" if row["artOnLeft"] else "right",
                    "right" if row["artOnLeft"] else "left",
                    row["artOnLeft"],
                ]
            )


def _write_review_html(rows: list[dict]) -> None:
    cards = []
    for row in rows:
        cards.append(
            f"""
<section class="pair" id="{row["pairId"]}">
  <h2>{row["pairId"]} · {row["style"]} · {row["title"]}</h2>
  <p class="meta">{row["tripId"]}（评委请忽略 tripId，只看图）</p>
  <div class="cols">
    <figure>
      <img src="{row["leftFile"]}" alt="left" />
      <figcaption>左</figcaption>
    </figure>
    <figure>
      <img src="{row["rightFile"]}" alt="right" />
      <figcaption>右</figcaption>
    </figure>
  </div>
  <p class="prompt">哪一张封面标题你更愿意直接分享？左 / 右 / 难分</p>
</section>
"""
        )
    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <title>CAL W3 盲评预览（路线 B）</title>
  <style>
    body {{ font-family: "Segoe UI", "PingFang SC", sans-serif; margin: 24px; background: #f6f4ef; color: #222; }}
    h1 {{ font-size: 1.4rem; }}
    .pair {{ background: #fff; border-radius: 12px; padding: 16px 18px 20px; margin: 0 0 22px; box-shadow: 0 1px 4px rgba(0,0,0,.06); }}
    .cols {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
    img {{ width: 100%; height: auto; border-radius: 8px; background: #ddd; }}
    figcaption {{ text-align: center; margin-top: 6px; color: #666; }}
    .meta, .prompt {{ color: #666; font-size: .92rem; }}
    .prompt {{ font-weight: 600; color: #333; }}
  </style>
</head>
<body>
  <h1>封面装帧标题 · W3 盲评预览（路线 B）</h1>
  <p>左右已随机打乱。请勿查看 <code>answer-key.csv</code> / <code>manifest.csv</code> 中的答案列。</p>
  {"".join(cards)}
</body>
</html>
"""
    (OUT_DIR / "review.html").write_text(html, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="W3 盲评路线 B 成对截图")
    parser.add_argument("--limit", type=int, default=0, help="只跑前 N 条（冒烟）")
    parser.add_argument(
        "--styles",
        default="",
        help="逗号分隔风格过滤，如 band-cut（按 SAMPLE_PLAN 原序号保留 pairId）",
    )
    parser.add_argument(
        "--merge-manifest",
        action="store_true",
        help="与已有 manifest.json 按 pairId 合并（局部重跑时用）",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="强制重生成 titleArt（配色/衬底修复后局部重跑用）",
    )
    parser.add_argument("--seed", type=int, default=20260808, help="左右打乱随机种子")
    args = parser.parse_args(argv)

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("需要 playwright：pip install playwright && python -m playwright install chromium")
        return 2

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    style_filter = {s.strip() for s in args.styles.split(",") if s.strip()}
    indexed_plan: list[tuple[int, tuple[str, str | None]]] = []
    for idx, item in enumerate(SAMPLE_PLAN, start=1):
        if args.limit > 0 and idx > args.limit:
            break
        trip_id, style_override = item
        planned = style_override or _plan_style_label(idx)
        if style_filter and planned not in style_filter:
            continue
        indexed_plan.append((idx, item))
    rng = random.Random(args.seed)

    port = _free_port()
    server = _start_server(TRIPS, port)
    base_url = f"http://127.0.0.1:{port}"
    rows: list[dict] = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport=VIEWPORT)
            for idx, (trip_id, style_override) in indexed_plan:
                pair_id = f"b{idx:02d}"
                try:
                    row = process_sample(
                        pair_id=pair_id,
                        trip_id=trip_id,
                        style_override=style_override,
                        page=page,
                        base_url=base_url,
                        rng=rng,
                        force=bool(args.force),
                    )
                except Exception as exc:  # noqa: BLE001
                    print(f"FAIL {pair_id} · {trip_id}: {exc}")
                    row = None
                if row:
                    rows.append(row)
            browser.close()
    finally:
        server.shutdown()
        server.server_close()

    if not rows:
        print("FAIL: no pairs produced")
        return 1

    if args.merge_manifest and (OUT_DIR / "manifest.json").is_file():
        existing = json.loads((OUT_DIR / "manifest.json").read_text(encoding="utf-8"))
        by_id = {r["pairId"]: r for r in existing if isinstance(r, dict)}
        for row in rows:
            by_id[row["pairId"]] = row
        rows = [by_id[k] for k in sorted(by_id.keys())]

    _write_manifest(rows)
    _write_review_html(rows)

    by_style: dict[str, int] = {}
    for row in rows:
        by_style[row["style"]] = by_style.get(row["style"], 0) + 1
    print(f"\nproduced {len(rows)} pairs → {OUT_DIR}")
    print("by style:", by_style)
    if len(rows) < 12:
        print(f"WARN: need ≥12 for full W3 pool, got {len(rows)}")
        return 1
    for style in ("band-cut", "veil-footer", "contact-stamp", "folio-overlap"):
        if by_style.get(style, 0) < 2:
            print(f"WARN: style {style} has <2 pairs")
            return 1
    print("PASS: ≥12 pairs and ≥2 per whitelist style")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
