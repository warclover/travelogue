"""Frozen import payload key contract for Wizard（PRD §16.3 / DS-03）.

Sheet 已退役后不再做 v2/v3 双路径对照；本契约冻结 `buildWizardPayload` /
`buildImportPayload` 允许出现的字段名，供 unit + e2e snapshot 共用。
"""

from __future__ import annotations

# 快速路径默认必有（含 buildImportPayload 基线 + Wizard 开关）
QUICK_SHARE_REQUIRED_KEYS = frozenset(
    {
        "albumPath",
        "title",
        "place",
        "placeUserSet",
        "mode",
        "force",
        "template_mode",
        "photoCullEnabled",
        "keepNearDuplicates",
    }
)

# 精细路径在必有键之外额外要求
FINE_CRAFT_REQUIRED_KEYS = QUICK_SHARE_REQUIRED_KEYS | frozenset({"layoutDensity"})

# 有条件注入（用户填写 / preview / 计划文件 / 手动模板）
OPTIONAL_KEYS = frozenset(
    {
        "userNotes",
        "travelNotes",
        "dateRange",
        "featuredDir",
        "materialDir",
        "planText",
        "eligibleCount",
        "template_id",
    }
)

ALLOWED_KEYS = QUICK_SHARE_REQUIRED_KEYS | FINE_CRAFT_REQUIRED_KEYS | OPTIONAL_KEYS
