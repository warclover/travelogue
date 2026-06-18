# Travelogue · 分层精选 PRD（Stratified Curation）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue |
| **文档版本** | v1.0.0-STRATIFIED |
| **状态** | Approved · 阶段讨论纪要落地 |
| **代号** | 「分类建标准、相册内排序、用途选型」— 解决混合语料下基线失真 |
| **前置条件** | [PRD-AESTHETIC-ALIGNMENT.md](./PRD-AESTHETIC-ALIGNMENT.md) M0–M3 工程已落地；`stratum` / `purpose` / 分层 blend 代码骨架已有 |
| **关联文档** | [PRD-AESTHETIC-ALIGNMENT.md](./PRD-AESTHETIC-ALIGNMENT.md)、[PRD-PORTRAIT-CULL.md](./PRD-PORTRAIT-CULL.md)、[cover-selection-plan.md](./cover-selection-plan.md)、[aesthetic-alignment/RUBRICS-v1.md](./aesthetic-alignment/RUBRICS-v1.md)、[aesthetic-alignment/DATA-CONTRACT.md](./aesthetic-alignment/DATA-CONTRACT.md)、[aesthetic-alignment/TASKS-STRATIFIED.md](./aesthetic-alignment/TASKS-STRATIFIED.md) |
| **实现模块（规划）** | `aesthetic_blind_review.py`、`aesthetic_learned_eval.py`、`aesthetic_merged_eval.py`、`album_profile`（新建）、`aesthetic_score.py`、`cover_scoring_v2.py` |
| **更新日期** | 2026-06-18 |

> **定位**
>
> - **问题**：游记相册组成差异极大（风景 70–100%、人像 70–100% 等）。用**单一 overall 人类分 + 单一 pooled SRCC** 验收，会在 skew 相册上系统性失真（merged v2：导出基线 0.295 → stratum blend pooled 0.191，但分 trip 内均有提升）。
> - **结论**：「好照片」是 **内容类型（stratum）× 图位用途（purpose）** 的二维问题，不是一维 overall。
> - **本 PRD**：在不推翻 AA 三层信号（rules / learned / MLLM）的前提下，升级**标注协议、语料结构、校准方式、选图策略、验收门禁**为**分层优先**。

---

## 0. 决策（阶段讨论拍板）

| ID | 议题 | 裁定 |
|----|------|------|
| **DS-1** | 人类标签粒度 | **按 stratum 分类打 1–5**，每类独立 rubric；允许盲评时**修正 stratum** |
| **DS-2** | 语料结构 | **全局校准库**（分层配额）+ **单册验收集**（按 album profile 抽样），不追求每 trip 各类均衡 |
| **DS-3** | 模型策略 | **共享特征 + 分 stratum 校准 + 分 purpose 权重**；全局一套参数，不按 trip 各一套 |
| **DS-4** | 选图策略 | **相册内同类比较 + purpose**；skew 相册用 profile，不用全局绝对分一刀切 |
| **DS-5** | 验收门禁 | **分层 SRCC + 分层 min-n + 单册 purpose 胜率**；pooled SRCC **仅健康检查**，不作 G3 主门禁 |
| **DS-6** | 默认开关 | AC-SC-* 未全过前，**禁止**改 `AppConfig.ml_calibrate` 默认 |

---

## 1. 设计原则（在 AA-PR-* 之上增补）

| ID | 原则 | 说明 |
|----|------|------|
| **SC-PR-01** | 分类建标准 | 跨相册学的是「某类图什么叫好」，不是「某本游记的平均口味」 |
| **SC-PR-02** | 相册内相对 | 同一 stratum 内用分位 / top-k 比较，避免风景册用人像册绝对分校准 |
| **SC-PR-03** | 用途正交 | cover / hero / moment / solo 与 stratum 正交；选型在「同类池 × 用途」内进行 |
| **SC-PR-04** | 分层可验 | 每个有足够样本的 stratum 必须单独可算 SRCC，禁止只看总数 |
| **SC-PR-05** | 诚实分层 | 自动 stratum 可错；人类可改；`general` 占比设上限，逼细分类 |
| **SC-PR-06** | 继承 fail-open | 与 [PRD-AESTHETIC-ALIGNMENT.md](./PRD-AESTHETIC-ALIGNMENT.md) AA-PR-03/04/05 一致 |

