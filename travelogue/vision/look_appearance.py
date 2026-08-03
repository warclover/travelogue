"""SSG M2 · upper-body appearance vectors (CLIP on torso crop · D-SSG-27).

Does NOT use ``face_crop_embedding`` (64×64 flatten) as appearance.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageOps

from travelogue.media.face_embed import cosine_similarity, l2_normalize
from travelogue.media.subject_detect import detect_faces_in_image
from travelogue.vision.cache import CACHE_DIR_NAME

_log = logging.getLogger(__name__)

LOOK_CACHE_FILE = "look_appearance.npz"
LOOK_CACHE_ABI = "look_clip_v1"


def face_area_ratio(box: tuple[int, int, int, int], img_w: int, img_h: int) -> float:
    _x, _y, w, h = box
    if img_w <= 0 or img_h <= 0:
        return 0.0
    return float(w * h) / float(img_w * img_h)


def upper_body_crop_box(
    box: tuple[int, int, int, int],
    *,
    img_w: int,
    img_h: int,
    side_expand: float = 0.85,
    down_expand: float = 2.6,
    up_expand: float = 0.35,
) -> tuple[int, int, int, int]:
    """Expand face box into an upper-body / outfit ROI."""
    x, y, w, h = box
    pad_x = int(w * side_expand)
    pad_up = int(h * up_expand)
    pad_down = int(h * down_expand)
    x0 = max(0, x - pad_x)
    y0 = max(0, y - pad_up)
    x1 = min(img_w, x + w + pad_x)
    y1 = min(img_h, y + h + pad_down)
    if x1 <= x0 or y1 <= y0:
        return (0, 0, img_w, img_h)
    return (x0, y0, x1 - x0, y1 - y0)


def select_main_face(
    faces: list[tuple[int, int, int, int]],
    *,
    img_w: int,
    img_h: int,
    min_area_ratio: float,
    max_faces: int,
) -> tuple[int, int, int, int] | None:
    """D-SSG-19 · skip when too many faces or largest face too small."""
    if not faces:
        return None
    if len(faces) >= max_faces:
        return None
    best = max(faces, key=lambda b: b[2] * b[3])
    if face_area_ratio(best, img_w, img_h) < min_area_ratio:
        return None
    return best


def resolve_asset_image_path(asset: dict, trip_dir: Path) -> Path | None:
    root = trip_dir.resolve()
    for key in ("sourceFile", "displayFile", "file"):
        rel = asset.get(key)
        if not rel:
            continue
        path = (root / str(rel).replace("\\", "/")).resolve()
        try:
            path.relative_to(root)
        except ValueError:
            continue
        if path.is_file():
            return path
    return None


def _cache_path(trip_dir: Path) -> Path:
    return trip_dir / CACHE_DIR_NAME / LOOK_CACHE_FILE


def load_look_appearance_cache(trip_dir: Path) -> dict[str, np.ndarray]:
    path = _cache_path(trip_dir)
    if not path.is_file():
        return {}
    try:
        data = np.load(path, allow_pickle=False)
        if str(data.get("abi", "")) != LOOK_CACHE_ABI:
            return {}
        ids = [str(x) for x in data["ids"].tolist()]
        vecs = data["vectors"]
        out: dict[str, np.ndarray] = {}
        for i, aid in enumerate(ids):
            out[aid] = l2_normalize(np.asarray(vecs[i], dtype=np.float64))
        return out
    except Exception:
        _log.warning("look appearance cache load failed · %s", path)
        return {}


def save_look_appearance_cache(trip_dir: Path, vectors: dict[str, np.ndarray]) -> None:
    if not vectors:
        return
    path = _cache_path(trip_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    ids = sorted(vectors.keys())
    stack = np.stack([l2_normalize(vectors[i]) for i in ids], axis=0)
    tmp = path.with_suffix(".tmp.npz")
    np.savez_compressed(tmp, abi=np.array(LOOK_CACHE_ABI), ids=np.array(ids), vectors=stack)
    tmp.replace(path)


def encode_pil_clip(img: Image.Image, encoder: Any) -> np.ndarray | None:
    """CLIP-encode a PIL RGB image via the shared ClipEncoder preprocess path."""
    try:
        import torch
    except ImportError:
        return None
    if getattr(encoder, "_model", None) is None or getattr(encoder, "_preprocess", None) is None:
        ensure = getattr(encoder, "_ensure_clip", None)
        if not callable(ensure) or not ensure():
            return None
    try:
        tensor = encoder._preprocess(img.convert("RGB")).unsqueeze(0).to(encoder._device)
        with encoder._infer_lock:
            with torch.no_grad():
                feat = encoder._model.encode_image(tensor)
                feat = feat / feat.norm(dim=-1, keepdim=True)
        return l2_normalize(feat.cpu().numpy()[0])
    except Exception:
        _log.debug("CLIP torso encode failed", exc_info=True)
        return None


def encode_pil_clip_batch(
    imgs: list[Image.Image], encoder: Any
) -> list[np.ndarray | None]:
    """ALG-V3 A6 · batch CLIP-encode PIL crops (same preprocess / L2 as single).

    On OOM or batch failure, halves recursively then falls back to
    ``encode_pil_clip`` per image so callers keep order-stable results.
    """
    if not imgs:
        return []
    try:
        import torch
    except ImportError:
        return [None] * len(imgs)
    if getattr(encoder, "_model", None) is None or getattr(encoder, "_preprocess", None) is None:
        ensure = getattr(encoder, "_ensure_clip", None)
        if not callable(ensure) or not ensure():
            return [None] * len(imgs)

    def _single_fallback(items: list[Image.Image]) -> list[np.ndarray | None]:
        return [encode_pil_clip(im, encoder) for im in items]

    if len(imgs) == 1:
        return _single_fallback(imgs)

    try:
        tensors = [encoder._preprocess(im.convert("RGB")) for im in imgs]
        with encoder._infer_lock:
            batch = torch.stack(tensors).to(encoder._device)
            with torch.no_grad():
                feats = encoder._model.encode_image(batch)
                feats = feats / feats.norm(dim=-1, keepdim=True)
        # One device→host copy for the whole batch (not N× full transfers).
        arr = feats.cpu().numpy()
        out: list[np.ndarray | None] = []
        for i in range(len(imgs)):
            out.append(l2_normalize(arr[i]))
        return out
    except RuntimeError as exc:
        if "out of memory" not in str(exc).lower() or len(imgs) <= 1:
            _log.debug("CLIP torso batch encode failed; falling back", exc_info=True)
            return _single_fallback(imgs)
        mid = len(imgs) // 2
        return encode_pil_clip_batch(imgs[:mid], encoder) + encode_pil_clip_batch(
            imgs[mid:], encoder
        )
    except Exception:
        _log.debug("CLIP torso batch encode failed; falling back", exc_info=True)
        return _single_fallback(imgs)


def appearance_distance(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine distance in [0, 2] for L2-normalized vectors."""
    return float(1.0 - cosine_similarity(a, b))


