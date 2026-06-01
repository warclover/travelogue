"""Studio 首页 v2 服务端门控（M20-i/j · FEATURE-FLAG §3）。

TRAVELOGUE_STUDIO_HOMEPAGE_V2：
  - off（默认）→ GET / 仍 v3；GET /v2 → v2
  - on（M20-j 100%）→ GET / → v2；GET /classic → v3
  - auto → holdback：按稳定分桶 + percent 决定 / 是否 302 → /v2

分桶：Cookie `travelogue.studio.hp_bucket`（0–99），无则 UA+盐 hash 写入。
percent：环境变量 TRAVELOGUE_STUDIO_HOMEPAGE_V2_PERCENT，或 config.yaml
  `studio.homepage.v2_bento.percent`（0–100）。

Query 覆盖（dev/测试）：`?homepageVariant=v2|v3` 强制 variant（仅 /）。
"""

from __future__ import annotations

import hashlib
import os
from typing import Any, Literal
from urllib.parse import parse_qs

from travelogue.web.studio_handlers.paths import HOME_CLASSIC_PATH, HOME_V2_PATH

ENV_MODE = "TRAVELOGUE_STUDIO_HOMEPAGE_V2"
ENV_PERCENT = "TRAVELOGUE_STUDIO_HOMEPAGE_V2_PERCENT"
COOKIE_BUCKET = "travelogue.studio.hp_bucket"
COOKIE_MAX_AGE = 365 * 24 * 3600
BUCKET_SALT = "travelogue-studio-homepage-v2"

HomepageGateMode = Literal["off", "on", "auto"]


def resolve_mode(raw: str | None = None) -> HomepageGateMode:
    val = (raw if raw is not None else os.environ.get(ENV_MODE, "off")).strip().lower()
    if val in ("on", "1", "true", "yes"):
        return "on"
    if val == "auto":
        return "auto"
    return "off"


def _parse_percent(raw: Any) -> float | None:
    if raw is None:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def resolve_percent(config_dict: dict[str, Any] | None = None) -> float:
    """Holdback 百分比 0–100。env 优先，其次 config yaml。"""
    env_pct = _parse_percent(os.environ.get(ENV_PERCENT))
    if env_pct is not None:
        return max(0.0, min(100.0, env_pct))
    if config_dict:
        studio = config_dict.get("studio") or {}
        if isinstance(studio, dict):
            homepage = studio.get("homepage") or {}
            if isinstance(homepage, dict):
                v2 = homepage.get("v2_bento") or homepage.get("v2Bento") or {}
                if isinstance(v2, dict):
                    pct = _parse_percent(v2.get("percent"))
                    if pct is not None:
                        return max(0.0, min(100.0, pct))
    return 0.0


def _cookie_map(cookie_header: str | None) -> dict[str, str]:
    out: dict[str, str] = {}
    if not cookie_header:
        return out
    for part in cookie_header.split(";"):
        part = part.strip()
        if not part or "=" not in part:
            continue
        key, val = part.split("=", 1)
        out[key.strip()] = val.strip()
    return out


def stable_bucket(user_agent: str, existing: int | None = None) -> int:
    """0–99 稳定分桶。existing 来自 cookie 时直接复用。"""
    if existing is not None and 0 <= existing <= 99:
        return existing
    ua = user_agent or "unknown"
    digest = hashlib.sha256(f"{BUCKET_SALT}:{ua}".encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % 100


def bucket_in_treatment(bucket: int, percent: float) -> bool:
    """percent=10 → bucket 0–9 进 v2 组。"""
    if percent <= 0:
        return False
    if percent >= 100:
        return True
    return bucket < percent


def query_variant_override(query: dict[str, list[str]]) -> str | None:
    """?homepageVariant=v2|v3 dev 覆盖。"""
    vals = query.get("homepageVariant") or query.get("homepagevariant") or []
    if not vals:
        return None
    v = str(vals[0]).strip().lower()
    if v in ("v2", "v3"):
        return v
    return None


def decide_root_variant(
    *,
    mode: HomepageGateMode,
    percent: float,
    bucket: int,
    query: dict[str, list[str]] | None = None,
) -> Literal["v2", "v3"]:
    """GET / 应展示的 variant（不含 redirect 细节）。"""
    override = query_variant_override(query or {})
    if override == "v2":
        return "v2"
    if override == "v3":
        return "v3"
    if mode == "on":
        return "v2"
    if mode == "auto":
        return "v2" if bucket_in_treatment(bucket, percent) else "v3"
    return "v3"


def should_redirect_root_to_v2(
    *,
    mode: HomepageGateMode,
    variant: Literal["v2", "v3"],
) -> bool:
    """auto holdback 用 302 → /v2；on 模式直接在 / serve v2（URL 不变）。"""
    return mode == "auto" and variant == "v2"


def parse_request_query(path_with_query: str) -> dict[str, list[str]]:
    if "?" not in path_with_query:
        return {}
    qs = path_with_query.split("?", 1)[1]
    return parse_qs(qs, keep_blank_values=False)



def set_bucket_cookie(handler: Any, bucket: int) -> None:
    """写入分桶 cookie（HttpOnly）。"""
    handler.send_header(
        "Set-Cookie",
        f"{COOKIE_BUCKET}={bucket}; Path=/; Max-Age={COOKIE_MAX_AGE}; HttpOnly; SameSite=Lax",
    )


def read_or_assign_bucket(handler: Any) -> tuple[int, bool]:
    """→ (bucket, is_new)。新分桶时需 Set-Cookie。"""
    cookies = _cookie_map(handler.headers.get("Cookie"))
    raw = cookies.get(COOKIE_BUCKET)
    if raw is not None and raw.isdigit():
        b = int(raw)
        if 0 <= b <= 99:
            return b, False
    ua = handler.headers.get("User-Agent", "")
    b = stable_bucket(ua)
    return b, True


def load_config_dict(handler: Any) -> dict[str, Any] | None:
    """从 handler 关联的 config 路径读 yaml（可选）。"""
    path = getattr(handler, "studio_config_path", None)
    if not path:
        cfg = getattr(handler, "app_config", None)
        path = getattr(cfg, "config_path", None) if cfg else None
    if not path:
        return None
    p = path if hasattr(path, "exists") else None
    if p is None or not p.exists():
        return None
    try:
        import yaml

        data = yaml.safe_load(p.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except Exception:
        return None
