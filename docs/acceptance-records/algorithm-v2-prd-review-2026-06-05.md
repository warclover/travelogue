# 算法优化 V2.0 PRD 评审会纪要

| 属性 | 内容 |
|------|------|
| **会议** | 算法优化 V2.0 PRD 评审讨论会 |
| **日期** | 2026-06-05 |
| **文档** | [PRD-ALGORITHM-OPTIMIZATION-V2.md](../PRD-ALGORITHM-OPTIMIZATION-V2.md) v2.0.0-draft |
| **主持** | CTO / 首席算法 |
| **结论** | **有条件通过** · 可进入 M-A0（fixture 冻结 + IMPLEMENTATION 编写）· Phase A/B 可并行立项 |

---

## 1. 参会专家

| 角色 | 姓名（模拟） | 领域 | 评审关注点 |
|------|--------------|------|------------|
| **主持** | — | CTO / 算法 | ROI、科学性、与 cover-selection 衔接 |
| **产品** | P | 首页/分享体验 | 质量优先是否可感知、featured 意图、用户预期 |
| **算法** | A | 打分/标定 | logit 模型、特征定义、Kendall 门禁合理性 |
| **策展工程** | C | curate 链路 | API 兼容、feature flag、hero 范围、回归 |
| **摄取管线** | I | ingest / media | sharpness 重算成本、ROI 依赖、懒重算 |
| **Vision** | V | CLIP / 聚类 | heuristic 语义、HDBSCAN 维数变化、缓存失效 |
| **审美体系** | E | PA 设计 | aesthetic 与 cover v2 权重、U-COVER 一致性 |
| **排版/Mosaic** | L | layout / beam | 特征层统一边界、mosaic 口径不割裂 |
| **数据科学** | D | 标定/评估 | 盲评样本量、LOO、pairwise 构造 |
| **设计** | U | 卷轴/Studio | coverExplain 可读性、web/mobile 双布局 |
| **QA** | Q | 验收/回归 | 门禁可执行、fixture、与 NR-P9 关系 |

---

## 2. 议程与讨论摘要

### 2.1 问题定义与优先级（一致通过）

**共识**：

- 三方审计（连乘封面、sharpness 传导、heuristic 冒充语义）**证据充分**，优先级 P0→P1→P2 合理。
- 「质量优先」与现网 `base = w/h` 主导 **存在结构性冲突**，必须从模型形态上修，而非继续 R1–R6 调乘子。

**补充（算法 A）**：

- Kendall τ ≥ 0.85 是**稳定性**门禁，不是**质量提升**门禁；M2 盲评 A 率才是质量门禁。两者缺一不可，PRD 表述正确，但需在 IMPLEMENTATION 中写清「τ 高但 A 率掉」时的处理流程（回滚权重，非回滚模型形态）。

---

### 2.2 Phase A：封面 logit 模型（核心争议区）

#### 争议 1：hero 是否纳入 V2.0？

| 观点 | 发言人 |
|------|--------|
| **纳入**（CTO、产品 P） | hero 与 cover 同构连乘 bug；章首是卷轴第二门面；共用 `extract_cover_features` 增量可控 |
| **延后**（策展 C，援引 cover-selection 评审） | cover-selection v0.2 明确 hero Phase 2；扩大范围会稀释封面盲评样本 |

**决议**：**纳入 Phase A，但验收分层**。

- cover 盲评仍按 [cover-selection-plan.md](../cover-selection-plan.md) **mobile 主评**；hero 单独 **3 本章首 fixture + 主观抽查**，**不阻塞** cover M1/M2。
- PRD §4.8 补充一行：hero v2 验收 ≠ 封面发布门禁。

#### 争议 2：`f_aspect` 全景固定 0.85 是否武断？

| 观点 | 发言人 |
|------|--------|
| 固定常数太硬（设计 U） | 用户选全景封面时期望「宽幅叙事」，完全压平会损失杂志感 |
| 有界即可（算法 A） | 关键是去掉 raw ratio 主导；0.85 可配置，初值待 R0' 微调 |

**决议**：

- 全景 `f_aspect` 改为 **`min(0.90, sigmoid_flat(ratio))`**，上限可配置 `panorama_aspect_cap`。
- **CV2-01** 保留：平庸 3:1 全景仍不得压过优质 16:9（权重 cap + fixture 双保险）。

#### 争议 3：featured / anchor 后置是否破坏用户意图？

