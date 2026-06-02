# Phase 9 · 附录 A · Quality Gate 算法规格

| 属性 | 内容 |
|------|------|
| **主文档** | [PRD-PHASE9.md](./PRD-PHASE9.md) |
| **代号** | P9-A |
| **文档版本** | v0.9.1 |
| **实现模块** | `travelogue/curation/photo_cull.py`（新建） |
| **更新** | 2026-06-02 |

---

## 1. 算法总览

Quality Gate 对 **trip 内全部 image assets**（全 trip re-cull · D-P9-10）执行 **四段 Pass**。

```text
Pass 1  减噪 · 硬剔除     mediaClass（非 featured）+ 极保守 blur（W1 无 exposure）
Pass 2  组内择优         featured 混合 dedupe/burst 组 + recalc 安全网
Pass 3  轻精选 · 软配额   非 featured ≥ floorTargetNonFeatured
Pass 4  max_photos 提示   方案 B：featured 全留；超 cap 仅 WARN
```

**与 ingest dedupe 分工**（Kickoff）：

| 阶段 | 职责 |
|------|------|
| **ingest 0b** | burst/phash **主去重**（保持现网逻辑不变） |
| **cull Pass 2** | **不重复** ingest 已删片；处理 **featured+material 同组多留**、`travelogue cull --recalc` |

**执行时机**：ingest 循环 **结束后**、低分辨率 `apply_layout_eligibility_marks` **之前**。

---

## 2. 输入 / 输出

### 2.1 输入

| 信号 | 来源 | 用途 |
|------|------|------|
| `quality.sharpness` | ingest | Pass 1/3 |
| `mediaClass` | `media_classify.py` | Pass 1 |
| `userTier` | ingest / 双文件夹 | Pass 1–4 豁免 |
| `burstGroupId` / `dedupeGroupId` | ingest dedupe | Pass 2 |
| `subjectClass` | CLIP（W2+ / curate 时）| P1 Pass 3 加权 |
| `faces` / `faceCount` | subject_detect | P1 人像加权 |

### 2.2 计数口径 · `N_scan`

```text
N_scan = len(trip.assets where type=image)   # 全 trip，非单 batch
N_feat = count(userTier == featured)
N_mat  = N_scan - N_feat
```

增量 ingest 仍 **全 trip re-cull**，保证 `cullSummary` 与 eligible 池一致。

---

## 3. Pass 1 · 减噪（硬剔除 · W1 保守）

### 3.1 规则（W1 生效）

| 规则 ID | 条件 | excludeReason | featured 豁免 |
|---------|------|---------------|---------------|
| **R-P9-01** | `mediaClass ∈ hard_exclude_media_classes` | `media_class` | ✅ 默认豁免 |
| **R-P9-02** | `sharpness < blur_threshold`（见 §3.2） | `blur` | ✅ 豁免 |
| **R-P9-03** | 全黑/全白 exposure | `exposure_extreme` | ⏸ **W1 不实现** |

### 3.2 blur 阈值（保守 · 避免 Pass 1 吃掉 80% 配额）

```python
# W1：只用绝对底 + 极离群分位，不用 P5 作为主阈值
P2_batch = percentile(sharpness of non-featured, 2)   # 第 2 分位，非 P5
blur_threshold = max(
    cull.sharpness_absolute_min,   # 默认 0 或配置极小正数
    P2_batch * 0.85,               # 仅剔除明显低于 P2 的离群
)
```

**原则（D-P9-13）**：Pass 1 目标 **明显废片**；80% 地板主要由 **Pass 3** 保障。

### 3.3 Pass 1 后统计

写入 `cullSummary.excludedByReason` 分项。

---

## 4. Pass 2 · 组内择优

### 4.1 何时生效

| 场景 | 行为 |
|------|------|
| 组内 **全非 featured** 且 ingest 已留 1 张 | **通常 skip**（与 ingest 一致） |
| 组内含 **≥1 featured** | **全部 featured** + **最多 1** 张非 featured（`cullScore` 最高） |
| `cull --recalc` | 对仍共享 `cullGroupId` 的多张 **强制** 择优 |

### 4.2 分组键

`cullGroupId = burstGroupId ?? dedupeGroupId`（写入 `quality.cullGroupId`）。

### 4.3 excludeReason

组内落选：`duplicate_group`。

---

## 5. Pass 3 · 轻精选（软配额）

### 5.1 评分 · P0（W1 默认）

```text
cullScore = 0.55 × norm(sharpness)
          + 0.25 × mediaClassWeight
          + 0.20 × featuredBonus   # material=0；featured 不参与 Pass 3 剔除
```

### 5.2 评分 · P1（W2 · 可选）

见 v0.9.0 公式；`cull.mode=rules` 强制 P0。

### 5.3 80% 地板（修订口径）

```text
floorTargetNonFeatured = ceil(cull.keep_ratio_floor × N_scan)   # 默认 ceil(0.80 × N_scan)
N_min = max(floorTargetNonFeatured, cull.min_keep)              # min_keep 默认 15

Pass 3 输入池 = 非 featured 且 Pass 1–2 后仍 eligible

若 len(输入池) <= N_min:
  → 跳过 Pass 3（全留），写 cullSummary.pass3Skipped = "pool_at_or_below_floor"

若 len(输入池) > N_min:
  → 按 cullScore 降序，保留 Top N_min，其余 excludeReason=cull_quota

若最终 eligible_non_feat / N_scan < keep_ratio_floor:
  → 写 cullSummary.floorNotMet = true（W1 仍可通过 AC-P9-02 · 见 ACCEPTANCE）
```

**分子不计 featured**（D-P9-02）：达标统计 `eligible_non_feat`；featured 叠加在 layout 池上。

### 5.4 用户摘要示例

```text
scanned=100, featured=15, eligible=97 (non-feat 82)
→ 「经挑选 97 张进入排版（精选 15 张已为您保留）」
```

CLI 可展示 `non-feat 82/85`（85 = N_mat）。

---

## 6. Pass 4 · max_photos（方案 B）

不变：超 cap **不剔除**；`maxPhotosExceeded` + WARN。

---

## 7. featured 豁免

不变（F-P9-FEAT-01～05）。**低清**：见 P9-C · featured 在 low-res 阶段仍 eligible。

---

## 8. Fail-open（D-P9-14）

`apply_photo_cull` 捕获异常时：

1. 所有 image `layoutEligible=true`  
2. `cullSummary.error = str(exc)`  
3. **不**写 cull 类 `excludeReason`  
4. ingest / Job **继续**（不 raise）

---

## 9. 验收标准

| ID | 条件 |
|----|------|
| **AC-P9-A-01** | mao：eligible_non_feat / N_scan ≥ 0.80 **或** `floorNotMet` 且 Pass 1–2 已保守 |
| **AC-P9-A-02** | 双文件夹 featured 100% eligible |
| **AC-P9-A-03** | featured+material 同 dedupe 组 → featured 全留 + ≤1 material |
| **AC-P9-A-04** | `cull.enabled=false` → Phase 7 等价 |
| **AC-P9-A-05** | fail-open 不阻断 ingest |
| **AC-P9-A-06** | 同 trip 双跑 cull  deterministic |

---

## 10. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.9.1 | 2026-06-02 | Kickoff：Pass 分工 · blur 保守 · floor 口径 · W1 无 exposure |
| v0.9.0 | 2026-06-02 | 初稿 |
