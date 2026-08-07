"""Font candidate pool for the clean pipeline (PRD §5.3 · D-CAL-07)."""

from __future__ import annotations

from dataclasses import dataclass

from PIL import ImageFont

FALLBACK_STACK: tuple[str, ...] = (
    "msyh.ttc",
    "msyhbd.ttc",
    "simhei.ttf",
    "NotoSerifSC-Regular.otf",
)


@dataclass(frozen=True)
class FontCandidate:
    name: str
    filename: str
    licensed: bool  # 商用授权核查通过（D-CAL-07）


#: §5.3 字库候选池。未核查授权的字体 ``licensed=False``，不得进生产默认。
FONT_POOL: tuple[FontCandidate, ...] = (
    FontCandidate(name="ZhiMangXing-Regular", filename="ZhiMangXing-Regular.ttf", licensed=True),
    FontCandidate(name="Aa剑豪体", filename="Aa剑豪体.ttf", licensed=False),
    FontCandidate(name="鸿雷板书简体-测试版", filename="鸿雷板书简体-测试版.ttf", licensed=False),
)


def licensed_fonts() -> tuple[FontCandidate, ...]:
    return tuple(f for f in FONT_POOL if f.licensed)


def pick_default_font() -> FontCandidate:
    """First licensed pool entry; raises if the pool is empty (D-CAL-07 门禁)."""
    pool = licensed_fonts()
    if not pool:
        raise RuntimeError("E_CAL_NO_LICENSED_FONT: no licensed font in pool")
    return pool[0]


def load_truetype(
    font: FontCandidate, size: int
) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Backward-compatible wrapper; discards the "which font actually loaded"
    detail. Prefer :func:`load_truetype_named` when that detail matters
    (e.g. reporting §8 ``font`` accurately instead of the requested name)."""
    return load_truetype_named(font, size)[0]


def load_truetype_named(
    font: FontCandidate, size: int
) -> tuple[ImageFont.FreeTypeFont | ImageFont.ImageFont, str]:
    """Try the named font file, then the CJK fallback stack, then Pillow default.

    Dev/CI machines may not have the licensed font file installed as a system
    font; falling back keeps rendering possible (degrades to a generic CJK
    face rather than failing outright — same safety-net spirit as
    ``travelogue.export.card_bookends._load_font``). Returns the *actually
    loaded* font name alongside the font object, so callers can report which
    face rendered the text instead of the originally requested candidate.
    """
    for name in (font.filename, *FALLBACK_STACK):
        try:
            return ImageFont.truetype(name, size=size), name
        except OSError:
            continue
    return ImageFont.load_default(), "pillow-default"


def glyphs_covered(font_candidates: tuple[str, ...], text: str) -> bool:
    """§4 字形覆盖检查（近似实现）。

    尝试加载候选字体列表中第一个可用的字体，逐字检查 ``getmask`` 是否非空。
    一个字体文件都加载不了（dev/CI 环境缺少 CJK 字体）时，视为不可渲染中文，
    直接判定未覆盖 → 调用方 fail-open，避免输出乱码/缺字方块。
    """
    if not text:
        return True
    for name in font_candidates:
        try:
            face = ImageFont.truetype(name, size=64)
        except OSError:
            continue
        for ch in text:
            if ch.isspace():
                continue
            try:
                mask = face.getmask(ch)
            except Exception:
                return False
            if mask.getbbox() is None:
                return False
        return True
    return False
