"""ALS · album_landscape 16:9 screen capture (PRD-ALBUM-LANDSCAPE-SCREENS-V1).

Captures already-rendered ``index.html`` screen nodes. Does not import
``_BROWSER_POOL`` / ``_PlaywrightBrowserPool`` (D-ALS-17). Does not touch
``album_spread`` / collage / CardGrouper.

Two failure modes that must not trade off:
- White PNG: never hide ``html[data-preview-toolbar]``; never clip with
  viewport coords; force ``.breath-reveal`` visible.
- Fake "too many screens" timeout: do not use Playwright ``page.screenshot``
  as the primary shot (it waits for webfonts/stability). CDP first.
"""

from __future__ import annotations

import json
import logging
import re
import threading
import time
from html.parser import HTMLParser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from PIL import Image

from travelogue.export.longshot import (
    EXPORT_OUTPUT_DIRNAME,
    CancelCheckFn,
    CancelRegisterFn,
    LongshotCancelled,
    LongshotExportError,
    LongshotExportResult,
    LongshotOutput,
    ProgressFn,
    _slug_title,
    _trip_title,
    acquire_browser,
    raise_if_longshot_cancelled,
    release_browser,
)
from travelogue.export.platform_longshot import PlatformExportWriter
from travelogue.export.platform_profiles import file_prefix_for_platform, get_profile

_log = logging.getLogger(__name__)

PLATFORM_ID = "album_landscape"
INDEX_NAME = "index.html"
PAGE_BLOCK_TYPES = frozenset(
    {"cover-opening", "chapter-separator", "layout-screen", "cover-closing"}
)
PAGE_BLOCK_SELECTOR = (
    '[data-block="cover-opening"], '
    '[data-block="chapter-separator"], '
    '[data-block="layout-screen"], '
    '[data-block="cover-closing"]'
)
VIEWPORT_CSS_W = 1920
VIEWPORT_CSS_H = 1080
DEVICE_SCALE_FACTOR = 2
OUTPUT_W = 3840
OUTPUT_H = 2160
PAGE_BG_HEX = "#f5f2ea"
PAGE_BG_RGB = (245, 242, 234)
JOB_TIMEOUT_SEC = 600
SCREEN_TIMEOUT_MS = 5_000
WAIT_IMGS_BUDGET_MS = 2_500
WAIT_FONTS_BUDGET_MS = 1_500
PLAYWRIGHT_SHOT_TIMEOUT_MS = 2_000
MIN_CAPTURE_BYTES = 64

CAPTURE_CSS = """
.layout-screen--viewport-fit {
  width: 100% !important;
  max-height: none !important;
  aspect-ratio: 16 / 9 !important;
}
.preview-toolbar,
.screenplay-toolbar,
[data-preview-toolbar]:not(html):not(body) {
  display: none !important;
  visibility: hidden !important;
}
.breath-reveal,
.cover-breath-reveal,
.closing-breath-reveal {
  opacity: 1 !important;
  transform: none !important;
  visibility: visible !important;
  filter: none !important;
}
*, *::before, *::after {
  animation: none !important;
  animation-duration: 0s !important;
  transition: none !important;
  scroll-behavior: auto !important;
}
"""

PREPARE_PAGE_JS = """() => {
  const hideSel = '.preview-toolbar, .screenplay-toolbar, [data-preview-toolbar]';
  document.querySelectorAll(hideSel).forEach((el) => {
    if (el === document.documentElement || el === document.body) return;
    el.style.setProperty('display', 'none', 'important');
    el.style.setProperty('visibility', 'hidden', 'important');
  });
  try {
    if (window.TravelogueBreath && typeof window.TravelogueBreath.destroy === 'function') {
      window.TravelogueBreath.destroy();
    }
  } catch (e) {}
  document.documentElement.setAttribute('data-breath', 'off');
  document.documentElement.classList.remove(
    'has-motion', 'motion-on', 'breath-scrub-active', 'cover-motion-active'
  );
  if (document.body) {
    document.body.classList.remove('has-motion', 'motion-on');
  }
  document.querySelectorAll(
    '.breath-reveal, .cover-breath-reveal, .closing-breath-reveal'
  ).forEach((el) => {
    el.classList.add('is-visible');
    el.style.setProperty('opacity', '1', 'important');
    el.style.setProperty('transform', 'none', 'important');
    el.style.setProperty('visibility', 'visible', 'important');
  });
}"""

