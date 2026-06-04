# Travelogue · 拼图系统设计文档（DESIGN · Mosaic Composition System）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue |
| **文档版本** | v0.3.0-DESIGN |
| **状态** | Draft（已过四方评审 · 收口中） |
| **系统代号** | 拼图系统（Mosaic Composition System，MCS） |
| **关联文档** | [PRD-PHASE15-photo-mosaic-evolution.md](./PRD-PHASE15-photo-mosaic-evolution.md)、[PRD-PHASE15-benchmark.md](./PRD-PHASE15-benchmark.md)、[PRD-PHASE9.md](./PRD-PHASE9.md)、[PRD-PHASE13.md](./PRD-PHASE13.md) |
| **关联代码** | `travelogue/curation/screen_planner.py`、`screen_planner_stages.py`、`layout_candidates.py`、`layout_scoring.py`、`layout_search.py`、`screen_layout_state.py`、`render/context.py` |
| **更新日期** | 2026-06-04 |

> **一句话职责**
>
> 在「干净照片池 + 已分段的故事段落」之上，决定**哪些照片、按什么版式、组成一屏拼图、主图放在哪个主位**，并把结构化 `screens[]` 与决策日志交给智能排版系统。

---

## 0. 已拍板决策（本文档前置约束）

| ID | 决策 | 结论 |
|----|------|------|
| **D-MCS-01** | 全局 beam 搜索（`maybe_replan_chapters`）归属 | **划归拼图系统**；智能排版系统只消费 `screens[]` 结果 |
| **D-MCS-02** | 模块组织 | **新建 `travelogue/curation/mosaic/`**，把分散逻辑收敛进去 |
| **D-MCS-03** | 自愈强度 | **允许丢弃个别坏图不进屏**（带护栏：featured 不丢、丢弃比例封顶、全 trip 可观测） |
| **D-MCS-04** | 张数覆盖 | **架构一次性支持全张数（张数无关）；运行时按档灰度启用**，S1 默认仅 5 张窗口走候选打分，其余 legacy；`unified_mode` 验证后一键全开 |
| **D-MCS-05** | 丢图阈值 | **按相册规模分档**（≤20 禁丢 / 21–80 5% / 81–200 8% / >200 10%）+ `min_keep` 绝对兜底 + featured 豁免 |
| **D-MCS-06** | beam 范围 | **首版段内 beam + 跨段共享节奏状态**（不做跨章联合最优）；S4 再加有界章节级再平衡 pass |

### 0.1 评审收口决策（v0.3 · 四方评审后新增）

四方评审（算法/架构/性能/产品）结论均为「有条件通过」。以下为收口拍板，作为 S1 开工前置约束：

| ID | 来源争议 | 收口结论 |
|----|----------|----------|
| **D-MCS-07** | 边界“名实不符”（架构·高） | 新增 **Editorial Layer** 概念：`arc/breath/folio/封面/章 hero/章元数据` 明确**不属于 MCS**，仍由 curate 的 Editorial 阶段负责；MCS = 候选生成 + 打分 + 段内 beam + 自愈，**可携带 arc 加权信号但不产出叙事结构**。见 §1.3 |
| **D-MCS-08** | 评分尺度未归一（算法·高） | 所有 `fᵢ / penaltyⱼ ∈ [0,1]`；总分采用**乘性衰减** `total = clamp(Σwᵢfᵢ,0,1) × Π(1−pⱼ·penaltyⱼ)`；权重与惩罚一并 `normalized()` 且绑定 `scorerVersion` 的权重哈希。见 §5 |
| **D-MCS-09** | `droppedAssetIds` 语义缺失（架构+产品·高） | 定义全链路契约：丢图为 **trip 级永久不进屏**；引入 `displayedAssetIds`；drop 后**强制** `compact_chapter_items_for_screens`；`photoCount` 等展示统计改用 `displayedAssetIds`；**S1 默认 `allow_drop=false`**（丢图属 S3）。见 §2.2 |
| **D-MCS-10** | beam 复杂度超预算 / 耗尽语义（性能·高） | 改 **分层预算**（`trip_cap + segment_cap`）；定义 `budget_exhausted_policy=legacy_segment`（禁止半 trip 静默）；候选每窗 Top-K 剪枝 + 默认增量打分。见 §6/§9 |
| **D-MCS-11** | `pattern_repeat` 与现有 rhythm/diversity 重复计分（算法·中） | **合并**：`layout_rhythm`=按 layoutKind、`diversity`=近 2 屏、`pattern_repeat` 删除或并入 rhythm；不得三重惩罚。见 §5 |
| **D-MCS-12** | KPI 不可度量 / `unified_mode` 无门禁（产品·高） | §8 为每个 KPI 补「定义+数据源+门禁」；§12 写死 `unified_mode` 全开灰度判据与自动回滚条件 |
| **D-MCS-13** | `screens/items` 不同步（架构·高） | S1 必做：beam/MCS 重写 `screens[]` 后调用 `compact_chapter_items_for_screens`，纳入 golden 回归 |
| **D-MCS-14** | `face_crop` 缺几何模型（算法·高） | S1 用 **proxy**（有人物 + cover + focal/salient 距边 < margin → 降分 / 优先 contain）；**几何版（slot rect × 人脸框 IoU）放 S2** |

