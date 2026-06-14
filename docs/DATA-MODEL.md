# Travelogue · 数据模型（trip.json v0.2）

| 属性 | 内容 |
|------|------|
| **版本** | trip.json `0.2` |
| **模板** | `visual-journal` |
| **机器校验** | [schemas/trip.schema.json](../schemas/trip.schema.json) |
| **关联** | `TEMPLATE-visual-journal.md`、`AGENT-ARCHITECTURE.md` §10 |
| **更新日期** | 2026-05-28 |

---

## 1. 设计原则

1. **单一真相源**：所有 Agent 与用户编辑只读写 `trip.json`（及二进制 `assets/`）。  
2. **渲染只读**：Agent 3 不修改叙事字段，仅补全 `alt` 等展示缺省。  
3. **与 manifest 对齐**：字数与数量上限以 `templates/visual-journal/manifest.json` 为准。  
4. **可演进**：`version` 字段升级；旧版由迁移脚本处理（P1）。

---

## 2. 目录结构

```
trips/{tripId}/
├── trip.json           # 本文档描述的结构
├── source/             # 原始导入（只增不删原片，可选）
├── assets/             # 展示用 WebP、视频循环、语音、poster
├── index.html          # Agent 3 输出
├── journal.css         # 模板样式（或内联）
├── preview.jpg         # 导出封面 9:16（可选）
└── runs/               # 编排运行日志（可选）
    └── run-{id}.json
```

---

## 3. 顶层字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `version` | string | ✅ | 固定 `"0.2"` |
| `tripId` | string | ✅ | 唯一 ID，如 `kyoto-2025-04` |
| `templateId` | string | ✅ | MVP 固定 `visual-journal` |
| `exportLayout` | enum | ✅ | `auto` \| `mobile` \| `web`，默认 `auto` |
| `export` | object | ❌ | 导出选项，见 §3.1 |
| `meta` | object | ✅ | 全书元信息与文案 |
| `coverAssetId` | string | ✅ | 封面图 asset |
| `momentAssetId` | string? | ❌ | Phase 23 · 签名时刻（∈ `curation.momentPoolIds`） |
| `coverCandidates` | string[] | ❌ | 策展提案的 3 张候选 |
| `assets` | array | ✅ | 媒体资源列表 |
| `chapters` | array | ✅ | 3–5 章 |
| `epilogue` | string | ❌ | ≤80 字 |
| `privacy` | object | ✅ | 隐私与导出确认 |
| `pipeline` | object | ✅ | 状态机与锁 |
| `userNotes` | string | ❌ | 全局备注，供 Agent 2 |
| `slug` | string \| null | ❌ | P2 托管用 |
| `publishedAt` | string \| null | ❌ | ISO8601 |
| `createdAt` | string | ✅ | ISO8601 |
| `updatedAt` | string | ✅ | ISO8601 |

**废弃（v0.1）**：顶层 `status: draft|ready|exported` → 由 `pipeline.status` 取代；`quotes[]` → 并入 `asset.voice` / caption。

### 3.1 `curation` 对象（可选 · v0.2.2+）

| 字段 | 类型 | 说明 |
|------|------|------|
| `orientationSummary` | object | `total` / `landscape` / `portrait` / `square` / `panorama` / `tall` / `exportLayout`；见 `LAYOUT-PLANNER.md` |
| `clustering` | object? | Phase 3 · Curate 聚类输出；见 §3.4 |
| `momentPoolIds` | string[]? | Phase 23 · 高光池（5% clamp 1–5） |
| `momentSecondaryIds` | string[]? | Phase 23 · 池内次要高光（无独立屏） |
| `momentPoolSize` | number? | 池目标大小（审计） |
| `momentCandidates` | string[]? | Studio 换签名 top-3 |
| `momentExplain` | object[]? | 签名时刻因子解释 |
| `momentPosition` | enum? | `before_closing` \| `arc_peak` |
| `momentSkipped` | string? | 跳过原因（`small_trip` / `disabled` 等） |
| `momentCollision` | string? | `closing` 软碰撞警告 |

### 3.4 `curation.clustering` 对象（可选 · Phase 3 · v0.3+）

由 **ClusteringLayer**（ingest 后、curate 前）写入。权威 PRD：[PRD-PHASE3.md](./PRD-PHASE3.md) §9.2。

