"""ALG-V3 W2-A6 · look batch encode + session/app_cfg wiring."""

from __future__ import annotations

import math
import threading
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from PIL import Image

from travelogue.config.shot_grouping import ShotGroupingConfig
from travelogue.media.face_embed import l2_normalize
from travelogue.vision import look_appearance as la


class _FakeModel:
    def __init__(self) -> None:
        self.calls: list[int] = []

    def encode_image(self, batch):  # noqa: ANN001
        import torch

        self.calls.append(int(batch.shape[0]))
        # Deterministic unit-ish features from batch mean of first channel.
        n = int(batch.shape[0])
        out = torch.zeros((n, 4), dtype=torch.float32)
        for i in range(n):
            out[i, 0] = float(batch[i].mean().item()) + 0.1 * (i + 1)
            out[i, 1] = 1.0
        return out


class _FakeEncoder:
    def __init__(self, *, batch_size: int = 2) -> None:
        import torch

        self.batch_size = batch_size
        self._device = torch.device("cpu")
        self._infer_lock = threading.Lock()
        self._model = _FakeModel()
        self._preprocess = lambda img: torch.ones(3, 8, 8, dtype=torch.float32)

    def _ensure_clip(self) -> bool:
        return True


def _rgb(path: Path, *, color: tuple[int, int, int] = (200, 40, 40)) -> None:
    Image.new("RGB", (64, 64), color).save(path)


