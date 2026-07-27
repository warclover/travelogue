"""Optional CLIP / heuristic embeddings for scene clustering (Phase 3 M13 · P7 batch)."""

from __future__ import annotations

import json
import logging
import math
import os
import threading
import time
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from travelogue.errors import PlainCodeError
from travelogue.layout_contract.subject_tagging import refresh_semantic_tag_for_asset

_log = logging.getLogger(__name__)

SUBJECT_CLASSES = (
    "landscape",
    "architecture",
    "food",
    "indoor",
    "person",
    "street",
    "temple",
    "mixed",
)
DEFAULT_SUBJECT_PROMPTS = tuple(f"a photo of {label}" for label in SUBJECT_CLASSES)
SUBJECT_PROMPTS = DEFAULT_SUBJECT_PROMPTS

_encoder_lock = threading.Lock()
_encoder_singleton: ClipEncoder | None = None
_prefetch_pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="clip-prefetch")


class VisionMissingError(PlainCodeError):
    def __init__(self, message: str = "vision extra not installed") -> None:
        super().__init__(message, code="E_CLUSTER_VISION_MISSING")


def vision_stack_available() -> bool:
    try:
        import numpy  # noqa: F401
        import sklearn  # noqa: F401

        return True
    except ImportError:
        return False


def clip_torch_available() -> bool:
    try:
        import open_clip  # noqa: F401
        import torch  # noqa: F401

        return True
    except ImportError:
        return False


def clip_weights_likely_cached(
    *,
    model_name: str = "ViT-B-32",
    pretrained: str = "openai",
) -> bool:
    """Best-effort check whether CLIP weights are already on disk (M13-5a stage hint)."""
    if not clip_torch_available():
        return True

    cache_roots = _clip_cache_roots()

    try:
        import open_clip  # type: ignore

        download = getattr(open_clip, "download_pretrained_from_hf", None) or getattr(
            open_clip, "get_pretrained_url", None
        )
        cfg = open_clip.get_pretrained_cfg(model_name, pretrained) if hasattr(
            open_clip, "get_pretrained_cfg"
        ) else None
        if cfg:
            filename = (
                cfg.get("hf_hub_filename")
                or cfg.get("hf_filename")
                or cfg.get("file")
                or ""
            )
            if filename:
                for root in cache_roots:
                    candidate = root / filename
                    if candidate.is_file() and candidate.stat().st_size > 500_000:
                        return True
        _ = download
    except Exception:  # pragma: no cover - open_clip API drift
        pass

    needles = {
        model_name.lower(),
        pretrained.lower(),
        "vit-b-32",
        "open_clip",
        f"{model_name.lower()}.{pretrained.lower()}",
    }
    for root in cache_roots:
        if not root.is_dir():
            continue
        try:
            for path in root.rglob("*"):
                name = path.name.lower()
                if not any(n in name for n in needles):
                    continue
                if path.is_file() and path.stat().st_size > 500_000:
                    return True
        except OSError:
            continue
    return False


def _clip_cache_roots() -> list[Path]:
    home = Path.home()
    roots = [
        home / ".cache" / "clip",
        home / ".cache" / "huggingface" / "hub",
        home / ".cache" / "huggingface",
        home / ".cache" / "open_clip",
    ]
    import os

    extra = os.environ.get("HF_HOME") or os.environ.get("HUGGINGFACE_HUB_CACHE")
    if extra:
        roots.append(Path(extra))
    return roots


HEURISTIC_V2_DIM = 18
HEURISTIC_MODEL_V2 = "heuristic-v2"