| 字段 | 类型 | 说明 |
|------|------|------|
| `version` | string | 固定 `"1"` |
| `segmentMode` | enum | `geo_event` \| `date_fallback` |
| `segments[]` | array | 地理/时间行程段，见下表 |
| `clusters[]` | array? | 场景簇（P3-Full · vision on）；见下表 |
| `visionModel` | string? | 如 `ViT-B/32`；分享时可 strip |

**`segments[]` 项**

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 如 `evt-01` |
| `name` | string | 展示名（地点 + 日期 span） |
| `startDate` | date | ISO 日期 |
| `endDate` | date | ISO 日期 |
| `location` | string? | 城市/地区文案 |
| `assetIds` | string[] | 本段 asset id 列表 |

**`clusters[]` 项**

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | number | 簇 ID；`-1` 表示噪声（若落盘） |
| `label` | string | 如 `theme_12` |
| `assetIds` | string[] | 簇内 asset |
| `medoidAssetId` | string? | 代表图，供 cover 加权 |

**兼容**：旧版 `curation.insights.*` **不再写入**；读取时忽略。`validate_trip` L1 将 `curation.clustering` 视为 optional 子树。

### 3.2 `export` 对象（v0.2.1+）

| 字段 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `longShot` | boolean \| null | 默认 **`true`**（P0） | 是否注入「保存长图」bundle；`false` 关闭 |
| `reading` | object? | v1.0+ · 见 §3.3 | 三阅读模式与 Hybrid 配置；权威见 [PRD-EXPERIENCE.md](./PRD-EXPERIENCE.md) |

CLI：`travelogue export … --no-longshot` 写入 `export.longShot=false`。

**分享语义**（见 `SHARING.md`）：长图路径 **不** 依赖 `privacy.confirmedAt`；zip/HTML 私密分享仍依赖 `privacy` 闸口。

### 3.3 `export.reading` 对象（v1.0+ · 体验 PRD）

| 字段 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `profile` | enum | `default_hybrid` | `legacy` \| `performance` \| `default_hybrid` \| `magazine`；展开为下方子字段默认值 |
| `present.dwellMs` | number | 2000 | 放映模式单屏停留（ms） |
| `present.featuredOnly` | boolean | false | 仅放映 `userTier: featured` 素材 |
| `present.syncScrollOnExit` | boolean | true | 退出放映时 scroll 位置与当前屏对齐 |
| `present.skipAuxBlocks` | boolean | false | 跳过 cover / epilogue 等辅助块 |
| `scroll.snap` | enum | 依 profile | `off` \| `proximity` \| `mandatory` |
| `scroll.breath` | enum | 依 profile | `off` \| `soft` \| `flow` \| `cinematic` \| `gallery` |
| `scroll.folio` | enum | 依 profile | `off` \| `lite` \| `full` |
| `longshot.breath` | enum | `off` | longshot 面强制 off |
| `longshot.folio` | enum | `off` | longshot 面强制 off |

**Profile 默认值**（见 [experience-matrix.yaml](./experience-matrix.yaml)）：工坊 draft web → `default_hybrid`；share zip / longshot 捕获 → `performance`；`index-mobile.html` → `legacy`（12 个月内不启用 breath/folio）。

**废弃别名（兼容 1 版本）**：`export.breathMode` → `reading.scroll.breath`；`export.folioMode` → `reading.scroll.folio`。

---

## 4. `meta` 对象

| 字段 | 类型 | 约束 | Agent |
|------|------|------|-------|
| `title` | string | ≤20 字 | 2 写，用户可改 |
| `subtitle` | string? | ≤32 字 | 2 |
| `hook` | string? | ≤56 字 | 2 |
| `dateStart` | date | ISO 日期 | 0/1 从 EXIF 推断 |
| `dateEnd` | date | ISO 日期 | 0/1 |
| `places` | string[] | 城市级 | 0/1 |
| `companions` | string? | 自由文本 | 用户 |
| `tone` | enum | `relaxed` \| `documentary` | 用户选，2 遵循 |

---

## 5. `pipeline` 对象