| 观点 | 发言人 |
|------|--------|
| 担心（产品 P） | featured ×1.35 后置后，logit 差过大时精选仍落选 |
| 支持（算法 A、CTO） | 主模型标定不含 featured 才科学；差过大说明精选图质量确实不行 |

**决议**：**维持后置**；新增验收 **CV2-06**：

> featured 图 logit 落在池内 top-30% 时，effective 分必须使其进入 `scoreRankedTop3`。

另：`featured_weight` 可调范围写入配置 schema（1.2–1.5），R5 改为调此后置系数。

#### 争议 4：`contribution` 公式二选一

**决议（算法 A + QA Q）**：采用 **`contribution = weight × feature`**（相对 0 基准），不用 `feature − baseline`。

- 理由：top-1 explain 应对用户解释「这张图凭什么高」，不是差分对比 rank-3。
- A-M4 改为：top-4 `|contribution|` 之和 ≥ **0.65 × logit(top-1)**（同一张图自解释）。

#### 争议 5：`w_aesthetic` 与 PA 体系

**审美 E** 指出：`aesthetic.enabled` 已在 v1 以乘子接入；v2 若 `w_aesthetic=0.10`，与 `w_sharp`、`w_thirds` 可能双重计入「质量」。

**决议**：

- `aesthetic.enabled=true` 时 **`w_sharp` 上限降至 0.18**（配置联动，非人工记忆）。
- PRD 增加对 [DESIGN-PHOTO-AESTHETIC-EVALUATION.md](../DESIGN-PHOTO-AESTHETIC-EVALUATION.md) 的交叉引用；`f_aesthetic` = `purpose_overall(asset, "cover")` 归一到 [0,1]。

**开放问题 Q2 决议**：排序用 **raw logit**；`exp(logit)` 仅 `scoreRankedTop10` 展示，保留 4 位小数。

---

### 2.3 Phase B：清晰度统一（有条件通过）

#### 争议：cover v2 是否硬依赖 sharpness v2？

| 观点 | 发言人 |
|------|--------|
| 硬依赖（CTO） | 否则 f_sharp 仍吃旧信号，Phase A 白做 |
| 软依赖（摄取 I） | 全库重算成本高；小 trip 可懒重算，大 trip 需批处理 |

**决议**：

- **灰度期**：cover v2 允许 `f_sharp` 回退 v1 `median_sharp` 比值（兼容层），但 **发布门禁必须 sharpness v2 全绿**。
- **Q3 决议**：**懒重算** + `travelogue ingest --recalc-quality` 可选全量；curate 入口检测 `quality.sharpnessVersion`，缺失则单 asset 补算。

#### 补充（摄取 I）

1. **ROI 链**：`salientBox` → `faces[0].bbox` → center 60% crop；三者皆无则全图，但 telemetry 记 `roi_fallback=full_frame` 比例，R0' 若 >40% 需降级预期。
2. **OpenCV**：Laplacian 优先 `cv2`；无 OpenCV 时 **PIL 卷积核回退**（与 subject_detect 一致），写入 algorithm-inventory。
3. **`sharpnessLegacy`**：保留 **2 个 minor 版本** 后废弃（比 PRD 写的 1 版本多一版，给 Studio 缓存迁移留时间）。

#### 补充（数据科学 D）

- `normalized_sharpness` 用 **percentile rank** 而非 z-score：trip 内小样本（≤15 张）更稳，与 cull 分位逻辑一致。
- 建议增加 **B-M5**：同一 burst 组内，v2 选出的代表与 v1 一致率 ≥ **80%**（防 burst 抖动）。

---

### 2.4 Phase C：启发式 embedding（一致通过，方案细化）

**Vision V**：

- **Q1 决议**：**先 C-A（诚实降级）再 C-B（向量修复）**；C-A 在 M-A1 当周可上线，零风险。
- C-B 的 18 维向量会使 **HDBSCAN 缓存失效**；需 bump `cluster-cache` schema version，旧 NPZ 自动 miss 重算。
- `sceneClusterId` 字段名 **不改**（避免破坏 layout cohort）；仅 `curation.sceneClusterLabel` 或 explain 文案改为「视觉分桶」。

**补充（排版 L）**：

- `category_coherence` / `cohort_coherence` 若读 scene cluster，heuristic 降级后预期下降；**不纳入 V2.0 回归门禁**（记录即可）。

**C-M2 修订**：|ρ| < 0.7 在 **≥3 个 fixture trip** 上测，单 trip 100 图不够稳。