---

## 1. 系统定位与边界

### 1.1 全链路位置

```
[筛选系统 P9]        [聚类系统 P3/P8]          [★拼图系统 MCS]            [智能排版系统]
质量门控/去重    →    分段/场景/地理事件    →    组屏 + 选模板 + 主图    →    叙事弧/封面/文案/渲染
layoutEligible       day_buckets/segments      screens[] + 决策日志        chapters → HTML/长图
```

### 1.2 职责边界（权威）

| 系统 | 负责 | 不负责 |
|------|------|--------|
| 筛选系统 P9 | 去重、低质剔除、`layoutEligible`、质量分 | 组屏、模板 |
| 聚类系统 P3/P8 | 时间/地理分段、场景簇、`subjectClass` | 组屏、模板 |
| **拼图系统 MCS** | **单屏组屏、模板匹配、主图定位、段内屏序节奏、段内全局择优（beam）、自愈** | 章节顺序、叙事弧、封面、文案、tone、最终渲染 |
| Editorial Layer（curate 内） | 叙事弧 `arc`、呼吸屏 `breath`、对开 `folio`、封面、章 hero、章元数据 | 单屏拼图几何 |
| 智能排版系统（render） | 渲染上下文、模板输出、HTML/长图 | 组屏决策 |

> **边界口径（D-MCS-01 + D-MCS-07）**：凡是「在多个候选屏方案里挑最优」的逻辑都属于 MCS。但 `run_curate` 中位于 MCS **之后**的 `folio/arc/breath/封面/章元数据` 属于 **Editorial Layer**，不归 MCS。MCS 在 beam 打分中**可以读取** arc/intent 信号作为加权（屏序更贴合章节意图），但**不产出**叙事结构本身。

### 1.3 真实 `run_curate` 编排（权威 · 收口名实不符）

下图标注每一步**是否允许改写 `screens[]`**，避免“MCS 是唯一组屏生产者”的误解：

```
run_curate 阶段                                         可改 screens[]?
─────────────────────────────────────────────────────────────────
preflight / eligible(P9) / buckets(P3)                  —（产出输入）
heroes / titles / pattern_hints / arc 预标注            —（Editorial 预置）
build_chapters_from_buckets + attach_screens            ✅ 初次组屏（MCS 候选+打分）
  └─ compact_chapter_items_for_screens                  （items 同步点①）
maybe_replan_chapters（段内 beam）  ←★ MCS 核心          ✅ 重写 screens
  └─ compact_chapter_items_for_screens  ←★ D-MCS-13 新增 （items 同步点②·必做）
SelfHeal（S3，allow_drop 默认关）  ←★ MCS                ✅ 可丢图 → droppedAssetIds
  └─ compact + items/统计重建                            （items/统计同步点③）
─────────────── 以下为 Editorial Layer，MCS 不参与 ───────────────
build_folio_plan / stamp_arc_segments / breath / explain ⛔ 只读 screens，不改组屏
封面 / epilogue 统计                                     ⛔ 读 displayedAssetIds
persist                                                  —
```

> **结论**：MCS 的写权限止于 SelfHeal；其后 Editorial 与 render **只读** `screens[]`。任何“组屏几何”变更必须发生在 MCS 阶段内。

---

## 2. 上下游数据契约（基于现有代码）

### 2.1 输入契约（来自筛选 + 聚类）

| 字段 | 来源 | MCS 用途 |
|------|------|----------|
| `asset.layoutEligible` | 筛选 P9 | 仅 eligible 资产参与组屏 |
| `asset.featured` | 筛选 P9 | 自愈时**永不丢弃** |
| `asset.quality.sharpness` | 筛选 P9 | 主图打分 / 坏例惩罚 |
| `asset.aspectKind` | ingest | 模板族匹配（横/竖/方/全景/长） |
| `asset.width/height` | ingest | 比例适配、切裁风险 |
| `asset.takenAt` | ingest | 连拍链 / 时间内聚 |
| `asset.focalPoint` + person tags | 检测 | 主图定位 / 切脸风险 |
| `asset.subjectClass` | 聚类 P8 | 主体一致 / 题材网格 |
| `day_buckets` / `segments` | 聚类 P3 | 组屏输入序列单元 |
| `scene_clusters` / `geo_events` | 聚类 P3/P8 | 段内细分、节奏边界 |

