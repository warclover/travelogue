"""PFM · portfolio_pages Writer + 这一本 zip 编排（BE-PFM-13 / BE-PFM-23）.

Pages: Playwright screenshots of preview ``index.html`` (not index-longshot.html).
Pillow only letterboxes the capture to 16:9. Never CardGrouper / 3:4 collage.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any, Callable

from travelogue.config.edition import is_portfolio_trip
from travelogue.export.longshot import (
    DEFAULT_EXPORT_SCALE,
    EXPORT_OUTPUT_DIRNAME,
    LongshotCancelled,
    LongshotExportError,
    LongshotOutput,
    PortfolioBundleResult,
    ProgressFn,
    _BROWSER_POOL,
    _slug_title,
    _start_static_server,
    _trip_title,
    playwright_longshot_available,
    raise_if_longshot_cancelled,
)
from travelogue.export.platform_longshot import PlatformExportWriter
from travelogue.export.platform_profiles import (
    PORTFOLIO_PLATFORM_IDS,
    file_prefix_for_platform,
    get_profile,
    normalize_platform_id,
    output_canvas_size,
)
from travelogue.export.slide_postprocess import fit_aspect

_log = logging.getLogger(__name__)

INDEX_HTML = "index.html"
SCREEN_SELECTOR = '.layout-screen[data-block="layout-screen"]'
COVER_SELECTOR = '[data-block="cover-opening"]'
COVER_FALLBACK = '[data-block="cover-hero"]'
CLOSING_SELECTOR = '[data-block="cover-closing"]'

CaptureFn = Callable[["PortfolioPageTarget"], bytes]
PackagerFn = Callable[[Path], Path]


class PageCaptureSkip(Exception):
    """One page could not be captured; caller continues with the rest."""

    def __init__(self, key: str, reason: str) -> None:
        self.key = key
        self.reason = reason
        super().__init__(reason)


@dataclass(frozen=True)
class PortfolioPageTarget:
    key: str
    label: str
    selector: str
    fallback_selector: str = ""
    nth: int | None = None
    optional: bool = False


def is_portfolio_pages_platform(raw: object) -> bool:
    """True when the request explicitly asks for portfolio page PNGs."""
    if raw in (None, ""):
        return False
    return normalize_platform_id(raw) in PORTFOLIO_PLATFORM_IDS


def list_portfolio_page_targets(trip: dict[str, Any] | None) -> list[PortfolioPageTarget]:
    """Cover (if rendered) + ``screens[]`` in chapter order + closing (if rendered)."""
    data = trip if isinstance(trip, dict) else {}
    targets: list[PortfolioPageTarget] = [
        PortfolioPageTarget(
            key="cover",
            label="封面",
            selector=COVER_SELECTOR,
            fallback_selector=COVER_FALLBACK,
            optional=True,
        )
    ]
    n = 0
    for chapter in data.get("chapters") or []:
        if not isinstance(chapter, dict):
            continue
        for screen in chapter.get("screens") or []:
            if not isinstance(screen, dict):
                continue
            n += 1
            sid = str(screen.get("screenId") or f"screen-{n:02d}").strip() or f"screen-{n:02d}"
            targets.append(
                PortfolioPageTarget(
                    key=sid,
                    label=f"第 {n} 屏",
                    selector=f'{SCREEN_SELECTOR}[data-screen-index="{n}"]',
                    nth=n - 1,
                    optional=False,
                )
            )
    targets.append(
        PortfolioPageTarget(
            key="closing",
            label="封底",
            selector=CLOSING_SELECTOR,
            optional=True,
        )
    )
    return targets


def _load_trip(trip_dir: Path) -> dict[str, Any]:
    trip_json = Path(trip_dir) / "trip.json"
    if not trip_json.is_file():
        raise LongshotExportError("E_TRIP_NOT_FOUND", "缺少 trip.json")
    try:
        data = json.loads(trip_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LongshotExportError("E_TRIP_NOT_FOUND", "trip.json 无法读取") from exc
    return data if isinstance(data, dict) else {}


def _canvas_size() -> tuple[int, int]:
    profile = get_profile("portfolio_pages")
    size = output_canvas_size(profile)
    if size:
        return size
    return 1920, 1080


def _letterbox_page(data: bytes, *, fmt: str) -> bytes:
    width, height = _canvas_size()
    return fit_aspect(data, pad_mode="letterbox", width=width, height=height, fmt=fmt)


def _purge_prefix(directory: Path, prefix: str, ext: str) -> None:
    if not directory.is_dir():
        return
    for path in directory.glob(f"{prefix}-*.{ext}"):
        try:
            path.unlink()
        except OSError:
            _log.debug("purge previous portfolio page failed: %s", path, exc_info=True)
    for path in directory.glob(f"{prefix}-*.{ext}.part"):
        try:
            path.unlink()
        except OSError:
            _log.debug("purge previous portfolio part failed: %s", path, exc_info=True)


def _hint_pages(*, page_count: int, skipped: list[str]) -> str:
    extra = ""
    if skipped:
        shown = "、".join(skipped[:5])
        more = f" 等 {len(skipped)} 页" if len(skipped) > 5 else ""
        extra = f"（跳过 {len(skipped)} 页：{shown}{more}）"
    return f"作品集已导出 · 共 {page_count} 页{extra}" if page_count else f"页图未产出{extra}"


def export_portfolio_pages(
    trip_dir: Path,
    *,
    scale: int = DEFAULT_EXPORT_SCALE,
    fmt: str = "png",
    progress: ProgressFn | None = None,
    capture_fn: CaptureFn | None = None,
    cancel_check: Any = None,
    cancel_register: Any = None,
    timeout_ms: int = 180_000,
    host: str = "127.0.0.1",
    port: int = 0,
) -> PortfolioBundleResult:
    """Write compact ``{title}-portfolio-{nn}.png``. Skip failures; never rollback successes."""
    trip_dir = Path(trip_dir).resolve()
    trip = _load_trip(trip_dir)
    if not is_portfolio_trip(trip):
        raise LongshotExportError("E_PORTFOLIO_PAGES_JOURNAL", "页图仅用于作品集")

    targets = list_portfolio_page_targets(trip)
    screen_n = sum(1 for t in targets if not t.optional)
    if screen_n <= 0:
        raise LongshotExportError("E_PORTFOLIO_PAGES_EMPTY", "没有可导出的作品集页")

    profile = get_profile("portfolio_pages")
    max_pages = int(profile.max_pages or 48)
    title = _trip_title(trip_dir)
    prefix = file_prefix_for_platform(title, "portfolio_pages")
    out_ext = "jpg" if str(fmt).lower() in ("jpeg", "jpg") else "png"
    out_fmt = "jpeg" if out_ext == "jpg" else "png"
    out_dir = trip_dir / EXPORT_OUTPUT_DIRNAME
    # Purge only after the first success so a total failure keeps prior pages.

    capture = capture_fn
    closer: Callable[[], None] | None = None
    if capture is None:
        capture, closer = _open_playwright_capture(
            trip_dir,
            scale=scale,
            timeout_ms=timeout_ms,
            host=host,
            port=port,
            cancel_register=cancel_register,
        )

    skipped: list[str] = []
    outputs: list[LongshotOutput] = []
    nn = 0
    body_written = 0
    purged = False
    total = len(targets)
    try:
        for i, target in enumerate(targets, start=1):
            raise_if_longshot_cancelled(cancel_check)
            if progress:
                progress(i - 1, total, f"页图 {i}/{total}")
            if not target.optional and body_written >= max_pages:
                skipped.append(f"{target.label}（超过 {max_pages} 页上限）")
                continue
            try:
                raw = capture(target)
                if not raw or len(raw) < 32:
                    raise PageCaptureSkip(target.key, "截图为空")
                data = _letterbox_page(raw, fmt=out_fmt)
            except PageCaptureSkip as exc:
                skipped.append(f"{target.label}（{exc.reason}）")
                continue
            except LongshotCancelled:
                raise
            except Exception as exc:
                _log.info("portfolio page skip %s: %s", target.key, exc)
                skipped.append(f"{target.label}（{exc}）")
                continue
            if not purged:
                _purge_prefix(out_dir, prefix, out_ext)
                purged = True
            nn += 1
            if not target.optional:
                body_written += 1
            writer = PlatformExportWriter(out_dir, prefix, ext=out_ext)
            writer.write(nn, data)
            finals = writer.commit()
            outputs.append(LongshotOutput(path=finals[0], capture_method="portfolio_pages"))
        if progress:
            progress(total, total, "页图完成")
    finally:
        if closer is not None:
            closer()

    if not outputs:
        raise LongshotExportError(
            "E_PORTFOLIO_PAGES_FAILED",
            "页图全部失败" + (f"：{skipped[0]}" if skipped else ""),
        )

    hint = _hint_pages(page_count=len(outputs), skipped=skipped)
    return PortfolioBundleResult(
        outputs=outputs,
        capture_method="portfolio_pages",
        title=_slug_title(title),
        segmented=len(outputs) > 1,
        segment_reason="portfolio_pages",
        user_hint=hint,
        platform="portfolio_pages",
        profile_label=profile.label,
        target_page_count=screen_n,
        publish_guide=(profile.publish_guide or "").strip(),
        page_count=len(outputs),
        output_format=out_fmt,
        skipped_pages=skipped,
    )


def export_portfolio_bundle(
    trip_dir: Path,
    *,
    scale: int = DEFAULT_EXPORT_SCALE,
    fmt: str = "png",
    progress: ProgressFn | None = None,
    capture_fn: CaptureFn | None = None,
    packager_fn: PackagerFn | None = None,
    cancel_check: Any = None,
    cancel_register: Any = None,
    timeout_ms: int = 180_000,
    host: str = "127.0.0.1",
    port: int = 0,
    include_zip: bool = True,
    include_pages: bool = True,
) -> PortfolioBundleResult:
    """One action, two artifacts. Either piece may fail without blocking the other."""
    trip_dir = Path(trip_dir).resolve()
    trip = _load_trip(trip_dir)
    if not is_portfolio_trip(trip):
        raise LongshotExportError("E_PORTFOLIO_PAGES_JOURNAL", "页图仅用于作品集")
    if not include_zip and not include_pages:
        raise LongshotExportError("E_PORTFOLIO_BUNDLE_FAILED", "未选择要导出的作品集产物")

    zip_path: Path | None = None
    zip_error = ""
    try:
        if include_zip:
            if progress:
                progress(0, 2, "正在打包这一本…")
            packager = packager_fn or _default_packager
            zip_path = Path(packager(trip_dir))
            if not zip_path.is_file():
                zip_path = None
                zip_error = "分享包未写出"
    except Exception as exc:
        zip_path = None
        zip_error = getattr(exc, "message", None) or str(exc)
        _log.info("portfolio share zip failed: %s", exc)

    pages: PortfolioBundleResult | None = None
    pages_error = ""
    try:
        if include_pages:
            if progress:
                progress(1, 2, "正在导出页图…")
            pages = export_portfolio_pages(
                trip_dir,
                scale=scale,
                fmt=fmt,
                progress=progress,
                capture_fn=capture_fn,
                cancel_check=cancel_check,
                cancel_register=cancel_register,
                timeout_ms=timeout_ms,
                host=host,
                port=port,
            )
    except LongshotCancelled:
        raise
    except Exception as exc:
        pages_error = getattr(exc, "message", None) or str(exc)
        _log.info("portfolio pages failed: %s", exc)

    if pages is None and zip_path is None:
        raise LongshotExportError(
            "E_PORTFOLIO_BUNDLE_FAILED",
            "这一本与页图都未产出"
            + (f"（页图：{pages_error}；这一本：{zip_error}）" if (pages_error or zip_error) else ""),
        )

    if pages is None:
        profile = get_profile("portfolio_pages")
        title = _trip_title(trip_dir)
        pages = PortfolioBundleResult(
            outputs=[],
            capture_method="portfolio_pages",
            title=_slug_title(title),
            platform="portfolio_pages",
            profile_label=profile.label,
            publish_guide=(profile.publish_guide or "").strip(),
            page_count=0,
            output_format="png" if str(fmt).lower() not in ("jpeg", "jpg") else "jpeg",
            skipped_pages=[],
        )

    pages.share_zip = zip_path
    hint_bits: list[str] = []
    if pages.outputs:
        hint_bits.append(pages.user_hint or f"页图 {len(pages.outputs)} 张已保存")
    elif pages_error:
        hint_bits.append(f"页图未产出：{pages_error}")
    if zip_path is not None:
        hint_bits.append("这一本已打包，可打开翻阅")
    elif zip_error:
        hint_bits.append(f"这一本打包失败：{zip_error}")
    pages.user_hint = "；".join(hint_bits) or pages.user_hint
    return pages


def _default_packager(trip_dir: Path) -> Path:
    from travelogue.export.packager import export_trip

    return export_trip(trip_dir / "trip.json", confirm_privacy=True)


def _open_playwright_capture(
    trip_dir: Path,
    *,
    scale: int,
    timeout_ms: int,
    host: str,
    port: int,
    cancel_register: Any,
) -> tuple[CaptureFn, Callable[[], None]]:
    index = trip_dir / INDEX_HTML
    if not index.is_file():
        raise LongshotExportError(
            "E_EXPORT_NOT_RENDERED",
            "未找到 index.html，请先完成渲染",
        )
    if not playwright_longshot_available():
        raise LongshotExportError(
            "E_LNG_PLAYWRIGHT",
            "页图需要 Playwright，请安装后再导出",
        )

    scale = max(1, min(int(scale), 3))
    width, height = _canvas_size()
    server = _start_static_server(trip_dir, host, port or 0)
    bound_port = server.server_address[1]
    url = f"http://{host}:{bound_port}/{INDEX_HTML}"
    if _BROWSER_POOL.needs_cold_start():
        _log.debug("playwright cold start for portfolio pages")
    browser = _BROWSER_POOL.acquire()
    page = browser.new_page(
        viewport={"width": width, "height": height},
        device_scale_factor=scale,
    )
    if cancel_register is not None:

        def _abort_page() -> None:
            try:
                page.close()
            except Exception:
                _log.debug("portfolio pages cancel page.close skipped", exc_info=True)

        cancel_register(_abort_page)
    try:
        # load, not networkidle: folio preview keeps image/analytics traffic
        # alive and used to hang the whole export (and cancel) for minutes.
        page.goto(url, wait_until="load", timeout=timeout_ms)
        page.wait_for_selector("main", timeout=min(timeout_ms, 30_000))
        _prepare_folio_capture(page)
        _wait_images(page)
    except Exception:
        try:
            page.close()
        except Exception:
            pass
        _BROWSER_POOL.release()
        try:
            server.shutdown()
        except Exception:
            pass
        raise LongshotExportError("E_LNG_CAPTURE_FAILED", "无法打开作品集预览页") from None

    def capture(target: PortfolioPageTarget) -> bytes:
        return _screenshot_target(page, target)

    def close() -> None:
        try:
            page.close()
        except Exception:
            _log.debug("portfolio pages page.close failed", exc_info=True)
        _BROWSER_POOL.release()
        try:
            server.shutdown()
        except Exception:
            _log.debug("portfolio pages static server shutdown failed", exc_info=True)

    return capture, close


# Folio page shots must NOT reuse journal longshot-capturing: that class
# pinches html/body/main to 428px and unwraps cover-hero to intrinsic height.
# Result: portrait letterboxed cover, upscaled milky inner pages, closing
# panorama jammed into a narrow box. Use a folio-only class instead.
_HIDE_CAPTURE_CHROME_JS = """() => {
  document.body.classList.add('folio-page-capturing');
  document.documentElement.classList.remove('longshot-capturing-root');
  document.body.classList.remove('longshot-capturing');
  document.documentElement.setAttribute('data-breath', 'off');
  document.querySelectorAll('.breath-reveal').forEach((el) => {
    el.classList.add('is-visible');
    el.style.setProperty('opacity', '1', 'important');
    el.style.setProperty('transform', 'none', 'important');
  });
  if (!document.getElementById('folio-page-capturing-style')) {
    const s = document.createElement('style');
    s.id = 'folio-page-capturing-style';
    s.textContent = [
      'body.folio-page-capturing .screenplay-toolbar,',
      'body.folio-page-capturing .screenplay-gate{display:none!important}',
      'body.folio-page-capturing .breath-reveal,',
      'body.folio-page-capturing .cover-breath-reveal,',
      'body.folio-page-capturing .closing-breath-reveal{',
      'opacity:1!important;transform:none!important}',
      'body.folio-page-capturing .cover-opening,',
      'body.folio-page-capturing .cover-closing{',
      'width:100%;max-width:none;min-height:0;height:auto;',
      'aspect-ratio:16/9;overflow:hidden}',
      'body.folio-page-capturing .cover-hero,',
      'body.folio-page-capturing .closing-hero{',
      'position:absolute;inset:0;width:100%;height:100%;',
      'max-width:none;max-height:none;aspect-ratio:auto}',
      'body.folio-page-capturing .cover-hero__media,',
      'body.folio-page-capturing .closing-hero__media,',
      'body.folio-page-capturing .cover-hero__img,',
      'body.folio-page-capturing .closing-hero__img{',
      'position:absolute;inset:0;width:100%;height:100%;object-fit:cover}',
    ].join('');
    document.head.appendChild(s);
  }
  for (const sel of ['.screenplay-toolbar', '.screenplay-gate']) {
    document.querySelectorAll(sel).forEach((el) => {
      el.setAttribute('hidden', '');
      el.style.setProperty('display', 'none', 'important');
    });
  }
  for (const img of document.images || []) {
    try { img.loading = 'eager'; } catch (e) {}
  }
}"""

_WAIT_NODE_IMAGES_JS = """async (el, ms) => {
  const imgs = Array.from((el && el.querySelectorAll) ? el.querySelectorAll('img') : []);
  const deadline = Date.now() + Math.max(0, Number(ms) || 0);
  const waitOne = async (img) => {
    try { img.loading = 'eager'; } catch (e) {}
    if (img.decode) {
      try { await img.decode(); } catch (e) {}
    }
    if (img.complete && img.naturalWidth > 0) return;
    await new Promise((resolve) => {
      const done = () => resolve();
      img.addEventListener('load', done, { once: true });
      img.addEventListener('error', done, { once: true });
      setTimeout(done, Math.max(0, deadline - Date.now()));
    });
  };
  await Promise.race([
    Promise.all(imgs.map(waitOne)),
    new Promise((resolve) => setTimeout(resolve, Math.max(0, Number(ms) || 0))),
  ]);
  return imgs.filter((img) => !img.complete || img.naturalWidth === 0).length;
}"""


def _prepare_folio_capture(page: Any) -> None:
    """Hide reader FABs and force eager decode before the first page shot."""
    try:
        page.evaluate(_HIDE_CAPTURE_CHROME_JS)
    except Exception:
        _log.debug("portfolio pages hide chrome skipped", exc_info=True)


def _wait_images(page: Any, timeout_ms: int = 8000) -> None:
    try:
        page.evaluate(
            """(ms) => Promise.race([
              Promise.all(
                Array.from(document.images || []).map((img) => {
                  try { img.loading = 'eager'; } catch (e) {}
                  if (img.decode) return img.decode().catch(() => null);
                  if (img.complete) return null;
                  return new Promise((resolve) => {
                    img.addEventListener('load', resolve, { once: true });
                    img.addEventListener('error', resolve, { once: true });
                  });
                })
              ),
              new Promise((resolve) => setTimeout(resolve, ms))
            ])""",
            max(0, int(timeout_ms)),
        )
    except Exception:
        _log.debug("portfolio pages wait images skipped", exc_info=True)


def _wait_locator_images(node: Any, timeout_ms: int = 8000) -> None:
    try:
        node.evaluate(_WAIT_NODE_IMAGES_JS, max(0, int(timeout_ms)))
    except Exception:
        _log.debug("portfolio pages wait node images skipped", exc_info=True)


def capture_is_blank(data: bytes) -> bool:
    """True when a page shot is a near-uniform light board (lazy decode miss)."""
    if not data or len(data) < 32:
        return True
    try:
        from PIL import Image

        im = Image.open(BytesIO(data)).convert("L").resize((80, 45))
    except Exception:
        return False
    hist = im.histogram()
    total = sum(hist)
    if total <= 0:
        return True
    mean = sum(i * count for i, count in enumerate(hist)) / total
    var = sum(count * (i - mean) ** 2 for i, count in enumerate(hist)) / total
    return mean >= 232 and var < 320


def _screenshot_target(page: Any, target: PortfolioPageTarget) -> bytes:
    loc = page.locator(target.selector)
    if loc.count() == 0 and target.fallback_selector:
        loc = page.locator(target.fallback_selector)
    if loc.count() == 0 and target.nth is not None:
        base = page.locator(SCREEN_SELECTOR)
        if target.nth < base.count():
            loc = base.nth(target.nth)
        else:
            loc = page.locator(target.selector)
    if loc.count() == 0:
        raise PageCaptureSkip(target.key, "预览里没有这一页")
    node = loc.first
    try:
        node.scroll_into_view_if_needed()
    except Exception:
        _log.debug("scroll into view skipped for %s", target.key, exc_info=True)
    _wait_locator_images(node)
    data = node.screenshot(type="png")
    if capture_is_blank(data):
        _wait_locator_images(node, timeout_ms=4000)
        try:
            page.wait_for_timeout(400)
        except Exception:
            _log.debug("portfolio pages blank retry pause skipped", exc_info=True)
        data = node.screenshot(type="png")
    if not data or len(data) < 32:
        raise PageCaptureSkip(target.key, "截图为空")
    if capture_is_blank(data):
        raise PageCaptureSkip(target.key, "页图未渲染")
    return data
