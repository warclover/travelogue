"""User-scoped LLM settings (Desktop LLM Setup V1 · user_data secrets)."""

from __future__ import annotations

import json
import logging
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from travelogue.util.llm_presets import PROVIDER_PRESETS

_log = logging.getLogger(__name__)

_SECRETS_NAME = "secrets.json"
_USER_CONFIG_NAME = "config.user.yaml"
_ALLOWED_PROVIDERS = frozenset({"deepseek", "dashscope"})


@dataclass(frozen=True)
class UserLlmSecrets:
    provider: str | None = None
    api_key: str | None = None
    model: str | None = None
    base_url: str | None = None
    last_ping_ok: bool | None = None

    @property
    def configured(self) -> bool:
        return bool(self.provider and self.api_key and self.provider in _ALLOWED_PROVIDERS)


def user_data_dir(*, ensure: bool = False) -> Path:
    """Resolve writable user data root (MF-DLLM / D-DLLM-11)."""
    from travelogue.paths import user_data_dir as _paths_user_data_dir

    return _paths_user_data_dir(ensure=ensure)


def secrets_path() -> Path:
    return user_data_dir(ensure=True) / _SECRETS_NAME


def user_config_path() -> Path:
    return user_data_dir(ensure=True) / _USER_CONFIG_NAME


def _atomic_write_text(path: Path, text: str, *, encoding: str = "utf-8") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding=encoding, newline="\n") as fh:
            fh.write(text)
        tmp_path.replace(path)
    except Exception:
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise
    _try_restrict_acl(path)


def _try_restrict_acl(path: Path) -> None:
    """Best-effort: current-user-only ACL on Windows; chmod elsewhere."""
    try:
        if os.name == "nt":
            import subprocess

            user = os.environ.get("USERNAME") or os.environ.get("USER") or ""
            if not user:
                return
            subprocess.run(
                [
                    "icacls",
                    str(path),
                    "/inheritance:r",
                    "/grant:r",
                    f"{user}:(R,W)",
                ],
                check=False,
                capture_output=True,
                timeout=5,
            )
        else:
            os.chmod(path, 0o600)
    except Exception:
        _log.debug("restrict ACL failed for %s", path, exc_info=True)


def read_user_llm_secrets() -> UserLlmSecrets:
    path = user_data_dir(ensure=False) / _SECRETS_NAME
    if not path.is_file():
        return UserLlmSecrets()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        _log.warning("user llm secrets unreadable; treating as empty", exc_info=True)
        return UserLlmSecrets()
    if not isinstance(raw, dict):
        return UserLlmSecrets()
    provider = str(raw.get("provider") or "").strip().lower() or None
    if provider and provider not in _ALLOWED_PROVIDERS:
        provider = None
    api_key = str(raw.get("api_key") or "").strip() or None
    model = str(raw.get("model") or "").strip() or None
    base_url = str(raw.get("base_url") or "").strip() or None
    last_ping = raw.get("last_ping_ok")
    last_ping_ok = bool(last_ping) if isinstance(last_ping, bool) else None
    return UserLlmSecrets(
        provider=provider,
        api_key=api_key,
        model=model,
        base_url=base_url,
        last_ping_ok=last_ping_ok,
    )


def write_user_llm_secrets(secrets: UserLlmSecrets) -> None:
    payload: dict[str, Any] = {
        "provider": secrets.provider,
        "api_key": secrets.api_key,
        "model": secrets.model,
        "base_url": secrets.base_url,
        "last_ping_ok": secrets.last_ping_ok,
    }
    _atomic_write_text(secrets_path(), json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def clear_user_llm_secrets() -> None:
    path = user_data_dir(ensure=False) / _SECRETS_NAME
    if path.is_file():
        try:
            path.unlink()
        except OSError:
            _log.warning("failed to delete llm secrets", exc_info=True)
    cfg_path = user_data_dir(ensure=False) / _USER_CONFIG_NAME
    if cfg_path.is_file():
        try:
            cfg_path.unlink()
        except OSError:
            _log.warning("failed to delete user llm config", exc_info=True)


def write_user_llm_config_overlay(*, provider: str, model: str | None, base_url: str | None) -> None:
    """Write config.user.yaml llm section (no api key)."""
    preset = PROVIDER_PRESETS.get(provider, {})
    lines = [
        "# Travelogue user overlay · do not commit",
        "llm:",
        f"  provider: {provider}",
        f"  model: {model or preset.get('default_model', '')}",
        f"  api_key_env: {preset.get('api_key_env', 'DEEPSEEK_API_KEY')}",
    ]
    if base_url:
        lines.append(f"  base_url: {base_url}")
    lines.append("")
    _atomic_write_text(user_config_path(), "\n".join(lines))


def load_user_llm_config_overlay() -> dict[str, Any]:
    """Return mapping suitable for merging into load_config data."""
    path = user_data_dir(ensure=False) / _USER_CONFIG_NAME
    if not path.is_file():
        return {}
    try:
        from travelogue.config.yaml_loader import load_yaml_mapping

        loaded = load_yaml_mapping(path.read_text(encoding="utf-8"), source=str(path))
    except Exception:
        _log.warning("user config overlay unreadable", exc_info=True)
        return {}
    return loaded if isinstance(loaded, dict) else {}


def inject_secrets_into_environ(secrets: UserLlmSecrets | None = None) -> None:
    """MF-DLLM-03: process-env injection for resolve_llm_runtime."""
    sec = secrets if secrets is not None else read_user_llm_secrets()
    if not sec.configured or not sec.provider or not sec.api_key:
        return
    preset = PROVIDER_PRESETS.get(sec.provider)
    if not preset:
        return
    env_name = preset["api_key_env"]
    os.environ[env_name] = sec.api_key


def mask_api_key(api_key: str | None) -> str | None:
    if not api_key:
        return None
    key = api_key.strip()
    if len(key) <= 8:
        return "***"
    return f"{key[:3]}***{key[-4:]}"


def readiness_state(secrets: UserLlmSecrets | None = None) -> str:
    """未配置 | 已保存未验证 | 已就绪 | 连接失败"""
    sec = secrets if secrets is not None else read_user_llm_secrets()
    if not sec.configured:
        return "未配置"
    if sec.last_ping_ok is True:
        return "已就绪"
    if sec.last_ping_ok is False:
        return "连接失败"
    return "已保存未验证"