### 2.2 输出契约（交给智能排版，沿用现有结构）

```json
{
  "screens": [
    {
      "screenId": "ch-01-sc-03",
      "patternId": "screen-mosaic-5-main-portrait-3land",
      "layoutHint": "person-grid-8 | food-grid | null",
      "slots": [
        {"assetId": "a12", "slot": 0, "fit": "cover", "role": "main"},
        {"assetId": "a13", "slot": 1, "fit": "cover", "role": "portrait"}
      ]
    }
  ],
  "mosaicDecisionLog": { "...": "见 §7" },
  "displayedAssetIds": ["a12", "a13", "..."],
  "droppedAssetIds": ["a99"]
}
```

- 下游 `render/context.py::build_layout_screen()` → `grid_class_for_pattern()` → 模板 CSS **保持不变**。

#### `droppedAssetIds` / `displayedAssetIds` 全链路契约（D-MCS-09）

| 维度 | 规则 |
|------|------|
| **作用域** | `droppedAssetIds` 为 **trip 级永久不进屏**（非屏级临时移出）；写入 `trip.curation.mosaicDroppedAssetIds` |
| **集合守恒** | 对每个 segment：`len(进屏 assets) + len(dropped) == len(输入 eligible)`；并打 `asset.mosaicDropped=true` 与 `layoutEligible` 区分 |
| **items 同步** | drop 或 beam 改写 `screens[]` 后，**必须**调用 `compact_chapter_items_for_screens(chapters)` 重建 `items[]`（D-MCS-13） |
| **展示统计** | `photoCount`、`build_epilogue_stats`、封面候选池统一改用 **`displayedAssetIds = 全 trip 进屏 ∪ 封面 hero`**，不再用全量 `layoutEligible` |
| **与 P9 联动** | drop **不计入** P9 `min_keep` 分子；drop 前校验剩余 eligible 不低于 `min_keep` 地板，否则拒绝丢图（避免双轨击穿） |
| **S1 默认** | `allow_drop=false`；S1 输出 `droppedAssetIds=[]`，`displayedAssetIds == 全 trip eligible`（除既有 P9 剔除外不静默丢失） |

---

## 3. 模块结构（新建目录 · D-MCS-02）

```
travelogue/curation/mosaic/
├── __init__.py            对外唯一入口 compose_mosaic_for_segment / compose_trip
├── features.py    [M1]    AssetFeatureAssembler：统一特征装配
├── hero.py        [M2]    HeroSelector：主图选择（薄封装 curate_scoring）
├── registry.py    [M3]    MosaicPatternRegistry：pattern 元数据 + grid + 适配条件
├── candidates.py  [M4]    CandidateGenerator：窗口 → 多 pattern 候选（软约束）
├── scorer.py      [M5]    MosaicScorer：统一打分（扩展 layout_scoring）
├── search.py      [M5']   段内 beam 择优（迁移 layout_search 核心，归 MCS）
├── selfheal.py    [M6]    SelfHeal：低分二次重排 + 坏例丢弃（带护栏）
├── state.py               节奏 / 配额状态（迁移 screen_layout_state + mobile）
└── log.py                 MosaicDecisionLog（扩展现有 LayoutDecisionLog）
```

### 3.1 与现有代码的迁移映射

| 子模块 | 现状代码 | 迁移策略 |
|--------|----------|----------|
| M1 features | 分散在 planner/scoring | **新建收敛**，旧调用改委托 |
| M2 hero | `curate_scoring.pick_chapter_hero` / `effective_hero_score` | **复用**，薄封装 |
| M3 registry | 硬编码 `PATTERN_GRID_CLASS` | **配置化**：pattern→grid→CSS→适配条件成对登记 |
| M4 candidates | `layout_candidates.generate_day_bucket_candidates` | **泛化**：支持 3/4/5/6/8/9 窗口与多 pattern |
| M5 scorer | `layout_scoring.score_screen_plan`（13 维） | **扩展**坏例惩罚 + 多样性 |
| M5' search | `layout_search.maybe_replan_chapters`（beam） | **迁移归属** MCS（D-MCS-01） |
| state | `screen_layout_state.py` / `mobile_layout_state.py` | **迁移**到 `mosaic/state.py` |
| log | `LayoutDecisionLog` | **扩展**字段（§7） |

> 迁移采用「保留旧入口为薄包装、逻辑收敛进 mosaic/」策略，分 PR 推进，避免一次性大爆炸（见 §10）。