---

## 2. 问题诊断（混合基线为何失败）

### 2.1 实测（merged v2 · 2026-06-18）

| 语料 | n | 组成 | rules SRCC | stratum blend SRCC |
|------|---|------|------------|-------------------|
| demo-2025-6 | 109 | group 为主 | 0.237 | **0.273** |
| demo-fc8b3a5c08（锡兰） | 54 | 修复前误为 group 为主 | -0.004 | **0.218** |

**锡兰册纠正（2026-06-18）**：eligible 146 中横图 **119 张（≈81%）**；原把 `quality.faceCount`（无 `faces[]` bbox）当合影 → 误标 group 122。修复后 stratum：**landscape 119 / person 27**。已标 54 张人类分仍有效，stratum 已重算为 landscape 46 / person 8。
| **pooled 合并** | 163 | group 127 / person 25 / general 11 | 0.109 | **0.191** |

- 分 trip **均有提升**，pooled **反而低于**导出时 rules 基线（0.295）→ 说明 **评估方式与语料结构** 不匹配，而非 learned 全面失效。
- landscape / food 在 merged 中 **几乎为零** → 因 **自动分层误判**（锡兰册已修复，见下）而非相册无风景。

### 2.2 根因归纳

```text
混合标注  →  一个 overall 承载多种审美
混合 SRCC  →  Spearman 对分布 skew 敏感
每 trip 各一套 blend  →  pooled 时参数不一致
无 album profile  →  选图未感知「这本以风景为主」
```

---

## 3. 三维框架

```text
                    purpose（图位）
            cover / hero / moment / solo
                        ↑
stratum（内容类型） ────┼──→ 人类标签（分类 rubric）
 person/group/landscape/food/general
                        ↑
              albumProfile（本册组成）
           例：landscape 0.70 · group 0.05
```

| 维度 | 回答的问题 | 数据字段（规划） |
|------|------------|------------------|
| **stratum** | 这是什么类型的图？按什么标准判好坏？ | `review_stratum` / 可改 `stratum` |
| **purpose** | 用在什么位置？ | `purpose_overall(asset, purpose)` |
| **albumProfile** | 这本游记各类占比？ | `trip.curation.albumProfile` |

---

## 4. 内容分类体系（v1）

| stratum | 自动判定（初版） | 精选关注点 |
|---------|------------------|------------|
| **person** | 单人脸 | 表情、清晰度、是否废片 |
| **group** | 多人脸 | 闭眼、糊脸、全员入画 |
| **landscape** | 风景/建筑/自然，少人 | 构图、光线、层次、代表性 |
| **food** | 食物主体 | 食欲感、色彩、主体清楚 |
| **general** | 混合或不确定 | 通用「是否值得重点展示」 |

**规则**

- 盲评 UI 展示自动 stratum，**允许作者修改**并写回标签。
- 单册 `general` 抽样占比 ≤ **15%**；全局库 `general` ≤ **10%**。
- 后续可拆 `street` / `architecture`，待 landscape 样本 ≥50 再议。

人类打分 rubric 见 [aesthetic-alignment/RUBRICS-v1.md](./aesthetic-alignment/RUBRICS-v1.md)。

---

## 5. 语料与标注

### 5.1 两类语料

| 类型 | 目的 | 抽样规则 |
|------|------|----------|
| **全局校准库** | 拟合 stratum blend、purpose 权重、跨 trip 统一参数 | 多 trip；**每 stratum 有下限** |
| **单册验收集** | 验证「这本游记选得好不好」 | 按 **albumProfile 比例** 分层抽；每类至少 k 张 |

### 5.2 全局校准库配额（v3 目标）

| stratum | 目标张数 | 说明 |
|---------|----------|------|
| group | 50 | 锡兰类等合影向相册 |
| person | 40 | 人像向相册 |
| landscape | 50 | 风景向相册 |
| food | 30 | 美食向相册 |
| general | 20 | 混合/边界 |
| **合计** | **190–250** | 允许增量冻结 |

