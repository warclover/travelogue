# 分层精选 · 标签与语料数据契约

> **权威**：标注 JSON、盲评导出、合并语料与 QA 以本文为准；[PRD-STRATIFIED-CURATION.md §5.4](../PRD-STRATIFIED-CURATION.md#54-标签字段扩展) 仅作摘要。  
> **关联**：[RUBRICS-v1.md](./RUBRICS-v1.md) · [TASKS-STRATIFIED.md](./TASKS-STRATIFIED.md) · 实现 `travelogue/curation/aesthetic_blind_review.py`

---

## 1. 文档范围

| 产物 | 路径示例 | 用途 |
|------|----------|------|
| **人类标签** | `docs/acceptance-records/aesthetic-human-labels.*.json` | SRCC / blend 校准 / signoff |
| **盲评导出** | `docs/acceptance-records/aesthetic-blind-export.*.json` | 生成 HTML 盲评、初始化标签 |
| **合并语料** | `docs/acceptance-records/aesthetic-human-labels.merged.v3.json` | 全局校准库（frozen） |
| **stratum 审计** | `docs/acceptance-records/aesthetic-stratum-audit.*.json` | 初判 vs 人工层别 diff |
| **purpose pairwise** | `docs/acceptance-records/purpose-pairwise.*.json` | 图位 A/B 胜率（AC-SC-03） |

本契约**不**覆盖 `trip.json` 全 schema；仅定义审美标注与 `trip.curation` 分层相关增量字段。

---

## 2. 枚举 · stratum

| 值 | 含义 | 初判函数 |
|----|------|----------|
| `person` | 单人照 | `review_stratum_for_asset()` |
| `group` | 合影（faceCount > 1） | 同上 |
| `landscape` | 风景 / 建筑 / 横图自然 | 同上 |
| `food` | 美食 | 同上 |
| `general` | 混合 / 边界 / 无法归类 | 同上 |

**规则来源**：`travelogue/curation/aesthetic_blind_review.py` · `review_stratum_for_asset`（人脸数 → aspect → subjectClass / semantic category）。

标注与评测脚本以 row 上的 **`stratum`（人工终值）** 分层；`stratumAuto` 仅作审计与 UI 提示，**不参与** SRCC 分桶 unless 显式 fallback（见 §4.2）。

---

## 3. 人类标签 JSON · `aesthetic-human-labels.*.json`

### 3.1 顶层字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `version` | string | ✓ | 语料版本；合并库当前为 `"3"` |
| `frozen` | boolean | | `true` 表示基线锁定，合并脚本默认只读 |
| `frozenAt` | string (ISO8601) | | 冻结时间 |
| `notes` | string | | 人工说明 |
| `mergedAt` | string | | 合并产物写入时间 |
| `trips` | string[] | | 来源 tripId 列表（合并库） |
| `sourceExport` | string | | 自盲评导出初始化时的 `exportedAt` |
| `stratumAudit` | object | | stratum 批量修正元数据（见 §6） |
| `rows` | array | ✓ | 标签行 |

### 3.2 `rows[]` · 标签行

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `assetId` | string | ✓ | trip 内 asset id |
| `tripId` | string | ✓ | 所属 trip |
| `stratum` | enum | ✓ | **人工终值**；盲评 UI 可改；SRCC / blend 分桶依据 |
| `stratumAuto` | enum | | **系统初判**；导出或审计时写入；可与 `stratum` 不同 |
| `humanScore` | number | ✓* | 人类审美分；见 §5 |
| `displayFile` | string | | 相对 trip 根的路径；合并/审计用 |
| `predictedOverall` | number | | 导出快照 · rules/overall |
| `predictedCover` | number | | 导出快照 · cover purpose |
| `predictedHero` | number | | 导出快照 · hero purpose |
| `predictedMoment` | number | | 导出快照 · moment purpose |
| `predictedSolo` | number | | 导出快照 · solo purpose |
| `defectTags` | string[] | | **P3 预留** · 人像缺陷标签；见 §7 |
| `notes` | string | | 标注员自由备注 |

\* 合并与 signoff 脚本仅保留 `humanScore != null` 的行。

**唯一性**：合并库内 `(tripId, assetId)` 唯一；`scripts/aesthetic_merge_labels.py` 后写入覆盖先写入。

### 3.3 示例

```jsonc
{
  "version": "3",
  "frozen": true,
  "notes": "Merged v3 · 332 rows",
  "rows": [
    {
      "assetId": "asset-091",
      "tripId": "demo-2025-6",
      "stratum": "landscape",
      "stratumAuto": "group",
      "humanScore": 3,
      "displayFile": "assets/asset-091-w2400.webp",
      "predictedOverall": 0.5682,
      "defectTags": []
    }
  ]
}
```

---

## 4. `stratum` vs `stratumAuto`

### 4.1 语义

| 字段 | 写入时机 | 可变性 | 消费方 |
|------|----------|--------|--------|
| **`stratumAuto`** | 盲评导出、`build_review_row()` | 仅随资产 metadata / 初判算法变化 | HTML 盲评 UI 默认值、审计 diff |
| **`stratum`** | 标注员在盲评 UI 修改，或 `aesthetic_stratum_audit.py --apply` | 人工权威 | `grid_search_stratum_blend`、`aesthetic_stratified_signoff`、分层 SRCC |

### 4.2 Fallback 规则（工具链）

| 场景 | 行为 |
|------|------|
| 盲评 HTML 展示 | 显示 `stratum`；下拉默认 `stratumAuto \|\| stratum` |
| 导出 → 初始化 labels | 复制 `stratumAuto`；若缺失则用 `stratum` |
| stratum 审计 `--apply` | 旧 `stratum` → `stratumAuto`；新算法结果 → `stratum` |
| 评测脚本缺 `stratum` | 禁止；必须补全或丢弃该行 |

### 4.3 何时两者应不同

- 初判将「多人合影」标为 `group`，标注员改为 `landscape`（实为风景空镜）。
- 算法升级后审计：保留 `stratumAuto` 记录旧标签，更新 `stratum` 为新初判或人工复核值。

---

## 5. `humanScore` 归一化

**输入格式**（盲评 UI / JSON）：

| 输入 | 示例 | 归一化 |
|------|------|--------|
| Likert 1–5（int 或整 float） | `4` | `(score - 1) / 4` → `[0, 1]` |
| 已是 [0, 1] | `0.75` | 不变 |
| 1–10 分制 | `8` | `score / 10` |

**实现**：`normalize_human_score()` · `aesthetic_blind_review.py`。

**Rubric 含义**：见 [RUBRICS-v1.md](./RUBRICS-v1.md)（按 stratum 补充说明）。

---

## 6. 盲评导出 JSON · `aesthetic-blind-export.*.json`

### 6.1 顶层

| 字段 | 类型 | 说明 |
|------|------|------|
| `exportedAt` | string | ISO8601 |
| `sampleCount` | number | `rows.length` |
| `trips` | object[] | `{ tripId, tripDir? }` |
| `rows` | array | 见下 |

### 6.2 导出行（较标签行多数字段）

| 字段 | 说明 |
|------|------|
| `displayOrder` | 盲评展示顺序（shuffle 后 1-based） |
| `tripDir` | 本地 trip 目录 |
| `imagePath` | 可选绝对/相对预览路径 |
| `dims` | rules aesthetic dims 快照 |
| `humanScore` | 导出时为 `null`，回填至 labels JSON |

生成命令：`python scripts/aesthetic_blind_review.py --export …`  
HTML：`build_blind_review_html()` · P0-7 支持 UI 内改 stratum。

---

## 7. `defectTags`（P3 · 盲评 UI 已支持）

> 状态：**盲评 HTML 可勾选**（P3-2）；选图硬降权待 P3-3。

| 标签 | 含义 | 预期用途 |
|------|------|----------|
| `closed_eyes` | 闭眼（重点人脸） | group/person 重点位硬降权 |
| `blur_face` | 人脸模糊 | 同上 |

**约束**：

- 类型：`string[]`，值取自上表枚举（可扩展需 bump `version`）。
- 仅对 `stratum ∈ {person, group}` 有意义；其他层应为 `[]` 或省略。
- 与 `humanScore` 独立：缺陷标签用于 **AC-PC 缺陷率**，不替代 Likert 分。
- 自动化度量：`python scripts/aesthetic_portrait_defect_signoff.py`（见 §10）。

**示例**：

```jsonc
{
  "assetId": "asset-042",
  "tripId": "demo-fc8b3a5c08",
  "stratum": "group",
  "humanScore": 2,
  "defectTags": ["closed_eyes"]
}
```

---

## 8. stratum 审计块 · `stratumAudit`

由 `scripts/aesthetic_stratum_audit.py --apply` 写入 labels 文档：

| 字段 | 说明 |
|------|------|
| `auditedAt` | ISO8601 |
| `changeCount` | 被改写的行数 |
| `changeRatio` | `changeCount / labeledCount` |
| `oldStrata` / `newStrata` | 层别计数 |
| `auditNote` | 人工说明 |

---

## 9. `trip.curation` 分层相关字段

与标签 JSON 并行、写入 `trip.json`：

### 9.1 `albumProfile`（P2 · AC-SC-04）

| 字段 | 类型 | 说明 |
|------|------|------|
| `version` | string | `"1"` |
| `computedAt` | string | ISO8601 |
| `eligibleImages` | number | layout-eligible 图片数 |
| `strata` | object | `{ stratum: share }`，share ∈ [0,1] |
| `dominantStratum` | enum | 占比最高层 |
| `isSkewed` | boolean | top share ≥ 0.7 |

计算：`album_profile.compute_album_profile()` · curate 时持久化。

### 9.2 `stratumPreference`（P4-3 · 用户微调）

| 值 | 说明 |
|----|------|
| `auto` | 默认 · 按 `albumProfile` |
| `landscape` | 更偏风景 · MLLM / blend 预设 |
| `portrait` | 更偏人像 · 优先 person+group |

Studio：`PATCH /__travelogue/trips/{id}/aesthetic/preference`。

---

## 10. purpose pairwise 标签（摘要）

完整字段见各 `purpose-pairwise.*.json`；核心：

| 字段 | 说明 |
|------|------|
| `purpose` | `cover` \| `hero` \| `moment` |
| `leftAssetId` / `rightAssetId` | A/B 候选 |
| `winner` | `left` \| `right` \| `tie` |
| `comparable` | 是否计入胜率 |

导出：`scripts/aesthetic_purpose_pairwise_export.py`。

---

## 10. 缺陷率 signoff 脚本（P3-4）

```bash
python scripts/aesthetic_portrait_defect_signoff.py \
  --trip demo-1a737d6205:trips/demo-1a737d6205 \
  --write docs/acceptance-records/portrait-defect-dogfood.v3.json

python scripts/aesthetic_portrait_defect_signoff.py \
  --input docs/acceptance-records/portrait-defect-dogfood.v3.json \
  --baseline docs/acceptance-records/portrait-defect-dogfood.baseline.json
```

输出 `aggregate.cover|hero|moment|all.defectRate`；与 baseline 比较时 **current ≤ baseline** 为 pass（AC-PC-D proxy）。

---

## 11. 版本与兼容

| version | 说明 |
|---------|------|
| `1` | AA 初版标签（无 stratumAuto） |
| `2` | 分层 stratum 字段引入 |
| `3` | merged v3 冻结 · 332 张 · 含 stratumAuto 审计 |

**破坏性变更**：新增 `defectTags` 枚举值、修改 stratum 枚举 → bump 文档 version + 修订记录。

---

## 12. 修订记录

| 日期 | 说明 |
|------|------|
| 2026-06-18 | P0-8 初版：`stratumAuto` / `defectTags` / 盲评与 trip.curation 契约 |
| 2026-06-18 | §10 缺陷率 signoff 脚本（P3-4） |
