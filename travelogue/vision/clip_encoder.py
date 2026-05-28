"""Optional CLIP / heuristic embeddings for scene clustering (Phase 3 M13)."""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

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
# Backwards-compatible alias; existing tests imported this name.
SUBJECT_PROMPTS = DEFAULT_SUBJECT_PROMPTS


class VisionMissingError(Exception):
    code = "E_CLUSTER_VISION_MISSING"

    def __init__(self, message: str = "vision extra not installed") -> None:
        super().__init__(message)
        self.message = message


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
    """Best-effort check whether CLIP weights are already on disk (M13-5a stage hint).

    Strategy:
    1. Ask open_clip for its expected local filename and probe the standard
       cache roots; this is the most accurate signal when open_clip is present.
    2. Fall back to a heuristic file-name match across known cache roots so
       fresh installs without open_clip importable still get a useful hint.
    """
    if not clip_torch_available():
        return True

    cache_roots = _clip_cache_roots()

    # Preferred signal: open_clip's own filename resolver.
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
        _ = download  # keep reference; some open_clip versions only expose helpers
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


def _heuristic_vector(asset: dict) -> list[float]:
    w = float(asset.get("width") or 1000)
    h = float(asset.get("height") or 1000)
    ratio = w / max(h, 1.0)
    sharp = float(asset.get("sharpness") or 0.0)
    luma = float(asset.get("meanLuma") or 0.5)
    tone_raw = str(asset.get("dominantTone") or "")
    tone = (int(hashlib.md5(tone_raw.encode()).hexdigest()[:8], 16) % 1000) / 1000.0
    subj = str(asset.get("subjectClass") or asset.get("subjectBucket") or "")
    subj_h = (int(hashlib.md5(subj.encode()).hexdigest()[:8], 16) % 1000) / 1000.0
    face = 1.0 if asset.get("faceCount") else 0.0
    return [ratio, sharp, luma, tone, subj_h, face, w / 4000.0, h / 4000.0]


@dataclass
class EmbedResult:
    asset_ids: list[str]
    vectors: Any  # np.ndarray
    source: str  # clip | heuristic
    model: str | None = None


def _labels_from_prompts(prompts: tuple[str, ...]) -> tuple[str, ...]:
    """Best-effort: turn "a photo of <label>" prompts back into bare labels."""
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


class ClipEncoder:
    """Lazy CLIP encoder; falls back to heuristic vectors when torch/open_clip absent."""

    def __init__(
        self,
        *,
        model_name: str = "ViT-B-32",
        pretrained: str = "openai",
        subject_prompts: tuple[str, ...] | None = None,
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
        """Return (label, confidence); None when text features unavailable."""
        if self._text_features is None:
            return None
        sim = (image_feat @ self._text_features.T).squeeze(0)
        idx = int(sim.argmax().item())
        if idx >= len(self._subject_labels):
            return None
        return self._subject_labels[idx], round(float(sim[idx].cpu()), 4)

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
    ) -> EmbedResult:
        import numpy as np

        photos = [a for a in assets if a.get("type", "image") != "video" and a.get("id")]
        if not photos:
            return EmbedResult([], np.zeros((0, 8), dtype=np.float32), "heuristic")

        if self._ensure_clip() and trip_dir is not None:
            try:
                return self._embed_clip(photos, trip_dir=trip_dir, deterministic=deterministic)
            except Exception as exc:
                _log.warning("CLIP embed failed, heuristic fallback: %s", exc)

        ids = [a["id"] for a in photos]
        mat = np.array([_heuristic_vector(a) for a in photos], dtype=np.float32)
        norms = np.linalg.norm(mat, axis=1, keepdims=True)
        norms = np.where(norms < 1e-8, 1.0, norms)
        mat = mat / norms
        return EmbedResult(ids, mat, "heuristic", model="heuristic-v1")

    def _embed_clip(
        self,
        photos: list[dict],
        *,
        trip_dir: Path,
        deterministic: bool,
    ) -> EmbedResult:
        import numpy as np
        import torch
        from PIL import Image

        if deterministic:
            torch.manual_seed(0)

        vectors: list[list[float]] = []
        ids: list[str] = []
        # Collect subject class proposals; only commit them once the whole batch
        # finishes so that a mid-batch failure does not leave half the trip with
        # CLIP labels and the other half without.
        subject_proposals: list[tuple[dict, str, float]] = []
        for asset in photos:
            path = _resolve_asset_path(asset, trip_dir)
            if path is None or not path.is_file():
                vectors.append(_heuristic_vector(asset))
                ids.append(asset["id"])
                continue
            img = Image.open(path).convert("RGB")
            tensor = self._preprocess(img).unsqueeze(0).to(self._device)
            with torch.no_grad():
                feat = self._model.encode_image(tensor)
                feat = feat / feat.norm(dim=-1, keepdim=True)
            subject = self._subject_class_for(feat)
            if subject is not None:
                subject_proposals.append((asset, subject[0], subject[1]))
            vectors.append(feat.cpu().numpy()[0].tolist())
            ids.append(asset["id"])

        for asset, label, confidence in subject_proposals:
            asset["subjectClass"] = label
            asset["subjectConfidence"] = confidence

        mat = np.array(vectors, dtype=np.float32)
        return EmbedResult(ids, mat, "clip", model=f"{self.model_name}/{self.pretrained}")


def _resolve_asset_path(asset: dict, trip_dir: Path) -> Path | None:
    rel = asset.get("path") or asset.get("file") or asset.get("src")
    if isinstance(rel, str) and rel.strip():
        p = Path(rel)
        if p.is_file():
            return p
        candidate = trip_dir / rel.lstrip("/\\")
        if candidate.is_file():
            return candidate
    aid = asset.get("id")
    if not aid:
        return None
    for sub in ("assets/web", "assets/original", "assets"):
        for ext in (".webp", ".jpg", ".jpeg", ".png"):
            candidate = trip_dir / sub / f"{aid}{ext}"
            if candidate.is_file():
                return candidate
    return None