def compute_look_vectors_for_assets(
    assets: list[dict],
    *,
    trip_dir: Path,
    cfg: Any,
    encoder: Any | None = None,
    app_cfg: Any | None = None,
) -> tuple[dict[str, np.ndarray], dict[str, int | float]]:
    """Return appearance vectors for look-eligible assets + skip / encode stats.

    ALG-V3 A6: encodes ``need_encode`` in ``vision.batch_size`` chunks via
    ``encode_pil_clip_batch`` (order-stable). ``batch_size<=1`` keeps the
    historical single-image path. Session uses ``get_clip_encoder(app_cfg)``.
    """
    import time

    look_cfg = cfg.look
    stats: dict[str, int | float] = {
        "lookSkippedNoFace": 0,
        "lookSkippedMulti": 0,
        "lookEncoded": 0,
        "lookCacheHits": 0,
        "lookElapsedMs": 0,
        "lookBatchSize": 0,
        "lookBatches": 0,
        "lookFallbackSingle": 0,
    }
    cached = load_look_appearance_cache(trip_dir)
    out: dict[str, np.ndarray] = {}
    need_encode: list[tuple[str, Image.Image]] = []

    for asset in assets:
        aid = str(asset.get("id") or "")
        if not aid or asset.get("type") == "video":
            continue
        if aid in cached:
            out[aid] = cached[aid]
            stats["lookCacheHits"] = int(stats["lookCacheHits"]) + 1
            continue
        path = resolve_asset_image_path(asset, trip_dir)
        if path is None:
            stats["lookSkippedNoFace"] = int(stats["lookSkippedNoFace"]) + 1
            continue
        try:
            with Image.open(path) as raw:
                img = ImageOps.exif_transpose(raw.convert("RGB"))
        except OSError:
            stats["lookSkippedNoFace"] = int(stats["lookSkippedNoFace"]) + 1
            continue
        require_face = bool(getattr(look_cfg, "require_face_or_subject", True))
        if require_face:
            faces = detect_faces_in_image(img)
            if len(faces) >= int(look_cfg.max_faces_before_skip):
                stats["lookSkippedMulti"] = int(stats["lookSkippedMulti"]) + 1
                continue
            main = select_main_face(
                faces,
                img_w=img.width,
                img_h=img.height,
                min_area_ratio=float(look_cfg.min_max_face_area_ratio),
                max_faces=int(look_cfg.max_faces_before_skip),
            )
            if main is None:
                stats["lookSkippedNoFace"] = int(stats["lookSkippedNoFace"]) + 1
                continue
            bx, by, bw, bh = upper_body_crop_box(
                main, img_w=img.width, img_h=img.height
            )
            crop = img.crop((bx, by, bx + bw, by + bh))
        else:
            # Intentional full-frame fallback when face gate is off (config).
            crop = img
        need_encode.append((aid, crop))

    if need_encode:
        if encoder is None:
            try:
                from travelogue.vision.clip_encoder import (
                    clip_torch_available,
                    get_clip_encoder,
                )

                if not clip_torch_available():
                    return out, stats
                encoder = get_clip_encoder(app_cfg)
            except Exception:
                return out, stats
        batch_size = int(getattr(encoder, "batch_size", 0) or 0)
        if batch_size <= 0:
            try:
                from travelogue.config import get_config

                vis = getattr(app_cfg or get_config(), "vision", None)
                batch_size = int(getattr(vis, "batch_size", 16) or 16)
            except Exception:
                batch_size = 16
        stats["lookBatchSize"] = max(1, batch_size)
        t0 = time.monotonic()
        if batch_size <= 1:
            stats["lookFallbackSingle"] = len(need_encode)
            for aid, crop in need_encode:
                stats["lookBatches"] = int(stats["lookBatches"]) + 1
                vec = encode_pil_clip(crop, encoder)
                if vec is None:
                    stats["lookSkippedNoFace"] = int(stats["lookSkippedNoFace"]) + 1
                    continue
                out[aid] = vec
                stats["lookEncoded"] = int(stats["lookEncoded"]) + 1
        else:
            for start in range(0, len(need_encode), batch_size):
                chunk = need_encode[start : start + batch_size]
                stats["lookBatches"] = int(stats["lookBatches"]) + 1
                vecs = encode_pil_clip_batch([crop for _aid, crop in chunk], encoder)
                if len(vecs) != len(chunk):
                    # Defensive: treat as total miss and single-fallback the chunk.
                    stats["lookFallbackSingle"] = int(stats["lookFallbackSingle"]) + len(
                        chunk
                    )
                    vecs = [encode_pil_clip(crop, encoder) for _aid, crop in chunk]
                for (aid, _crop), vec in zip(chunk, vecs, strict=True):
                    if vec is None:
                        stats["lookSkippedNoFace"] = int(stats["lookSkippedNoFace"]) + 1
                        continue
                    out[aid] = vec
                    stats["lookEncoded"] = int(stats["lookEncoded"]) + 1
        stats["lookElapsedMs"] = int(round((time.monotonic() - t0) * 1000))
        # Merge into cache
        merged = dict(cached)
        merged.update(out)
        try:
            save_look_appearance_cache(trip_dir, merged)
        except Exception:
            _log.warning("look appearance cache save failed", exc_info=True)

    return out, stats
