"""Studio API error mapping (Phase 2 M8)."""

from __future__ import annotations

from travelogue.demo.build import DemoError
from travelogue.errors import CodeError

USER_MESSAGES: dict[str, str] = {
    "E_DEMO_EXISTS": "该画册已存在。是否覆盖？",
    "E_DEMO_NOT_DIR": "所选路径不是文件夹",
    "E_DEMO_TOO_FEW": "至少需要 4 张照片，请换一个文件夹",
    "E_INGEST_EMPTY": "文件夹里没有找到照片",
    "E_INGEST_TOO_FEW": "至少需要 4 张照片，请换一个文件夹",
    "E_STUDIO_JOB_BUSY": "排队中，请稍候",
    "E_STUDIO_UPLOAD_EMPTY": "未收到任何照片文件",
    "E_STUDIO_CANCELLED": "已取消",
    "E_STUDIO_PIPELINE": "导入失败，请重试",
    "E_TRIP_SAVE_BUSY": "画册文件正被占用，请关闭预览/资源管理器后重试",
    "E_STUDIO_AUTH": "Studio 请求未授权",
    "E_STUDIO_PATH": "路径不在允许范围内",
    "E_STUDIO_BAD_BODY": "请求体无效",
    "E_STUDIO_BODY_TOO_LARGE": "请求体过大",
    "E_STUDIO_ALBUM_DENIED": "不允许从该路径导入",
    "E_STUDIO_REVEAL_DENIED": "无法打开该文件",
    "E_PICK_FOLDER_UNSUPPORTED": "当前环境不支持原生选文件夹，请改用路径导入或浏览器上传",
    "E_PICK_FOLDER_DENIED": "仅允许本机访问选文件夹",
    "E_PICK_FOLDER_FAILED": "无法打开本机文件夹选择器，请改用粘贴路径或浏览器上传",
    "E_STUDIO_CONFIG_WRITE": "无法写入 config.yaml，请检查文件权限",
    "E_LNG_CAPTURE_FAILED": "长图生成失败，请重试",
    "E_LNG_NO_LONGSHOT": "未找到长图页面，请先完成渲染",
    "E_LNG_PLAYWRIGHT": "高清长图组件不可用，将尝试兼容模式",
    "E_LNG_CLIENT_FALLBACK": "正在使用兼容模式保存长图…",
    "E_STUDIO_SHUTDOWN": "Studio 正在退出",
    # NAS · 默认面中性（暗门恢复后仍可走 E_LLM_* 配置面专用句）
    "E_AI_SURFACE_DISABLED": "当前版本不可用",
    # BE-09 / COPY-L0G-09 · 默认面去配置引导（NAS FE-NAS-07）
    "E_LLM_AUTH": "检查文件夹是否仍可访问、照片是否足够，然后点「重试」或换文件夹再试。",
    "E_LLM_NETWORK": "文案生成时网络中断，请重试",
    "E_LLM_PROVIDER": "当前不可用，请稍后重试",
    "E_LLM_PING": "连接测试失败，请稍后重试",
    "E_LLM_STUB": "当前为本机文案模式",
    "E_LLM_ENDPOINT": "当前地域与 Key 不匹配。请改选中国站/国际站，或检查自定义 API 地址。",
    "E_LLM_MODEL": "模型不可用。请改选列表中的模型，或在高级中填写控制台可见的模型名。",
    "E_LLM_QUOTA": "余额或配额不足。请到服务商控制台充值，或检查是否开启了「仅使用免费额度」。",
    "E_LLM_QUOTA_FREE_TIER": "免费额度已用尽（Key 本身有效）。请到通义百炼控制台关闭「仅使用免费额度」，或充值后再试。",
    "E_LLM_RATE": "服务商繁忙，请稍后重试。",
    "E_LLM_BASE_URL": "自定义 API 地址仅支持公网 https（不可用 localhost / 内网）。",
    "E_LLM_TIMEOUT": "无法连接服务商。请检查网络后重试。",
    "E_LLM_CONNECT": "无法连接服务商。请检查网络后重试。",
    "E_NARRATE_API": "文案生成失败，请重试",
    "E_TRIP_NOT_FOUND": "画册不存在",
    "E_TRIP_CONFLICT": "内容已被其他操作更新，请刷新",
    "E_EXPORT_PRIVACY": "导出 zip 需要确认隐私设置",
    "E_SERVER": "服务内部错误，请稍后重试",
    "E_STUDIO_RERENDER": "预览重新渲染失败，请稍后重试",
    # PRD-MEDIA-REFERENCE-STORAGE-V1
    "E_MEDIA_SOURCE_MISSING": "原相册无法访问，请重新指定目录",
    "E_MEDIA_REMOUNT_MISMATCH": "所选目录与作品照片对不上",
    "E_MEDIA_CONTENT_CHANGED": "照片内容已变化，无法自动关联",
    "E_MEDIA_CLEANUP_REFUSED": "无法安全删除源文件拷贝",
    "E_MEDIA_CLEANUP_PARTIAL": "清理未完成，查看详情",
    "E_MEDIA_INCREMENTAL_SOURCE": "追加导入缺少可访问的原片",
    "E_PORTFOLIO_UNAVAILABLE": "作品集暂时排不出，可改回游记",
    "E_CLG_NEEDS_JOURNAL": "长图要在游记里做",
}

