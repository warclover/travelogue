"""Title Art engine (PRD-COVER-CALLIGRAPHY-TITLE-V1 · CAL).

封面标题艺术字：把 ``trip.meta.title`` 渲染成一枚透明标题贴纸
（PNG-RGBA），由现网 Opening（白名单内）叠加展示。

- 路线 B（``clean-pipeline-v1``）：字库直出，零特效，默认兜底（D-CAL-01/02）。
- 路线 C（``diffusion-fixed-prompt-v1``）：固定提示词分层生图候选，
  W0.5 Spike（26 条真实/边界标题，2026-08-08）实测 OCR 回读通过率仅 57.7%，
  未达生产门槛，不进默认路径；失败必须静默降级路线 B（D-CAL-14/16）。

对外主入口见 :func:`travelogue.cover_engine.title_art.engine.resolve_title_art`。
"""

from __future__ import annotations

from travelogue.cover_engine.title_art.engine import resolve_title_art
from travelogue.cover_engine.title_art.models import TitleArtResult

__all__ = ["resolve_title_art", "TitleArtResult"]
