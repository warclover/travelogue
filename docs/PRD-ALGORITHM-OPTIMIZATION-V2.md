# 算法优化 V2.0 PRD

| 属性 | 内容 |
|------|------|
| **文档版本** | v2.0.0-rc |
| **状态** | RC · 已落地 · **默认 v2**（开发期无灰度） |
| **评审纪要** | [algorithm-v2-prd-review-2026-06-05.md](./acceptance-records/algorithm-v2-prd-review-2026-06-05.md) |
| **实施清单** | [IMPLEMENTATION-ALGORITHM-V2.md](./IMPLEMENTATION-ALGORITHM-V2.md) |
| **日期** | 2026-06-05 |
| **负责人** | CTO / 算法 |
| **范围** | 封面·英雄打分重构 · 清晰度信号统一 · 启发式聚类语义修正 |
| **实现模块** | `curate_scoring.py` · `cover_scoring_params.py` · `sharpness.py` · `clip_encoder.py` · `asset_quality.py` |
| **关联** | [cover-selection-plan.md](./cover-selection-plan.md) · [algorithm-inventory.md](./algorithm-inventory.md) · [PRD-PHASE9-A-quality-gate-algorithm.md](./PRD-PHASE9-A-quality-gate-algorithm.md) · [layout_scoring.py](../travelogue/curation/layout_scoring.py) |
| **原则** | **质量优先，不受拍摄时间限制**；trip 内相对排序；确定性 + fail-open |

**背景**：全项目算法工程化水平高（回退链、预算、增量缓存到位），短板集中在「打分体系手工魔法常数、缺数据驱动标定」，且 cover 连乘 / layout 加性 / mosaic 乘性惩罚口径割裂；底层 `sharpness` 信号不稳并向上传导。本 PRD 以 **投入产出比** 排序，优先修复产品门面（封面/英雄），再统一底层质量信号，最后修正启发式聚类语义。

---

## 1. 问题定义

### 1.1 现状评分（算法科学性审计摘要）

| 算法 | 模块 | 科学性 | 核心问题 |
|------|------|--------|----------|
| dHash + 汉明去重 | `phash.py` | ⭐⭐⭐⭐ | 业界标准，无异议 |
| CIE Lab ΔE76 | `color_metrics.py` | ⭐⭐⭐⭐ | sRGB→Lab 正确；ΔE76 偏老但够用 |
| 清晰度 = 边缘方差 | `sharpness.py` | ⭐⭐⭐ | **内容混淆**，跨图不可靠 |
| geo 分段 | `geo_events.py` | ⭐⭐⭐ | 自适应阈值 ad-hoc，fail-open 稳健 |
| HDBSCAN + 真 CLIP | `scene_clusters.py` | ⭐⭐⭐⭐ | 归一化+回退正确；eps 偏紧 |
| 启发式 8 维 embedding | `clip_encoder.py` | ⭐ | **序数误用、量纲主导、色相环形** |
| layout 加权和 | `layout_scoring.py` | ⭐⭐⭐⭐ | 结构科学，权重手调 |
| **封面/英雄连乘** | `curate_scoring.py` | ⭐⭐ | **最需优化：画幅主导、难标定** |
| mosaic 乘性惩罚 | `mosaic/scorer.py` | ⭐⭐⭐ | 模型合理，魔法常数多 |
| beam search | `mosaic/search.py` | ⭐⭐⭐⭐ | 预算/缓存设计良好 |

### 1.2 三个结构性短板（按严重度）

#### P0 · 封面/英雄「多因子连乘」

当前：

```text
effective_cover_score = base × media × quality × person × face_bbox × saturation
                      × composition × thirds × featured × anchor
```

其中 `base` 为 raw 画幅比（web `w/h` 约 0.5–3.6+，panorama 再 ×1.2），其余乘子约在 `[0.35, 1.35]`。最终分数量级被画幅比主导——实为「画幅比优先，质量微调」，与 [cover-selection-plan.md](./cover-selection-plan.md) 写的「质量优先」结构性冲突。

连带问题：

- 连乘难标定：单因子边际效应依赖其他乘子取值（强耦合非线性）
- `build_cover_explain` 按 `|mult−1|` 排序 ≠ 真实贡献度，解释误导调参
- `cover_scoring_params.py` 常数全靠盲评试错（R0–R6），不可控
- 跨 trip 绝对分不可比（现靠 top-3 排序规避）

