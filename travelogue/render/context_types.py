"""Typed template context contracts (leaf nodes; expand incrementally)."""

from __future__ import annotations

from typing import Any, NotRequired, TypedDict


class VoiceSourceContext(TypedDict, total=False):
    """Asset/chapter item voice payload before template enrichment."""

    audioFile: str
    durationSec: float | int
    transcript: str
    transcriptPreview: str
    showTranscript: bool


class VoiceRenderContext(TypedDict, total=False):
    """Handlebars voice bar context from build_voice."""

    hasVoice: bool
    audioFile: str
    duration: str
    ariaLabel: str
    transcript: str
    transcriptOpen: bool
    editableTranscript: bool
    editPathTranscript: str | None


class MediaCardContext(TypedDict, total=False):
    """Handlebars context for a single media card (required keys enforced at build)."""

    isMediaCard: bool
    isMediaRow: bool
    isMediaScroll: bool
    classes: str
    assetId: str
    aspectKind: str
    tagsAttr: str | None
    hasTags: bool
    isVideo: bool
    src: str
    hasSrcset: bool
    srcset: str
    sizes: str
    alt: str
    loading: str
    title: str
    hasTitle: bool
    caption: str
    hasCaption: bool
    editable: bool
    editPathTitle: str | None
    editPathCaption: str | None
    hasVoice: bool
    playBadge: str | None
    poster: NotRequired[str]
    videoFile: NotRequired[str]
    voiceAriaLabel: NotRequired[str]
    voiceTranscript: NotRequired[Any]


class MediaRowCellContext(TypedDict, total=False):
    src: str
    srcset: str
    hasSrcset: bool
    alt: str
    sizes: str
    aspectKind: str


class MediaRowContext(TypedDict, total=False):
    isMediaCard: bool
    isMediaRow: bool
    isMediaScroll: bool
    cells: list[MediaRowCellContext]
    caption: str
    hasCaption: bool
    rowLayout: str | None
    rowClass: str
    layoutHint: str | None
    hasLayoutHint: bool
    editable: bool
    editPathCaption: str | None


class MediaScrollSlideContext(TypedDict, total=False):
    src: str
    srcset: str
    hasSrcset: bool
    alt: str
    sizes: str
    aspectKind: str


class MediaScrollContext(TypedDict, total=False):
    isMediaCard: bool
    isMediaRow: bool
    isMediaScroll: bool
    slides: list[MediaScrollSlideContext]
    caption: str
    hasCaption: bool
    hasVoice: bool
    editable: bool
    editPathCaption: str | None


class LayoutScreenSlotContext(TypedDict, total=False):
    slotIndex: int
    fit: str
    src: str
    hasSrc: bool
    hasSrcset: bool
    srcset: str
    sizes: str
    alt: str
    loading: str
    slotStyle: str
    role: NotRequired[str]
    hasBlurFill: NotRequired[bool]
    blurSrc: NotRequired[str]


class LayoutScreenContext(TypedDict, total=False):
    patternId: str
    gridClass: str
    screenTone: str | None
    screenStyle: str
    layoutHint: str | None
    hasLayoutHint: bool
    slots: list[LayoutScreenSlotContext]
    isFeatured: bool
    screenIndex: NotRequired[int]
    hasScreenIndex: NotRequired[bool]
    chapterIndex: NotRequired[str]
    hasChapterIndex: NotRequired[bool]
    assetIds: NotRequired[str]
    hasAssetIds: NotRequired[bool]
    folioLite: NotRequired[bool]
    isPlate: NotRequired[bool]
    plateCaption: NotRequired[str]
    hasPlateCaption: NotRequired[bool]
    folioPageLabel: NotRequired[str]


class ScreenSpreadContext(TypedDict, total=False):
    src: str
    hasSrcset: bool
    srcset: str
    sizes: str
    alt: str
    body: str
    pullQuote: str
    hasPullQuote: bool


class ChapterDividerContext(TypedDict, total=False):
    showDivider: bool
    dividerDatetime: NotRequired[str]
    dividerDate: NotRequired[str]
    dividerPlace: NotRequired[str]


class TripIndexEntryContext(TypedDict, total=False):
    id: str
    index: str
    title: str
    desc: str
    hasDesc: bool


class ForewordSpreadContext(TypedDict, total=False):
    chapterTitle: str
    hasChapterTitle: bool
    lead: str
    pullQuote: str
    hasPullQuote: bool


class FeaturedGridCardContext(TypedDict, total=False):
    assetId: str
    src: str
    hasSrcset: bool
    srcset: str
    sizes: str
    alt: str


class BreathPauseItemContext(TypedDict, total=False):
    isBreathPause: bool
    breathLabel: str
    breathStyle: str


class ChapterRenderContext(TypedDict, total=False):
    """Per-chapter Handlebars bundle (screens engine path)."""

    id: str
    patternId: str
    index: str
    title: str
    lead: str
    hasLead: bool
    decorLine: str
    hasDecorLine: bool
    editableLead: bool
    editLeadPath: str | None
    hasMemoryAnchors: bool
    memoryAnchors: str | None
    useScreensEngine: bool
    screens: list[LayoutScreenContext]
    hasScreenSpread: bool
    screenSpread: ScreenSpreadContext
    items: list[Any]
    useChapterSeparator: bool
    chapterSeparatorStyle: str
    showDivider: NotRequired[bool]
    dividerDatetime: NotRequired[str]
    dividerDate: NotRequired[str]
    dividerPlace: NotRequired[str]


class CoverRenderContext(TypedDict, total=False):
    src: str
    hasSrcset: bool
    srcset: str
    sizes: str
    alt: str


class EpilogueStatsContext(TypedDict, total=False):
    dayCount: int
    placeCount: int
    photoCount: int
    summaryLine: str


class TripIndexBundleContext(TypedDict, total=False):
    entries: list[TripIndexEntryContext]


class FeaturedGridBundleContext(TypedDict, total=False):
    cards: list[FeaturedGridCardContext]


class TripRenderContext(TypedDict, total=False):
    """Root Handlebars context from build_render_context."""

    lang: str
    htmlExtraAttrs: str
    includeLongShot: bool
    includeLongshotBridge: bool
    longshotMobileUrl: str | None
    includeScreenplay: bool
    assetVersion: str
    hasShareZip: bool
    shareZipFile: str | None
    exportLayout: str
    copyDisplay: str
    isPhotosOnly: bool
    layoutEngine: str
    exportMode: str
    isDraft: bool
    isShare: bool
    title: str
    subtitle: str
    hasSubtitle: bool
    coverShowTitle: bool
    cover: CoverRenderContext
    tripMetaLine: str
    tripMetaDatetime: str | None
    hook: str
    hasHook: bool
    editableHook: bool
    epilogue: str
    hasEpilogue: bool
    editableEpilogue: bool
    tripId: str
    chapters: list[ChapterRenderContext]
    tripRoot: str | None
    readingJson: str
    includeBreath: bool
    includeBreathFlow: bool
    includeBreathScrub: bool
    includeBreathGsapRuntime: bool
    includeScrollKeyboardNav: bool
    presentPreviewUrl: str | None
    hasFeaturedAssets: bool
    folioLite: bool
    folioFull: bool
    hasTripIndex: bool
    tripIndex: TripIndexBundleContext
    hasFeaturedGrid: bool
    featuredGrid: FeaturedGridBundleContext
    hasForewordSpread: bool
    forewordSpread: ForewordSpreadContext
    isLongshotSurface: bool
    epilogueStats: EpilogueStatsContext | None
    useEpilogueStats: bool
    useEpilogueScreen: bool