| 字段 | 类型 | 说明 |
|------|------|------|
| `status` | enum | 见下表 |
| `lastBatchId` | string? | 最近导入批次 |
| `pendingAssets` | string[]? | 未归入章节的 asset id |
| `locks.structure` | boolean | G1 确认后为 `true` |
| `locks.copy` | boolean | G2 确认后为 `true` |
| `runs` | array? | 每次 Agent 运行的摘要 |

### 5.1 `pipeline.status` 枚举

| 值 | 含义 |
|----|------|
| `draft_ingest` | 导入中 |
| `ingest_ready` | 素材就绪 |
| `structure_draft` | 章提案待确认 |
| `structure_locked` | 结构已锁定 |
| `copy_draft` | 文案待确认 |
| `copy_locked` | 文案已锁定 |
| `rendered` | 已生成 HTML |
| `exported` | 已导出 zip |

状态转换见 `AGENT-ARCHITECTURE.md` §3.2。

### 5.2 `runs[]` 项

| 字段 | 类型 |
|------|------|
| `runId` | string |
| `agent` | `media_lab` \| `curator` \| `storyteller` \| `publisher` |
| `startedAt` | ISO8601 |
| `finishedAt` | ISO8601 |
| `model` | string \| null |

---

## 6. `assets[]` · 媒体资源

### 6.1 公共字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 如 `asset-001` |
| `type` | `image` \| `video` \| `audio` | 语音可独立或挂 image/video |
| `sourceFile` | string | 相对 `trips/{id}/` |
| `ingestBatchId` | string? | 分批上传 |
| `dedupeGroupId` | string? | 连拍分组 |
| `locked` | boolean? | `true` 时 Agent 不可删 |
| `takenAt` | string? | ISO8601 |
| `place` | object? | `{ city, country? }` 城市级 |
| `width` / `height` | number? | 像素 |
| `aspectKind` | enum? | `portrait` \| `landscape` \| `square` \| `panorama` \| `tall`（`classify_aspect`） |
| `tags` | string[]? | Agent 0 语义标签，**3–5 个推荐**，供 Agent 2 |
| `tagsSource` | enum? | `heuristic` \| `exif` \| `clip` \| `vlm` \| `user` |
| `eventId` | string? | Phase 3 · 关联 `curation.clustering.segments[].id` |
| `sceneClusterId` | number? | Phase 3 · 场景簇 ID；`-1` 噪声 |
| `subjectClass` | enum? | Phase 3 / 排版 V2 · `person` \| `pet` \| `landscape` \| `architecture` \| `food` \| `indoor` \| `mixed` \| `unknown` |
| `subjectConfidence` | number? | [0, 1] |
| `clusterSource` | enum? | `clip` \| `heuristic` \| `none` |
| `userTier` | enum? | v1.0+ · `featured` \| `material`；默认 `material`；见 [PRD-EXPERIENCE-附录A-精选上传.md](./PRD-EXPERIENCE-附录A-精选上传.md) |
| `userTierSource` | enum? | `ingest` \| `user`（G2 serve 升格为 featured） |

### 6.2 图片 `type: image`

| 字段 | 说明 |
|------|------|
| `displayFile` | 主展示 WebP，如 `w1600` |
| `srcset` | `[{ file, width }]` |
| `cropMobile` | 可选 9:16 裁切 |
| `cropWeb` | 可选 16:9 裁切 |
| `focalPoint` | `{ x, y }` 0–1，裁切中心 |
| `exif` | object? | Phase 23 · 相机 EXIF（ingest 写入）；见 §6.2.1 |
| `voice` | 可选，见 §6.4 |

### 6.2.1 `exif` 子对象（Phase 23 · v0.2.3+）

| 字段 | 类型 | 说明 |
|------|------|------|
| `make` / `model` / `lens` | string? | 厂商 / 机型 / 镜头 |
| `focalLengthMm` | number? | 焦段 mm |
| `aperture` | number? | f 值 |
| `shutter` | string? | 如 `1/500` |
| `iso` | number? | ISO |
| `altitudeM` | number? | GPS 海拔（有则写） |
| `completeness` | enum | `full` \| `partial` \| `none` |

### 6.3 视频 `type: video`

| 字段 | 说明 |
|------|------|
| `displayFile` | 3–8s 循环 mp4/webm |
| `posterFile` | 封面帧 |
| `duration` | 秒 |
| `hasAudio` | boolean；`true` 时同卡不叠 voice |

