"""Agent 2 · Storyteller — rule-based copy stub (no LLM)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

from travelogue.paths import MANIFEST_PATH

# F-NAR-05 · manifest limits (F-NAR-01)
HOOK_MAX = 56
LEAD_MAX = 80
EPILOGUE_MAX = 80

BANNED_PHRASES: tuple[str, ...] = (
    "综上所述",
    "值得一提的是",
    "不可否认",
    "众所周知",
    "总而言之",
    "换句话说",
)


@lru_cache(maxsize=1)
def _manifest_limits() -> dict[str, int]:
    if not MANIFEST_PATH.is_file():
        return {
            "hookMaxChars": HOOK_MAX,
            "chapterLeadMaxChars": LEAD_MAX,
            "epilogueMaxChars": EPILOGUE_MAX,
        }
    data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    lim = data.get("limits") or {}
    return {
        "hookMaxChars": int(lim.get("hookMaxChars", HOOK_MAX)),
        "chapterLeadMaxChars": int(lim.get("chapterLeadMaxChars", LEAD_MAX)),
        "epilogueMaxChars": int(lim.get("epilogueMaxChars", EPILOGUE_MAX)),
    }


def _strip_banned(text: str) -> str:
    out = text
    for phrase in BANNED_PHRASES:
        out = out.replace(phrase, "")
    return re.sub(r"\s{2,}", " ", out).strip()


def _finalize_copy(text: str, max_chars: int, *, seen: set[str] | None = None) -> str:
    """Clamp length, drop banned phrases, optional de-dupe within a narrate run."""
    t = _strip_banned((text or "").strip())
    if not t:
        return ""
    if seen is not None:
        base = t[:max_chars]
        candidate = base
        n = 2
        while candidate in seen:
            suffix = f"·{n}"
            candidate = (base[: max(0, max_chars - len(suffix))] + suffix)[:max_chars]
            n += 1
        seen.add(candidate)
        return candidate
    return t[:max_chars]


class NarrateError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


@dataclass
class NarrateResult:
    fields_updated: list[str]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_iso_date(raw: str) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except ValueError:
        return None


def _format_date_span(start: str, end: str) -> str:
    ds, de = _parse_iso_date(start), _parse_iso_date(end)
    if ds and de and ds.date() != de.date():
        if ds.year == de.year and ds.month == de.month:
            return f"{ds.month}月{ds.day}日到{de.day}日"
        if ds.year == de.year:
            return f"{ds.month}月{ds.day}日到{de.month}月{de.day}日"
        return f"{ds.year}年{ds.month}月{ds.day}日"
    if ds:
        return f"{ds.month}月{ds.day}日"
    return ""


def _chapter_asset_ids(chapter: dict) -> list[str]:
    ids: list[str] = []
    for item in chapter.get("items") or []:
        if item.get("type") == "media-card" and item.get("assetId"):
            ids.append(item["assetId"])
    return ids


def _chapter_places(chapter: dict, assets: dict[str, dict]) -> list[str]:
    places: list[str] = []
    cur = (chapter.get("curation") or {}).get("places") or []
    for p in cur:
        if p and p not in places:
            places.append(p)
    for aid in _chapter_asset_ids(chapter):
        city = ((assets.get(aid) or {}).get("place") or {}).get("city")
        if city and city not in places:
            places.append(city)
    return places


def _voice_excerpt(chapter: dict, assets: dict[str, dict]) -> str:
    for aid in _chapter_asset_ids(chapter):
        voice = (assets.get(aid) or {}).get("voice") or {}
        preview = (voice.get("transcriptPreview") or voice.get("transcript") or "").strip()
        if preview:
            return preview[:40]
    return ""


def _build_hook(meta: dict, *, photo_count: int, tone: str) -> str:
    places = meta.get("places") or ["旅途"]
    place = places[0]
    title = meta.get("title") or "旅途"
    span = _format_date_span(meta.get("dateStart", ""), meta.get("dateEnd", ""))

    if tone == "documentary":
        if span and photo_count:
            return f"{place}，{span}，{photo_count} 帧记录。"
        if span:
            return f"{place}，{span}。"
        return f"{title} · {place}。"

    if span and photo_count:
        return f"在{place}的{span}，{photo_count} 张碎片拼成这一页。"
    if span:
        return f"{place}的{span}，慢慢翻。"
    return f"{title} · 关于{place}的几帧。"


def _build_lead(
    chapter: dict,
    *,
    assets: dict[str, dict],
    default_place: str,
    tone: str,
    chapter_index: int,
    chapter_total: int,
) -> str:
    title = (chapter.get("title") or "").strip()
    places = _chapter_places(chapter, assets)
    place = places[0] if places else default_place
    n = len(_chapter_asset_ids(chapter))
    voice = _voice_excerpt(chapter, assets)

    if voice and tone != "documentary":
        lead = f"「{voice}」——{title or place}。" if title else f"「{voice}」"
        return lead

    if chapter_index == 1:
        if tone == "documentary":
            return f"第 1 章 · {title or place}，{n} 张。"
        return f"从{title or '这里'}开始，{place}比想象中安静。"

    if chapter_index >= chapter_total and chapter_total > 1:
        if tone == "documentary":
            return f"末章 · {title or place}。"
        return f"快到尾声，{title or place}还留着余温。"

    if tone == "documentary":
        return f"{title or place}，{n} 张。"
    subject = place or title or "这一段"
    if n >= 2:
        return f"{subject}这一段，{n} 帧慢慢铺开。"
    return f"{subject}，再走一步。"


def _build_epilogue(meta: dict, *, tone: str) -> str:
    places = meta.get("places") or ["旅途"]
    place = places[0]
    if tone == "documentary":
        return f"{place}，行程归档。"
    return f"下次再见，{place}。"


def run_narrate(
    trip: dict,
    *,
    tone: str | None = None,
    dry_run: bool = False,
    provider: str | None = None,
    regenerate: bool = False,
    cache_dir: Path | None = None,
) -> NarrateResult:
    """Fill meta.hook, chapter leads, captions, epilogue (stub or LLM)."""
    from travelogue.config import get_config
    from travelogue.services.llm_narrate import run_llm_narrate

    prov = (provider or get_config().llm.provider or "stub").strip().lower()
    if prov not in ("stub", "deepseek", "dashscope"):
        raise NarrateError("E_NARRATE_PROVIDER", f"unknown provider {prov!r}")
    if prov == "stub":
        return _run_narrate_stub(trip, tone=tone, dry_run=dry_run, regenerate=regenerate)
    return run_llm_narrate(
        trip,
        provider=prov,
        tone=tone,
        dry_run=dry_run,
        regenerate=regenerate,
        cache_dir=cache_dir,
    )


def _run_narrate_stub(
    trip: dict,
    *,
    tone: str | None = None,
    dry_run: bool = False,
    regenerate: bool = False,
) -> NarrateResult:
    """Rule-based hook and chapter leads (no LLM)."""
    meta = trip.setdefault("meta", {})
    if tone:
        meta["tone"] = tone if tone in ("relaxed", "documentary") else meta.get("tone", "relaxed")

    updated: list[str] = []
    places = meta.get("places") or ["旅途"]
    place = places[0]
    tone_val = meta.get("tone") or "relaxed"
    assets = {a["id"]: a for a in trip.get("assets") or []}
    photo_count = sum(1 for a in assets.values() if a.get("type", "image") == "image")
    chapters = trip.get("chapters") or []
    chapter_total = len(chapters)

    lead_seen: set[str] = set()

    lim = _manifest_limits()

    if not meta.get("edited") and (regenerate or not (meta.get("hook") or "").strip()):
        if not dry_run:
            meta["hook"] = _finalize_copy(
                _build_hook(meta, photo_count=photo_count, tone=tone_val),
                lim["hookMaxChars"],
            )
        updated.append("meta.hook")

    for ch in chapters:
        if ch.get("edited"):
            continue
        if not regenerate and (ch.get("lead") or "").strip():
            continue
        idx = int(ch.get("index") or 0)
        if not dry_run:
            ch["lead"] = _finalize_copy(
                _build_lead(
                    ch,
                    assets=assets,
                    default_place=place,
                    tone=tone_val,
                    chapter_index=idx,
                    chapter_total=chapter_total,
                ),
                lim["chapterLeadMaxChars"],
                seen=lead_seen,
            )
        updated.append(f"chapters[{ch.get('index')}].lead")

    if chapter_total >= 2 and (regenerate or not (trip.get("epilogue") or "").strip()):
        if not dry_run:
            trip["epilogue"] = _finalize_copy(
                _build_epilogue(meta, tone=tone_val),
                lim["epilogueMaxChars"],
            )
        updated.append("epilogue")

    if dry_run:
        return NarrateResult(fields_updated=updated)

    pipe = trip.setdefault("pipeline", {})
    pipe["status"] = "copy_draft"
    pipe.setdefault("runs", []).append(
        {
            "runId": f"narrate-{_utc_now_iso()}",
            "agent": "storyteller",
            "startedAt": _utc_now_iso(),
            "finishedAt": _utc_now_iso(),
            "model": "rule-stub",
        }
    )
    trip["updatedAt"] = _utc_now_iso()
    return NarrateResult(fields_updated=updated)