---

## 4. 内部子模块职责

### M1 AssetFeatureAssembler（特征装配）
聚合每个资产的：`aspectKind`、`ratio`、`sharpness`、`subjectClass`、`hasPerson`、`focalPoint`、`takenAt`、`featured`，输出统一 `AssetFeature`，供候选/打分/主图/自愈共享，避免各处重复解析。

### M2 HeroSelector（主图选择）
复用 `effective_hero_score`（清晰度 + featured 权重 + median 基准）。扩展：人脸完整度、主体代表性、曝光。为含 `role=main` 的 pattern 定位主图槽。

### M3 MosaicPatternRegistry（模板族注册）
将 pattern 从硬编码升级为可登记元数据：

```python
MosaicPattern(
    pattern_id="screen-mosaic-5-main-portrait-3land",
    slot_count=5,
    grid_class="layout-screen__grid--mosaic-5-main-portrait-3land",
    roles=["main","portrait","landscape","landscape","landscape"],
    accepts=AspectProfile(min_portrait=1, min_landscape=4),
    soft_conditions=["time_cohesion","trip_total>=35"],  # 软约束→打分
    css_verified=True,
)
```

发布约束：pattern 与 grid_class / CSS **成对验收**，未配对不得登记（防错位）。

### M4 CandidateGenerator（候选生成）
- 滑窗扫描，窗口 ∈ {1,2,3,4,5,6,8,9}。
- **张数无关设计（D-MCS-04）**：候选生成不对某一张数写死；新增张数 = 在 `registry` 注册 pattern 即可。
- **运行时分档启用（D-MCS-04）**：由 `mosaic.enabled_window_sizes` 控制哪些窗口走候选打分，其余回落 legacy planner；`unified_mode=true` 时全部窗口走候选打分。
- 每窗口生成多个 pattern 候选（不再命中即停），**每窗保留 Top-K**（剪枝，D-MCS-10）。
- 硬约束仅保留结构性：slot 数一致、角色位可填、数据合法。
- 其余（`trip_total>=35`、严格连拍、单一比例）**软化为打分项**。

> **现状澄清（评审·算法/架构/性能三票）**：现有 `generate_day_bucket_candidates` 是对**整段 bucket** 重跑 `plan_screens_for_chapter` 的 3–5 个**规划变体**，`try_mosaic_five` 是命中即返回，**不是**窗口级多 pattern。`mosaic/` 目录尚不存在。下方明确 S1 可落地语义，避免按“目标态”一次性开发而低估工作量。

#### S1 MVP 语义（可落地，避免误实现全窗 DP）

```python
# S1: 仅 window_size ∈ enabled_window_sizes(=[5]) 进入 MCS；其余走 legacy stage。
def compose_segment_s1(assets, state, budget, cfg):
    screens, i = [], 0
    while i < len(assets):
        win = assets[i : i + 5]
        if len(win) == 5 and 5 in cfg.enabled_window_sizes:
            # 1) 该窗生成多 pattern 候选（registry 中所有 5-slot pattern × 主图槽排列）
            cands = generate_window_candidates(win, registry, size=5)   # 已 Top-K 剪枝
            cands = [c for c in cands if state.can_emit_pattern(c.pattern_id)]
            if cands and budget.can_evaluate():
                best = max(cands, key=lambda c: score_screen(c, state, cfg))  # M5 打分
                screens.append(best); state.note_screen(best); i += 5
                continue
        # 2) 回落 legacy：沿用 screen_planner_stages 命中即停（打 plannerPath=legacy）
        scr = legacy_plan_one(assets, i, state)
        screens.append(scr); state.note_screen(scr); i += scr.slot_count
    return screens
```

- **段内 beam（D-MCS-06）= per day_bucket 的屏序择优**：在上面贪心基础上，beam 宽度 `width=3` 保留前缀屏序（按累计分），用于跨窗权衡（例：窗 A 让分换窗 B 更优），**不是**跨章联合搜索。
- **混用一致性**：同一 segment 内 5 窗走 MCS、其余 legacy 时，`screen_layout_state`（九宫格/portrait-grid8 配额）**只由最终合并屏序一次性 `note_screen` 提交**，避免双路径并发写状态。
- **术语对照**：`segment`(geo/time) · `chapter` · `day_bucket`(curate 桶，beam 实际粒度) · `window`(滑窗)。文中“段内 beam”= per `day_bucket` + trip 级共享 `state`。

### M5 MosaicScorer（统一打分）
见 §5。

### M5' Segment Beam Search（段内择优）
迁移 `maybe_replan_chapters` 的 beam，**段内**在候选屏序中选最优，受 `SearchBudget` 约束（超时/评估上限），保证性能可控与可复现。