#### P1 · 清晰度「内容混淆」

`sharpness_score` 使用 `FIND_EDGES` 全图方差：高纹理失焦图方差高、低纹理清晰图方差低、浅景深背景虚化拉低主体分。信号为绝对量纲，但 cover quality、cull 阈值、burst 选优、heuristic embedding 均做 **跨图比较**，误差向上传导。

#### P2 · 启发式 8 维 embedding 冒充语义聚类

CLIP 不可用时 `_heuristic_vector` → L2 归一 → HDBSCAN(cosine)。`sharp` 未归一主导向量方向；`subject_idx` 序数误用；`hue` 环形量线性化。默认配置下「场景聚类」≈「按清晰度分箱」。

### 1.3 不在本轮范围

| 类别 | 说明 |
|------|------|
| ingest phash / WebP 管线 | 不重写 |
| geo 分段 / 章 cap | 阈值微调可记录，非主项 |
| mosaic beam search 架构 | 保留乘性惩罚语义 |
| ΔE76 → ΔE2000 | 低优，封面链路影响面窄 |
| CLIP 安装率推广 | 单独运营项；本轮只修 fallback 语义 |
| 画幅硬门槛（mobile/web 池） | **保留**，与软先验分离 |
| `takenAt` / geo / sceneCluster 进封面分 | **明确禁止**（延续 cover-selection-plan） |

---

## 2. 目标与非目标

### 2.1 目标

| ID | 目标 | 衡量方式 |
|----|------|----------|
| **ALG-V2-01** | 封面打分以**质量因子**为主、画幅为软先验 | 固定 fixture：平庸全景不得压过优质 16:9 |
| **ALG-V2-02** | 打分可解释、可单因子 A/B | `coverExplain` 输出可加性贡献项 |
| **ALG-V2-03** | 盲评不退化 | 人工盲评 A 率 ≥ v1 基线；Kendall τ(v1,v2) ≥ 0.85 |
| **ALG-V2-04** | 清晰度信号跨模块一致 | cover / cull / burst / heuristic 共用归一化出口 |
| **ALG-V2-05** | 启发式路径语义诚实 | 产品/日志不再称「语义场景聚类」；或向量修复后 cluster 可解释 |
| **ALG-V2-06** | 为数据驱动标定铺路 | 盲评 JSON 可导出 feature 矩阵 + pairwise label |

### 2.2 非目标

- 本轮不上全量 logistic 回归自动上线（S2 标定为 Phase 2）
- 不统一 mosaic 乘性惩罚为加性模型（长期特征层统一即可）
- 不改动 featured 池逻辑（有 featured 时只在 featured 子池比）
- 不引入 pyiqa / 新深度学习审美模型

---

## 3. 总体方案：三阶段交付

```text
Phase A（P0）封面/英雄  连乘 → 加性 logit  · 2–3 周
Phase B（P1）清晰度      Laplacian + ROI + trip 内 percentile  · 1–2 周（可与 A 后半并行）
Phase C（P2）启发式向量  降级命名 或  快速特征修复  · 1–3 人日
Phase D（P3）数据标定    pairwise logistic / Bradley-Terry  · 2–4 周（依赖盲评样本）
Phase E（P4）特征层统一  cover / layout / mosaic 共享特征定义  · 按需
```

**Feature Flag**（`config.curate` / `config.ingest`）：

| 开关 | 默认 | 说明 |
|------|------|------|
| `cover_scoring.version` | 默认 **`v2`** | `v1` 保留连乘可回退，`v2` 加性 logit |
| `ingest.sharpness.version` | 默认 **`v2`** | 重算 `quality.sharpness`；`sharpnessLegacy` 并存 |
| `vision.heuristic_embedding.version` | `v1` → `v2` | 向量定义升级 |
| `vision.heuristic_cluster_label` | `scene` → `quality_bucket` | 仅文案/telemetry，不改 cluster ID 字段名 |

---

## 4. Phase A · 封面/英雄打分 V2（P0）

### 4.1 设计原则

1. **硬门槛不变**：`cover_asset_pool` / `aspect_kind` 过滤逻辑不改（mobile 竖、web 横、方图出局等）。
2. **画幅 = 软先验**：映射到有界 `[0, 1]` 特征，权重 capped（建议 ≤ 25% logit 总量）。
3. **质量 = 主信号**：清晰度、色彩、三分法、审美等占主导权重。
4. **用户意图后置**：`featured` ×1.35、`anchor` +5% 作为 **post-hoc bonus** 或 tie-break，不进主 logit 标定集。
5. **与 layout 对齐**：采用与 `layout_scoring.py` 相同的「加性加权 + 权重归一化」范式。

