"""Calligraphy Style Registry (PRD §5.5.1 · 路线 C 候选).

固定提示词模板；新增/改动须过轻量评审（几张样图 + 小样本人审），运行时
只允许替换 ``{{title}}`` / ``{{subtitle}}`` 两个占位符（D-CAL-15：禁止拼接
用户自由文本进 prompt 主体）。

文案系参考用户提供样本（已归档
``docs/acceptance-records/attachments/cover-calligraphy-title-route-c-refs-2026-08-07/``）
后原创改写的风格描述，不照抄参考图内嵌"口令"文案（§9 · Prompt 模板版权）。
五款均固定生成"白底/宣纸底 + 纯黑墨迹"（无印章、无边框、无其它文字或
装饰），便于 Route C 后处理阶段统一抠字重上色（D-CAL-17）与叠加自制印章
（D-CAL-12，与路线 B 共用同一枚印章渲染逻辑）。

``prompt_version``：
- ``v1`` — W0.5 Spike 基线模板（2026-08-08，OCR 57.7%）
- ``v2`` — W0.5b 冲质量：强化逐字准确 / 禁增删 / 标点保留 / 可辨识笔画
  （默认用于新生成；v1 仅保留对照与回滚）
"""

from __future__ import annotations

from dataclasses import dataclass, replace

_NEGATIVE_PROMPT_V1 = "印章,图章,红色装饰,边框,多余文字,水印,插画,卡通,人物,风景"
_NEGATIVE_PROMPT_V2 = (
    "印章,图章,红色装饰,边框,多余文字,水印,插画,卡通,人物,风景,"
    "错字,别字,形近字替换,增字,缺字,多出来的汉字,漏字,乱码,"
    "难以辨认的连笔,糊字,看不清的笔画"
)

_GLYPH_ACCURACY_V2 = (
    "文字内容必须与给定标题逐字完全一致，禁止增字、缺字、改字或形近替换；"
    "标题中的标点与拉丁字母必须原样保留；笔画清晰可辨，避免过度连笔导致字形糊成他字；"
)


@dataclass(frozen=True)
class CalligraphyStyle:
    style_id: str
    label: str
    prompt_template: str
    negative_prompt: str = _NEGATIVE_PROMPT_V1
    aspect_ratio: str = "4:3"
    ref_image: str = ""
    prompt_version: str = "v1"


_STYLE_SPECS: tuple[tuple[str, str, str, str], ...] = (
    (
        "cascade-seal",
        "错落双行·收尾拖尾",
        (
            "中文毛笔书法特写，纯黑浓墨手写{{title}}，字形上下错落、大小对比强烈，"
            "行笔洒脱，收尾笔画多做舒展拖尾处理；宣纸质感白底，留白疏朗；"
            "无印章、无边框、无任何其他文字或装饰元素；"
            "高清微距摄影呈现笔锋细节与纸面肌理。"
        ),
        "ref-01-cascade-seal.png",
    ),
    (
        "flowing-brush",
        "洒脱飘逸·飞白毛边",
        (
            "中文毛笔书法特写，纯黑墨迹手写{{title}}，运笔洒脱飘逸、顿挫分明，"
            "长笔画带自然飞白与毛边肌理，墨色浓淡干湿变化丰富；白色宣纸底，"
            "无印章、无边框、无任何其他文字或装饰元素；高清微距摄影呈现笔锋与纸面细节。"
        ),
        "ref-02-flowing-brush.png",
    ),
    (
        "loose-running-script",
        "松弛行楷·细腻锐利",
        (
            "中文毛笔手写艺术字特写，行楷结合、随性洒脱的行书风格，"
            "纯黑墨迹手写{{title}}，笔触细腻清晰锐利，边缘带自然毛边粗糙感，"
            "干笔与润笔质感兼具；纯白背景，无印章、无边框、无任何其他文字或装饰元素；"
            "居中排布，疏密节奏自然。"
        ),
        "ref-03-loose-running-script.png",
    ),
    (
        "bold-vigorous",
        "大气刚劲·浓墨对比",
        (
            "中文毛笔书法特写，大气刚劲的行书风格，纯黑浓墨手写{{title}}，"
            "笔锋凌厉锐利，起收笔顿挫分明，笔画粗细对比强烈，长撇捺舒展飘逸；"
            "浅米白宣纸底色，无印章、无边框、无任何其他文字或装饰元素；"
            "居中排布，字距疏密均衡，整体气质清冽雅致。"
        ),
        "ref-04-bold-vigorous.png",
    ),
    (
        "casual-handwritten",
        "随性连笔·生活手写",
        (
            "中文软头笔手写艺术字特写，随性洒脱的行书风格，纯黑墨迹手写{{title}}，"
            "笔触松弛自然，笔画粗细有起伏、连笔流畅，不刻板、偏生活化的随笔手写质感；"
            "纯白背景，无印章、无边框、无任何其他文字或装饰元素；笔锋边缘清晰自然。"
        ),
        "ref-05-casual-handwritten.png",
    ),
)


