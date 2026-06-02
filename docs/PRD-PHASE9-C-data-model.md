# Phase 9 · 附录 C · 数据模型与 Schema

| 属性 | 内容 |
|------|------|
| **主文档** | [PRD-PHASE9.md](./PRD-PHASE9.md) |
| **代号** | P9-C |
| **Schema** | `schemas/trip.schema.json`（W1 同步） |
| **文档版本** | v0.9.1 |

---

## 1. 设计原则

1. **被筛资产不删除**：仍在 `assets[]`，仅 `layoutEligible=false`。
2. **与低清剔除正交**：低清 `excludeReason=low_resolution`；cull 用独立 reason。
3. **可复现**：同 asset 元数据 + config → 同 cull 结果。
4. **下游只读 `layoutEligible`**：不解析 cull 细节。

---

## 2. Asset 字段扩展

### 2.1 `layoutEligible` / `excludeReason`

| 字段 | 类型 | 说明 |
|------|------|------|
| `layoutEligible` | bool | 默认 true；false = 不参与 cover/章/屏 |
| `excludeReason` | string? | 首个导致 false 的原因 |

**`excludeReason` 枚举（Phase 9 新增）**

| 值 | Pass | 说明 |
|----|------|------|
| `low_resolution` | asset_quality | 既有 |
| `media_class` | 1 | screenshot/thumbnail/reupload |
| `blur` | 1 | 极端模糊 |
| `exposure_extreme` | 1 | 全黑/全白 · **W2+** |
| `duplicate_group` | 2 | 组内非代表 |
| `cull_quota` | 3 | 软配额淘汰 |

**featured 豁免**：featured 资产 **无** cull 类 excludeReason（低清仍可能有 `low_resolution`——见 §4 冲突处理）。

### 2.2 `quality` 对象扩展

```json
{
  "quality": {
    "sharpness": 842.5,
    "cullScore": 0.732,
    "cullRank": 12,
    "aestheticScore": 0.68,
    "cullRoute": "portrait",
    "cullGroupId": "burst:2024-05-01T12:00:00Z"
  }
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `cullScore` | number | W1 | [0,1] 综合分 |
| `cullRank` | int | W1 | 批内排名，1=最高 |
| `aestheticScore` | number | P1 | pyiqa 原始归一化 |
| `cullRoute` | string | P1 | portrait / landscape / general |
| `cullGroupId` | string | W1 | Pass 2 分组键（调试） |

### 2.3 既有字段（消费，不修改）

| 字段 | cull 用途 |
|------|-----------|
| `userTier` | featured 豁免 |
| `mediaClass` | Pass 1 |
| `burstGroupId` / `dedupeGroupId` | Pass 2 |
| `subjectClass` | P1 路由（P9-E） |
| `ingestBatchId` | 增量 cull |

---

## 3. Trip · `curation` 扩展

### 3.1 `cullSummary`

```json
{
  "curation": {
    "cullSummary": {
      "enabled": true,
      "mode": "rules",
      "scanned": 100,
      "featuredCount": 15,
      "layoutEligibleCount": 97,
      "nonFeaturedEligibleCount": 82,
      "keepRatioFloor": 0.8,
      "floorTargetNonFeatured": 80,
      "pass3Skipped": null,
      "floorNotMet": false,
      "error": null,
      "excludedByCull": 31,
      "excludedByReason": {
        "duplicate_group": 18,
        "blur": 5,
        "cull_quota": 6,
        "media_class": 2
      },
      "maxPhotosExceeded": true,
      "maxPhotosLimit": 250,
      "warnMessage": "精选与素材共 297 张进入排版，超过建议上限 250 张…"
    },
    "excludedByCullAssetIds": ["a042", "a043"]
  }
}
```

| 字段 | 说明 |
|------|------|
| `excludedByCullAssetIds` | 因 cull **仅** 剔除的 id（不含 low_res） |
| `excludedLowResAssetIds` | **既有** · 低清 |
| `floorTargetNonFeatured` | `ceil(keep_ratio_floor × N_scan)` |
| `pass3Skipped` | 输入池 ≤ N_min 时原因 |
| `floorNotMet` | 最终 non-feat 率仍 &lt; floor |
| `error` | fail-open 异常信息 |
| `maxPhotosExceeded` | 方案 B WARN 标志 |

**口径**：`floorTargetNonFeatured = ceil(keep_ratio_floor × N_scan)`（例：100 张 → 80）。

### 3.2 用户可见摘要字符串（冗余，便于 Job）

`curation.cullUserLine`（可选）：

```text
经挑选 97 张进入排版
```

分项由前端/CLI 从 `cullSummary` 组装，见 P9-D。

---

## 4. featured 与 low_resolution 冲突

| 场景 | 规则 |
|------|------|
| featured + 低清 | **D-P9-03 优先**：`layoutEligible=true`；可写 `quality.lowResSuspected=true` 供 curate 降权 |
| 实现 | `apply_layout_eligibility_marks` 在 cull **之后**；featured 跳过 low_res 标记 **或** cull 末强制 featured eligible |

**推荐（D-P9-03 + Kickoff）**：`cull.featured_exempt_low_res: true`（config）— featured **不**因低清设 `layoutEligible=false`；可写 `quality.lowResSuspected=true`。**W1 curate 不降权**，仅标记。

---

## 5. ingest_stats（Job / CLI）

扩展 `IngestResult.stats`：

| 键 | 说明 |
|----|------|
| `cull_excluded` | 总数 |
| `cull_duplicate_group` | Pass 2 |
| `cull_blur` | Pass 1 |
| `cull_quota` | Pass 3 |
| `cull_layout_eligible` | 最终 eligible 数 |
| `cull_user_line` | 人话一行 |

---

## 6. Schema 变更清单

| 路径 | 变更 |
|------|------|
| `assets[].quality.cullScore` | 新增 optional number |
| `assets[].quality.cullRank` | 新增 optional integer |
| `assets[].excludeReason` | enum 扩展 |
| `curation.cullSummary` | 新增 object |
| `curation.excludedByCullAssetIds` | 新增 string[] |
| `curation.cullUserLine` | 新增 optional string |

**向后兼容**：旧 trip 无 cull 字段 → curate 视全员 eligible（与现行为一致）。

---

## 7. 验收

| ID | 条件 |
|----|------|
| **AC-P9-C-01** | schema validate 通过含 cull 字段的 fixture |
| **AC-P9-C-02** | `excludedByCullAssetIds` ∩ `excludedLowResAssetIds` 可重叠为空或文档化 |
| **AC-P9-C-03** | round-trip ingest → trip.json 含 cullSummary |

---

## 8. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.9.1 | 2026-06-02 | floorTargetNonFeatured · pass3Skipped/floorNotMet/error |
| v0.9.0 | 2026-06-02 | 初稿 |
