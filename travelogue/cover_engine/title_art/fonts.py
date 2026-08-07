"""Font candidate pool for the clean pipeline (PRD §5.3 · D-CAL-07)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import ImageFont

FALLBACK_STACK: tuple[str, ...] = (
    "msyh.ttc",
    "msyhbd.ttc",
    "simhei.ttf",
    "NotoSerifSC-Regular.otf",
)

#: 随包分发的字库资产目录（D-CAL-07 授权字库实际落地位置）。
#: 仅打包已核查 ``licensed=True`` 的字体文件——不随包分发未核查授权的候选，
#: 避免误用；未核查字体保留在候选池仅用于评估，永不进 :func:`pick_default_font`。
_ASSET_DIR = Path(__file__).resolve().parent / "assets" / "fonts"


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


def resolve_font_source(filename: str) -> str:
    """Resolve a pool filename to a loadable source for :class:`PIL.ImageFont`.

    Prefers the bundled asset under ``assets/fonts/`` (works regardless of
    whether the font is installed as an OS font — the original bug this
    fixes: ``ImageFont.truetype("ZhiMangXing-Regular.ttf", ...)`` silently
    fails on any machine without that font *installed*, degrading every
    render to the generic ``msyh.ttc`` fallback and defeating the "calligraphy
    sticker" premise while still *looking* fine because the fallback chain
    never raises). Falls back to the bare filename (OS-resolvable) when no
    bundled asset exists, so unlicensed pool entries (not shipped as assets)
    still resolve the same way they did before.
    """
    bundled = _ASSET_DIR / filename
    if bundled.is_file():
        return str(bundled)
    return filename


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
    """Try the bundled asset, then the bare filename (OS-installed), then the
    CJK fallback stack, then Pillow default.

    Falling back keeps rendering possible (degrades to a generic CJK face
    rather than failing outright — same safety-net spirit as
    ``travelogue.export.card_bookends._load_font``). Returns the *actually
    loaded* font's reported name alongside the font object, so callers can
    report which face rendered the text instead of the originally requested
    candidate.
    """
    for name in (resolve_font_source(font.filename), *FALLBACK_STACK):
        try:
            loaded = ImageFont.truetype(name, size=size)
        except OSError:
            continue
        reported = font.filename if name == resolve_font_source(font.filename) else name
        return loaded, reported
    return ImageFont.load_default(), "pillow-default"


def glyphs_covered(font_candidates: tuple[str, ...], text: str) -> bool:
    """§4 字形覆盖检查（近似实现）。

    尝试加载候选字体列表中第一个可用的字体，逐字检查 ``getmask`` 是否非空。
    一个字体文件都加载不了（dev/CI 环境缺少 CJK 字体）时，视为不可渲染中文，
    直接判定未覆盖 → 调用方 fail-open，避免输出乱码/缺字方块。

    每个候选名先经 :func:`resolve_font_source` 解析——确保这里探测的是
    render_b.py 实际会用的那款字库（例如随包字体资产），而不是因为裸文件名
    在系统里解析不到就静默降级去探测 ``msyh.ttc`` 的覆盖率（那样探测出来的
    "覆盖"跟实际渲染用的字体是两张脸，字形覆盖检查形同虚设）。
    """
    if not text:
        return True
    for name in font_candidates:
        try:
            face = ImageFont.truetype(resolve_font_source(name), size=64)
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