**全局节奏（D-MCS-06）**：不做跨章联合最优；跨段一致性由 `mosaic/state.py` 的**共享节奏/配额状态**保证（九宫格配额、portrait-grid8 配额等已是跨段共享）。S4 再加一个**有界章节级再平衡 pass**（限定评估次数），用于均衡 hero / 大版式在各章的分布，而非全量联合搜索。

### M6 SelfHeal（自愈 · D-MCS-03）
两次机会机制：

1. 第一次：正常候选 + 打分。
2. winner < 阈值 → 自愈：
   - a. 收紧质量约束重排；
   - b. 降级到更稳模板；
   - c. **丢弃个别坏图**（仅丢“已低分且任何候选都掉分”的图；护栏见 D-MCS-05：featured 不丢；按规模分档比例上限；不得击穿 P9 `min_keep` 地板；记入 `droppedAssetIds`）；
   - d. 仍不达标 → legacy 兜底。

---

## 5. 评分函数设计

### 5.1 归一化与合成（D-MCS-08）

所有正向项 `fᵢ ∈ [0,1]`、所有惩罚 `penaltyⱼ ∈ [0,1]`。采用**乘性衰减**，保证总分始终落在 [0,1] 且单个惩罚不会把分数压成负数 / 一项定胜负：

```
base  = clamp(Σ wᵢ·fᵢ, 0, 1)          # 正向，权重 normalized 后 Σwᵢ = 1
total = base × Π (1 − pⱼ · penaltyⱼ)   # 乘性衰减，pⱼ 为惩罚权重 ∈ [0,1]
```

- 正向权重 `weights` 与惩罚权重 `penalties` **一并 `normalized()`**，并绑定 `scorerVersion` 的**权重 JSON 哈希**（`weightsHash`），写入决策日志与回放包。
- `featured_beam`（现有 `+0.15/张`）改为纳入 `weights` 的归一化项，不再额外破坏 [0,1] 解释性。

### 5.2 正向项（多数已在 `ScoringWeights`）
- `aspect_match` 横竖适配 · `sharpness` 清晰度 · `hero_separation` 主图分隔
- `temporal_coherence` 时间内聚 · `subject_run` / `category_coherence` 主体一致
- `layout_rhythm` 节奏 · `diversity` 多样性

### 5.3 惩罚项（坏例压制 · 全自动核心）
- `face_crop_penalty`：切脸风险。
  - **S1（proxy，D-MCS-14）**：有人物 + `fit=cover` + focal/salient 距边 < `FOCAL_EDGE_MARGIN` → 降分；有人物时优先 `portrait_fit→contain`。复用现有 `check_focal_not_at_edge` / `score_gravity_balance` 信号。
  - **S2（几何版）**：registry 登记各 pattern 的归一化 slot rect，计算 `IoU(face_box, visible_region(slot, asset_aspect, focal))`。
- `main_quality_penalty`：仅惩罚 `role=main` 的 sharpness/meanLuma 分位偏低；**不与全屏 `sharpness` 重复加权**。
- `duplicate_density_penalty`：段内滑动窗口内同 `burstGroupId`/相似组计数 / 窗口长度（`contentSig` 仅作弱先验，主信号在 P9 cull 前）。

### 5.4 去重计分冲突收口（D-MCS-11）
现有已有三处相关项：`score_layout_rhythm`（同 `patternId`→0）、`score_screen.diversity`（近 2 屏重复→0）、beam 硬过滤 `plan_violates_consecutive_pattern`。**删除独立 `pattern_repeat_penalty`**，口径统一为：
- `layout_rhythm` = 按 **layoutKind** 聚合；`diversity` = 近 **2 屏** patternId 重复。二者权重互斥，不再叠加第三项。

硬约束（仅结构性）：slot 数一致、角色位可填、数据合法。

---

## 6. 端到端决策流程（段内）

```
对每个 segment / bucket：
1. M1 装配特征
2. 滑窗扫描（窗口大小集合）
3. M4 生成多 pattern 候选（软约束）
4. M2 为含主位候选定位 hero
5. M5 统一打分（适配 + 主图 − 切脸 − 重复 − 重复模板）
6. M5' beam 选段内最优屏序（SearchBudget 约束）
7. winner < 阈值 → M6 自愈（收紧 → 降级 → 丢图[S3] → legacy）
8. log 写决策（top3 候选 + winner reason + fallback/drop）
→ 输出 screens[] + mosaicDecisionLog + displayedAssetIds + droppedAssetIds
```

### 6.1 预算与耗尽语义（D-MCS-10）