READ_BG_JS = """() => {
  const v = getComputedStyle(document.documentElement)
    .getPropertyValue('--bg-page').trim();
  return v || '#f5f2ea';
}"""

WAIT_IMGS_JS = """async (el) => {
  const vw = window.innerWidth || 1920;
  const vh = window.innerHeight || 1080;
  const budget = 2500;
  const imgs = Array.from(el.querySelectorAll('img')).filter((img) => {
    const r = img.getBoundingClientRect();
    return r.width > 0 && r.height > 0 && r.bottom > 0 && r.right > 0
      && r.top < vh && r.left < vw;
  });
  const waitOne = (img) => {
    try { img.loading = 'eager'; } catch (e) {}
    if (img.complete) return Promise.resolve();
    if (!img.currentSrc && !img.src) return Promise.resolve();
    return new Promise((resolve) => {
      const done = () => resolve();
      img.addEventListener('load', done, { once: true });
      img.addEventListener('error', done, { once: true });
    });
  };
  await Promise.race([
    Promise.all(imgs.map(waitOne)),
    new Promise((resolve) => setTimeout(resolve, budget)),
  ]);
}"""

WAIT_FONTS_JS = """async () => {
  try {
    await Promise.race([
      document.fonts.ready,
      new Promise((resolve) => setTimeout(resolve, 1500)),
    ]);
  } catch (e) {}
}"""

RECT_JS = """(el) => {
  const r = el.getBoundingClientRect();
  return {
    x: r.x,
    y: r.y,
    width: r.width,
    height: r.height,
    pageX: r.x + window.scrollX,
    pageY: r.y + window.scrollY,
  };
}"""

FREEZE_NODE_JS = """(el) => {
  el.querySelectorAll('img').forEach((img) => {
    if (!img.complete || img.naturalWidth === 0) {
      img.style.setProperty('visibility', 'hidden', 'important');
    }
  });
  el.querySelectorAll('video').forEach((v) => {
    try { v.pause(); } catch (e) {}
  });
}"""

PAINT_JS = """() => new Promise((resolve) => {
  requestAnimationFrame(() => requestAnimationFrame(resolve));
})"""


def album_landscape_enabled(cfg: Any | None = None) -> bool:
    if cfg is None:
        try:
            from travelogue.config import get_config

            cfg = get_config()
        except Exception:
            return True
    studio = getattr(cfg, "studio", None)
    flag = getattr(studio, "album_landscape", None) if studio is not None else None
    return bool(getattr(flag, "enabled", True))


def _load_trip(trip_dir: Path) -> dict[str, Any]:
    trip_json = trip_dir / "trip.json"
    if not trip_json.is_file():
        return {}
    try:
        data = json.loads(trip_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _parse_css_color(raw: str) -> tuple[int, int, int]:
    s = str(raw or "").strip()
    if s.startswith("#"):
        hexpart = s[1:]
        if len(hexpart) == 3:
            hexpart = "".join(ch * 2 for ch in hexpart)
        if len(hexpart) >= 6:
            try:
                return (int(hexpart[0:2], 16), int(hexpart[2:4], 16), int(hexpart[4:6], 16))
            except ValueError:
                return PAGE_BG_RGB
    match = re.match(
        r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)",
        s,
        flags=re.IGNORECASE,
    )
    if match:
        return (int(match.group(1)), int(match.group(2)), int(match.group(3)))
    return PAGE_BG_RGB


def png_is_flat_white(png_bytes: bytes) -> bool:
    """True when the bitmap is a single near-white color (the html-hidden bug)."""
    try:
        img = Image.open(BytesIO(png_bytes)).convert("RGB")
    except Exception:
        return False
    extrema = img.getextrema()
    if not extrema or len(extrema) < 3:
        return False
    return all(lo == hi and int(lo) >= 250 for lo, hi in extrema[:3])


def letterbox_to_landscape(
    png_bytes: bytes,
    *,
    bg: tuple[int, int, int] = PAGE_BG_RGB,
    width: int = OUTPUT_W,
    height: int = OUTPUT_H,
) -> bytes:
    """Contain-fit onto a 16:9 canvas. No cover crop, no black bars."""
    img = Image.open(BytesIO(png_bytes)).convert("RGB")
    if img.size == (width, height):
        buf = BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    canvas = Image.new("RGB", (width, height), bg)
    src_w, src_h = img.size
    scale = min(width / max(src_w, 1), height / max(src_h, 1))
    tw = max(1, int(round(src_w * scale)))
    th = max(1, int(round(src_h * scale)))
    fg = img.resize((tw, th), Image.Resampling.LANCZOS)
    x0 = (width - tw) // 2
    y0 = (height - th) // 2
    canvas.paste(fg, (x0, y0))
    buf = BytesIO()
    canvas.save(buf, format="PNG")
    return buf.getvalue()