### 6.4 `voice` 对象（挂在 asset 上）

| 字段 | 约束 |
|------|------|
| `audioFile` | 相对路径 |
| `durationSec` | 5–180 |
| `transcript` | ASR 全文 |
| `transcriptPreview` | ≤40 字 |
| `source` | `user` |
| `showTranscript` | 默认 true |

---

## 7. `chapters[]` · 章节

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 如 `ch-01` |
| `index` | number | 1-based 排序 |
| `patternId` | enum | `open` \| `gallery` \| `moment` \| `close` |
| `title` | string | ≤12 字 |
| `lead` | string? | ≤80 字，可空 |
| `items` | array | 块序列，见 §8 |
| `curation` | object? | 策展元数据，Agent 1 写 |

### 7.1 `curation` 对象

| 字段 | 说明 |
|------|------|
| `anchorAssetId` | 章代表图 |
| `daySpan` | `["2025-04-02"]` |
| `places` | 本章涉及城市 |
| `memoryAnchors` | string[]? | G1 用户记忆锚点，每章 **0–3** 条，≤24 字/条，供 Agent 2 |

---

## 8. `items[]` · 章内块

### 8.1 `media-card`

| 字段 | 类型 | 说明 |
|------|------|------|
| `type` | const | `media-card` |
| `assetId` | string | 关联 assets |
| `title` | string? | ≤14 字 |
| `caption` | string? | ≤60 字 |
| `edited` | boolean? | 用户改过则 true |
| `layout` | object? | `{ fill, bleed, overlay }` |

### 8.2 `media-row`

| 字段 | 说明 |
|------|------|
| `type` | `media-row` |
| `assetIds` | 恰好 2 个 image |

### 8.3 `media-scroll`

| 字段 | 说明 |
|------|------|
| `type` | `media-scroll` |
| `assetIds` | 3–5 个 image |
| `voice` | 可选组级语音 |

---

## 9. `privacy` 对象

| 字段 | 类型 | 说明 |
|------|------|------|
| `level` | string | MVP 默认 `private` |
| `stripExifOnExport` | boolean | 默认 true |
| `confirmedAt` | string \| null | 非空才允许 `exported` |

---

## 10. Agent 读写矩阵

| 路径 | Agent 0 | Agent 1 | Agent 2 | Agent 3 | 用户 |
|------|---------|---------|---------|---------|------|
| `assets[]` | W | R | R | R | W |
| `chapters[]` | — | W | R | R | W* |
| `meta.*` | — | — | W | R | W |
| items 文案 | — | — | W | R | W |
| `coverAssetId` | — | W | R | R | W |
| `pipeline` | W | W | W | W | W |
| `index.html` | — | — | — | W | — |

\* G1 锁定后改结构需解锁或「重新策展」。

---

## 11. 完整示例（精简）

- 可校验样例：[schemas/fixtures/trip.example.json](../schemas/fixtures/trip.example.json)  
- 字段说明：`TEMPLATE-visual-journal.md` §10

---

## 12. 校验流程

1. **JSON Schema**：`trip.schema.json`  
2. **业务规则**：对照 `manifest.json`（章数、pattern、视频位置等）  
3. **Agent 2 输出**：先 patch JSON，再 validate，失败重试 ≤2 次  

---

## 13. 版本迁移

| 从 | 到 | 要点 |
|----|-----|------|
| 0.1 | 0.2 | `templateId` → visual-journal；`chapters[].assetIds` → `items[]`；`quotes` → voice；`status` → `pipeline.status` |

迁移脚本：`scripts/migrate_trip_01_to_02.py`（待实现）。

---

## 14. 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.2 | 2026-05-19 | P0 冻结：pipeline、items、visual-journal |
| v0.2.1 | 2026-05-19 | ADR-001：`tags`/`tagsSource`、`memoryAnchors`；交付形态澄清 |
| v0.2.2 | 2026-05-28 | Phase 3：`curation.clustering`；asset `eventId` / `sceneClusterId` / `subjectClass` |

> 架构决策：[adr/001-delivery-and-media.md](./adr/001-delivery-and-media.md) · Phase 3：[adr/007-native-clustering.md](./adr/007-native-clustering.md)