- **分层预算**：`trip_cap` + `segment_cap = f(segment_eligible_count)`，大相册优先保证每段最低评估配额，避免“前半 beam、后半静默”。
- **耗尽策略 `budget_exhausted_policy = legacy_segment`**：某 segment 预算耗尽（超时/评估用尽）时，该 **整段** 回落 legacy planner 并打 `fallbackReason=BUDGET_EXHAUSTED`，**禁止**停在半段（修复现状 `_replan_day_buckets_beam` 直接 `break` 导致的半 trip 不一致）。
- **生成不重**：候选生成只产出“单屏 slot 分配 + patternId”，beam 在屏序列上扩展并复用 `IncrementalScoreState`，避免“每候选整段重跑 `plan_screens_for_chapter`”。
- **确定性**：`deterministic_strict=true` 时，候选排序键固定为 `(window_start, pattern_id, asset_ids)`；日志去掉 wall-clock（或仅 debug 级保留），保证同输入 `screens` 签名一致、可回放。

---

## 7. 可观测 / 决策日志（扩展 `LayoutDecisionLog`）

```json
{
  "segmentId": "day-bucket-2",
  "windowSize": 5,
  "candidatesCount": 4,
  "winnerPatternId": "screen-mosaic-5-main-portrait-3land",
  "winnerScore": 0.72,
  "top3Patterns": ["...", "...", "..."],
  "top3Scores": [0.72, 0.66, 0.51],
  "winnerReasonCodes": ["R_TIME_COHESION", "R_HERO_STRONG"],
  "fallbackUsed": false,
  "fallbackReason": null,
  "selfHealApplied": false,
  "droppedAssetIds": [],
  "scorerVersion": "p15-s1",
  "weightsHash": "sha256:...",
  "plannerPath": "mosaic | legacy",
  "budgetExhausted": false
}
```

对齐 PRD `AC-P15-07/08`。

### 7.1 日志分级（D-MCS-10 · 防膨胀）

按每窗口写 top3+breakdown 在 200 张相册会产生数百条/段，需三级：

| 级别 | 内容 | 默认 |
|------|------|------|
| `summary` | 每 segment 1 条：windowCount、fallbackRate、dropCount、avgWinnerScore | 常开 |
| `window` | 仅 winner（patternId+score+reasonCodes）；距阈值内才记 top3 | 常开 |
| `debug` | top3 全量 + 完整 score breakdown | 采样 / 默认关 |

- 禁止默认序列化完整 `ScoreBreakdown.to_dict()`；`winnerScore` 必记，`top3Scores` 仅 debug。
- 验收：200 张 trip 的常开日志条数/体积设上限（CI 断言）。

---

## 8. 系统级 KPI（D-MCS-12 · 补定义/数据源/门禁）

| KPI | 定义（公式） | 数据源 | 目标 / 门禁 |
|-----|--------------|--------|-------------|
| `AutoAcceptRate`（北极星） | **离线**：golden trip 人工 3 档标注 ≥“可接受”比例；**在线代理**：`1 − severe_defect_proxy − high_fallback_share`。二者不混用 | 离线标注集 / telemetry | 离线 ≥ 基线；在线代理用于趋势 |
| `SevereDefectRate` | (切脸 + 糊主图 + 重复灾难屏数) / 总屏数；阈值与 `face_crop`/`main_quality` penalty 对齐 | 离线检测脚本抽检 | ≤ 基线 + ε |
| `LayoutDiversityScore` | `1 − pattern_repeat_rate` 或 Shannon(patternId) 归一 | screens[] | ↑，与 `diversity` 权重联动 |
| `eligible_to_screen_coverage` | `displayedAssetIds / layoutEligible`（与 drop_rate 对照） | curation 输出 | S1 ≈ 1.0（不丢图） |
| `mosaic.fallback_rate` | `fallback 段数 / 总段数`，分 reason（含 `BUDGET_EXHAUSTED`、`low_score`） | decisionLog | 观测，全开判据见 §12 |
| `self_heal_rate` | 触发自愈段数 / 总段数 | decisionLog | 观测 |
| `mosaic.drop_rate` | `len(droppedAssetIds) / layoutEligible` | curation 输出 | 受控，≤ 分档上限 50% |
| `mosaic5.exposure_rate` | 含 5-slot pattern 的屏数 / 总屏数 | screens[] | ↑（对齐 AC-P15-03） |
| `trip_export_success_rate` | 渲染/导出无 error 的 trip 比例 | render telemetry | 不劣于基线 |

> **指标命名映射（与 PRD 对齐，防 telemetry 分裂）**：`mosaic.fallback_rate ↔ layout.mosaic_v2.fallback_rate`、`mosaic5.exposure_rate ↔ layout.mosaic5.exposure_rate`、`low_score_fallback ↔ layout.mosaic_v2.low_score_fallback_rate`。