def viewport_intersection(
    rect: dict[str, float],
    *,
    vw: int = VIEWPORT_CSS_W,
    vh: int = VIEWPORT_CSS_H,
) -> dict[str, Any] | None:
    """Visible 16:9-viewport slice of a node, plus element-relative clip."""
    rx = float(rect.get("x") or 0)
    ry = float(rect.get("y") or 0)
    rw = float(rect.get("width") or 0)
    rh = float(rect.get("height") or 0)
    ix = max(0.0, rx)
    iy = max(0.0, ry)
    ix2 = min(float(vw), rx + rw)
    iy2 = min(float(vh), ry + rh)
    vis_w = ix2 - ix
    vis_h = iy2 - iy
    if vis_w < 1 or vis_h < 1:
        return None
    return {
        "clip": {
            "x": max(0.0, ix - rx),
            "y": max(0.0, iy - ry),
            "width": vis_w,
            "height": vis_h,
        },
        "origin": (ix, iy),
        "width": vis_w,
        "height": vis_h,
    }


def place_clip_on_landscape(
    png_bytes: bytes,
    origin_css: tuple[float, float],
    *,
    bg: tuple[int, int, int] = PAGE_BG_RGB,
    dsf: int = DEVICE_SCALE_FACTOR,
) -> bytes:
    """Paste a viewport-clipped element shot onto 3840×2160 paper (no cover crop)."""
    img = Image.open(BytesIO(png_bytes)).convert("RGB")
    if img.size == (OUTPUT_W, OUTPUT_H) and origin_css == (0.0, 0.0):
        buf = BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    canvas = Image.new("RGB", (OUTPUT_W, OUTPUT_H), bg)
    x = int(round(float(origin_css[0]) * dsf))
    y = int(round(float(origin_css[1]) * dsf))
    canvas.paste(img, (x, y))
    buf = BytesIO()
    canvas.save(buf, format="PNG")
    return buf.getvalue()


def compose_viewport_box(
    png_bytes: bytes,
    rect: dict[str, float],
    *,
    vw: int = VIEWPORT_CSS_W,
    vh: int = VIEWPORT_CSS_H,
    dsf: int = DEVICE_SCALE_FACTOR,
    bg: tuple[int, int, int] = PAGE_BG_RGB,
) -> bytes:
    """Crop the viewport-visible slice of an element screenshot onto 16:9 paper.

    Tall nodes: take the visible 16:9 slice (do not letterbox the full flow).
    Short nodes: paste onto a paper-colored 16:9 canvas at the viewport position.
    """
    img = Image.open(BytesIO(png_bytes)).convert("RGB")
    rx = float(rect.get("x") or 0)
    ry = float(rect.get("y") or 0)
    rw = float(rect.get("width") or 0)
    rh = float(rect.get("height") or 0)
    vis_left = max(0.0, rx)
    vis_top = max(0.0, ry)
    vis_right = min(float(vw), rx + rw)
    vis_bottom = min(float(vh), ry + rh)
    if vis_right <= vis_left or vis_bottom <= vis_top:
        return letterbox_to_landscape(png_bytes, bg=bg)

    crop_x = int(round((vis_left - rx) * dsf))
    crop_y = int(round((vis_top - ry) * dsf))
    crop_w = max(1, int(round((vis_right - vis_left) * dsf)))
    crop_h = max(1, int(round((vis_bottom - vis_top) * dsf)))
    crop_x = max(0, min(crop_x, max(img.width - 1, 0)))
    crop_y = max(0, min(crop_y, max(img.height - 1, 0)))
    crop_w = min(crop_w, max(img.width - crop_x, 1))
    crop_h = min(crop_h, max(img.height - crop_y, 1))
    piece = img.crop((crop_x, crop_y, crop_x + crop_w, crop_y + crop_h))

    canvas = Image.new("RGB", (vw * dsf, vh * dsf), bg)
    paste_x = max(0, int(round(vis_left * dsf)))
    paste_y = max(0, int(round(vis_top * dsf)))
    canvas.paste(piece, (paste_x, paste_y))
    buf = BytesIO()
    canvas.save(buf, format="PNG")
    return buf.getvalue()