def _v2_template(v1_template: str) -> str:
    # 把准确性约束插在风格描述之后、收尾摄影句之前；仍只含 {{title}} 占位。
    if "；高清" in v1_template:
        head, tail = v1_template.split("；高清", 1)
        return f"{head}；{_GLYPH_ACCURACY_V2}高清{tail}"
    if "；居中排布" in v1_template:
        head, tail = v1_template.split("；居中排布", 1)
        return f"{head}；{_GLYPH_ACCURACY_V2}居中排布{tail}"
    if "；笔锋边缘" in v1_template:
        head, tail = v1_template.split("；笔锋边缘", 1)
        return f"{head}；{_GLYPH_ACCURACY_V2}笔锋边缘{tail}"
    return f"{v1_template}{_GLYPH_ACCURACY_V2}"


STYLE_REGISTRY: tuple[CalligraphyStyle, ...] = tuple(
    CalligraphyStyle(
        style_id=sid,
        label=label,
        prompt_template=tmpl,
        negative_prompt=_NEGATIVE_PROMPT_V1,
        ref_image=ref,
        prompt_version="v1",
    )
    for sid, label, tmpl, ref in _STYLE_SPECS
)

_BY_ID: dict[str, CalligraphyStyle] = {s.style_id: s for s in STYLE_REGISTRY}


def get_style(style_id: str, *, prompt_version: str = "v2") -> CalligraphyStyle | None:
    """按 style_id 取模板；默认 ``v2``（冲质量后的生产候选）。

    ``prompt_version="v1"`` 保留 W0.5 基线以便 Spike 对照。
    """
    base = _BY_ID.get(style_id)
    if base is None:
        return None
    version = (prompt_version or "v2").strip().lower() or "v2"
    if version == "v1":
        return base
    if version != "v2":
        return None
    return replace(
        base,
        prompt_template=_v2_template(base.prompt_template),
        negative_prompt=_NEGATIVE_PROMPT_V2,
        prompt_version="v2",
    )


def list_styles(*, prompt_version: str = "v2") -> tuple[CalligraphyStyle, ...]:
    styles = [get_style(s.style_id, prompt_version=prompt_version) for s in STYLE_REGISTRY]
    return tuple(s for s in styles if s is not None)


def default_style_id() -> str:
    return STYLE_REGISTRY[0].style_id


def render_prompt(style: CalligraphyStyle, *, title: str, subtitle: str | None = None) -> str:
    """替换固定模板中的 ``{{title}}``/``{{subtitle}}`` 占位符（D-CAL-15）。"""
    text = style.prompt_template.replace("{{title}}", title)
    if "{{subtitle}}" in text:
        text = text.replace("{{subtitle}}", subtitle or "")
    return text
