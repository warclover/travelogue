"""ALG-V3 · read-only LLM Ready probe (layer-safe; no web/studio imports)."""

from __future__ import annotations

import os

from travelogue.config import AppConfig, get_config
from travelogue.config._common import capability_allows, normalize_tri_state
from travelogue.llm.errors import LlmError

_ENV_AI_SURFACE = "TRAVELOGUE_AI_SURFACE"
_TRUTHY = frozenset({"1", "true", "on", "yes"})


def _probe_provider_and_ready(
    *,
    cfg: AppConfig | None = None,
    inject_environ: bool,
) -> tuple[bool, str]:
    """Shared resolve path for Ready probing.

    When ``inject_environ`` is False (ALG-V3 ``probe_llm_ready``), never mutate
    ``os.environ``. Studio interactive paths may inject for subsequent real calls.
    """
    app_cfg = cfg or get_config()
    provider = (app_cfg.llm.provider or "stub").strip().lower()
    secrets = None
    try:
        from travelogue.llm.user_settings import inject_secrets_into_environ, read_user_llm_secrets

        secrets = read_user_llm_secrets()
        if inject_environ:
            inject_secrets_into_environ(secrets)
        if secrets.configured and secrets.provider:
            provider = secrets.provider
    except Exception:
        secrets = None
    if provider == "stub":
        return False, "stub"
    try:
        from travelogue.llm.client import resolve_llm_runtime

        # When secrets are configured, pass them request-locally so Ready does
        # not require environ injection (AC-07). Otherwise resolve may read
        # already-present env vars only — never inject here when inject=False.
        if secrets is not None and secrets.configured:
            resolve_llm_runtime(provider, cfg=app_cfg, secrets=secrets)
            # DLLM L1：user_data Key 须 ping 成功才算 Available（禁止「有 Key 即就绪」）
            if secrets.last_ping_ok is not True:
                return False, provider
        else:
            resolve_llm_runtime(provider, cfg=app_cfg)
        return True, provider
    except LlmError:
        return False, provider


def probe_llm_ready(*, cfg: AppConfig | None = None) -> bool:
    """ALG-V3 · read-only Ready probe (AC-07).

    Does **not** inject secrets into ``os.environ``, does not ping the network,
    and does not mutate global config. User secrets require ``last_ping_ok``.
    """
    ready, _provider = _probe_provider_and_ready(cfg=cfg, inject_environ=False)
    return ready


def studio_llm_status(
    *,
    cfg: AppConfig | None = None,
    inject_environ: bool = False,
) -> dict[str, object]:
    """Studio status helper · BAI W1a: only DashScope + last_ping_ok.

    DeepSeek-only secrets / env do **not** light Studio Ready (AC-BAI-04).
    ALG-V3 ``probe_llm_ready`` still accepts DeepSeek env/secrets for CLI.

    Default does **not** inject secrets into process env (request-local Ready).
    Pass ``inject_environ=True`` only for legacy desktop paths that still need it.
    """
    app_cfg = cfg or get_config()
    secrets = None
    try:
        from travelogue.llm.user_settings import inject_secrets_into_environ, read_user_llm_secrets

        secrets = read_user_llm_secrets()
        if inject_environ:
            inject_secrets_into_environ(secrets)
    except Exception:
        secrets = None

    studio_ok = False
    provider = "stub"
    if secrets is not None and secrets.studio_configured:
        provider = "dashscope"
        if secrets.last_ping_ok is True:
            try:
                from travelogue.llm.client import resolve_llm_runtime

                resolve_llm_runtime("dashscope", cfg=app_cfg, secrets=secrets)
                studio_ok = True
            except LlmError:
                studio_ok = False

    return {
        "llmAvailable": studio_ok,
        "llmProvider": provider,
        "connectionOk": studio_ok,
        "copyReady": studio_ok,
    }


def resolve_llm_may_call(*, cfg: AppConfig | None = None) -> bool:
    """ALG-V3 MayCall · Surface ∨ dark env ∨ ``studio.ai_surface_enabled``.

    NAS default is False. Layer-safe duplicate of ``web.ai_surface`` semantics
    (env ∪ studio flag) so ``llm`` / ``services`` never import ``web``.
    """
    env = (os.environ.get(_ENV_AI_SURFACE) or "").strip().lower()
    if env in _TRUTHY:
        return True
    app_cfg = cfg or get_config()
    studio = getattr(app_cfg, "studio", None)
    if studio is None:
        return False
    return getattr(studio, "ai_surface_enabled", False) is True


def resolve_ready_provider(*, cfg: AppConfig | None = None) -> str:
    """Return resolved provider when probe succeeds; else ``stub`` (no environ inject)."""
    ready, provider = _probe_provider_and_ready(cfg=cfg, inject_environ=False)
    if not ready or provider == "stub":
        return "stub"
    return provider


def resolve_llm_ready_summary(*, cfg: AppConfig | None = None) -> dict[str, object]:
    """Build ``algoV3.llm`` Ready accounting (no Import side effects)."""
    app_cfg = cfg or get_config()
    capability = normalize_tri_state(getattr(app_cfg.llm, "capability", "auto"), default="auto")
    prefer = bool(getattr(app_cfg.llm, "prefer_llm_when_ready", False))
    probe_ready = probe_llm_ready(cfg=app_cfg)
    allowed, degrade = capability_allows(capability, ready=probe_ready)
    may_call = resolve_llm_may_call(cfg=app_cfg)
    used_on_import = bool(prefer and allowed and may_call)
    if not getattr(app_cfg.narrative, "decor_line_llm_enabled", False):
        decor = "off"
    elif not may_call:
        decor = "skipped_may_call"
    elif not allowed:
        decor = "skipped_no_key"
    else:
        # Flag on but call-site still gates; summary is not "applied".
        decor = "off"
    out: dict[str, object] = {
        "capability": capability,
        "preferLlmWhenReady": prefer,
        "ready": bool(allowed),
        "mayCall": may_call,
        "usedOnImport": used_on_import,
        "decorLine": decor,
        "mllm": "off",
    }
    if degrade:
        out["degradeReason"] = degrade
    return out