---

## 9. 配置（草案）

```yaml
mosaic:
  enabled: true
  scorer_version: "p15-s1"
  deterministic_strict: true     # 固定候选排序键，保证可回放（D-MCS-10）
  min_candidate_score: 0.35
  # 架构支持全张数；运行时分档启用（D-MCS-04）
  supported_window_sizes: [1, 2, 3, 4, 5, 6, 8, 9]
  enabled_window_sizes: [5]      # S1 默认仅 5 张走候选打分，其余 legacy
  unified_mode: false            # 验证后置 true → 全窗口走候选打分（判据见 §12）
  scope:
    web: true                    # S1 仅 web screens[] / screen_layout_state
    mobile: false                # mobile_layout_state 暂 out-of-scope（M7 MobileMosaicAdapter，S4+）
  self_heal:
    enabled: true
    allow_drop: false            # ★ S1 默认关闭（丢图属 S3）；D-MCS-09
    never_drop_featured: true
    respect_min_keep: true       # 不得击穿 P9 min_keep 地板
    # 分档丢弃上限（D-MCS-05，allow_drop=true 时生效）
    drop_tiers:
      - { max_eligible: 20,  max_drop_ratio: 0.0 }
      - { max_eligible: 80,  max_drop_ratio: 0.05 }
      - { max_eligible: 200, max_drop_ratio: 0.08 }
      - { max_eligible: null, max_drop_ratio: 0.10 }
  fallback_to_legacy: true
  beam:
    width: 3
    scope: "segment"             # per day_bucket（D-MCS-06）；S4 加 bounded 章节级再平衡
    candidate_top_k: 4           # 每窗候选剪枝（D-MCS-10）
    incremental_scoring: true    # 默认增量打分
    search_timeout_ms: 2000
    # 分层预算（D-MCS-10）：避免半 trip 静默
    max_evaluations_per_trip: 500
    max_evaluations_per_segment: 64
    budget_exhausted_policy: "legacy_segment"   # 整段回落，禁止半段
  log_level: "window"            # summary | window | debug（D-MCS-10）
  weights:                       # 与 penalties 一并 normalized()，绑定 weightsHash
    aspect_match: 0.20
    sharpness: 0.15
    hero_separation: 0.10
    temporal_coherence: 0.15
    subject_run: 0.10
    layout_rhythm: 0.10          # 含 pattern 连发口径（pattern_repeat 已并入，D-MCS-11）
    diversity: 0.10
    category_coherence: 0.10
  penalties:                     # 乘性衰减 total *= Π(1 − pⱼ·penaltyⱼ)（D-MCS-08）
    face_crop: 0.30              # S1 proxy / S2 几何（D-MCS-14）
    main_quality: 0.25
    duplicate_density: 0.20
    # pattern_repeat 已删除，合并进 layout_rhythm / diversity（D-MCS-11）
```

---

## 10. 演进路线（分阶段，避免大爆炸）

| 阶段 | 范围 | 出口 |
|------|------|------|
| **S1（=Phase15）** | 5 张窗口候选+打分；模板族注册；决策日志 | 5 图问题解决，机制跑通 |
| **S2** | 3/4/6 张统一候选评分；坏例惩罚项 | 全面替换硬规则 |
| **S3** | 自愈二次重排 + 丢图护栏 | 全自动低坏例 |
| **S4** | 段内 → 章节级全局节奏优化 | 叙事更自然 |
| **S5** | 模块目录收敛完成 + 离线回放调参看板 | 可持续运营 |

> 目录迁移（D-MCS-02）随 S1–S5 渐进完成：S1 先建 `mosaic/` 骨架与新入口，旧文件保留薄包装；S5 完成收敛。

### 10.1 S1 用户可感知能力边界（防超额承诺）

| S1 **包含** | S1 **不含** |
|-------------|-------------|
| 5 张窗口多 pattern 候选 + 统一打分 | 3/4/6/8/9 张候选打分（仍 legacy） |
| 段内 beam + 共享节奏状态 | 跨章节联合最优（S4） |
| 决策日志 + low-score 回落 legacy | 自愈丢图（`allow_drop=false`，S3） |
| `screens/items` 同步修复（D-MCS-13） | 切脸几何模型（S2 proxy→几何） |
| web 路径 | mobile 拼图（S4+） |

> **对外口径**：S1 解决“5 张几乎不出现”+“多候选择优机制跑通”，**不是**全张数全自动重写。`allow_drop` 配置预置但默认关闭。

### 10.2 迁移 ADR（依赖方向 · 防环依赖）