def _z_score(value: float, values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    var = sum((x - mean) ** 2 for x in values) / len(values)
    std = var**0.5
    if std < 1e-8:
        return 0.0
    return (value - mean) / std


def _p95(values: list[float]) -> float:
    if not values:
        return 1.0
    ordered = sorted(values)
    idx = min(len(ordered) - 1, int(0.95 * (len(ordered) - 1)))
    return max(float(ordered[idx]), 1.0)


def _trip_heuristic_stats(pool: list[dict]) -> dict[str, Any]:
    log_ratios: list[float] = []
    widths: list[float] = []
    heights: list[float] = []
    areas: list[float] = []
    for item in pool:
        w = float(item.get("width") or 1000)
        h = float(item.get("height") or 1000)
        widths.append(w)
        heights.append(h)
        areas.append((w * h) ** 0.5)
        log_ratios.append(math.log(max(w / max(h, 1.0), 0.01)))
    return {
        "log_ratios": log_ratios,
        "p95_width": _p95(widths),
        "p95_height": _p95(heights),
        "p95_area": _p95(areas),
    }


def _heuristic_vector(
    asset: dict,
    *,
    pool: list[dict] | None = None,
    sharp_pct: float | None = None,
    stats: dict[str, Any] | None = None,
) -> list[float]:
    """18-dim quality-aware heuristic embedding (Phase C-B · PRD §6.2)."""
    from colorsys import rgb_to_hls

    from travelogue.layout_contract.quality import asset_sharpness, normalized_sharpness

    search_pool = pool if pool else [asset]
    trip_stats = stats or _trip_heuristic_stats(search_pool)

    w = float(asset.get("width") or 1000)
    h = float(asset.get("height") or 1000)
    ratio = w / max(h, 1.0)
    log_ratio = math.log(max(ratio, 0.01))
    ratio_norm = _z_score(log_ratio, trip_stats["log_ratios"])

    if sharp_pct is not None:
        sharp = sharp_pct
    else:
        q = asset.get("quality") or {}
        if isinstance(q, dict) and q.get("sharpness") is not None:
            sharp = normalized_sharpness(asset, search_pool, bucket_by="mediaClass")
        else:
            sharp = float(asset.get("sharpness") or asset_sharpness(asset) or 0.0) / 4000.0
    luma = float(asset.get("meanLuma") or 0.5)

    tone_raw = str(asset.get("dominantTone") or "")
    hue, saturation = 0.0, 0.0
    if tone_raw.startswith("#") and len(tone_raw) >= 7:
        try:
            r = int(tone_raw[1:3], 16) / 255.0
            g = int(tone_raw[3:5], 16) / 255.0
            b = int(tone_raw[5:7], 16) / 255.0
            hue, _l, saturation = rgb_to_hls(r, g, b)
        except ValueError:
            pass

    subj = str(asset.get("subjectClass") or asset.get("subjectBucket") or "")
    subject_one_hot = [0.0] * len(SUBJECT_CLASSES)
    if subj in SUBJECT_CLASSES:
        subject_one_hot[SUBJECT_CLASSES.index(subj)] = 1.0

    face = 1.0 if asset.get("faceCount") else 0.0
    width_norm = w / trip_stats["p95_width"]
    height_norm = h / trip_stats["p95_height"]
    area_norm = (w * h) ** 0.5 / trip_stats["p95_area"]

    return [
        ratio_norm,
        sharp,
        luma,
        math.sin(2.0 * math.pi * hue),
        math.cos(2.0 * math.pi * hue),
        saturation,
        *subject_one_hot,
        face,
        width_norm,
        height_norm,
        area_norm,
    ]


@dataclass
class EmbedResult:
    asset_ids: list[str]
    vectors: Any  # np.ndarray
    source: str  # clip | heuristic
    model: str | None = None


@dataclass
class EmbedStats:
    """P7 telemetry for CLIP embedding runs."""

    elapsed_ms: float = 0.0
    batch_size: int = 0
    batches: int = 0
    prefetch_enabled: bool = False
    web_derivative_hits: int = 0
    web_derivative_fallbacks: int = 0
    web_derivative_gated: bool = False
    cache_hit_ratio: float | None = None
    fallback_single: int = 0
    oom_halves: int = 0
    auto_batch_tuned: bool = False
    recommended_batch_size: int | None = None

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "elapsedMs": round(self.elapsed_ms, 2),
            "batchSize": self.batch_size,
            "batches": self.batches,
            "prefetchEnabled": self.prefetch_enabled,
            "webDerivativeHits": self.web_derivative_hits,
            "webDerivativeFallbacks": self.web_derivative_fallbacks,
            "webDerivativeGated": self.web_derivative_gated,
            "fallbackSingle": self.fallback_single,
            "oomHalves": self.oom_halves,
            "autoBatchTuned": self.auto_batch_tuned,
        }
        if self.cache_hit_ratio is not None:
            out["cacheHitRatio"] = round(self.cache_hit_ratio, 4)
        if self.recommended_batch_size is not None:
            out["recommendedBatchSize"] = self.recommended_batch_size
        return out


def _labels_from_prompts(prompts: tuple[str, ...]) -> tuple[str, ...]:
    out: list[str] = []
    for prompt in prompts:
        text = prompt.strip()
        for prefix in ("a photo of ", "a picture of ", "an image of "):
            if text.lower().startswith(prefix):
                text = text[len(prefix) :]
                break
        text = text.strip(" .。,，:：").lower()
        out.append(text or prompt.strip())
    return tuple(out)


