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
"""

from __future__ import annotations

from dataclasses import dataclass

_NEGATIVE_PROMPT_COMMON = "印章,图章,红色装饰,边框,多余文字,水印,插画,卡通,人物,风景"


@dataclass(frozen=True)
class CalligraphyStyle:
    style_id: str
    label: str
    prompt_template: str
    negative_prompt: str = _NEGATIVE_PROMPT_COMMON
    aspect_ratio: str = "4:3"
    ref_image: str = ""
    prompt_version: str = "v1"


STYLE_REGISTRY: tuple[CalligraphyStyle, ...] = (
    CalligraphyStyle(
        style_id="cascade-seal",
        label="错落双行·收尾拖尾",
        prompt_template=(
            "中文毛笔书法特写，纯黑浓墨手写{{title}}，字形上下错落、大小对比强烈，"
            "行笔洒脱，收尾笔画多做舒展拖尾处理；宣纸质感白底，留白疏朗；"
            "无印章、无边框、无任何其他文字或装饰元素；"
            "高清微距摄影呈现笔锋细节与纸面肌理。"
        ),
        ref_image="ref-01-cascade-seal.png",
    ),
    CalligraphyStyle(
        style_id="flowing-brush",
        label="洒脱飘逸·飞白毛边",
        prompt_template=(
            "中文毛笔书法特写，纯黑墨迹手写{{title}}，运笔洒脱飘逸、顿挫分明，"
            "长笔画带自然飞白与毛边肌理，墨色浓淡干湿变化丰富；白色宣纸底，"
            "无印章、无边框、无任何其他文字或装饰元素；高清微距摄影呈现笔锋与纸面细节。"
        ),
        ref_image="ref-02-flowing-brush.png",
    ),
    CalligraphyStyle(
        style_id="loose-running-script",
        label="松弛行楷·细腻锐利",
        prompt_template=(
            "中文毛笔手写艺术字特写，行楷结合、随性洒脱的行书风格，"
            "纯黑墨迹手写{{title}}，笔触细腻清晰锐利，边缘带自然毛边粗糙感，"
            "干笔与润笔质感兼具；纯白背景，无印章、无边框、无任何其他文字或装饰元素；"
            "居中排布，疏密节奏自然。"
        ),
        ref_image="ref-03-loose-running-script.png",
    ),
    CalligraphyStyle(
        style_id="bold-vigorous",
        label="大气刚劲·浓墨对比",
        prompt_template=(
            "中文毛笔书法特写，大气刚劲的行书风格，纯黑浓墨手写{{title}}，"
            "笔锋凌厉锐利，起收笔顿挫分明，笔画粗细对比强烈，长撇捺舒展飘逸；"
            "浅米白宣纸底色，无印章、无边框、无任何其他文字或装饰元素；"
            "居中排布，字距疏密均衡，整体气质清冽雅致。"
        ),
        ref_image="ref-04-bold-vigorous.png",
    ),
    CalligraphyStyle(
        style_id="casual-handwritten",
        label="随性连笔·生活手写",
        prompt_template=(
            "中文软头笔手写艺术字特写，随性洒脱的行书风格，纯黑墨迹手写{{title}}，"
            "笔触松弛自然，笔画粗细有起伏、连笔流畅，不刻板、偏生活化的随笔手写质感；"
            "纯白背景，无印章、无边框、无任何其他文字或装饰元素；笔锋边缘清晰自然。"
        ),
        ref_image="ref-05-casual-handwritten.png",
    ),
)

_BY_ID: dict[str, CalligraphyStyle] = {s.style_id: s for s in STYLE_REGISTRY}


def get_style(style_id: str) -> CalligraphyStyle | None:
    return _BY_ID.get(style_id)


def list_styles() -> tuple[CalligraphyStyle, ...]:
    return STYLE_REGISTRY


def default_style_id() -> str:
    return STYLE_REGISTRY[0].style_id


def render_prompt(style: CalligraphyStyle, *, title: str, subtitle: str | None = None) -> str:
    """替换固定模板中的 ``{{title}}``/``{{subtitle}}`` 占位符（D-CAL-15）。"""
    text = style.prompt_template.replace("{{title}}", title)
    if "{{subtitle}}" in text:
        text = text.replace("{{subtitle}}", subtitle or "")
    return text
