"""Studio 首页 v2 服务端门控（M20-i/j · FEATURE-FLAG §3）。

TRAVELOGUE_STUDIO_HOMEPAGE_V2：
  - off（回滚）→ GET / 仍 classic 冻结页；GET /v2 → 302 /
  - on（M20-j 100%）→ GET / → v2；GET /classic → classic 冻结页
  - auto → holdback：按稳定分桶 + percent 决定 / 返回 v2 或 classic

分桶：Cookie `travelogue.studio.hp_bucket`（HMAC 签名 bucket.sig），无则 UA+盐 hash 写入。
percent：环境变量 TRAVELOGUE_STUDIO_HOMEPAGE_V2_PERCENT，或 config.yaml
  `studio.homepage.v2_bento.percent`（0–100）。

Query 覆盖（仅 loopback）：`?homepageVariant=v2|v3` 强制 variant（仅 /）。
"""

from __future__ import annotations

import hashlib
import hmac
import html as html_module
import logging
import os
from typing import Any, Literal
from urllib.parse import parse_qs

from travelogue.paths import STUDIO_TEMPLATE_DIR

ENV_MODE = "TRAVELOGUE_STUDIO_HOMEPAGE_V2"
ENV_PERCENT = "TRAVELOGUE_STUDIO_HOMEPAGE_V2_PERCENT"
ENV_BUCKET_SECRET = "TRAVELOGUE_STUDIO_HP_BUCKET_SECRET"
COOKIE_BUCKET = "travelogue.studio.hp_bucket"
COOKIE_MAX_AGE = 365 * 24 * 3600
BUCKET_SALT = "travelogue-studio-homepage-v2"
LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})
_log = logging.getLogger(__name__)

HomepageGateMode = Literal["off", "on", "auto"]


def resolve_mode(raw: str | None = None) -> HomepageGateMode:
    val = (raw if raw is not None else os.environ.get(ENV_MODE, "on")).strip().lower()
    if val in ("on", "1", "true", "yes"):
        return "on"
    if val == "auto":
        return "auto"
    return "off"


def is_loopback_host(host: str | None) -> bool:
    """Studio 绑定地址是否为 loopback（dev harness / query override 门控）。"""
    if not host:
        return True
    h = host.strip().lower()
    if h in LOOPBACK_HOSTS:
        return True
    if h.startswith("127."):
        return True
    return False


def allow_variant_override(host: str | None) -> bool:
    """?homepageVariant= 仅 loopback 生效，防止生产 holdback  bypass。"""
    return is_loopback_host(host)


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
    """0–99 稳定分桶。existing 来自已验证 cookie 时直接复用。"""
    if existing is not None and 0 <= existing <= 99:
        return existing
    ua = user_agent or "unknown"
    digest = hashlib.sha256(f"{BUCKET_SALT}:{ua}".encode()).hexdigest()
    return int(digest[:8], 16) % 100


def bucket_in_treatment(bucket: int, percent: float) -> bool:
    """percent=10 → bucket 0–9 进 v2 组。"""
    if percent <= 0:
        return False
    if percent >= 100:
        return True
    return bucket < percent


def _bucket_secret(handler: Any) -> str:
    token = getattr(handler, "studio_token", None) or ""
    if token:
        return token
    env = os.environ.get(ENV_BUCKET_SECRET, "").strip()
    if env:
        return env
    return BUCKET_SALT


def sign_bucket_value(bucket: int, secret: str) -> str:
    """Cookie 值：{bucket}.{hmac16}。"""
    sig = hmac.new(
        secret.encode("utf-8"),
        str(bucket).encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()[:16]
    return f"{bucket}.{sig}"


def verify_bucket_cookie(raw: str, secret: str) -> int | None:
    """验证签名 cookie；篡改返回 None。"""
    if not raw or "." not in raw:
        return None
    bucket_part, sig = raw.split(".", 1)
    if not bucket_part.isdigit() or not sig:
        return None
    bucket = int(bucket_part)
    if not 0 <= bucket <= 99:
        return None
    expected = sign_bucket_value(bucket, secret).split(".", 1)[1]
    if not hmac.compare_digest(sig, expected):
        return None
    return bucket


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
    allow_override: bool = False,
) -> Literal["v2", "v3"]:
    """GET / 应展示的 variant（不含 redirect 细节）。"""
    if allow_override:
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
    """M21-c 后统一在根路径渲染，不再从 / 跳转到 /v2。"""
    return False


def parse_request_query(path_with_query: str) -> dict[str, list[str]]:
    if "?" not in path_with_query:
        return {}
    qs = path_with_query.split("?", 1)[1]
    return parse_qs(qs, keep_blank_values=False)


def inject_home_placeholders(html: str, handler: Any, bucket: int) -> str:
    """替换 __STUDIO_*__ 占位符（token escape + bucket + dev 标志）。"""
    token = html_module.escape(getattr(handler, "studio_token", None) or "", quote=True)
    host = getattr(handler, "studio_host", "127.0.0.1") or "127.0.0.1"
    dev_flag = "1" if is_loopback_host(host) else ""
    miniapp_qr = (
        "1"
        if (STUDIO_TEMPLATE_DIR / "assets" / "miniapp-qr.webp").is_file()
        else "0"
    )
    return (
        html.replace("__STUDIO_TOKEN__", token)
        .replace("__STUDIO_BUCKET_ID__", str(bucket))
        .replace("__STUDIO_DEV__", dev_flag)
        .replace("__STUDIO_MINIAPP_QR__", miniapp_qr)
    )


def _cookie_secure_flag(handler: Any) -> str:
    """HTTPS 或反向代理 X-Forwarded-Proto=https 时追加 Secure。"""
    headers = getattr(handler, "headers", None)
    if headers is None:
        return ""
    proto = (headers.get("X-Forwarded-Proto") or "").split(",")[0].strip().lower()
    if proto == "https":
        return "; Secure"
    return ""


def set_bucket_cookie(handler: Any, bucket: int) -> None:
    """写入 HMAC 签名分桶 cookie（HttpOnly）。"""
    secret = _bucket_secret(handler)
    value = sign_bucket_value(bucket, secret)
    secure = _cookie_secure_flag(handler)
    handler.send_header(
        "Set-Cookie",
        f"{COOKIE_BUCKET}={value}; Path=/; Max-Age={COOKIE_MAX_AGE}; HttpOnly; SameSite=Lax{secure}",
    )


def read_or_assign_bucket(handler: Any) -> tuple[int, bool]:
    """→ (bucket, is_new)。新分桶或 cookie 无效时需 Set-Cookie。"""
    secret = _bucket_secret(handler)
    cookies = _cookie_map(handler.headers.get("Cookie"))
    raw = cookies.get(COOKIE_BUCKET)
    if raw is not None:
        verified = verify_bucket_cookie(raw, secret)
        if verified is not None:
            return verified, False
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
        _log.debug("studio homepage gate yaml load failed for %s", p, exc_info=True)
        return None