def get_clip_encoder(cfg: Any | None = None) -> ClipEncoder:
    """Process-level ClipEncoder singleton when session_singleton is enabled (P7-A2)."""
    from travelogue.config import VisionConfig, get_config

    vis = (cfg.vision if cfg is not None and hasattr(cfg, "vision") else None) or get_config().vision
    if not isinstance(vis, VisionConfig):
        vis = get_config().vision

    global _encoder_singleton
    if vis.session_singleton:
        with _encoder_lock:
            if _encoder_singleton is None:
                _encoder_singleton = ClipEncoder.from_vision_config(vis)
            return _encoder_singleton
    return ClipEncoder.from_vision_config(vis)


def preload_clip_encoder(cfg: Any | None = None) -> None:
    """Warm CLIP weights asynchronously (P7-C2); failures are silent."""
    def _warm() -> None:
        try:
            enc = get_clip_encoder(cfg)
            enc._ensure_clip()
        except Exception as exc:  # pragma: no cover - best effort
            _log.debug("CLIP preload skipped: %s", exc)

    threading.Thread(target=_warm, name="clip-preload", daemon=True).start()


def reset_clip_encoder_singleton() -> None:
    """Clear process singleton (tests)."""
    global _encoder_singleton
    with _encoder_lock:
        _encoder_singleton = None


def _clip_tune_path(trips_dir: Path) -> Path:
    return trips_dir / ".cache" / "clip-tune.json"


def load_persisted_batch_size(
    *,
    trip_dir: Path | None = None,
    trips_dir: Path | None = None,
) -> int | None:
    """P7-G1 · load recommended batch from trip manifest or trips-level tune file."""
    if trip_dir is not None:
        from travelogue.vision.cache import load_cache_manifest

        manifest = load_cache_manifest(trip_dir)
        if manifest and manifest.get("recommendedBatchSize") is not None:
            return int(manifest["recommendedBatchSize"])
    if trips_dir is not None:
        path = _clip_tune_path(trips_dir)
        if path.is_file():
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(raw, dict) and raw.get("recommendedBatchSize") is not None:
                    return int(raw["recommendedBatchSize"])
            except (OSError, json.JSONDecodeError, TypeError, ValueError):
                pass
    return None


def persist_recommended_batch_size(
    size: int,
    *,
    trips_dir: Path,
    trip_dir: Path | None = None,
) -> None:
    """P7-G1 · persist auto-tuned batch size for subsequent sessions."""
    _ = trip_dir
    payload = {
        "recommendedBatchSize": int(size),
        "updatedAt": datetime.now(UTC).replace(microsecond=0).isoformat(),
    }
    tune_path = _clip_tune_path(trips_dir)
    tune_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = tune_path.with_suffix(".json.tmp")
    tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp_path, tune_path)


