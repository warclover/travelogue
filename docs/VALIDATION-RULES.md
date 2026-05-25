# Travelogue · 校验规则（L1 Schema + L2 Manifest）

| 属性 | 内容 |
|------|------|
| **文档版本** | v0.1 |
| **L1** | [schemas/trip.schema.json](../schemas/trip.schema.json) |
| **L2** | [templates/visual-journal/manifest.json](../templates/visual-journal/manifest.json) |
| **实现** | `travelogue/services/validate.py` |
| **更新日期** | 2026-05-22 |

---

## 1. 校验分层

```mermaid
flowchart LR
  JSON[trip.json] --> L1[L1 JSON Schema]
  L1 --> L2[L2 Manifest 业务规则]
  L2 --> L3[L3 渲染前资源存在性]
  L3 --> OK[通过]
```

| 层 | 时机 | 失败错误码 |
|----|------|------------|
| L1 | 任何 Agent 写盘后 | `E_VALIDATE_SCHEMA` |
| L2 | curate / narrate / render 前 | `E_VALIDATE_MANIFEST` |
| L3 | render / export 前 | `E_RENDER_ASSET_MISSING` |

---

## 2. L1 · Schema（摘要）

由 JSON Schema 自动检查，详见 `DATA-MODEL.md`。包括但不限于：

- `version === "0.2"`，`templateId === "visual-journal"`  
- `chapters` 长度 3–5  
- `items[].assetId` 类型正确  
- 字符串 `maxLength` 与 schema 一致  

---

## 3. L2 · Manifest 业务规则

### 3.1 数量与字数（`limits`）

| 规则 ID | 检查 | 错误码 |
|---------|------|--------|
| VR-L01 | `meta.title` 字数 ≤ `tripTitleMaxChars` (20) | `E_VALIDATE_LIMIT` |
| VR-L02 | `meta.hook` ≤ 56 | 同上 |
| VR-L03 | `chapter.title` ≤ 12 | 同上 |
| VR-L04 | `chapter.lead` ≤ 80 | 同上 |
| VR-L05 | `item.caption` ≤ 60 | 同上 |
| VR-L06 | 图片 asset 数 ≤ `maxPhotosPerTrip` (**250**) | `E_INGEST_LIMIT_PHOTOS` |
| VR-L07 | 视频 asset 数 ≤ 3 | `E_VALIDATE_MANIFEST` |
| VR-L08 | trip 级 voice 数 ≤ 15 | `E_VALIDATE_MANIFEST` |

字数：**中文按字符计**（`len()`），非字节。

### 3.2 引用完整性

| 规则 ID | 检查 | 错误码 |
|---------|------|--------|
| VR-R01 | `coverAssetId` ∈ `assets` 且 type=image | `E_VALIDATE_REF` |
| VR-R02 | 所有 `items[].assetId` / `assetIds[]` 存在 | 同上 |
| VR-R03 | 每个 asset 最多出现在 **1 个** media-card（scroll/row 内允许多 id） | `E_VALIDATE_MANIFEST` |

### 3.3 Pattern 与章结构

| 规则 ID | 检查 | 错误码 |
|---------|------|--------|
| VR-P01 | `patternId` ∈ {open, gallery, moment, close} | `E_VALIDATE_MANIFEST` |
| VR-P02 | 第 1 章（index=1）`patternId === open` | 同上 |
| VR-P03 | 最后 1 章 `patternId === close` | 同上 |
| VR-P04 | `gallery` 章含 `media-scroll` 且 3–5 图 | `E_VALIDATE_MANIFEST`（已实现） |
| VR-P05 | `moment` 章含至少 **2 个视觉单元**（`media-card` / `media-row` / `media-scroll` 各计 1，每个 `layout-screen` 计 1） | 同上 |

### 3.4 视频与语音

| 规则 ID | 检查 | 错误码 |
|---------|------|--------|
| VR-M01 | `coverAssetId` 不得为 video | `E_VALIDATE_MANIFEST` |
| VR-M02 | 第 1 章 items 中不得含 video | 同上 |
| VR-M03 | 每章 video 数 ≤ `maxVideosPerChapter` (1) | `E_VALIDATE_MANIFEST`（已实现） |
| VR-M04 | `hasAudio===true` 的 video 卡不得同卡挂 `voice` | 同上 |
| VR-M05 | trip 存在任意 `voice` 时，至少 1 章 `moment` 且该章有带 voice 的 card | 同上（警告级可配置） |

### 3.5 叙事内容

| 规则 ID | 检查 | 错误码 |
|---------|------|--------|
| VR-N01 | 禁用词表命中 → 失败 | `E_VALIDATE_MANIFEST`（已实现；词表见 `config.yaml` → `narrative.banned_phrases`） |
| VR-N02 | `meta.places` 与章 `curation.places` 不得含未在 assets 出现的境外城市（启发式） | `WARN:`（已实现） |
| VR-N03 | caption 不得等于 transcript 全文（>80% 重合） | `WARN:`（已实现） |
| VR-N04 | chapter lead 不得复述 chapter.title（开头一致或高重合） | `E_VALIDATE_MANIFEST`（已实现） |

禁用词默认：`config.yaml` → `narrative.banned_phrases`。

### 3.6 流水线一致性

| 规则 ID | 检查 | 错误码 |
|---------|------|--------|
| VR-S01 | `structure_locked` 时 `locks.structure === true` | `E_VALIDATE_MANIFEST` |
| VR-S02 | `copy_locked` 时 `locks.copy === true` | 同上 |
| VR-S03 | `exported` 时 `privacy.confirmedAt` 非空 | `E_EXPORT_PRIVACY` |

---

## 4. L3 · 资源文件

| 规则 ID | 检查 |
|---------|------|
| VR-F01 | 每个引用的 `displayFile`、`posterFile`、`voice.audioFile` 在 trip 目录下存在 |
| VR-F02 | 导出用图若 `stripExifOnExport`，不得含 GPS EXIF（抽检工具） |

---

## 5. Agent 与校验责任

| Agent | 写入后必须 L1 | 运行前必须 L2 |
|-------|---------------|---------------|
| 0 media_lab | ✅ | — |
| 1 curator | ✅ | ✅ |
| 2 storyteller | ✅ | ✅ |
| 3 publisher | — | L2 + L3 |

---

## 6. 自动修复策略

| 场景 | 行为 |
|------|------|
| 超字数 | Agent 2 截断后重试；仍失败 → `E_NARRATE_RETRY_EXHAUSTED` |
| 缺 alt | Agent 3 用 `caption` 或 `title` 补全，不改 JSON |
| pattern 与 items 不匹配 | **不**静默改，返回 `E_VALIDATE_MANIFEST` |

---

## 7. Fixtures 预期

| 文件 | 应通过 |
|------|--------|
| `trip.example.json` | L1 + L2（VR-M05 可有 voice+moment） |
| `trip.ingest_ready.json` | L1；L2 章结构为占位 |
| `trip.structure_locked.json` | L1 + L2 |
| `trip.copy_locked.json` | L1 + L2 |

---

## 8. 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1 | 2026-05-19 | L2 规则初稿 |
