"""Studio config GET/PATCH and native folder picker."""

from __future__ import annotations

import sys
from pathlib import Path

from travelogue.config import load_config, patch_config_file, studio_config_expose
from travelogue.web.studio_auth import is_loopback_host
from travelogue.web.studio_errors import client_error_payload, user_message
from travelogue.web.studio_handlers.common import studio_ctx
from travelogue.web.studio_handlers.protocols import StudioHandlerProtocol


def studio_capabilities(*, client_host: str = "") -> dict[str, bool]:
    """Expose client-side feature gates (not UA sniffing on the browser)."""
    import os

    from travelogue.export.longshot import playwright_longshot_available
    from travelogue.paths import is_frozen

    host = (client_host or "").strip()
    pick_folder = sys.platform == "win32" and (not host or is_loopback_host(host))
    # OQ-SAS-02 · 正式包（frozen）默认隐藏 AI 运维台；内测可用 TRAVELOGUE_AI_OPS=1
    ai_ops_env = os.environ.get("TRAVELOGUE_AI_OPS", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )
    return {
        "pickFolder": pick_folder,
        "longshotServer": playwright_longshot_available(),
        "longshotClientFallback": True,
        "desktopExit": bool(is_frozen()),
        "aiOpsAdminEnabled": bool(ai_ops_env or not is_frozen()),
    }

def _project_config_body(
    cfg,
    *,
    client_host: str = "",
    include_pipeline_estimates: bool = False,
) -> dict:
    """Build GET/PATCH config body; NAS off strips LLM/path projection (D-NAS-17b)."""
    from travelogue.web.ai_surface import resolve_ai_surface_enabled
    from travelogue.web.studio_narrate import studio_llm_status
    from travelogue.web.studio_stages import pipeline_estimate_tiers

    enabled = resolve_ai_surface_enabled(cfg)
    caps = studio_capabilities(client_host=client_host)
    body: dict = {
        "ok": True,
        "aiSurfaceEnabled": enabled,
        **studio_config_expose(cfg),
        "capabilities": caps,
        # SAS · OQ-SAS-02 convenience projection (also under capabilities)
        "aiOpsAdminEnabled": bool(caps.get("aiOpsAdminEnabled")),
    }
    if include_pipeline_estimates:
        body["pipelineEstimates"] = pipeline_estimate_tiers()
    if enabled:
        body.update(studio_llm_status(cfg=cfg))
        return body
    # D-QFX-04b / D-NAS-17b：off 时不得暴露 LLM 与 tripsDir
    body.pop("tripsDir", None)
    for key in ("llmAvailable", "llmProvider"):
        body.pop(key, None)
    return body


def handle_config(handler: StudioHandlerProtocol) -> None:
    if handler.command == "PATCH":
        payload = handler._read_json_body()
        if not payload:
            handler._json_response(400, {"ok": False, "error": "empty body"})
            return
        target = handler.studio_config_path or (Path.cwd() / "config.yaml")
        try:
            patch_config_file(target, payload)
        except (ValueError, TypeError) as exc:
            handler._json_response(400, client_error_payload(exc))
            return
        except (OSError, PermissionError):
            handler._json_response(
                500,
                {
                    "ok": False,
                    "error": "E_STUDIO_CONFIG_WRITE",
                    "message": user_message("E_STUDIO_CONFIG_WRITE"),
                },
            )
            return
        cfg = load_config(target if target.is_file() else None)
        client_host = handler.client_address[0] if handler.client_address else ""
        handler._json_response(
            200,
            _project_config_body(cfg, client_host=client_host),
        )
        return

    ctx = studio_ctx(handler)
    cfg = ctx.cfg
    if handler.studio_config_path and handler.studio_config_path.is_file():
        cfg = load_config(handler.studio_config_path)
    client_host = handler.client_address[0] if handler.client_address else ""
    handler._json_response(
        200,
        _project_config_body(
            cfg,
            client_host=client_host,
            include_pipeline_estimates=True,
        ),
    )


def handle_pick_folder(handler: StudioHandlerProtocol) -> None:
    client_host = handler.client_address[0] if handler.client_address else ""
    if not is_loopback_host(client_host):
        handler._json_response(
            403,
            {
                "ok": False,
                "error": "E_PICK_FOLDER_DENIED",
                "message": user_message("E_PICK_FOLDER_DENIED"),
            },
        )
        return
    if sys.platform != "win32":
        handler._json_response(
            501,
            {
                "ok": False,
                "error": "E_PICK_FOLDER_UNSUPPORTED",
                "message": user_message("E_PICK_FOLDER_UNSUPPORTED"),
            },
        )
        return
    from travelogue.desktop.folder_picker_service import request_folder

    result = request_folder(title="选择照片文件夹")
    if result.error:
        handler._json_response(
            500,
            {
                "ok": False,
                "error": "E_PICK_FOLDER_FAILED",
                "message": user_message("E_PICK_FOLDER_FAILED"),
                "detail": result.error[:240],
            },
        )
        return
    if result.cancelled or result.path is None:
        handler._json_response(200, {"ok": True, "cancelled": True})
        return
    handler._json_response(200, {"ok": True, "albumPath": str(result.path.resolve())})