class ClipEncoder:
    """Lazy CLIP encoder; falls back to heuristic vectors when torch/open_clip absent."""

    def __init__(
        self,
        *,
        model_name: str = "ViT-B-32",
        pretrained: str = "openai",
        subject_prompts: tuple[str, ...] | None = None,
        batch_size: int = 16,
        prefer_web_derivative: bool = True,
        prefetch: bool = True,
        dynamic_backoff: bool = True,
        batch_auto_tune: bool = False,
        batch_auto_tune_samples: int = 8,
        web_derivative_cosine_max: float = 0.02,
    ) -> None:
        self.model_name = model_name
        self.pretrained = pretrained
        if subject_prompts:
            self._subject_prompts = tuple(subject_prompts)
            self._subject_labels = _labels_from_prompts(self._subject_prompts)
        else:
            self._subject_prompts = DEFAULT_SUBJECT_PROMPTS
            self._subject_labels = SUBJECT_CLASSES
        self._model = None
        self._preprocess = None
        self._device = None
        self._text_features = None
        self.batch_size = max(0, int(batch_size))
        self.prefer_web_derivative = prefer_web_derivative
        self.prefetch = prefetch
        self.dynamic_backoff = dynamic_backoff
        self.batch_auto_tune = batch_auto_tune
        self.batch_auto_tune_samples = max(1, int(batch_auto_tune_samples))
        self.web_derivative_cosine_max = float(web_derivative_cosine_max)
        self._tuned_batch_size: int | None = None
        self._oom_cap: int | None = None
        self._prefetch_disabled = False
        self._web_derivative_disabled = False
        self.last_embed_stats: EmbedStats | None = None
        self.decision_log: list[str] = []
        self._infer_lock = threading.RLock()

    @classmethod
    def from_vision_config(cls, vis: Any) -> ClipEncoder:
        return cls(
            model_name=str(vis.model).replace("/", "-"),
            subject_prompts=vis.subject_prompts or None,
            batch_size=int(getattr(vis, "batch_size", 16)),
            prefer_web_derivative=bool(getattr(vis, "prefer_web_derivative", True)),
            prefetch=bool(getattr(vis, "prefetch", True)),
            dynamic_backoff=bool(getattr(vis, "dynamic_backoff", True)),
            batch_auto_tune=bool(getattr(vis, "batch_auto_tune", False)),
            batch_auto_tune_samples=int(getattr(vis, "batch_auto_tune_samples", 8)),
            web_derivative_cosine_max=float(getattr(vis, "web_derivative_cosine_max", 0.02)),
        )

    def _effective_prefer_web(self) -> bool:
        return bool(self.prefer_web_derivative and not self._web_derivative_disabled)

    def _load_persisted_batch_if_needed(self, trip_dir: Path) -> None:
        if self._tuned_batch_size is not None:
            return
        persisted = load_persisted_batch_size(
            trip_dir=trip_dir,
            trips_dir=trip_dir.parent,
        )
        if persisted is not None and persisted > 0:
            self._tuned_batch_size = persisted
            self.decision_log.append(f"loaded persisted batch={persisted}")

    def _encode_path_vector(self, path: Path) -> list[float]:
        import torch

        tensor = self._load_image_tensor(path).unsqueeze(0).to(self._device)
        with torch.no_grad():
            feat = self._model.encode_image(tensor)
            feat = feat / feat.norm(dim=-1, keepdim=True)
        return feat.cpu().numpy()[0].tolist()

    @staticmethod
    def _cosine_distance(a: list[float], b: list[float]) -> float:
        import numpy as np

        va = np.array(a, dtype=np.float32)
        vb = np.array(b, dtype=np.float32)
        denom = float(np.linalg.norm(va) * np.linalg.norm(vb))
        if denom < 1e-8:
            return 0.0
        return float(1.0 - np.dot(va, vb) / denom)

    def _maybe_gate_web_derivative(self, photos: list[dict], trip_dir: Path) -> None:
        """P7-A4 · disable web derivative when drift exceeds cosine threshold."""
        if not self._effective_prefer_web() or self.web_derivative_cosine_max <= 0:
            return
        sample = photos[: min(len(photos), 3)]
        distances: list[float] = []
        for asset in sample:
            web_path, used_web = _resolve_asset_path(
                asset, trip_dir, prefer_web_derivative=True
            )
            orig_path, _ = _resolve_asset_path(
                asset, trip_dir, prefer_web_derivative=False
            )
            if not used_web or web_path is None or orig_path is None:
                continue
            if web_path.resolve() == orig_path.resolve():
                continue
            try:
                web_vec = self._encode_path_vector(web_path)
                orig_vec = self._encode_path_vector(orig_path)
                distances.append(self._cosine_distance(web_vec, orig_vec))
            except Exception as exc:
                _log.debug("web derivative gate sample failed: %s", exc)
        if not distances:
            return
        mean_dist = sum(distances) / len(distances)
        if mean_dist > self.web_derivative_cosine_max:
            self._web_derivative_disabled = True
            self.decision_log.append(
                f"web derivative gated off (mean cosine drift {mean_dist:.4f} > {self.web_derivative_cosine_max})"
            )
            _log.info(
                "CLIP web derivative disabled: mean drift %.4f > %.4f",
                mean_dist,
                self.web_derivative_cosine_max,
            )

    def _ensure_subject_text_features(self) -> None:
        if self._text_features is not None:
            return
        import open_clip
        import torch

        tokens = open_clip.tokenize(list(self._subject_prompts)).to(self._device)
        with torch.no_grad():
            feats = self._model.encode_text(tokens)
            feats = feats / feats.norm(dim=-1, keepdim=True)
        self._text_features = feats

    def _subject_class_for(self, image_feat: Any) -> tuple[str, float] | None:
        if self._text_features is None:
            return None
        sim = (image_feat @ self._text_features.T).squeeze(0)
        idx = int(sim.argmax().item())
        if idx >= len(self._subject_labels):
            return None
        return self._subject_labels[idx], round(float(sim[idx].cpu()), 4)

    def apply_subject_labels_from_vectors(
        self,
        assets: list[dict],
        *,
        asset_ids: list[str],
        vectors: Any,
        only_missing: bool = True,
    ) -> int:
        """Write subjectClass from cached CLIP vectors (reuse/prune hydrate path).

        Parallel embed persists vectors with ``apply_subject_class=False``; clustering
        may then hit cache reuse and never call ``embed_assets``. This backfills labels
        without re-encoding images. Returns how many assets were labeled.
        """
        if not asset_ids:
            return 0
        if not self._ensure_clip():
            return 0
        import numpy as np
        import torch

        id_to_asset = {str(a.get("id")): a for a in assets if a.get("id")}
        idxs: list[int] = []
        targets: list[dict] = []
        for i, aid in enumerate(asset_ids):
            asset = id_to_asset.get(str(aid))
            if asset is None or asset.get("type", "image") == "video":
                continue
            if only_missing and asset.get("subjectClass"):
                continue
            idxs.append(i)
            targets.append(asset)
        if not idxs or self._text_features is None:
            return 0

        mat = np.asarray(vectors, dtype=np.float32)[idxs]
        if mat.ndim != 2 or mat.shape[0] == 0:
            return 0
        norms = np.linalg.norm(mat, axis=1, keepdims=True)
        mat = mat / np.clip(norms, 1e-8, None)
        feats = torch.from_numpy(mat).to(self._device)
        sim = feats @ self._text_features.T
        best = sim.argmax(dim=-1)
        conf = sim.max(dim=-1).values
        labeled = 0
        for asset, idx, score in zip(targets, best.tolist(), conf.tolist(), strict=True):
            if idx >= len(self._subject_labels):
                continue
            asset["subjectClass"] = self._subject_labels[int(idx)]
            asset["subjectConfidence"] = round(float(score), 4)
            refresh_semantic_tag_for_asset(asset)
            labeled += 1
        return labeled

    def _ensure_clip(self) -> bool:
        if self._model is not None:
            return True
        if not clip_torch_available():
            return False
        import open_clip
        import torch

        self._device = "cuda" if torch.cuda.is_available() else "cpu"
        model, _, preprocess = open_clip.create_model_and_transforms(
            self.model_name,
            pretrained=self.pretrained,
            quick_gelu=(self.pretrained == "openai"),
        )
        model.eval()
        model.to(self._device)
        self._model = model
        self._preprocess = preprocess
        self._ensure_subject_text_features()
        return True

    def embed_assets(
        self,
        assets: list[dict],
        *,
        trip_dir: Path | None = None,
        deterministic: bool = True,
        apply_subject_class: bool = True,
    ) -> EmbedResult:
        import numpy as np

        photos = [a for a in assets if a.get("type", "image") != "video" and a.get("id")]
        if not photos:
            return EmbedResult([], np.zeros((0, HEURISTIC_V2_DIM), dtype=np.float32), "heuristic")

        if self._ensure_clip() and trip_dir is not None:
            try:
                return self._embed_clip(
                    photos,
                    trip_dir=trip_dir,
                    deterministic=deterministic,
                    apply_subject_class=apply_subject_class,
                )
            except Exception as exc:
                _log.warning("CLIP embed failed, heuristic fallback: %s", exc)

        ids = [a["id"] for a in photos]
        from travelogue.layout_contract.quality import normalized_sharpness

        sharp_map = {
            a["id"]: normalized_sharpness(a, photos, bucket_by="mediaClass") for a in photos
        }
        trip_stats = _trip_heuristic_stats(photos)
        mat = np.array(
            [
                _heuristic_vector(
                    a,
                    pool=photos,
                    sharp_pct=sharp_map.get(a["id"], 0.5),
                    stats=trip_stats,
                )
                for a in photos
            ],
            dtype=np.float32,
        )
        norms = np.linalg.norm(mat, axis=1, keepdims=True)
        norms = np.where(norms < 1e-8, 1.0, norms)
        mat = mat / norms
        return EmbedResult(ids, mat, "heuristic", model=HEURISTIC_MODEL_V2)

    def _effective_batch_size(self, photos: list[dict], trip_dir: Path) -> int:
        if self.batch_size == 0:
            base = 1
        elif self._tuned_batch_size is not None:
            base = self._tuned_batch_size
        elif not self.batch_auto_tune:
            base = self.batch_size
        else:
            tuned = self._auto_tune_batch_size(photos, trip_dir)
            self._tuned_batch_size = tuned
            base = tuned
        if self._oom_cap is not None:
            return max(1, min(base, self._oom_cap))
        return base

    def _auto_tune_batch_size(self, photos: list[dict], trip_dir: Path) -> int:
        """P7-G1 · probe batch sizes on a small sample."""
        import torch

        sample = photos[: min(len(photos), self.batch_auto_tune_samples)]
        if not sample:
            return max(1, self.batch_size)
        candidates = [b for b in (32, 16, 8, 4, 2, 1) if b <= max(1, self.batch_size)] or [1]
        best = 1
        with self._infer_lock:
            for bs in candidates:
                try:
                    tensors = self._load_batch_tensors(sample[:bs], trip_dir)
                    if not tensors:
                        continue
                    batch = torch.stack(tensors).to(self._device)
                    t0 = time.monotonic()
                    with torch.no_grad():
                        _ = self._model.encode_image(batch)
                    elapsed = time.monotonic() - t0
                    if elapsed < 2.0 or bs == 1:
                        best = bs
                        break
                except RuntimeError as exc:
                    if "out of memory" in str(exc).lower():
                        if self._device == "cuda":
                            torch.cuda.empty_cache()
                        continue
                    break
        _log.info("CLIP auto batch tune → %d (requested %d)", best, self.batch_size)
        return best

    def _load_image_tensor(self, path: Path, *, preprocess: Any | None = None) -> Any:
        from PIL import Image

        pp = preprocess if preprocess is not None else self._preprocess
        with Image.open(path) as img:
            return pp(img.convert("RGB"))

    def _load_batch_tensors(
        self,
        batch_assets: list[dict],
        trip_dir: Path,
        *,
        stats: EmbedStats | None = None,
    ) -> list[Any]:
        tensors: list[Any] = []
        for asset in batch_assets:
            path, used_web = _resolve_asset_path(
                asset, trip_dir, prefer_web_derivative=self._effective_prefer_web()
            )
            if path is None or not path.is_file():
                continue
            if stats and used_web:
                stats.web_derivative_hits += 1
            tensors.append(self._load_image_tensor(path))
        return tensors

    def _encode_batch_tensors(
        self,
        tensors: list[Any],
        batch_assets: list[dict],
        *,
        stats: EmbedStats,
    ) -> tuple[list[list[float]], list[tuple[dict, str, float]]]:
        import torch

        if not tensors:
            return [], []

        with self._infer_lock:
            batch = torch.stack(tensors).to(self._device)
            t0 = time.monotonic()
            try:
                with torch.no_grad():
                    feats = self._model.encode_image(batch)
                    feats = feats / feats.norm(dim=-1, keepdim=True)
            except RuntimeError as exc:
                if "out of memory" not in str(exc).lower() or len(tensors) <= 1:
                    raise
                stats.oom_halves += 1
                if self.dynamic_backoff:
                    half = max(1, len(tensors) // 2)
                    if self._oom_cap is None:
                        self._oom_cap = half
                    else:
                        self._oom_cap = min(self._oom_cap, half)
                mid = len(tensors) // 2
                left_v, left_s = self._encode_batch_tensors(
                    tensors[:mid], batch_assets[:mid], stats=stats
                )
                right_v, right_s = self._encode_batch_tensors(
                    tensors[mid:], batch_assets[mid:], stats=stats
                )
                return left_v + right_v, left_s + right_s

            elapsed = time.monotonic() - t0
            if self.dynamic_backoff and elapsed > 1.5 and len(tensors) > 1:
                self._prefetch_disabled = True
                _log.info("CLIP dynamic backoff: disabling prefetch (batch took %.2fs)", elapsed)

            vectors: list[list[float]] = []
            proposals: list[tuple[dict, str, float]] = []
            for i, asset in enumerate(batch_assets[: len(tensors)]):
                feat = feats[i : i + 1]
                subject = self._subject_class_for(feat)
                if subject is not None:
                    proposals.append((asset, subject[0], subject[1]))
                vectors.append(feat.cpu().numpy()[0].tolist())
            return vectors, proposals

    def _embed_clip(
        self,
        photos: list[dict],
        *,
        trip_dir: Path,
        deterministic: bool,
        apply_subject_class: bool = True,
    ) -> EmbedResult:
        import numpy as np
        import torch

        if not self._ensure_clip():
            raise RuntimeError("CLIP model unavailable")

        if deterministic:
            torch.manual_seed(0)

        self._oom_cap = None
        self._load_persisted_batch_if_needed(trip_dir)
        self._maybe_gate_web_derivative(photos, trip_dir)

        stats = EmbedStats(prefetch_enabled=self.prefetch and not self._prefetch_disabled)
        t_start = time.monotonic()
        batch_size = self._effective_batch_size(photos, trip_dir)
        stats.batch_size = batch_size
        stats.auto_batch_tuned = self._tuned_batch_size is not None

        vectors: list[list[float]] = []
        ids: list[str] = []
        subject_proposals: list[tuple[dict, str, float]] = []
        prefetch_future: Future[list[Any]] | None = None
        prefetch_assets: list[dict] = []

        i = 0
        while i < len(photos):
            batch_assets = photos[i : i + batch_size]
            ready: list[tuple[dict, Path]] = []
            missing: list[dict] = []
            for asset in batch_assets:
                path, used_web = _resolve_asset_path(
                    asset, trip_dir, prefer_web_derivative=self._effective_prefer_web()
                )
                if path is None or not path.is_file():
                    missing.append(asset)
                    continue
                if used_web:
                    stats.web_derivative_hits += 1
                ready.append((asset, path))

            if missing and ready:
                stats.fallback_single += len(missing)
                tensors = [self._load_image_tensor(p) for _, p in ready]
                encode_assets = [a for a, _ in ready]
                try:
                    batch_vectors, batch_proposals = self._encode_batch_tensors(
                        tensors, encode_assets, stats=stats
                    )
                    vectors.extend(batch_vectors)
                    ids.extend(a["id"] for a in encode_assets[: len(batch_vectors)])
                    subject_proposals.extend(batch_proposals)
                except RuntimeError:
                    stats.fallback_single += len(ready)
                    for asset, path in ready:
                        with self._infer_lock:
                            tensor = self._load_image_tensor(path).unsqueeze(0).to(self._device)
                            with torch.no_grad():
                                feat = self._model.encode_image(tensor)
                                feat = feat / feat.norm(dim=-1, keepdim=True)
                        subject = self._subject_class_for(feat)
                        if subject is not None:
                            subject_proposals.append((asset, subject[0], subject[1]))
                        vectors.append(feat.cpu().numpy()[0].tolist())
                        ids.append(asset["id"])
                trip_stats = _trip_heuristic_stats(photos)
                for asset in missing:
                    vectors.append(_heuristic_vector(asset, pool=photos, stats=trip_stats))
                    ids.append(asset["id"])
                stats.batches += 1
                i += len(batch_assets)
                continue

            if missing and not ready:
                trip_stats = _trip_heuristic_stats(photos)
                for asset in missing:
                    vectors.append(_heuristic_vector(asset, pool=photos, stats=trip_stats))
                    ids.append(asset["id"])
                stats.batches += 1
                i += len(batch_assets)
                continue

            if ready:
                if (
                    stats.prefetch_enabled
                    and prefetch_future is not None
                    and prefetch_assets
                    and len(ready) == len(batch_assets)
                ):
                    try:
                        tensors = prefetch_future.result(timeout=30)
                        if len(tensors) != len(ready):
                            tensors = [self._load_image_tensor(p) for _, p in ready]
                    except Exception:
                        tensors = [self._load_image_tensor(p) for _, p in ready]
                else:
                    tensors = [self._load_image_tensor(p) for _, p in ready]

                encode_assets = [a for a, _ in ready]
                try:
                    batch_vectors, batch_proposals = self._encode_batch_tensors(
                        tensors, encode_assets, stats=stats
                    )
                except RuntimeError:
                    stats.fallback_single += len(encode_assets)
                    for asset, path in ready:
                        with self._infer_lock:
                            tensor = self._load_image_tensor(path).unsqueeze(0).to(self._device)
                            with torch.no_grad():
                                feat = self._model.encode_image(tensor)
                                feat = feat / feat.norm(dim=-1, keepdim=True)
                        subject = self._subject_class_for(feat)
                        if subject is not None:
                            subject_proposals.append((asset, subject[0], subject[1]))
                        vectors.append(feat.cpu().numpy()[0].tolist())
                        ids.append(asset["id"])
                else:
                    vectors.extend(batch_vectors)
                    ids.extend(a["id"] for a in encode_assets[: len(batch_vectors)])
                    if len(batch_vectors) < len(encode_assets):
                        for asset, path in ready[len(batch_vectors) :]:
                            tensor = self._load_image_tensor(path).unsqueeze(0).to(self._device)
                            with self._infer_lock:
                                with torch.no_grad():
                                    feat = self._model.encode_image(tensor)
                                    feat = feat / feat.norm(dim=-1, keepdim=True)
                            subject = self._subject_class_for(feat)
                            if subject is not None:
                                subject_proposals.append((asset, subject[0], subject[1]))
                            vectors.append(feat.cpu().numpy()[0].tolist())
                            ids.append(asset["id"])
                            stats.fallback_single += 1
                    subject_proposals.extend(batch_proposals)

            stats.batches += 1
            i += len(batch_assets)

            next_i = i
            if stats.prefetch_enabled and next_i < len(photos):
                prefetch_assets = photos[next_i : next_i + batch_size]
                prefer_web = self._effective_prefer_web()
                preprocess = self._preprocess

                def _prefetch_load(
                    assets: list[dict] = prefetch_assets,
                    td: Path = trip_dir,
                    pw: bool = prefer_web,
                    pp: Any = preprocess,
                ) -> list[Any]:
                    out: list[Any] = []
                    for a in assets:
                        p, _ = _resolve_asset_path(
                            a, td, prefer_web_derivative=pw
                        )
                        if p is not None and p.is_file():
                            out.append(self._load_image_tensor(p, preprocess=pp))
                    return out

                prefetch_future = _prefetch_pool.submit(_prefetch_load)

        for asset, label, confidence in subject_proposals:
            if apply_subject_class:
                asset["subjectClass"] = label
                asset["subjectConfidence"] = confidence

                refresh_semantic_tag_for_asset(asset)

        stats.elapsed_ms = (time.monotonic() - t_start) * 1000.0
        stats.recommended_batch_size = self._tuned_batch_size or batch_size
        stats.web_derivative_gated = self._web_derivative_disabled
        self.last_embed_stats = stats
        self._oom_cap = None
        if vectors:
            dim = len(vectors[0])
            if any(len(row) != dim for row in vectors):
                _log.warning("CLIP embed mixed dimensions; falling back to heuristic")
                ids = [a["id"] for a in photos]
                from travelogue.layout_contract.quality import normalized_sharpness

                sharp_map = {
                    a["id"]: normalized_sharpness(a, photos, bucket_by="mediaClass")
                    for a in photos
                }
                trip_stats = _trip_heuristic_stats(photos)
                mat = np.array(
                    [
                        _heuristic_vector(
                            a,
                            pool=photos,
                            sharp_pct=sharp_map.get(a["id"], 0.5),
                            stats=trip_stats,
                        )
                        for a in photos
                    ],
                    dtype=np.float32,
                )
                norms = np.linalg.norm(mat, axis=1, keepdims=True)
                norms = np.where(norms < 1e-8, 1.0, norms)
                mat = mat / norms
                return EmbedResult(ids, mat, "heuristic", model=HEURISTIC_MODEL_V2)
        mat = np.array(vectors, dtype=np.float32)
        return EmbedResult(ids, mat, "clip", model=f"{self.model_name}/{self.pretrained}")


def _path_within_trip(candidate: Path, trip_dir: Path) -> bool:
    try:
        candidate.resolve().relative_to(trip_dir.resolve())
        return True
    except (ValueError, OSError):
        return False


def _resolve_asset_path(
    asset: dict,
    trip_dir: Path,
    *,
    prefer_web_derivative: bool = False,
) -> tuple[Path | None, bool]:
    """Return (path, used_web_derivative). P7-A4 prefers 800px WebP."""
    used_web = False
    aid = asset.get("id")
    trip_resolved = trip_dir.resolve()

    if prefer_web_derivative and aid:
        web_candidates: list[Path] = [
            trip_dir / "assets" / f"{aid}-w800.webp",
            trip_dir / "assets" / "web" / f"{aid}.webp",
            trip_dir / "assets" / "web" / f"{aid}-w800.webp",
        ]
        srcset = asset.get("srcset") or []
        for entry in srcset:
            if not isinstance(entry, dict):
                continue
            w = entry.get("width")
            rel = entry.get("file")
            if w == 800 and isinstance(rel, str) and rel.strip():
                candidate = (trip_dir / rel.lstrip("/\\")).resolve()
                if _path_within_trip(candidate, trip_resolved):
                    web_candidates.insert(0, candidate)
        for candidate in web_candidates:
            if candidate.is_file() and _path_within_trip(candidate, trip_resolved):
                return candidate, True

    # NR profile / prefer_web=false: prefer original pixels (D-MRS-09 / D-PT-07).
    if not prefer_web_derivative:
        from travelogue.media.source_resolve import resolve_source_path

        resolved_src = resolve_source_path(asset, trip_dir)
        if resolved_src is not None and resolved_src.is_file():
            return resolved_src, False
        # Do not fall through to WebP when prefer_web=false (avoids silent quality drop).
        return None, False

    rel = asset.get("path") or asset.get("file") or asset.get("src") or asset.get("displayFile")
    if isinstance(rel, str) and rel.strip():
        p = Path(rel)
        if p.is_file():
            return p, used_web
        candidate = (trip_dir / rel.lstrip("/\\")).resolve()
        if candidate.is_file() and _path_within_trip(candidate, trip_resolved):
            return candidate, used_web
    if not aid:
        return None, used_web
    for sub in ("assets/web", "assets/original", "assets"):
        for ext in (".webp", ".jpg", ".jpeg", ".png"):
            candidate = trip_dir / sub / f"{aid}{ext}"
            if candidate.is_file():
                return candidate, sub == "assets/web" or candidate.suffix.lower() == ".webp"
    return None, used_web
