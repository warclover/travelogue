"""QA-SFI-05 · 附录章 +1 不破 LTN Narrative Contract（三读法保组感）。"""

from __future__ import annotations

import json
from pathlib import Path

from travelogue.config import get_config
from travelogue.curation.curate import run_curate
from travelogue.curation.time_outlier import is_appendix_chapter
from travelogue.layout_contract.chapter_items import (
    resolve_longshot_mode,
    screens_to_longshot_items,
)
from travelogue.layout_contract.narrative_contract import (
    ensure_narrative_contract_on_chapters,
)

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "sfi"


def test_appendix_does_not_break_mosaic_preserve_group() -> None:
    trip = json.loads(
        (FIXTURES / "trip.sfi_semporna_appendix.json").read_text(encoding="utf-8")
    )
    run_curate(trip, cfg=get_config())
    chapters = trip.get("chapters") or []
    content = [ch for ch in chapters if not is_appendix_chapter(ch)]
    appendix = [ch for ch in chapters if is_appendix_chapter(ch)]
    assert len(appendix) == 1
    assert 1 <= len(content) <= 5
    assert appendix[0].get("index") == len(chapters)

    ensure_narrative_contract_on_chapters(chapters)

    for ch in content:
        for sc in ch.get("screens") or []:
            pid = str(sc.get("patternId") or "")
            if "mosaic" not in pid:
                continue
            assert sc.get("preserveGroup") is True, pid
            # 保组感：不得静默 flatten
            mode = resolve_longshot_mode(sc)
            assert mode != "flatten" or sc.get("preserveGroup") is False

    # Longshot item projection still defined for content chapters with screens
    for ch in content:
        if not ch.get("screens"):
            continue
        items = screens_to_longshot_items(ch)
        assert isinstance(items, list)
