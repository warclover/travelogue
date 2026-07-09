"""Config dict lookup helpers (snake + camel)."""

from __future__ import annotations

from travelogue.config import VisionConfig
from travelogue.config_helpers import cfg_bool, cfg_float, cfg_get, cfg_int, cfg_str


def test_cfg_get_snake_wins_over_camel() -> None:
    raw = {"auto_min_photos": 10, "autoMinPhotos": 99}
    assert cfg_get(raw, "auto_min_photos", "autoMinPhotos", 80) == 10


def test_cfg_get_falls_back_to_camel() -> None:
    raw = {"autoMinPhotos": 42}
    assert cfg_get(raw, "auto_min_photos", "autoMinPhotos", 80) == 42


def test_cfg_get_default() -> None:
    assert cfg_get({}, "missing_snake", "missingCamel", 80) == 80


def test_cfg_typed_helpers() -> None:
    raw = {"parallelEmbed": True, "parallelEmbedChunk": "64", "cacheAbiVersion": "v2"}
    assert cfg_bool(raw, "parallel_embed", "parallelEmbed", False) is True
    assert cfg_int(raw, "parallel_embed_chunk", "parallelEmbedChunk", 32) == 64
    assert cfg_str(raw, "cache_abi_version", "cacheAbiVersion", "v1") == "v2"
    assert cfg_float({"autoMinEligibleRatio": "0.75"}, "auto_min_eligible_ratio", "autoMinEligibleRatio", 0.6) == 0.75


def test_vision_from_dict_accepts_camel_keys() -> None:
    from travelogue.config.vision import vision_from_dict

    cfg = vision_from_dict(
        {
            "enabled": "auto",
            "autoMinPhotos": 120,
            "batchSize": 24,
            "preferWebDerivative": False,
            "subjectPrompts": ["landscape", "food"],
        }
    )
    assert isinstance(cfg, VisionConfig)
    assert cfg.auto_min_photos == 120
    assert cfg.batch_size == 24
    assert cfg.prefer_web_derivative is False
    assert cfg.subject_prompts == ("landscape", "food")