# Codes with a fixed user-facing line — do not append raw exception text.
_PLAIN_ONLY_CODES = frozenset(
    {
        "E_AI_SURFACE_DISABLED",
        "E_LLM_NETWORK",
        "E_LLM_AUTH",
        "E_LLM_PROVIDER",
        "E_LLM_PING",
        "E_LLM_ENDPOINT",
        "E_LLM_MODEL",
        "E_LLM_QUOTA",
        "E_LLM_QUOTA_FREE_TIER",
        "E_LLM_RATE",
        "E_LLM_BASE_URL",
        "E_LLM_TIMEOUT",
        "E_LLM_CONNECT",
        "E_SERVER",
        "E_STUDIO_PIPELINE",
        "E_TRIP_SAVE_BUSY",
        "E_STUDIO_AUTH",
        "E_STUDIO_ALBUM_DENIED",
        "E_STUDIO_REVEAL_DENIED",
        "E_LNG_CAPTURE_FAILED",
        "E_LNG_PLAYWRIGHT",
        "E_NARRATE_API",
        "E_PICK_FOLDER_FAILED",
        "E_STUDIO_CONFIG_WRITE",
        "E_STUDIO_RERENDER",
        "E_TRIP_CONFLICT",
        "E_TRIP_NOT_FOUND",
        "E_PORTFOLIO_UNAVAILABLE",
    }
)


def internal_error_payload() -> dict[str, str | bool]:
    """JSON body for unexpected server failures (no exception text leaked)."""
    return {
        "ok": False,
        "error": "E_SERVER",
        "message": user_message("E_SERVER"),
    }


def client_error_payload(
    exc: Exception,
    *,
    default_code: str = "E_BAD_REQUEST",
) -> dict[str, str | bool]:
    """Map a client-facing exception to a stable error code + user message."""
    if isinstance(exc, CodeError):
        return {
            "ok": False,
            "error": exc.code,
            "message": user_message(exc.code, exc.message),
        }
    if isinstance(exc, DemoError):
        body = demo_error_payload(exc)
        body["ok"] = False
        return body
    text = str(exc).strip()
    code = default_code
    if text.startswith("E_"):
        candidate = text.split(":", 1)[0].strip()
        if candidate and " " not in candidate:
            code = candidate
    return {"ok": False, "error": code, "message": user_message(code, text)}


def user_message(code: str, fallback: str = "") -> str:
    text = USER_MESSAGES.get(code, fallback or code)
    if fallback and code not in USER_MESSAGES:
        detail = str(fallback).split(": ", 1)[-1]
        if detail and detail != text:
            return detail
    if code in USER_MESSAGES and fallback and code not in _PLAIN_ONLY_CODES:
        detail = str(fallback).split(": ", 1)[-1]
        if detail and detail not in text and len(detail) < 120:
            return f"{text}（{detail}）"
    return text


def demo_error_payload(exc: DemoError) -> dict:
    payload: dict = {
        "error": exc.code,
        "message": user_message(exc.code, str(exc)),
    }
    if exc.code == "E_DEMO_EXISTS":
        text = str(exc)
        if "trip already exists:" in text:
            trip_dir = text.split("trip already exists:", 1)[1].split("(", 1)[0].strip()
            if trip_dir:
                from pathlib import Path

                from travelogue.web.studio_pipeline import _trip_collision_meta

                path = Path(trip_dir)
                payload["existingTripId"] = path.name
                meta = _trip_collision_meta(path, path.name)
                payload["existingTitle"] = meta.get("title") or path.name
                payload["existingEdition"] = meta.get("edition") or "journal"
    if is_llm_auth_recoverable(exc.code):
        payload["recoverableWithStub"] = True
    return payload


def is_llm_auth_recoverable(code: str | None) -> bool:
    """Import may still surface E_LLM_AUTH on legacy/edge paths — FE can continue with stub."""
    return code == "E_LLM_AUTH"


def job_error_payload(code: str, *, detail: str = "") -> dict[str, object]:
    """Build a Studio job ``error`` object; mark LLM auth as stub-recoverable (BE-06)."""
    payload: dict[str, object] = {
        "code": code,
        "message": user_message(code, detail),
    }
    if is_llm_auth_recoverable(code):
        payload["recoverableWithStub"] = True
    return payload