---

### 2.5 Phase D：数据标定（不阻塞 V2.0）

**数据科学 D**：

- 10 本相册 pairwise 对数 **<200**，LOO 70% 置信区间宽；**同意 Q4：P3 不纳入 V2.0 发布门禁**。
- 但要求在 **M-A0** 交付 `scripts/cover_scoring_calibrate.py` **骨架** + 特征导出，避免 v2.1 从零开始。
- Pairwise 构造补充 **负样本**：C 类「都不行」相册中评委标注的「较好一张」vs 算法 top-1，权重 0.5（防标签稀疏）。

**产品 P**：同意；但希望 v2.1 标定目标改为 **A≥7/10（M2）**，而非仅 beat 手工权重。

---

### 2.6 与 cover-selection-plan 关系（一致通过）

**Q5 决议**：**R1–R6 冻结**；新调参走 `cover_scoring_v2.weights` + 单因子 A/B（一次只动一个 `wᵢ`）。

**QA Q** 要求 PRD 明确：

| 项 | 规则 |
|----|------|
| 盲评主指标 | 仍 **mobile**、`scoreRankedTop3` |
| web 池 | 单独 R0' 记录，不阻塞发布 |
| 人像为主 | §1.4 方案 A **原样保留** |
| CI proxy 60% | 保留，v2 分支需 `--scoring-version v2` |

---

### 2.7 工期与并行（策展 C + CTO）

**共识**：Phase A 与 Phase B **允许并行**，但 **M-GB 发布** 必须满足：

```text
cover_scoring.version = v2
AND ingest.sharpness.version = v2
AND B-M1～B-M5 全绿
```

Phase C（C-A）可与 M-A2 并行；C-B 不阻塞发布。

**风险补充（QA Q）**：Kendall τ 高不代表用户无感——增加 **ΔcoverId** 指标：10 本相册中 cover 变更数 ≤ **3/10**（除非 CV2 fixture 故意触发），超则需产品签字。

---

## 3. 各领域补充建议汇总

### 3.1 产品（P）

1. **用户可感知说明**：Studio 封面备选若因 v2 大变，需「系统已优化封面质量排序」一次性提示（文案即可，非阻塞）。
2. **web 封面**：宽屏阅读仍用 web 池；R0' 单独记 A 率，避免 mobile 达标但 web 丑图上线。
3. **时间线**：再次书面确认 v2 **不使用 takenAt**（与 cover-selection 一致）。

### 3.2 算法（A）

1. 增加 **`extract_cover_features()` 单测黄金向量**：每个 feature 冻结 6 位小数，防重构漂移。
2. `person_demote` 从乘子改惩罚项时，建议 `f_person = 1`（无 tag）/ `1 - penalty`（有 tag），penalty 默认 0.28（≈1−0.72），保持 v1 语义。
3. Phase D 优先 **Bradley-Terry** 而非 pointwise logistic（小样本更稳）。

### 3.3 策展工程（C）

1. `CoverScoringParams` 与 `CoverScoringParamsV2` **并存**，不要 in-place 改字段语义。
2. `build_cover_layout_review` 增加 `scoringVersion` 字段，盲评 JSON 可追溯。
3. `pick_chapter_hero` tie-break 第二键保留 `asset_sharpness` 原始值，直到 sharpness v2 全量。

### 3.4 摄取管线（I）

1. ingest 写入 `quality.sharpnessVersion: "v2"` 元数据字段（新）。
2. 大图 ROI 裁切注意 EXIF orientation，复用 `image_ops` 现有旋转逻辑。
3. 提供 `scripts/migrate_sharpness_v2.py` 批量迁移脚本（按 trip 目录）。

### 3.5 Vision（V）

1. C-A 改名同步 **用户可见 explain**（若有「场景：X」改为「视觉分桶：X」）。
2. CLIP 路径 **不动**；回归矩阵需覆盖 `vision.enabled=true` 子集至少 1 本 fixture。
3. heuristic-v2 维数变化后 `min_cluster_size` 建议可配置（默认保持现值）。

### 3.6 审美体系（E）

1. v2 启用 aesthetic 时，cover explain 需展示 `aesthetic` contribution，与 PA 文档 U-COVER 对齐。
2. 长期：`f_aesthetic` 应逐步吃掉部分 `f_sharp` + `f_color` 权重，v2.0 仅做 cap 联动即可。

### 3.7 排版/Mosaic（L）

