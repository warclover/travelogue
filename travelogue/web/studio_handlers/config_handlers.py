"""Studio config GET/PATCH and native folder picker."""

from __future__ import annotations

import sys
from pathlib import Path

from travelogue.config import load_config, patch_config_file, studio_config_expose
from travelogue.web.studio_auth import is_loopback_host
from travelogue.web.studio_errors import user_message
from travelogue.web.studio_handlers.common import studio_ctx
from travelogue.web.studio_handlers.protocols import StudioHandlerProtocol


def studio_capabilities(*, client_host: str = "") -> dict[str, bool]:
    """Expose client-side feature gates (not UA sniffing on the browser)."""
    host = (client_host or "").strip()
    pick_folder = sys.platform == "win32" and (not host or is_loopback_host(host))
    return {"pickFolder": pick_folder}

def handle_config(handler: StudioHandlerProtocol) -> None:
    from travelogue.web.studio_narrate import studio_llm_status
    from travelogue.web.studio_stages import pipeline_estimate_tiers

    if handler.command == "PATCH":
        payload = handler._read_json_body()
        if not payload:
            handler._json_response(400, {"ok": False, "error": "empty body"})
            return
        target = handler.studio_config_path or (Path.cwd() / "config.yaml")
        try:
            patch_config_file(target, payload)
        except (ValueError, TypeError) as exc:
            handler._json_response(400, {"ok": False, "error": str(exc)})
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
        body = {
            "ok": True,
            **studio_config_expose(cfg),
            **studio_llm_status(cfg=cfg),
            "capabilities": studio_capabilities(
                client_host=handler.client_address[0] if handler.client_address else ""
            ),
        }
        handler._json_response(200, body)
        return

    ctx = studio_ctx(handler)
    cfg = ctx.cfg
    if handler.studio_config_path and handler.studio_config_path.is_file():
        cfg = load_config(handler.studio_config_path)
    status = studio_llm_status(cfg=cfg)
    client_host = handler.client_address[0] if handler.client_address else ""
    handler._json_response(
        200,
        {
            "ok": True,
            **studio_config_expose(cfg),
            **status,
            "pipelineEstimates": pipeline_estimate_tiers(),
            "capabilities": studio_capabilities(client_host=client_host),
        },
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