def test_a6_batch_encode_chunks_by_batch_size(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(la, "detect_faces_in_image", lambda _img: [(8, 8, 24, 24)])
    enc = _FakeEncoder(batch_size=2)
    assets = []
    for i in range(5):
        name = f"p{i}.jpg"
        _rgb(tmp_path / name, color=(40 + i * 20, 80, 120))
        assets.append({"id": f"a{i}", "type": "photo", "sourceFile": name})
    cfg = ShotGroupingConfig()
    # Face gate on; min area tiny so synthetic face always qualifies.
    cfg = SimpleNamespace(
        look=SimpleNamespace(
            require_face_or_subject=True,
            max_faces_before_skip=4,
            min_max_face_area_ratio=0.001,
        )
    )
    out, stats = la.compute_look_vectors_for_assets(
        assets, trip_dir=tmp_path, cfg=cfg, encoder=enc
    )
    assert len(out) == 5
    assert stats["lookEncoded"] == 5
    assert stats["lookBatchSize"] == 2
    assert stats["lookBatches"] == math.ceil(5 / 2)
    assert enc._model.calls == [2, 2, 1]
    assert stats["lookElapsedMs"] >= 0


def test_a6_batch_size_one_uses_single_path(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(la, "detect_faces_in_image", lambda _img: [(8, 8, 24, 24)])
    single_calls: list[str] = []
    batch_calls: list[int] = []

    def _single(img, encoder):  # noqa: ANN001
        single_calls.append("x")
        return l2_normalize(np.asarray([1.0, 0.0, 0.0], dtype=np.float64))

    def _batch(imgs, encoder):  # noqa: ANN001
        batch_calls.append(len(imgs))
        raise AssertionError("batch path must not run when batch_size<=1")

    monkeypatch.setattr(la, "encode_pil_clip", _single)
    monkeypatch.setattr(la, "encode_pil_clip_batch", _batch)
    enc = _FakeEncoder(batch_size=1)
    name = "p0.jpg"
    _rgb(tmp_path / name)
    assets = [{"id": "a0", "type": "photo", "sourceFile": name}]
    cfg = SimpleNamespace(
        look=SimpleNamespace(
            require_face_or_subject=True,
            max_faces_before_skip=4,
            min_max_face_area_ratio=0.001,
        )
    )
    out, stats = la.compute_look_vectors_for_assets(
        assets, trip_dir=tmp_path, cfg=cfg, encoder=enc
    )
    assert set(out) == {"a0"}
    assert single_calls == ["x"]
    assert batch_calls == []
    assert stats["lookFallbackSingle"] == 1
    assert stats["lookBatches"] == 1


def test_a6_batch_preserves_asset_id_order(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(la, "detect_faces_in_image", lambda _img: [(8, 8, 24, 24)])

    def _batch(imgs, encoder):  # noqa: ANN001
        # Distinct directions so order bugs would swap ids after L2.
        return [
            l2_normalize(np.asarray([1.0 if i == 0 else 0.0, 1.0 if i == 1 else 0.0, 1.0 if i == 2 else 0.0], dtype=np.float64))
            for i in range(len(imgs))
        ]

    monkeypatch.setattr(la, "encode_pil_clip_batch", _batch)
    enc = _FakeEncoder(batch_size=8)
    assets = []
    for aid in ["z", "a", "m"]:
        name = f"{aid}.jpg"
        _rgb(tmp_path / name)
        assets.append({"id": aid, "type": "photo", "sourceFile": name})
    cfg = SimpleNamespace(
        look=SimpleNamespace(
            require_face_or_subject=True,
            max_faces_before_skip=4,
            min_max_face_area_ratio=0.001,
        )
    )
    out, _stats = la.compute_look_vectors_for_assets(
        assets, trip_dir=tmp_path, cfg=cfg, encoder=enc
    )
    assert list(out.keys()) == ["z", "a", "m"]
    assert int(np.argmax(out["z"])) == 0
    assert int(np.argmax(out["a"])) == 1
    assert int(np.argmax(out["m"])) == 2


def test_a6_get_clip_encoder_receives_app_cfg(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(la, "detect_faces_in_image", lambda _img: [(8, 8, 24, 24)])
    seen: dict[str, object] = {}

    class _Vis:
        batch_size = 2

    app_cfg = SimpleNamespace(vision=_Vis())

    def _get(cfg=None):  # noqa: ANN001
        seen["cfg"] = cfg
        return _FakeEncoder(batch_size=2)

    monkeypatch.setattr(
        "travelogue.vision.clip_encoder.clip_torch_available", lambda: True
    )
    monkeypatch.setattr("travelogue.vision.clip_encoder.get_clip_encoder", _get)
    monkeypatch.setattr(
        la,
        "encode_pil_clip_batch",
        lambda imgs, encoder: [
            l2_normalize(np.asarray([1.0, 0.0], dtype=np.float64)) for _ in imgs
        ],
    )
    name = "p0.jpg"
    _rgb(tmp_path / name)
    assets = [{"id": "a0", "type": "photo", "sourceFile": name}]
    cfg = SimpleNamespace(
        look=SimpleNamespace(
            require_face_or_subject=True,
            max_faces_before_skip=4,
            min_max_face_area_ratio=0.001,
        )
    )
    la.compute_look_vectors_for_assets(
        assets, trip_dir=tmp_path, cfg=cfg, app_cfg=app_cfg
    )
    assert seen["cfg"] is app_cfg


def test_a6_cache_hit_skips_batch(tmp_path: Path, monkeypatch) -> None:
    vectors = {
        "a1": l2_normalize(np.asarray([1.0, 0.0], dtype=np.float64)),
        "a2": l2_normalize(np.asarray([0.0, 1.0], dtype=np.float64)),
    }
    la.save_look_appearance_cache(tmp_path, vectors)

    def _boom_batch(*_a, **_k):
        raise AssertionError("batch encode must not run on full cache hit")

    def _boom_single(*_a, **_k):
        raise AssertionError("single encode must not run on full cache hit")

    monkeypatch.setattr(la, "encode_pil_clip_batch", _boom_batch)
    monkeypatch.setattr(la, "encode_pil_clip", _boom_single)
    assets = [
        {"id": "a1", "type": "photo", "sourceFile": "missing.jpg"},
        {"id": "a2", "type": "photo", "sourceFile": "missing.jpg"},
    ]
    out, stats = la.compute_look_vectors_for_assets(
        assets, trip_dir=tmp_path, cfg=ShotGroupingConfig()
    )
    assert set(out) == {"a1", "a2"}
    assert stats["lookEncoded"] == 0
    assert stats["lookBatches"] == 0