class _BlockCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.stack: list[str] = []
        self.has_main = False
        self._all: list[tuple[bool, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.stack.append(tag.lower())
        if tag.lower() == "main":
            self.has_main = True
        attrs_d = {k: (v or "") for k, v in attrs}
        block = attrs_d.get("data-block")
        if block in PAGE_BLOCK_TYPES:
            self._all.append(("main" in self.stack, block))

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i] == tag:
                del self.stack[i:]
                break

    def result(self) -> list[str]:
        if self.has_main:
            return [block for in_main, block in self._all if in_main]
        return [block for _, block in self._all]


def collect_page_blocks_from_html(html: str) -> list[str]:
    """DOM-order page blocks inside ``<main>`` (or ``body`` if no main)."""
    parser = _BlockCollector()
    parser.feed(html or "")
    return parser.result()


def resolve_preview_index_url(
    trip_dir: Path,
    *,
    base_url: str | None = None,
    trip_id: str | None = None,
    host: str = "127.0.0.1",
    port: int = 0,
) -> tuple[str, ThreadingHTTPServer | None]:
    """HTTP URL for ``index.html``. Never ``file://`` / ``index-longshot.html``."""
    if base_url:
        base = str(base_url).rstrip("/")
        slug = trip_id or trip_dir.name
        url = f"{base}/{slug}/{INDEX_NAME}"
        _assert_preview_index_url(url)
        return url, None

    server = _start_static_server(trip_dir, host, port or 0)
    bound_port = server.server_address[1]
    url = f"http://{host}:{bound_port}/{INDEX_NAME}"
    _assert_preview_index_url(url)
    return url, server


def _assert_preview_index_url(url: str) -> None:
    path = urlparse(str(url)).path.lower()
    if "index-longshot.html" in path or "index-mobile.html" in path:
        raise LongshotExportError(
            "E_ALS_CAPTURE_FAILED",
            "截取横版画册失败，请重试",
        )
    if not path.endswith("/index.html") and not path.endswith("index.html"):
        raise LongshotExportError(
            "E_ALS_CAPTURE_FAILED",
            "截取横版画册失败，请重试",
        )
    if str(url).startswith("file:"):
        raise LongshotExportError(
            "E_ALS_CAPTURE_FAILED",
            "截取横版画册失败，请重试",
        )


def _start_static_server(directory: Path, host: str, port: int) -> ThreadingHTTPServer:
    handler = lambda *args, **kwargs: SimpleHTTPRequestHandler(  # noqa: E731
        *args, directory=str(directory), **kwargs
    )
    server = ThreadingHTTPServer((host, port or 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def _is_screens_engine(trip: dict[str, Any]) -> bool:
    from travelogue.layout_engine.planner.screen_planner import screens_layout_active

    return bool(screens_layout_active(trip))


def export_album_landscape(
    trip_dir: Path,
    *,
    scale: int = 2,
    fmt: str = "png",
    progress: ProgressFn | None = None,
    cancel_check: CancelCheckFn | None = None,
    cancel_register: CancelRegisterFn | None = None,
    base_url: str | None = None,
    trip_id: str | None = None,
    host: str = "127.0.0.1",
    port: int = 0,
    slide_count: int | None = None,
    pad_mode: str | None = None,
    cfg: Any | None = None,
) -> LongshotExportResult:
    """Capture each preview screen as a 16:9 PNG. Ignores slideCount / padMode."""
    if not album_landscape_enabled(cfg):
        raise LongshotExportError("E_ALS_DISABLED", "横版画册未开启")

    trip_dir = Path(trip_dir).resolve()
    if slide_count is not None:
        _log.info("album_landscape ignores slideCount=%s", slide_count)
    if pad_mode:
        _log.info("album_landscape ignores padMode=%s", pad_mode)
    _log.info("album_landscape scale=%s (geometry locked 16:9)", scale)
    _ = fmt

    index_html = trip_dir / INDEX_NAME
    if not index_html.is_file():
        raise LongshotExportError("E_ALS_NO_INDEX", "请先完成预览渲染")

    trip = _load_trip(trip_dir)
    if not _is_screens_engine(trip):
        raise LongshotExportError(
            "E_ALS_NOT_SCREENS",
            "横版画册需要 16:9 预览（screens）",
        )

    title = _trip_title(trip_dir)
    prefix = file_prefix_for_platform(title, PLATFORM_ID)
    profile = get_profile(PLATFORM_ID)
    url, server = resolve_preview_index_url(
        trip_dir, base_url=base_url, trip_id=trip_id, host=host, port=port
    )

    def _report(cur: int, total: int, hint: str) -> None:
        if progress:
            progress(cur, total, hint)

    acquired = False
    page = None
    cdp = None
    writer: PlatformExportWriter | None = None
    deadline = time.monotonic() + JOB_TIMEOUT_SEC
    try:
        raise_if_longshot_cancelled(cancel_check)
        try:
            browser = acquire_browser()
        except LongshotExportError as exc:
            if exc.code == "E_LNG_PLAYWRIGHT":
                raise LongshotExportError(
                    "E_LNG_PLAYWRIGHT",
                    "横版画册需要本机浏览器组件",
                ) from exc
            raise
        acquired = True

        page = browser.new_page(
            viewport={"width": VIEWPORT_CSS_W, "height": VIEWPORT_CSS_H},
            device_scale_factor=DEVICE_SCALE_FACTOR,
        )
        if cancel_register is not None:

            def _abort_page() -> None:
                try:
                    page.close()
                except Exception:
                    _log.debug("als cancel page.close skipped", exc_info=True)

            cancel_register(_abort_page)

        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60_000)
            page.wait_for_selector(PAGE_BLOCK_SELECTOR, timeout=30_000)
        except Exception as exc:
            _raise_timeout_or_capture(exc)

        page.add_style_tag(content=CAPTURE_CSS)
        page.evaluate(PREPARE_PAGE_JS)
        try:
            page.evaluate(WAIT_FONTS_JS, timeout=WAIT_FONTS_BUDGET_MS + 1_000)
        except Exception:
            _log.debug("als wait fonts skipped", exc_info=True)
        bg = _parse_css_color(str(page.evaluate(READ_BG_JS) or PAGE_BG_HEX))

        locators = _page_block_locators(page)
        n = int(locators.count())
        if n <= 0:
            raise LongshotExportError("E_ALS_NO_PAGES", "预览里没有可导出的屏")

        writer = PlatformExportWriter(
            trip_dir / EXPORT_OUTPUT_DIRNAME, prefix, ext="png", single_file=False
        )
        cdp = _attach_cdp(page)
        try:
            with writer:
                for i in range(n):
                    if time.monotonic() > deadline:
                        raise LongshotExportError(
                            "E_ALS_TIMEOUT",
                            "屏数较多导致超时，请重试或减少章节后导出",
                        )
                    raise_if_longshot_cancelled(cancel_check)
                    item = locators.nth(i)
                    _report(i, n, f"正在截取横版页 第 {i + 1}/{n} 屏…")
                    try:
                        item.evaluate(
                            "el => el.scrollIntoView({block:'start',inline:'nearest'})",
                            timeout=SCREEN_TIMEOUT_MS,
                        )
                        item.evaluate(
                            WAIT_IMGS_JS, timeout=WAIT_IMGS_BUDGET_MS + 1_000
                        )
                        item.evaluate(FREEZE_NODE_JS, timeout=3_000)
                        try:
                            page.evaluate(PAINT_JS, timeout=1_000)
                        except Exception:
                            pass
                        raw = _screenshot_viewport(page, cdp=cdp)
                        if png_is_flat_white(raw):
                            page.evaluate(PREPARE_PAGE_JS, timeout=3_000)
                            try:
                                page.evaluate(PAINT_JS, timeout=1_000)
                            except Exception:
                                pass
                            raw = _screenshot_viewport(page, cdp=cdp)
                    except LongshotCancelled:
                        raise
                    except Exception as exc:
                        _log.warning("als screen %s/%s failed: %s", i + 1, n, exc)
                        _raise_timeout_or_capture(exc)
                    if not raw or len(raw) < MIN_CAPTURE_BYTES or png_is_flat_white(raw):
                        raise LongshotExportError(
                            "E_ALS_CAPTURE_FAILED",
                            "截取横版画册失败，请重试",
                        )
                    png = letterbox_to_landscape(raw, bg=bg)
                    if Image.open(BytesIO(png)).size != (OUTPUT_W, OUTPUT_H):
                        png = letterbox_to_landscape(png, bg=bg)
                    writer.write(i + 1, png)
                raise_if_longshot_cancelled(cancel_check)
                finals = writer.commit()
        except LongshotCancelled:
            if writer is not None:
                writer.rollback()
            raise
        except Exception:
            if writer is not None:
                writer.rollback()
            raise

        _report(n, n, f"已生成 {len(finals)} 张 16:9 横版页（与预览同屏）")
        outputs = [
            LongshotOutput(path=path, capture_method="album_landscape") for path in finals
        ]
        guide = (profile.publish_guide or "").strip()
        n_out = len(outputs)
        return LongshotExportResult(
            outputs=outputs,
            capture_method="album_landscape",
            title=_slug_title(title),
            segmented=n_out > 1,
            segment_reason="album_landscape",
            user_hint=(
                f"已生成 {n_out} 张 16:9 横版页（与预览同屏）· "
                "可预览或送印（套 A4 请留白，勿裁切）。页数较多时文件较大。"
            ),
            platform=PLATFORM_ID,
            profile_label=profile.label,
            target_page_count=n_out,
            publish_guide=guide,
            page_count=n_out,
            output_format="png",
        )
    finally:
        if cdp is not None:
            try:
                cdp.detach()
            except Exception:
                _log.debug("als cdp.detach skipped", exc_info=True)
        if page is not None:
            try:
                page.close()
            except Exception:
                _log.debug("als page.close skipped", exc_info=True)
        if acquired:
            release_browser()
        if server is not None:
            try:
                server.shutdown()
                server.server_close()
            except Exception:
                _log.debug("als static server shutdown skipped", exc_info=True)


def _page_block_locators(page: Any) -> Any:
    main = page.locator("main")
    if int(main.count()) > 0:
        loc = main.locator(PAGE_BLOCK_SELECTOR)
        if int(loc.count()) > 0:
            return loc
    return page.locator("body").locator(PAGE_BLOCK_SELECTOR)


def _screenshot_viewport(page: Any, *, cdp: Any | None = None) -> bytes:
    """Current viewport. CDP first — Playwright screenshot waits on fonts."""
    cdp_raw = _cdp_viewport_png(page, session=cdp)
    if cdp_raw and len(cdp_raw) >= MIN_CAPTURE_BYTES and not png_is_flat_white(cdp_raw):
        return cdp_raw
    last: BaseException | None = None
    try:
        raw = page.screenshot(
            type="png",
            caret="hide",
            timeout=PLAYWRIGHT_SHOT_TIMEOUT_MS,
        )
        if raw and len(raw) >= MIN_CAPTURE_BYTES:
            return raw
    except Exception as exc:
        last = exc
        _log.debug("als playwright screenshot fallback failed", exc_info=True)
    if cdp_raw and len(cdp_raw) >= MIN_CAPTURE_BYTES:
        return cdp_raw
    if last is not None:
        raise last
    raise LongshotExportError(
        "E_ALS_CAPTURE_FAILED",
        "截取横版画册失败，请重试",
    )


def _attach_cdp(page: Any) -> Any | None:
    try:
        ctx = getattr(page, "context", None)
        if ctx is None:
            return None
        session = ctx.new_cdp_session(page)
        session.send(
            "Emulation.setDeviceMetricsOverride",
            {
                "mobile": False,
                "width": VIEWPORT_CSS_W,
                "height": VIEWPORT_CSS_H,
                "deviceScaleFactor": DEVICE_SCALE_FACTOR,
            },
        )
        return session
    except Exception:
        _log.debug("als cdp attach skipped", exc_info=True)
        return None


def _cdp_viewport_png(page: Any, *, session: Any | None = None) -> bytes | None:
    try:
        import base64

        sess = session
        if sess is None:
            ctx = getattr(page, "context", None)
            if ctx is None:
                return None
            sess = ctx.new_cdp_session(page)
        result = sess.send(
            "Page.captureScreenshot",
            {"format": "png", "fromSurface": True},
        )
        data = result.get("data") if isinstance(result, dict) else None
        if not data:
            return None
        return base64.b64decode(data)
    except Exception:
        _log.debug("als cdp screenshot skipped", exc_info=True)
        return None


def _raise_timeout_or_capture(exc: BaseException) -> None:
    name = type(exc).__name__
    text = str(exc).lower()
    if "timeout" in name.lower() or "timeout" in text:
        raise LongshotExportError(
            "E_ALS_TIMEOUT",
            "屏数较多导致超时，请重试或减少章节后导出",
        ) from exc
    raise LongshotExportError(
        "E_ALS_CAPTURE_FAILED",
        "截取横版画册失败，请重试",
    ) from exc