### 4.2 数学模型

#### 4.2.1 Cover Score V2

```text
logit(a) = bias_layout
         + w_aspect   · f_aspect(kind, export_layout)      # ∈ [0, 1]，有界
         + w_media    · f_media(mediaClass)                # ∈ [0, 1]
         + w_sharp    · f_sharp(a, pool)                  # trip 内 percentile
         + w_color    · f_color(a)                         # color_richness 归一
         + w_thirds   · f_thirds(a)                        # rule-of-thirds 归一
         + w_comp     · f_composition_bias(kind, layout)   # 横竖偏好，有界
         + w_person   · f_person(a, pool)                  # demote 改为加性惩罚项
         + w_face     · f_face_bbox(a, pool)               # 加分项
         + w_date     · f_date_conf(a)                       # low → 负向
         + w_aesthetic· f_aesthetic(a, pool)              # 可选，aesthetic.enabled

score_v2(a) = exp(logit(a))   # 仅用于排序；也可直接用 logit 排序
```

**画幅特征 `f_aspect`（示例，实现可微调）**：

| export_layout | kind | f_aspect 定义 |
|---------------|------|---------------|
| web | landscape | `sigmoid(−|ratio − 16/9| / σ)`，σ≈0.15 |
| web | panorama | `0.85`（固定软奖励，非 raw ratio） |
| mobile | portrait / tall | `sigmoid((h/w − 1.0) / σ)`，上限 1.0 |

> **禁止**将 raw `w/h` 或 `h/w` 直接作为乘法主项。

#### 4.2.2 Hero Score V2

与 cover 共用特征提取函数 `extract_cover_features(asset, pool, export_layout="web")`，权重向量 `HeroScoringWeights` 单独配置（强调横构图、审美 composition/subjectClarity）。

```text
logit_hero(a) = bias_hero + Σ wᵢ · fᵢ(a)    # 无 mobile 竖图特征
```

#### 4.2.3 Effective Score（用户层）

```text
effective_cover_score_v2 = score_v2(a)
                         × featured_weight_multiplier(a)      # 默认 1.35，后置
                         × anchor_match_multiplier(a)         # 默认 1.05，后置
```

主模型标定与盲评训练 **不含** featured/anchor 项。

### 4.3 配置结构

扩展 `CoverScoringParams` → `CoverScoringParamsV2`：

```yaml
# config.yaml · curate.cover_scoring_v2
curate:
  cover_scoring:
    version: v2          # v1 | v2
  cover_scoring_v2:
    bias_mobile: 0.0
    bias_web: 0.0
    weights:
      aspect: 0.15
      media: 0.05
      sharpness: 0.25
      color: 0.12
      thirds: 0.15
      composition_bias: 0.08
      person: 0.10
      face_bbox: 0.05
      date_confidence: 0.05
      aesthetic: 0.10    # aesthetic.enabled 时生效
    person_demote: 0.72          # 映射为 f_person 惩罚幅度，非乘子
    person_dominant_tag_ratio: 0.40
    # … 其余阈值保留语义，改为特征边界
```

权重默认求和归一化（与 `ScoringWeights.normalized()` 一致）。

### 4.4 Explain 输出 V2

`build_cover_explain` 重写为：

```json
{
  "code": "sharpness",
  "label": "清晰度",
  "feature": 0.82,
  "weight": 0.25,
  "contribution": 0.205,
  "reason": "清晰度提升封面优先级"
}
```

排序键：`abs(contribution)` 降序。`contribution = weight × (feature − feature_baseline)` 或 `weight × feature`（实现时二选一并文档化）。

### 4.5 API 兼容

| 函数 | 行为 |
|------|------|
| `cover_score()` | `version=v1` 调旧实现；`v2` 调 `cover_score_v2()` |
| `effective_cover_score()` | 同上 + featured/anchor 后置 |
| `hero_score()` / `effective_hero_score()` | 同步 v2 |
| `pick_cover_asset_id()` | 读 `config.curate.cover_scoring.version` |
| `score_ranked_cover_ids()` | 输出增加 `"scoringVersion": "v2"` |
| `build_cover_layout_review()` | `coverExplain` 结构升级；保留 `scoreRankedTop3` 契约 |

