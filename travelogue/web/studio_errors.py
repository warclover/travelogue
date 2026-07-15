"""Studio API error mapping (Phase 2 M8)."""

from __future__ import annotations

from travelogue.demo.build import DemoError
from travelogue.errors import CodeError

USER_MESSAGES: dict[str, str] = {
    "E_DEMO_EXISTS": "该游记已存在。是否覆盖？",
    "E_DEMO_NOT_DIR": "所选路径不是文件夹",
    "E_DEMO_TOO_FEW": "至少需要 4 张照片，请换一个文件夹",
    "E_INGEST_EMPTY": "文件夹里没有找到照片",
    "E_INGEST_TOO_FEW": "至少需要 4 张照片，请换一个文件夹",
    "E_STUDIO_JOB_BUSY": "排队中，请稍候",
    "E_STUDIO_UPLOAD_EMPTY": "未收到任何照片文件",
    "E_STUDIO_CANCELLED": "已取消",
    "E_STUDIO_PIPELINE": "导入失败，请重试",
    "E_STUDIO_AUTH": "Studio 请求未授权",
    "E_STUDIO_BODY_TOO_LARGE": "请求体过大",
    "E_STUDIO_ALBUM_DENIED": "不允许从该路径导入",
    "E_STUDIO_REVEAL_DENIED": "无法打开该文件",
    "E_PICK_FOLDER_UNSUPPORTED": "当前环境不支持原生选文件夹，请改用路径导入或浏览器上传",
    "E_PICK_FOLDER_DENIED": "仅允许本机访问选文件夹",
    "E_PICK_FOLDER_FAILED": "无法打开本机文件夹选择器，请粘贴路径或安装 pip install -e \".[desktop]\"",
    "E_STUDIO_CONFIG_WRITE": "无法写入 config.yaml，请检查文件权限",
    "E_LNG_CAPTURE_FAILED": "长图生成失败，请重试",
    "E_LNG_NO_LONGSHOT": "未找到长图页面，请先完成渲染",
    "E_LNG_PLAYWRIGHT": "无法生成长图，请安装 Playwright",
    "E_LLM_AUTH": "要生成杂志感文案，请先在设置中配置写作引擎",
    "E_LLM_NETWORK": "文案生成时网络中断，请重试",
    "E_LLM_PROVIDER": "请选择支持的写作引擎服务商",
    "E_LLM_PING": "连接测试失败，请检查 Key 或稍后重试",
    "E_LLM_STUB": "当前为本机文案模式",
    "E_NARRATE_API": "文案生成失败，请重试",
    "E_TRIP_NOT_FOUND": "游记不存在",
    "E_TRIP_CONFLICT": "内容已被其他操作更新，请刷新",
    "E_EXPORT_PRIVACY": "导出 zip 需要确认隐私设置",
    "E_SERVER": "服务内部错误，请稍后重试",
    "E_STUDIO_RERENDER": "预览重新渲染失败，请稍后重试",
}

# Codes with a fixed user-facing line — do not append raw exception text.
_PLAIN_ONLY_CODES = frozenset(
    {
        "E_LLM_NETWORK",
        "E_LLM_AUTH",
        "E_LLM_PROVIDER",
        "E_LLM_PING",
        "E_SERVER",
        "E_STUDIO_PIPELINE",
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

                payload["existingTripId"] = Path(trip_dir).name
    return payload
