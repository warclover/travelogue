"""字形 OCR 回读校验 (PRD D-CAL-19)。

复用现有 ``travelogue.llm.client.vision_chat_completion``（OpenAI 兼容多模态
接口，DashScope 已支持），把视觉语言模型当"OCR"角色：要求模型只回读画面中
出现的汉字，与期望文本严格比对（去空白后完全一致才算通过）。

任何调用异常/解析失败/模型判定不一致 → 返回 ``False``（不向上抛异常）；
调用方把 ``False`` 当作路线 C 门槛未过，按 D-CAL-16 fallback 到路线 B。
"""

from __future__ import annotations

import base64
import io
import logging

from PIL import Image

from travelogue.llm.client import LlmRuntime, parse_json_content, vision_chat_completion
from travelogue.util.llm_presets import DASHSCOPE_OCR_DEFAULT, dashscope_ocr_candidates

_log = logging.getLogger(__name__)

_OCR_MODEL_DEFAULT = DASHSCOPE_OCR_DEFAULT


def _image_to_data_url(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=90)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/jpeg;base64,{b64}"


def ocr_verify(
    img: Image.Image,
    expected_text: str,
    *,
    runtime: LlmRuntime | None = None,
    model: str | None = None,
) -> bool:
    expected = "".join(expected_text.split())
    if not expected:
        return False
    try:
        data_url = _image_to_data_url(img)
        messages = [
            {
                "role": "system",
                "content": (
                    "你是严格的书法文字校验器。只输出 JSON，格式："
                    '{"recognized": "画面中识别到的汉字（按从上到下、从左到右顺序，'
                    '不含印章/水印/其他装饰文字）", "match": true 或 false}。'
                    "match 表示 recognized 是否与用户给出的期望文字完全一致（不含空白）。"
                ),
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"期望文字：{expected}"},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            },
        ]
        content = None
        last_err: Exception | None = None
        for cand in dashscope_ocr_candidates(model or _OCR_MODEL_DEFAULT):
            try:
                content = vision_chat_completion(
                    messages,
                    provider="dashscope",
                    model=cand,
                    runtime=runtime,
                    temperature=0.0,
                )
                break
            except Exception as exc:  # noqa: BLE001 — try next OCR model
                last_err = exc
                _log.info("title_art OCR model %s failed: %s", cand, exc)
                continue
        if content is None:
            if last_err is not None:
                raise last_err
            return False
        data = parse_json_content(content)
        recognized = "".join(str(data.get("recognized") or "").split())
        matched = bool(data.get("match")) and recognized == expected
        if not matched:
            _log.info(
                "title_art OCR verify mismatch: expected=%r recognized=%r",
                expected,
                recognized,
            )
        return matched
    except Exception:  # noqa: BLE001 — OCR 校验失败即判负，不阻断主流程
        _log.exception("title_art OCR verify call failed")
        return False