**保留 `cover_score_v1` 别名** 至 v2 全量切换后 1 个 minor 版本。

### 4.6 默认权重推导（S1 初值）

1. 从 v1 乘子在 **median 特征点** 做 log 线性化：`|ln(mult_default)|` 比例 → 初始 `wᵢ`
2. `w_aspect` 刻意压低（≤ 0.15），补偿 v1 画幅主导
3. R0 盲评基线跑 v2 初值 → 人工微调 → 锁定 S1 默认

### 4.7 验收标准（Phase A）

| 门禁 | 条件 |
|------|------|
| **A-M1 排序稳定** | 10 本盲评相册 Kendall τ(v1,v2) ≥ **0.85** |
| **A-M2 质量优先** | 固定 fixture `tests/fixtures/cover_v2_quality_priority.json` 全通过 |
| **A-M3 盲评不退化** | 双人盲评 **A+B ≥ 9/10** 且 **A ≥ 6/10**（与 [cover-selection-plan.md](./cover-selection-plan.md) M1 对齐） |
| **A-M4 解释可读** | `coverExplain` top-4 贡献项之和可重构 ≥ 80% logit 差（同池内 top-1 vs top-3） |
| **A-M5 回归** | `test_curate_scoring.py` + `test_phase6_cover_scoring.py` + `demo verify` 无回归 |
| **A-M6 CI proxy** | `phase6_cover_blind_review.py --score-proxy` ≥ **60%**（非发布门禁，仅防剧烈退化） |

**固定 fixture 用例（必过）**：

| 用例 ID | 描述 |
|---------|------|
| `CV2-01` | web：16:9 清晰风景 vs 3:1 平庸全景 → 前者 `score_v2` 更高 |
| `CV2-02` | mobile：竖图清晰度差异 2× → 更清晰者胜 |
| `CV2-03` | 人像为主 trip（tag 比 ≥40%）：`person_demote` 不生效 |
| `CV2-04` | `dateConfidence=low` 不得超越同池 top 清晰图 |
| `CV2-05` | featured 后置：两图 logit 接近时 featured 胜 |

### 4.8 与 cover-selection-plan 的关系

| cover-selection-plan | 本 PRD |
|----------------------|--------|
| R1–R6 调乘子 | **暂停**；改为 v2 权重调参 + 单因子 A/B |
| `scoreRankedTop3` 契约 | **保留** |
| M1/M2 盲评门禁 | **保留**，对比对象为 v1 基线 |
| hero 不在范围 | **纳入** Phase A（`hero_score` 同构重构） |
| §1.4 人像为主方案 A | **保留** |

---

## 5. Phase B · 清晰度信号统一（P1）

### 5.1 新算法定义

```python
def sharpness_score_v2(img, *, max_edge=512, roi: Box | None = None) -> float:
    """
    Laplacian variance on grayscale downscale.
    ROI: salientBox > face bbox > center crop 60%.
    """
```

| 项 | v1 | v2 |
|----|----|----|
| 算子 | `FIND_EDGES` 方差 | **Laplacian 方差** |
| 统计区域 | 全图 | **主体 ROI 优先** |
| 输出量纲 | 绝对值（0–数千） | 绝对值 ingest 写入；**消费侧用 percentile** |

### 5.2 统一消费接口

新增 `travelogue/curation/asset_quality.py`（或扩展）：

```python
def normalized_sharpness(
    asset: dict,
    pool: list[dict],
    *,
    bucket_by: str | None = "mediaClass",  # None = 全池
) -> float:
    """Return [0, 1] percentile rank within pool (or bucket)."""
```

**调用方迁移**：

| 模块 | 改动 |
|------|------|
| `curate_scoring._quality_multiplier` | 改用 `normalized_sharpness`；v2 cover 的 `f_sharp` 直接读此值 |
| `photo_cull` Pass 1 | `bucketed_blur_thresholds` 推广到 v2 sharpness；默认开启（v2 切换时） |
| `sort_bucket_asset_ids` burst 选优 | 改用 `normalized_sharpness` 或 v2 原始值 |
| `clip_encoder._heuristic_vector` | `sharp` 维改为 percentile，非 raw |

### 5.3 迁移策略