**已有资产**：merged v2 的 163 张保留为 group/person 主来源；**下一批定向补** landscape + food，而非再随机混合抽。

### 5.3 单册验收集

- 每本游记 **20–40 张**（或 eligible 的 15–25% 取小）。
- 按 `albumProfile` 加权分层；某类为 0% 则不抽该类。
- 纯风景册：可 100% landscape 样本 + 额外 5–10 张 **cover pairwise**。

### 5.4 标签字段（扩展）

> **完整 schema**：[aesthetic-alignment/DATA-CONTRACT.md](./aesthetic-alignment/DATA-CONTRACT.md) §3–§7（`stratumAuto` · `defectTags` · 归一化 · 审计）。

```jsonc
{
  "assetId": "asset-042",
  "tripId": "demo-fc8b3a5c08",
  "stratum": "group",              // 作者可改 · 评测权威
  "stratumAuto": "group",          // 系统初判（可选）
  "humanScore": 4,                   // 1–5 Likert
  "defectTags": [],                // Phase 3：closed_eyes, blur_face
  "notes": ""
}
```

### 5.5 可选：图位 pairwise（Phase 2+）

对 cover / hero 候选做 **A/B**（「哪张更适合当封面」），降低 1–5 打分噪声；工具复用 `export_pairwise_pairs` / `algorithm_v2_signoff`。

---

## 6. 相册组成（albumProfile）

### 6.1 计算时机

`ingest` 或 `curate` 预检后，对 layout-eligible 图片统计 stratum 占比，写入：

```jsonc
"trip": {
  "curation": {
    "albumProfile": {
      "version": "1",
      "computedAt": "2026-06-18T12:00:00Z",
      "eligibleImages": 146,
      "strata": {
        "person": 0.05,
        "group": 0.72,
        "landscape": 0.18,
        "food": 0.02,
        "general": 0.03
      },
      "dominantStratum": "group"
    }
  }
}
```

### 6.2 用途

- 盲评抽样加权（单册验收集）。
- 选图：**同类池内分位** `score / P75_within_album(stratum)`。
- MLLM 短名单：优先从 **dominant + secondary** stratum 取候选。
- Studio 展示：「本册以合影为主，封面将优先在 landscape/横图规则下比较」。

---

## 7. 模型与校准（在 AA 路线 A/B/C 上升级）

### 7.1 信号层（不变）

- L1：rules dims + Portrait → `subjectClarity`
- L2：learned（nima 等）→ `learnedAesthetic`
- L3：MLLM 短名单 → `mllmScore` + `critique`

### 7.2 校准层（升级）

| 项 | v0.1（旧） | v1（本 PRD） |
|----|------------|--------------|
| blend | 全局或每 trip 各一套 | **跨 trip 统一** `stratum_blends`（在全局库上拟合） |
| purpose 权重 | 全局 purpose 预设 | **stratum × purpose** 网格或至少 purpose 分层拟合 |
| 相对分 | 无 | **album-relative multiplier**（同类分位） |
| 验收 | pooled SRCC +0.15 | **分层 SRCC 表** + 加权 Δ |

### 7.3 选图流水线

```text
1. 计算 albumProfile + 每张 stratum + purpose 分
2. 封面：layout-eligible 池 → cover purpose
         同类内 album-relative top-k → logit（含 MLLM tie-break）
3. hero/moment：章节候选 → 先 stratum 过滤/加权 → purpose 比较
4. group/person：Portrait 缺陷硬降权（闭眼/糊脸不进 top-k）
```

---

## 8. 评测方法论（分层版）

| 方法 | 用途 | 门禁级别 |
|------|------|----------|
| **分层 SRCC** | 每 stratum：rules vs stratum-blend | **主门禁** |
| **分层 min-n** | 每 stratum 样本 ≥ N 才可判过 | **主门禁** |
| **单册 purpose 胜率** | rules vs aligned 的 cover/hero/moment | **主门禁**（按册验） |
| **pooled SRCC** | 全库 Spearman | **健康检查**（不阻塞 G3） |
| **加权分层 Δ** | Σ (w_s · ΔSRCC_s)，w_s ∝ n_s | **AC-SC-02 候选** |
| **缺陷率** | 重点位闭眼/糊脸 | 继承 Portrait AC-PC-D* |

