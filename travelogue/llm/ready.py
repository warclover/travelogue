"""ALG-V3 · read-only LLM Ready probe (layer-safe; no web/studio imports)."""

from __future__ import annotations

from travelogue.config import AppConfig, get_config
from travelogue.config._common import capability_allows, normalize_tri_state
from travelogue.llm.errors import LlmError


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
        else:
            resolve_llm_runtime(provider, cfg=app_cfg)
        return True, provider
    except LlmError:
        return False, provider


def probe_llm_ready(*, cfg: AppConfig | None = None) -> bool:
    """ALG-V3 · read-only Ready probe (AC-07).

    Does **not** inject secrets into ``os.environ``, does not ping the network,
    and does not mutate global config.
    """
    ready, _provider = _probe_provider_and_ready(cfg=cfg, inject_environ=False)
    return ready


def studio_llm_status(*, cfg: AppConfig | None = None) -> dict[str, object]:
    """Studio status helper. May inject secrets into environ for subsequent calls."""
    ready, provider = _probe_provider_and_ready(cfg=cfg, inject_environ=True)
    return {"llmAvailable": ready, "llmProvider": provider}


def resolve_llm_ready_summary(*, cfg: AppConfig | None = None) -> dict[str, object]:
    """Build ``algoV3.llm`` Ready accounting (no MayCall / no Import side effects)."""
    app_cfg = cfg or get_config()
    capability = normalize_tri_state(getattr(app_cfg.llm, "capability", "auto"), default="auto")
    probe_ready = probe_llm_ready(cfg=app_cfg)
    allowed, degrade = capability_allows(capability, ready=probe_ready)
    out: dict[str, object] = {
        "capability": capability,
        "ready": bool(allowed),
        "mayCall": False,  # NAS default; W1a-2 / AIR may open
        "usedOnImport": False,
        "decorLine": "off",
        "mllm": "off",
    }
    if degrade:
        out["degradeReason"] = degrade
    return out