1. Phase E 接口草案在 IMPLEMENTATION 末尾附 **1 页 sketch** 即可，无需阻塞。
2. `sort_bucket_asset_ids` 改用 `normalized_sharpness` 时，mosaic hero pick 路径一并检查（只读，可能同 release）。

### 3.8 数据科学（D）

1. 盲评 export 增加 **per-asset feature vector JSON**，M-A2 交付。
2. Kendall 报告按 **featured / 非 featured / 人像为主** 分层出 τ，全局 τ 可能掩盖子集退化。
3. Hold-out 3 本相册 **永不参与权重调参**（从 cover-selection 10 本中预留或新增）。

### 3.9 设计（U）

1. `coverExplain` contribution 展示在 Studio：**百分比条形**比裸数字友好（前端可选，后端先出数）。
2. mobile 竖图 `f_aspect` 不要鼓励极端细长（9:16 以上），建议 cap `f_aspect` at 0.95。

### 3.10 QA（Q）

1. 新增门禁 **A-M7**：`ΔcoverId ≤ 3/10`（见 §2.7）。
2. `demo verify` 需覆盖 `cover_scoring.version=v2` 配置 profile。
3. 验收记录统一写入 `docs/acceptance-records/algorithm-v2-signoff.json`（与 PRD §12 一致）。

---

## 4. 开放问题表决结果

| # | 问题 | **决议** |
|---|------|----------|
| Q1 | Phase C 先 A 还是 B？ | **先 A 再 B** |
| Q2 | exp(logit) 还是 logit 排序？ | **logit 排序**；exp 仅展示 |
| Q3 | sharpness 强制全库重算？ | **懒重算** + 可选 `ingest --recalc-quality` |
| Q4 | P3 纳入 V2.0 发布门禁？ | **否**；v2.1 · 交付标定骨架 |
| Q5 | R1–R6 废止？ | **冻结**；改 v2 权重 A/B |

---

## 5. PRD 修订清单（评审后必须更新）

| 章节 | 修订内容 |
|------|----------|
| §4.2.1 | 全景 `f_aspect` 改为可配置 cap；mobile `f_aspect` 上限 0.95 |
| §4.4 | `contribution = weight × feature`；A-M4 公式更新 |
| §4.3 | aesthetic 启用时 `w_sharp` cap 0.18 |
| §4.7 | 新增 CV2-06（featured top-30% → Top3）；新增 A-M7（ΔcoverId） |
| §4.8 | hero 纳入但 **不阻塞 cover M1/M2** |
| §5.3 | `sharpnessVersion` 字段；懒重算 + 批处理脚本 |
| §5.4 | 新增 B-M5（burst 一致率 ≥80%） |
| §6.3 | C-M2 改为 ≥3 fixture trips |
| §9.1 | M-GB 发布条件 = cover v2 + sharpness v2 双开 |
| §11 | 增加 ΔcoverId、cluster-cache 失效风险 |
| §13 | 开放问题改为「已决议」；新增 Q6（见下） |

**新增 Q6（遗留 IMPLEMENTATION）**：`composition_bias` 与 `f_aspect` 是否语义重叠？  
→ **实现时合并为一维 `f_layout_fit`**，避免共线；若共线 VIF>5 则删 `w_comp`。

---

## 6. 会议结论

| 项 | 结论 |
|----|------|
| **PRD 状态** | v2.0.0-draft → **v2.0.0-rc**（完成 §5 修订后） |
| **立项** | Phase A + Phase B **立即立项**；Phase C-A 本周可动 |
| **阻塞项** | 无 |
| **下次会议** | M-A3 后 · Kendall + R0' 盲评预审（预计 2 周后） |

---

## 7. Action Items

| 负责人 | 事项 | 截止 |
|--------|------|------|
| CTO / 算法 | 按 §5 修订 PRD → v2.0.0-rc | +2 天 |
| 策展 C | 编写 `IMPLEMENTATION-ALGORITHM-V2.md` | +3 天 |
| QA Q | 冻结 `cover_v2_quality_priority.json` + CV2-06 | M-A0 |
| 摄取 I | `migrate_sharpness_v2.py` 方案草图 | M-B1 |
| 数据 D | `cover_scoring_calibrate.py` 骨架 + feature export | M-A2 |
| 产品 P | 确认 Studio 提示文案（可选） | M-GA 前 |

---

## 8. 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0 | 2026-06-05 | 算法优化 V2.0 PRD 首次评审会纪要 |