1. ingest 写入 `quality.sharpness`（v2）+ `quality.sharpnessLegacy`（v1，可选保留 1 版本）
2. `config.ingest.sharpness.version: v2` 触发重算；`travelogue cull --recalc` 文档化
3. cover v2 **依赖** sharpness v2；灰度时两者同开

### 5.4 验收标准（Phase B）

| 门禁 | 条件 |
|------|------|
| **B-M1** | `tests/test_sharpness.py` 新增雪景/天空/虚化人像 fixture |
| **B-M2** | `test_photo_cull.py::test_bucketed_blur_thresholds` 在 v2 下仍通过 |
| **B-M3** | 盲评 `blur` 标签相册 ≤ v1 基线数量（R0 对比） |
| **B-M4** | heuristic embedding 中 sharp 维不再主导余弦方向（见 §6.3 指标） |

---

## 6. Phase C · 启发式 Embedding（P2）

### 6.1 方案选择（二选一，评审拍板）

| 方案 | 工作量 | 做法 |
|------|--------|------|
| **C-A 诚实降级**（推荐先行） | 0.5–1 人日 | telemetry / UI 改称 `quality_bucket`；文档注明非语义聚类 |
| **C-B 向量修复** | 2–3 人日 | 特征工程修复（见 §6.2） |

可先做 C-A 上线，C-B 跟 sprint。

### 6.2 向量修复规格（C-B）

```text
v2 向量（示例 18 维）:
  ratio_norm          # log(ratio) z-score within trip
  sharp_pct           # normalized_sharpness ∈ [0,1]
  luma                # 已在 [0,1]
  sin(2π·hue), cos(2π·hue)
  saturation          # [0,1]
  one_hot(subjectClass) × 8
  face                # 0/1
  width_norm          # w / p95_width(trip)
→ L2 normalize → HDBSCAN(cosine)
```

**禁止**：`subject_idx = index / (n−1)` 序数编码。

### 6.3 验收标准（Phase C）

| 门禁 | 条件 |
|------|------|
| **C-M1** | `EmbedResult.model` 为 `heuristic-v2` 时可区分 |
| **C-M2** | 随机 100 图 trip：sharp 单维与 cosine 相关度 |ρ| < **0.7**（v1 通常 >0.9） |
| **C-M3** | CLIP 路径行为不变（回归 `test_clip_encoder_atomic.py`） |

---

## 7. Phase D · 数据驱动标定（P3，可选续期）

### 7.1 数据资产

| 来源 | 字段 |
|------|------|
| `docs/acceptance-records/cover-selection-signoff.json` | `judgeVerdict` A/B/C |
| `scripts/cover_selection_blind_review.py` 导出 | `scoreRankedTop3` + features |
| 合成 proxy 相册 | 仅开发，不进训练 |

### 7.2 标定方法

1. **Pairwise**：top-1 vs rank-2/3 构造胜负对；A 类=正例，B 类=负例（top-1 败给 top-3 内某张）
2. **模型**：Bradley-Terry 或 logistic：`P(i≻j) = σ(logit_i − logit_j)`
3. **约束**：`wᵢ ≥ 0`（可解释）；`w_aspect ≤ 0.20`（硬约束）
4. **输出**：`cover_scoring_v2.weights` 建议值 + 置信区间；人工 approve 后写入默认配置

### 7.3 验收

| 门禁 | 条件 |
|------|------|
| **D-M1** | 留一法（LOO）pairwise accuracy ≥ **70%** |
| **D-M2** | 标定权重盲评 A 率 ≥ 手工 S1 权重 |

---

## 8. Phase E · 特征层统一（P4，长期）

不在 V2.0 阻塞发布，仅定义方向：

```text
travelogue/curation/feature_vector.py
  extract_quality_features(asset, pool) → QualityFeatures
  CoverScoringHead(weights) → logit
  LayoutScoringHead(weights) → score   # 逐步对齐字段
```

mosaic `scorer.py` 可引用 `QualityFeatures.sharp_pct` 等，但保留乘性惩罚组合逻辑。

---

## 9. 实施计划

### 9.1 里程碑

