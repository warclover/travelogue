"""Server-side longshot PNG export via Playwright (Phase 2 M9)."""

from __future__ import annotations

import base64
import json
import re
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from travelogue.render.engine import LONGSHOT_INDEX_NAME

CAPTURE_WIDTH = 428
DEFAULT_EXPORT_SCALE = 2
MAX_SINGLE_HEIGHT_PX = 5000
MAX_CHAPTER_CARDS = 60
MAX_WECHAT_BYTES = 20 * 1024 * 1024

ProgressFn = Any  # Callable[[int, int, str], None] — avoid circular import noise


class LongshotExportError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


@dataclass
class LongshotOutput:
    path: Path
    capture_method: str = "p0"


@dataclass
class LongshotExportResult:
    outputs: list[LongshotOutput] = field(default_factory=list)
    capture_method: str = "p0"
    title: str = "travelogue"
    segmented: bool = False
    segment_reason: str = ""
    user_hint: str = ""

    @property
    def paths(self) -> list[Path]:
        return [item.path for item in self.outputs]


class _PlaywrightBrowserPool:
    IDLE_SECONDS = 60

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._playwright: Any = None
        self._browser: Any = None
        self._idle_timer: threading.Timer | None = None

    def acquire(self) -> Any:
        with self._lock:
            if self._idle_timer:
                self._idle_timer.cancel()
                self._idle_timer = None
            if self._browser is None:
                try:
                    from playwright.sync_api import sync_playwright
                except ImportError as exc:
                    raise LongshotExportError(
                        "E_LNG_PLAYWRIGHT",
                        "无法生成长图。请运行：pip install 'travelogue[playwright]' "
                        "&& playwright install chromium",
                    ) from exc
                self._playwright = sync_playwright().start()
                self._browser = self._playwright.chromium.launch(headless=True)
            return self._browser

    def _close(self) -> None:
        with self._lock:
            if self._browser:
                try:
                    self._browser.close()
                except Exception:
                    pass
                self._browser = None
            if self._playwright:
                try:
                    self._playwright.stop()
                except Exception:
                    pass
                self._playwright = None
            self._idle_timer = None

    def release(self) -> None:
        with self._lock:
            if self._idle_timer:
                self._idle_timer.cancel()

            def _idle_close() -> None:
                self._close()

            self._idle_timer = threading.Timer(self.IDLE_SECONDS, _idle_close)
            self._idle_timer.daemon = True
            self._idle_timer.start()


_BROWSER_POOL = _PlaywrightBrowserPool()


def warm_playwright_browser() -> bool:
    """P5-L4 · lazy-warm Chromium pool on Studio startup (best-effort)."""
    try:
        _BROWSER_POOL.acquire()
        _BROWSER_POOL.release()
        return True
    except LongshotExportError:
        return False


def _estimate_output_bytes(metrics: dict[str, Any], *, scale: int, fmt: str) -> int:
    """Rough byte budget for WeChat 20MB gate (P5-L2)."""
    scroll_h = max(int(metrics.get("scrollHeight") or 0), 844)
    width = CAPTURE_WIDTH * scale
    height = scroll_h * scale
    bpp = 1.1 if fmt == "jpeg" else 2.2
    return int(width * height * bpp)


def _segment_user_hint(total: int, reason: str) -> str:
    if total <= 1:
        return ""
    base = f"相册较长，已自动分成 {total} 张"
    if reason == "size":
        return base + "（单张 ≤20MB，便于微信发送）"
    if reason == "height":
        return base + "（单张过高，按章导出更稳）"
    if reason == "cards":
        return base + "（单章照片过多，按章导出更清晰）"
    return base + "，便于按序发微信"


def _segment_reason(metrics: dict[str, Any], *, scale: int, fmt: str) -> str:
    if _estimate_output_bytes(metrics, scale=scale, fmt=fmt) > MAX_WECHAT_BYTES:
        return "size"
    estimated_height = int(metrics.get("scrollHeight") or 0) * scale
    if estimated_height > MAX_SINGLE_HEIGHT_PX:
        return "height"
    per_chapter = metrics.get("perChapter") or []
    if any(int(n or 0) > MAX_CHAPTER_CARDS for n in per_chapter):
        return "cards"
    return ""


def _should_segment(metrics: dict[str, Any], scale: int, *, fmt: str = "png") -> bool:
    return bool(_segment_reason(metrics, scale=scale, fmt=fmt))