- 允许：`mosaic/*` → import `screen_planner` / `layout_scoring` / `screen_layout_state`。
- 禁止：`mosaic/*` → import `curate` / `run_curate` 子路径。
- 编排：`run_curate` 单向调用 `mosaic.compose_segment / compose_trip`；`mosaic` 不反向依赖编排层。
- 每个旧模块保留的薄包装公共 API 需列入迁移清单并被现有测试（`test_layout_search.py` 等）覆盖。

---

## 11. 风险与缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| 丢图误删好片 | 内容缺失 | featured 不丢 + 丢弃比例封顶 + 全量可观测回放 |
| 打分权重不佳 | 布局波动 | 版本化权重 + 灰度 + A/B 回放 |
| beam 性能 | 大相册（200+）超时 | 分层预算 + 每窗 Top-K + 增量打分 + `legacy_segment` 兜底（D-MCS-10） |
| 预算耗尽半 trip 不一致 | 前 beam 后静默 | `budget_exhausted_policy=legacy_segment`（整段兜底） |
| legacy/MCS 混用状态分叉 | 节奏配额错乱 | 同段单一路径写 `state`，合并屏序一次 `note_screen` |
| `screens/items` 不同步 | 文案/统计错位 | beam/drop 后强制 `compact_chapter_items_for_screens`（D-MCS-13） |
| 丢图伤用户信任 | 照片“消失” | S1 默认不丢；`displayedAssetIds` 可观测；trip 级 `dropSummary` |
| 决策日志膨胀 | 体积/性能 | 三级日志 + 采样（D-MCS-10） |
| 目录迁移回归 | 渲染/编排回归 | 薄包装兼容 + golden 回归 + 分 PR + 依赖 ADR（§10.2） |
| 新 pattern 错位 | 渲染崩版 | pattern↔grid↔CSS 成对验收 |

---

## 12. 决策结论（原待确认问题，已拍板）

| 原问题 | 结论 | 对应决策 |
|--------|------|----------|
| 张数覆盖 | 架构一次性支持全张数；S1 默认仅 5 张窗口走候选打分，其余 legacy；`unified_mode` 验证后全开 | D-MCS-04 |
| 丢图阈值 | 按规模分档（≤20 禁丢 / 21–80 5% / 81–200 8% / >200 10%）+ `min_keep` 兜底 + featured 豁免 | D-MCS-05 |
| beam 范围 | 首版段内 beam + 跨段共享节奏状态；S4 再加有界章节级再平衡 | D-MCS-06 |

### 12.1 `unified_mode` 全开灰度判据（D-MCS-12 · 已写死）

`unified_mode: false → true`（全窗口走候选打分）需**同时满足**，且基于回放集 + 在线灰度校准数值：

| 判据 | 阈值（待回放集校准） |
|------|----------------------|
| 观测时长 / 样本 | 连续 **7 天** 或 **≥200 trip** |
| `SevereDefectRate` | ≤ 基线 + ε（ε 待定，建议 2%） |
| `mosaic.fallback_rate` | ≤ X%，且 `low_score_fallback` 不上升 |
| `mosaic.drop_rate` | ≤ 分档上限的 **50%** |
| `mosaic5.exposure_rate` | 达到 AC-P15-03 相对提升目标 |
| `trip_export_success_rate` | 不劣于基线 |

**自动回滚**：上述任一项**连续 2 天恶化** → 自动将 `unified_mode` 置回 `false` 或缩小 `enabled_window_sizes`，并告警。

剩余可选讨论项（不阻塞 S1）：

1. S4 章节级再平衡的评估预算上限取值。
2. `face_crop` 几何版（S2）的 slot rect 标注来源（手工登记 vs 从 CSS 解析）。

---

## 13. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.3.0 | 2026-06-04 | 四方评审收口：新增 D-MCS-07~14（Editorial Layer 边界、评分归一化乘性衰减、droppedAssetIds 全链路契约、分层预算+耗尽兜底、去重计分合并、KPI 门禁、items 同步、face_crop 分期）；新增 §1.3 真实流水线图、§6.1 预算语义、§7.1 日志分级、§8 KPI 定义、§10.1 S1 能力边界、§10.2 迁移 ADR、§12.1 unified_mode 灰度判据；M4 增 S1 MVP 伪代码；S1 默认 `allow_drop=false` |
| v0.2.0 | 2026-06-04 | 拍板 D-MCS-04/05/06：全张数架构+分档启用、分档丢图阈值、段内 beam+共享节奏；§12 转为决策结论 |
| v0.1.0 | 2026-06-04 | 初稿：拼图系统完整设计；纳入 D-MCS-01/02/03 三项已拍板决策 |
