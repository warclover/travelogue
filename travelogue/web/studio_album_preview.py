"""Wizard album preview: thumb sample + date-range peek (not import persist)."""

from __future__ import annotations

import time
from pathlib import Path

from travelogue.media.ingest import IngestError, scan_image_paths

ALBUM_PREVIEW_FAST_DEGRADE_THRESHOLD = 800
MAX_ALBUM_PREVIEW_THUMBS = 6


def count_album_photos(album_dir: Path, *, max_photos: int = 250) -> int:
    paths, _ = scan_image_paths(album_dir, max_photos=max_photos)
    return len(paths)


def _even_sample_indices(total: int, count: int) -> list[int]:
    if total <= 0:
        return []
    if total <= count:
        return list(range(total))
    if count <= 1:
        return [0]
    step = (total - 1) / (count - 1)
    return [min(total - 1, round(i * step)) for i in range(count)]


def _fast_candidate_paths(album_dir: Path) -> list[Path]:
    """Extension-only scan，不打开图片，仅用于预估候选数量与降级抽样。"""
    from travelogue.media.ingest import HEIC_SUFFIXES, IMAGE_SUFFIXES

    candidates: list[Path] = []
    for path in album_dir.rglob("*"):
        if not path.is_file():
            continue
        suf = path.suffix.lower()
        if suf in IMAGE_SUFFIXES or suf in HEIC_SUFFIXES:
            candidates.append(path)
    return candidates


def list_album_preview_candidates(album_dir: Path) -> list[Path]:
    """Shared candidate list for thumbs + date-range preview (one rglob)."""
    try:
        return _fast_candidate_paths(album_dir)
    except OSError:
        return []


def _render_thumb_data_url(path: Path, thumb_px: int) -> str | None:
    import base64
    from io import BytesIO

    from travelogue.media.image_ops import load_image_normalized

    try:
        loaded = load_image_normalized(path)
        img = loaded.image
        img.thumbnail((thumb_px, thumb_px))
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=78)
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        return f"data:image/jpeg;base64,{b64}"
    except Exception:
        return None


def _peek_photo_datetime(path: Path):
    """Lightweight taken-at for preview prefill (EXIF/filename/mtime; no RGB decode)."""
    from datetime import datetime

    from PIL import Image

    from travelogue.media.image_ops import resolve_photo_datetime

    try:
        with Image.open(path) as img:
            taken_at, _source = resolve_photo_datetime(path, img)
            return taken_at
    except Exception:
        try:
            return datetime.fromtimestamp(path.stat().st_mtime)
        except OSError:
            return None


def _mtime_sample_paths(candidates: list[Path]) -> list[Path]:
    """Pick earliest / latest / mid by mtime without a full sort copy when large."""
    if not candidates:
        return []
    if len(candidates) <= 64:
        try:
            by_mtime = sorted(candidates, key=lambda p: p.stat().st_mtime)
        except OSError:
            return candidates[:1]
        sample = [by_mtime[0]]
        if len(by_mtime) > 1:
            sample.append(by_mtime[-1])
        if len(by_mtime) > 4:
            mid = by_mtime[len(by_mtime) // 2]
            if mid not in sample:
                sample.append(mid)
        return sample

    earliest = latest = None
    earliest_t = latest_t = None
    mid = candidates[len(candidates) // 2]
    for path in candidates:
        try:
            t = path.stat().st_mtime
        except OSError:
            continue
        if earliest is None or t < earliest_t:
            earliest, earliest_t = path, t
        if latest is None or t > latest_t:
            latest, latest_t = path, t
    sample: list[Path] = []
    if earliest is not None:
        sample.append(earliest)
    if latest is not None and latest not in sample:
        sample.append(latest)
    if mid not in sample:
        sample.append(mid)
    return sample


def infer_album_preview_date_range(
    album_dir: Path,
    *,
    budget_s: float = 1.0,
    candidates: list[Path] | None = None,
) -> tuple[str | None, str | None]:
    """Best-effort ISO date range for Wizard 2b prefill (A1-07)."""
    from datetime import datetime

    started = time.monotonic()
    if candidates is None:
        try:
            candidates = _fast_candidate_paths(album_dir)
        except OSError:
            return None, None
    if not candidates:
        return None, None

    sample = _mtime_sample_paths(candidates)
    if not sample:
        return None, None

    taken: list[datetime] = []
    for path in sample:
        if time.monotonic() - started > budget_s:
            break
        peeked = _peek_photo_datetime(path)
        if peeked is not None:
            taken.append(peeked)

    if not taken:
        try:
            times = []
            for path in sample[:2]:
                times.append(datetime.fromtimestamp(path.stat().st_mtime))
            taken = times
        except OSError:
            return None, None

    if not taken:
        return None, None
    start_d = min(taken).date().isoformat()
    end_d = max(taken).date().isoformat()
    return start_d, end_d


def sample_album_preview_thumbs(
    album_dir: Path,
    *,
    count: int = 4,
    thumb_px: int = 112,
    max_photos: int = 250,
    candidates: list[Path] | None = None,
) -> tuple[list[str], int, list[str]]:
    """Return JPEG data-URL thumbs evenly sampled from *album_dir*."""
    count = max(1, min(int(count or count), MAX_ALBUM_PREVIEW_THUMBS))

    if candidates is None:
        try:
            fast_candidates = _fast_candidate_paths(album_dir)
        except OSError:
            return [], 0, []
    else:
        fast_candidates = list(candidates)

    if not fast_candidates:
        return [], 0, []

    if len(fast_candidates) > ALBUM_PREVIEW_FAST_DEGRADE_THRESHOLD:
        fast_candidates.sort(key=lambda p: str(p).lower())
        photo_count = len(fast_candidates)
        thumbs: list[str] = []
        names: list[str] = []
        for idx in _even_sample_indices(photo_count, count):
            path = fast_candidates[idx]
            url = _render_thumb_data_url(path, thumb_px)
            if url:
                thumbs.append(url)
                names.append(path.name)
        return thumbs, photo_count, names

    try:
        paths, _stats = scan_image_paths(album_dir, max_photos=max_photos)
    except IngestError:
        return [], 0, []

    photo_count = len(paths)
    if not paths:
        return [], 0, []

    thumbs = []
    names = []
    for idx in _even_sample_indices(len(paths), count):
        path = paths[idx]
        url = _render_thumb_data_url(path, thumb_px)
        if url:
            thumbs.append(url)
            names.append(path.name)
    return thumbs, photo_count, names