---

## 9. 里程碑（Stratified Phase 0–4）

| 阶段 | 名称 | 出口 |
|------|------|------|
| **P0** | 标准冻结 | RUBRICS-v1 + 分层 signoff 模板 + AC 文案更新 |
| **P1** | 分层标注协议 | corpus v3 + 全局库 ≥190 张分层标签 |
| **P2** | 分类校准 | 跨 trip 统一 blend + albumProfile + album-relative 分 |
| **P3** | 人像质量闭环 | Portrait M1 + defectTags + 重点位硬规则 |
| **P4** | 产品化 | Studio 展示 + profile-aware 短名单 + 可选用户微调 |

任务拆解见 [aesthetic-alignment/TASKS-STRATIFIED.md](./aesthetic-alignment/TASKS-STRATIFIED.md)。

---

## 10. 验收标准（AC-SC-*）

| ID | 条件 |
|----|------|
| **AC-SC-00** | 全局校准库冻结：每 stratum ≥ **min-n**（landscape/food ≥20，其余 ≥30），可复跑分层 SRCC |
| **AC-SC-01** | 对每个 **n ≥ min-n** 的 stratum：`stratum-blend` SRCC **>** 该层 rules SRCC |
| **AC-SC-02** | **加权分层 Δ** ≥ 0.10，或任一主 stratum（n≥40）Δ ≥ 0.15；**不以 pooled +0.15 为唯一条件** |
| **AC-SC-03** | 每本验收集：cover/hero/moment 自动化+人工 pairwise 胜率 ≥ **60%**（至少 3 本不同 profile 的 dogfood） |
| **AC-SC-04** | `albumProfile` 写入 trip；skew 册（dominant ≥70%）选图不回归 |
| **AC-SC-05** | 继承 AC-AA-04~08（fail-open、MLLM 缓存、调用上限、开关回退） |
| **AC-SC-06** | 关闭分层校准可回到 rules-only 行为 |

### 与 AC-AA-* 的映射

| 原 AC | 本 PRD 处理 |
|-------|-------------|
| AC-AA-00 | → **AC-SC-00**（分层配额） |
| AC-AA-01 | → **AC-SC-01**（按层验证） |
| AC-AA-02 | **降级**为健康检查；主门禁 → **AC-SC-02** |
| AC-AA-03 | → **AC-SC-03**（按册 + pairwise） |

---

## 11. 数据模型增补

```jsonc
"trip": {
  "curation": {
    "albumProfile": { /* §6.1 */ },
    "aestheticAlignment": { /* 已有 telemetry */ },
    "stratifiedSignoff": {
      "version": "1",
      "corpusVersion": "v3",
      "perStratumSrcc": { "group": 0.31, "landscape": 0.42 },
      "recordedAt": "..."
    }
  }
}
```

标签 corpus：`docs/acceptance-records/aesthetic-alignment-corpus.v3.json`（规划）。

---

## 12. 配置规格增补

```yaml
aesthetic:
  # 继承 PRD-AA §8 …
  stratified:
    enabled: true
    use_album_relative: true      # P2：同类分位乘数
    global_stratum_blends:        # P2：跨 trip 统一（由 v3 校准回填）
      group: 0.35
      person: 0.40
      landscape: 0.38
      food: 0.30
      general: 0.25
    min_stratum_samples: 30       # 验收 min-n
    general_cap_ratio: 0.15       # 单册 general 抽样上限
```

---

## 13. 风险与缓解

| 风险 | 缓解 |
|------|------|
| 自动 stratum 误判 | 盲评可改；**无 bbox 时不用 quality.faceCount**；横图优先 landscape（2026-06-18 锡兰册修复） |
| 某类样本长期不足 | 定向补 corpus；该类暂不参与 blend 拟合 |
| 作者打分尺度不一致 | 分类 rubric + pairwise；分册验收 |
| 工程范围膨胀 | P0–P2 不新建训练平台；复用 pyiqa + 网格搜索 |

---

## 14. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0.0 | 2026-06-18 | 初版：混合基线诊断；三维框架；语料/标注/校准/验收升级；AC-SC-*；P0–P4 里程碑 |
