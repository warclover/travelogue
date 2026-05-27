"""Studio API error mapping (Phase 2 M8)."""

from __future__ import annotations

from travelogue.demo.build import DemoError

USER_MESSAGES: dict[str, str] = {
    "E_DEMO_EXISTS": "该游记已存在。是否覆盖？",
    "E_DEMO_NOT_DIR": "所选路径不是文件夹",
    "E_DEMO_TOO_FEW": "至少需要 4 张照片，请换一个文件夹",
    "E_INGEST_EMPTY": "文件夹里没有找到照片",
    "E_INGEST_TOO_FEW": "至少需要 4 张照片，请换一个文件夹",
    "E_STUDIO_JOB_BUSY": "已有导入任务进行中，请稍候",
    "E_STUDIO_UPLOAD_EMPTY": "未收到任何照片文件",
    "E_STUDIO_CANCELLED": "已取消",
}


def user_message(code: str, fallback: str = "") -> str:
    return USER_MESSAGES.get(code, fallback or code)


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