def _slug_title(title: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", title).strip()
    return cleaned or "travelogue"


def _start_static_server(directory: Path, host: str, port: int) -> ThreadingHTTPServer:
    handler = lambda *args, **kwargs: SimpleHTTPRequestHandler(  # noqa: E731
        *args, directory=str(directory), **kwargs
    )
    server = ThreadingHTTPServer((host, port or 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def _trip_title(trip_dir: Path) -> str:
    trip_json = trip_dir / "trip.json"
    if not trip_json.is_file():
        return "travelogue"
    meta = (json.loads(trip_json.read_text(encoding="utf-8")).get("meta") or {})
    return str(meta.get("title") or "travelogue").strip() or "travelogue"


def _resolve_longshot_url(
    trip_dir: Path,
    *,
    base_url: str | None,
    host: str,
    port: int,
    trip_id: str | None = None,
) -> tuple[str, ThreadingHTTPServer | None]:
    if base_url:
        base = base_url.rstrip("/")
        slug = trip_id or trip_dir.name
        return f"{base}/{slug}/{LONGSHOT_INDEX_NAME}", None

    server = _start_static_server(trip_dir, host, port or 0)
    bound_port = server.server_address[1]
    return f"http://{host}:{bound_port}/{LONGSHOT_INDEX_NAME}", server


def _page_metrics(page) -> dict[str, Any]:
    return page.evaluate(
        """() => {
          const main = document.querySelector('main');
          if (!main) return { scrollHeight: 0, chapterCount: 0, perChapter: [] };
          const chapters = Array.from(main.querySelectorAll('section.chapter'));
          const perChapter = chapters.map(
            (ch) => ch.querySelectorAll('[data-block="media-card"]').length
          );
          return {
            scrollHeight: Math.max(main.scrollHeight, main.offsetHeight, 1),
            chapterCount: chapters.length,
            perChapter,
          };
        }"""
    )


_CAPTURE_P0_JS = """
async (opts) => {
  const out = await window.TravelogueLongshot.captureMainToBlob({
    scale: opts.scale,
    format: opts.format,
    quietProgress: true,
  });
  const ab = await out.blob.arrayBuffer();
  const u8 = new Uint8Array(ab);
  let binary = "";
  const chunk = 0x8000;
  for (let i = 0; i < u8.length; i += chunk) {
    binary += String.fromCharCode.apply(null, u8.subarray(i, i + chunk));
  }
  return {
    base64: btoa(binary),
    title: out.title,
    outputWidth: out.outputWidth,
    method: "p0",
  };
}
"""

_CHAPTER_CAPTURE_P0_JS = """
async (opts) => {
  const main = document.querySelector("main");
  const chapters = Array.from(main.querySelectorAll("section.chapter"));
  const cover = main.querySelector(".cover-hero");
  const pageEl = main.querySelector(".page");
  const hook = pageEl && pageEl.querySelector(".hook-line");
  const epilogue = pageEl && pageEl.querySelector(".epilogue");
  const tripMeta = pageEl && pageEl.querySelector(".trip-meta");
  function stash(el, show) {
    if (!el) return;
    el.hidden = !show;
    el.style.display = show ? "" : "none";
  }
  chapters.forEach((ch, i) => stash(ch, i === opts.chapterIndex));
  stash(cover, opts.chapterIndex === 0);
  stash(hook, opts.chapterIndex === 0);
  stash(tripMeta, opts.chapterIndex === 0);
  stash(epilogue, false);
  const out = await window.TravelogueLongshot.captureMainToBlob({
    scale: opts.scale,
    format: opts.format,
    quietProgress: true,
  });
  const ab = await out.blob.arrayBuffer();
  const u8 = new Uint8Array(ab);
  let binary = "";
  const chunk = 0x8000;
  for (let i = 0; i < u8.length; i += chunk) {
    binary += String.fromCharCode.apply(null, u8.subarray(i, i + chunk));
  }
  const ch = chapters[opts.chapterIndex];
  const titleEl =
    ch &&
    (ch.querySelector(".chapter-separator__title") ||
      ch.querySelector(".chapter-header h2"));
  const chTitle = (titleEl || {}).textContent || "";
  return {
    base64: btoa(binary),
    title: out.title,
    chapterTitle: chTitle,
    outputWidth: out.outputWidth,
    method: "p0",
  };
}
"""


def _capture_p0(page, *, scale: int, fmt: str, chapter_index: int | None = None) -> tuple[bytes, str]:
    if chapter_index is None:
        payload = page.evaluate(_CAPTURE_P0_JS, {"scale": scale, "format": fmt})
    else:
        payload = page.evaluate(
            _CHAPTER_CAPTURE_P0_JS,
            {"scale": scale, "format": fmt, "chapterIndex": chapter_index},
        )
    data = base64.b64decode(payload["base64"])
    if len(data) < 1024:
        raise LongshotExportError("E_LNG_CAPTURE_FAILED", "captureMainToBlob 输出过小")
    return data, str(payload.get("method") or "p0")


def _capture_p1(page, *, fmt: str) -> tuple[bytes, str]:
    ext = "jpeg" if fmt == "jpeg" else "png"
    data = page.locator("main").screenshot(type=ext)
    if len(data) < 1024:
        raise LongshotExportError("E_LNG_CAPTURE_FAILED", "screenshot 输出过小")
    return data, "p1"


def _capture_bytes(page, *, scale: int, fmt: str, chapter_index: int | None = None) -> tuple[bytes, str]:
    try:
        return _capture_p0(page, scale=scale, fmt=fmt, chapter_index=chapter_index)
    except Exception:
        return _capture_p1(page, fmt=fmt)


def _write_output(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    if not path.is_file() or path.stat().st_size == 0:
        raise LongshotExportError("E_LNG_CAPTURE_FAILED", f"写入失败: {path}")


def _watermark_font(size: int):
    from PIL import ImageFont

    for name in ("msyh.ttc", "segoeui.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(name, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def apply_chapter_watermark(
    data: bytes,
    *,
    page: int,
    total: int,
    fmt: str = "png",
) -> bytes:
    """F-LNG-13 · semi-transparent page label like ``2/5`` at bottom center."""
    if page < 1 or total < 2 or page > total:
        return data

    from io import BytesIO

    from PIL import Image, ImageDraw

    img = Image.open(BytesIO(data)).convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    label = f"{page}/{total}"
    font_size = max(14, img.width // 22)
    font = _watermark_font(font_size)
    bbox = draw.textbbox((0, 0), label, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    pad = max(10, img.width // 40)
    x = (img.width - text_w) // 2
    y = img.height - text_h - pad * 2
    pill = [x - pad, y - pad // 2, x + text_w + pad, y + text_h + pad // 2]
    draw.rounded_rectangle(pill, radius=pad, fill=(0, 0, 0, 120))
    draw.text((x, y), label, fill=(255, 255, 255, 210), font=font)
    composed = Image.alpha_composite(img, overlay)
    buf = BytesIO()
    if fmt == "jpeg":
        composed.convert("RGB").save(buf, format="JPEG", quality=92)
    else:
        composed.save(buf, format="PNG")
    return buf.getvalue()


def _maybe_watermark(
    data: bytes,
    *,
    page: int,
    total: int,
    fmt: str,
    watermark: bool,
) -> bytes:
    if not watermark or total < 2:
        return data
    return apply_chapter_watermark(data, page=page, total=total, fmt=fmt)


def export_trip_longshot(
    trip_dir: Path,
    *,
    scale: int = DEFAULT_EXPORT_SCALE,
    fmt: str = "png",
    chapter: int | None = None,
    output: Path | None = None,
    base_url: str | None = None,
    trip_id: str | None = None,
    host: str = "127.0.0.1",
    port: int = 0,
    timeout_ms: int = 180_000,
    watermark: bool = True,
    progress: ProgressFn | None = None,
) -> LongshotExportResult:
    trip_dir = trip_dir.resolve()
    longshot_html = trip_dir / LONGSHOT_INDEX_NAME
    if not longshot_html.is_file():
        raise LongshotExportError(
            "E_LNG_NO_LONGSHOT",
            "未找到 index-longshot.html，请先完成渲染",
        )

    scale = max(1, min(int(scale), 3))
    fmt = "jpeg" if str(fmt).lower() == "jpeg" else "png"
    ext = "jpg" if fmt == "jpeg" else "png"
    title = _slug_title(_trip_title(trip_dir))

    url, server = _resolve_longshot_url(
        trip_dir, base_url=base_url, host=host, port=port, trip_id=trip_id
    )
    browser = _BROWSER_POOL.acquire()
    capture_method = "p0"
    outputs: list[LongshotOutput] = []
    segment_reason = ""
    user_hint = ""

    def _report(cur: int, total: int, hint: str) -> None:
        if progress:
            progress(cur, total, hint)

    try:
        _report(0, 1, "正在打开浏览器…")
        page = browser.new_page(viewport={"width": CAPTURE_WIDTH, "height": 844})
        page.goto(url, wait_until="networkidle", timeout=timeout_ms)
        _report(0, 1, "正在加载长图页面…")
        page.wait_for_function(
            "() => window.TravelogueLongshot && document.documentElement.dataset.longshot === 'on'",
            timeout=30_000,
        )

        metrics = _page_metrics(page)
        chapter_count = max(int(metrics.get("chapterCount") or 0), 1)
        do_segment = chapter is None and _should_segment(metrics, scale, fmt=fmt)
        if do_segment:
            segment_reason = _segment_reason(metrics, scale=scale, fmt=fmt) or "height"

        if chapter is not None:
            if chapter < 1 or chapter > chapter_count:
                raise LongshotExportError("E_LNG_CAPTURE_FAILED", f"章节 {chapter} 不存在")
            _report(1, 1, f"第 {chapter}/{chapter_count} 段")
            data, method = _capture_bytes(
                page, scale=scale, fmt=fmt, chapter_index=chapter - 1
            )
            capture_method = method
            out_path = output or trip_dir / f"{title}-ch{chapter:02d}.{ext}"
            _write_output(out_path, data)
            outputs.append(LongshotOutput(path=out_path, capture_method=method))
        elif do_segment:
            for idx in range(chapter_count):
                _report(idx + 1, chapter_count, f"第 {idx + 1}/{chapter_count} 段")
                data, method = _capture_bytes(
                    page, scale=scale, fmt=fmt, chapter_index=idx
                )
                capture_method = method if idx == 0 else capture_method
                if len(data) > MAX_WECHAT_BYTES and fmt == "png":
                    data, method = _capture_bytes(
                        page, scale=scale, fmt="jpeg", chapter_index=idx
                    )
                    ext = "jpg"
                data = _maybe_watermark(
                    data,
                    page=idx + 1,
                    total=chapter_count,
                    fmt=fmt if ext != "jpg" else "jpeg",
                    watermark=watermark,
                )
                out_path = trip_dir / f"{title}-ch{idx + 1:02d}.{ext}"
                _write_output(out_path, data)
                outputs.append(LongshotOutput(path=out_path, capture_method=method))
            user_hint = _segment_user_hint(chapter_count, segment_reason)
        else:
            _report(1, 1, "正在合成长图…")
            data, method = _capture_bytes(page, scale=scale, fmt=fmt)
            capture_method = method
            if len(data) > MAX_WECHAT_BYTES:
                segment_reason = "size"
                for idx in range(chapter_count):
                    _report(idx + 1, chapter_count, f"第 {idx + 1}/{chapter_count} 段")
                    data, method = _capture_bytes(
                        page, scale=scale, fmt=fmt, chapter_index=idx
                    )
                    capture_method = method if idx == 0 else capture_method
                    if len(data) > MAX_WECHAT_BYTES and fmt == "png":
                        data, method = _capture_bytes(
                            page, scale=scale, fmt="jpeg", chapter_index=idx
                        )
                        ext = "jpg"
                    data = _maybe_watermark(
                        data,
                        page=idx + 1,
                        total=chapter_count,
                        fmt=fmt if ext != "jpg" else "jpeg",
                        watermark=watermark,
                    )
                    out_path = trip_dir / f"{title}-ch{idx + 1:02d}.{ext}"
                    _write_output(out_path, data)
                    outputs.append(LongshotOutput(path=out_path, capture_method=method))
                user_hint = _segment_user_hint(chapter_count, segment_reason)
            else:
                out_path = output or trip_dir / f"{title}-longshot.{ext}"
                _write_output(out_path, data)
                outputs.append(LongshotOutput(path=out_path, capture_method=method))

        page.close()
    finally:
        _BROWSER_POOL.release()
        if server is not None:
            server.shutdown()
            server.server_close()

    segmented = len(outputs) > 1
    if segmented and not user_hint:
        user_hint = _segment_user_hint(len(outputs), segment_reason or "height")

    return LongshotExportResult(
        outputs=outputs,
        capture_method=capture_method,
        title=title,
        segmented=segmented,
        segment_reason=segment_reason,
        user_hint=user_hint,
    )


def reveal_path_in_folder(path: Path, *, allowed_root: Path) -> None:
    target = path.resolve()
    root = allowed_root.resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise LongshotExportError("E_STUDIO_REVEAL_DENIED", "路径不在 trips 目录内") from exc
    if not target.exists():
        raise LongshotExportError("E_STUDIO_REVEAL_DENIED", "文件不存在")

    if sys.platform == "win32":
        subprocess.Popen(["explorer", "/select,", str(target)], close_fds=True)
        return
    if sys.platform == "darwin":
        subprocess.Popen(["open", "-R", str(target)], close_fds=True)
        return
    subprocess.Popen(["xdg-open", str(target.parent)], close_fds=True)


def reset_browser_pool_for_tests() -> None:
    _BROWSER_POOL._close()