| 里程碑 | 交付 | 工期 |
|--------|------|------|
| **M-A0** | PRD 评审通过 + fixture 清单冻结 | 2 天 |
| **M-A1** | `cover_score_v2` + feature flag + 单测 | 1 周 |
| **M-A2** | `hero_score_v2` + explain v2 + 盲评脚本适配 | 3 天 |
| **M-A3** | Kendall τ 门禁 + 固定 fixture 全绿 | 2 天 |
| **M-B1** | `sharpness_score_v2` + `normalized_sharpness` | 1 周 |
| **M-B2** | cull / burst / cover 消费侧迁移 | 3 天 |
| **M-C1** | heuristic C-A 或 C-B 上线 | 1–3 人日 |
| **M-GA** | 灰度 `version: v2` + R0' 盲评（10 本） | 1 周 |
| **M-GB** | 默认切 v2 + cover-selection M2 复验 | 发布 |

### 9.2 人力

- **P0**：1 算法 + 1 熟悉 curate 链路工程，2–3 周
- **P1**：可与 P0 第 2 周并行，0.5–1 人
- **P2**：任意 1 人 sprint 内完成

### 9.3 分支策略

```text
feat/alg-v2-cover-scoring
feat/alg-v2-sharpness
feat/alg-v2-heuristic-embedding
→ 合并至 main 前：Kendall τ + 盲评子集 smoke
```

---

## 10. 测试与回归

### 10.1 新增测试文件

| 文件 | 覆盖 |
|------|------|
| `tests/test_cover_scoring_v2.py` | logit 模型、fixture CV2-01–05 |
| `tests/test_sharpness_v2.py` | Laplacian、ROI、分桶 |
| `tests/test_heuristic_embedding_v2.py` | 向量维度、相关度 |
| `tests/fixtures/cover_v2_quality_priority.json` | 质量优先固定样例 |

### 10.2 脚本

| 脚本 | 用途 |
|------|------|
| `scripts/cover_scoring_v2_kendall.py` | 批量算 τ(v1,v2) |
| `scripts/cover_selection_blind_review.py` | 增加 `--scoring-version v2` |
| `scripts/cover_scoring_calibrate.py` | Phase D 标定（P3 交付） |

### 10.3 持续门禁

- `demo verify`
- `test_phase6_cover_scoring.py`
- NR-P9（如适用）

---

## 11. 风险与缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| v2 排序抖动大 | 用户感知封面突变 | Kendall τ ≥0.85；feature flag 灰度 |
| sharpness v2 需重 ingest | 旧 trip 分数不一致 | `sharpnessLegacy` 并存；`cull --recalc` 文档 |
| 盲评样本仅 10 本 | P3 过拟合 | LOO + hold-out 3 本；权重硬约束 |
| hero 纳入范围扩大 | 延期 | hero 与 cover 共用 `extract_cover_features`，增量 ≤2 人日 |
| mosaic 口径仍割裂 | 长期技术债 | Phase E 仅定义接口，不阻塞 V2.0 |

---

## 12. 交付物清单

| 交付物 | 路径 |
|--------|------|
| 本 PRD | `docs/PRD-ALGORITHM-OPTIMIZATION-V2.md` |
| 实施清单（开发拆 task 用） | `docs/IMPLEMENTATION-ALGORITHM-V2.md`（评审后编写） |
| 验收记录 | `docs/acceptance-records/algorithm-v2-signoff.json` |
| 固定 fixture | `tests/fixtures/cover_v2_quality_priority.json` |
| Kendall 报告 | `docs/reports/algorithm-v2-kendall.md` |
| 权重变更 changelog | PR 附件 / `cover_scoring_v2` 配置 diff |

---

## 13. 开放问题（评审决议）

| # | 问题 | 选项 |
|---|------|------|
| Q1 | Phase C 先 A 还是直接 B？ | 建议 **先 A 再 B** |
| Q2 | `score_v2` 用 `exp(logit)` 还是直接 `logit` 排序？ | 建议 **logit 排序**，`exp` 仅展示 |
| Q3 | sharpness v2 是否强制重跑全库 trip？ | 建议 **懒重算**：curate 时缺 v2 则算 |
| Q4 | P3 标定是否纳入 V2.0 发布门禁？ | 建议 **不纳入**；S1 手工权重先发布，P3 为 v2.1 |
| Q5 | `cover-selection-plan` R1–R6 是否废止？ | 建议 **冻结**；v2 上线后新调参走权重 A/B |

---

## 14. 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v2.0.0-draft | 2026-06-05 | 初稿：P0 封面 logit · P1 sharpness · P2 heuristic · P3 标定 · P4 特征层 |
| v2.0.0-rc | 2026-06-05 | 评审决议合并；默认切 v2（开发期直切） |
