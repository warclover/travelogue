# Travelogue · 美食角色策略 PRD（Food Role Policy · FRP）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue |
| **文档版本** | v0.1.0 |
| **状态** | Implemented · Fixture Dogfood 绿；真人目视待签 |
| **特性代号** | FRP（Food Role Policy，美食角色策略） |
| **文档类型** | 策展选型 + 章内组屏策略增量 PRD（实现方案） |
| **前置条件** | [PRD-PHASE10-food-grid.md](./PRD-PHASE10-food-grid.md) 已上线；[PRD-PHASE9-E-subject-bridge.md](./PRD-PHASE9-E-subject-bridge.md) `subjectClass` / `is_mundane_clusterable` 可用；封面 / 封底 / Peak Moment 主链可跑通 |
| **关联文档** | [ACCEPTANCE-FOOD-ROLE-POLICY.md](./ACCEPTANCE-FOOD-ROLE-POLICY.md)、[PRD-PHASE23-peak-moment.md](./PRD-PHASE23-peak-moment.md)、[PRD-TEMPLATE-SEMANTIC-LAYER.md](./PRD-TEMPLATE-SEMANTIC-LAYER.md)（TSL-P-01 已知债）、[PRD-BOOKENDS-ENGINE-V1.md](./PRD-BOOKENDS-ENGINE-V1.md)、[INSIGHT-WECHAT-TRAVEL-PHOTO-STORYLINE-2026-07-23.md](./INSIGHT-WECHAT-TRAVEL-PHOTO-STORYLINE-2026-07-23.md)、[PRD-STRATIFIED-CURATION.md](./PRD-STRATIFIED-CURATION.md) |
| **验收** | [ACCEPTANCE-FOOD-ROLE-POLICY.md](./ACCEPTANCE-FOOD-ROLE-POLICY.md) |
| **更新日期** | 2026-07-24 |

> **定位**
>
> 美食是「旅程调味」，不是「游记封面」。  
> **单张可展示，多张应成桌；默认不抢风景与人物的封面 / 封底 / 高光位。**
>
> 本 PRD 在既有 Phase 10 food-grid 与 Phase 9-E subject bridge 之上，补齐三条默认策略：
>
> 1. **封面 / 封底 / 章首 hero**：美食默认 demote（可配置硬排除）  
> 2. **Peak Moment / 高光池**：单张美食默认不进；「一桌菜」以 **food-grid 组屏** 承担热闹感，而非单张签名时刻  
> 3. **组屏门槛**：连续/同餐段 ≥2 张美食优先拼图；仅 1 张时单张展示
>
> **铁律**：不引入菜品级分类；不跨章聚合；Studio 手工「设为封面 / 加入高光」必须能覆盖默认策略。

---

## 1. 背景与问题

### 1.1 实测现象

当美食照片混入旅行相册时，当前成稿常见：

| 现象 | 读者体感 |
|------|----------|
| 每道菜各占一屏全幅 | 「游记变成菜单」 |
| 诱人横构图菜品被选为封面 | 「封面不像旅行」 |
| 美食偶发进入高光池 / 签名时刻 | 「高光变成一盘菜」 |
| 同桌菜被风景/人像打断后无法组屏 | 「明明一桌菜，却散成单张」 |

### 1.2 现状能力（已有）

| 能力 | 状态 | 说明 |
|------|------|------|
| 粗粒度美食识别 | **有** | CLIP `subjectClass=food`（置信度门槛）+ tags / L1 `semanticTag` / heuristic |
| food-grid 组屏 | **有** | `try_mundane_grid` / `try_food_grid`；默认 `enable_food_grid=true` |
| 组屏门槛 | **偏严** | 章内连续 mundane **≥3**；`tolerance=1`；无时间窗软聚合 |
| 封面 / 封底打分 | **不读美食** | `effective_cover_score` / ClosingScorer **无** `subjectClass=food` 项 |
| 审美 stratum | **部分** | cover/hero 的 stratum blend 不含 food（不抬升），但仍可被清晰度/色彩/画幅选中 |
| Peak Moment | **不读美食** | `peak_moment_score` / `build_moment_pool` 无 food demote |
| 菜品级分类 | **无** | 本 PRD **不**要求 |

### 1.3 问题陈述（FRP-P-*）

| ID | 问题 | 根因 |
|----|------|------|
| **FRP-P-01** | 美食可上封面 / 封底 | 选型层未消费 `food` 语义 |
| **FRP-P-02** | 单张美食易进高光池 | Moment 打分与 food 正交 |
| **FRP-P-03** | 1–2 张美食常单屏刷屏 | food-grid 硬门槛 ≥3 |
| **FRP-P-04** | 同餐段被打断无法成桌 | 仅时间线游程 + tolerance=1，无时间窗聚合 |
| **FRP-P-05** | 与洞察「一桌菜=高光」叙事错位 | 洞察指组屏热闹感；算法把单张菜当峰值 |

### 1.4 与 TSL 的边界

[PRD-TEMPLATE-SEMANTIC-LAYER.md](./PRD-TEMPLATE-SEMANTIC-LAYER.md) **TSL-P-01**（美食不该进 hero、风景不该进九宫格）是**全局内容-版式匹配**债。

本 PRD **不**实现完整 TSL；只在三个**确定性选型点**打补丁止血：

```text
cover / closing / chapter hero / moment pool   ← FRP（本 PRD）
MCS / LTE 语义打分 / semantic_vocabulary.yaml ← 仍归 TSL
```

后续 TSL 落地后，FRP 的 demote 系数可迁入统一语义权重，但 **默认行为不得回退**。

---

## 2. 目标与非目标

### 2.1 目标

| ID | 目标 | 验收口径 |
|----|------|----------|
| **G-FRP-01** | 默认成稿中，封面与封底 **不是** `food` 类照片 | 含美食 fixture：`coverAssetId` / `closingAssetId` 的 `subject_class≠food`（或走 fallback 例外） |
| **G-FRP-02** | 章首 hero 默认不选 `food` | `_pick_chapter_hero` 跳过 food；无非美食 landscape 时可降级 |
| **G-FRP-03** | 单张 `food` 默认不进 `momentPoolIds` / 不作 `momentAssetId` | 池构建阶段过滤；Studio 手工加入除外 |
| **G-FRP-04** | 同章同餐段 ≥2 张美食优先 food-grid；仅 1 张则单张 | 门槛 `min_grid_items=2`；pattern：2→双槽/ square-4；≥3 维持现行为 |
| **G-FRP-05** | 同餐段软聚合：时间窗内可跨少量非美食打断 | `food_cluster_window_seconds` + 打断容忍可配 |
| **G-FRP-06** | 全部策略可配置关闭，关闭后行为与 FRP 前一致 | feature flags / 权重 = 0 回退 |
| **G-FRP-07** | Studio 手工 override 优先于默认 demote | 用户指定封面 / 签名时刻时不因 food 被拒 |

### 2.2 非目标

- **不**做菜品 / 餐厅 / 菜单 OCR 细分类  
- **不**跨章聚合美食  
- **不**改 MCS 几何打分公式（美食 vs mosaic 的模板语义匹配仍归 TSL）  
- **不**把 food-grid 屏自动标为 `data-role="moment"`（避免与 Phase 23 签名语义冲突）  
- **不**新增 Studio 美食专用控件（MVP）；沿用既有「设封面 / 改签名时刻」  
- **不**改变 `mediaClass=collage`（用户自制拼图）既有单屏逻辑  

---

## 3. 产品规则（读者可见合同）

### 3.1 角色定义

| 角色 | 美食默认 | 例外 |
|------|----------|------|
| **封面** | 不当选 | ① 用户手工指定；② 候选池几乎全是美食（fallback） |
| **封底** | 不当选 | 同上 |
| **章首 hero** | 不当选 | 章内无可用 landscape/panorama 非美食时，允许降级（可不选 hero，优于强上美食） |
| **Peak Moment（单张签名 / 高光池）** | 单张美食不进 | 用户手工加入；或 `allow_food_in_moment=true` |
| **正文组屏（food-grid）** | ≥2 张成桌；1 张单展 | `enable_food_grid=false` 回退 |
| **「一桌菜」热闹感** | 由 food-grid 承担 | **不**自动升格为签名时刻角标 |

### 3.2 数量 → 版式

| 同餐段美食数（章内） | 版式 |
|----------------------|------|
| **0** | — |
| **1** | 单张正文屏（非 hero / 非 moment） |
| **2** | 优先双联或 `screen-square-4`（2 图占格，与 Phase 10 三图占 square-4 同家族） |
| **3–4** | `screen-square-4` |
| **5–6** | `screen-square-6` |
| **7–9** | `screen-square-9` |
| **>9** | 拆多个 grid（维持 Phase 10） |

### 3.3 与洞察文对齐

洞察文将「一桌菜」标为高光（热闹、好理解）。本 PRD 解读为：

> **叙事高光** = 组屏呈现的一桌热闹；  
> **算法签名时刻** = 仍留给人物 / 风景 / 决定性瞬间。

二者不互相替代。

---

## 4. 功能规格

### 4.0 共享判定：`is_food_asset`

新增（或抽自现有）统一判定，供 cover / closing / hero / moment / grid 共用：

```text
is_food_asset(asset) :=
  subject_class_for_asset(asset) == "food"
  OR is_mundane_clusterable(asset) == "food"
  OR semantic_category_for_asset(asset) in FOOD_L1_SET
```

`FOOD_L1_SET`（初值，可配）：`food`, `meal`, `cafe`, `restaurant`（与 Phase 10 / L1 词表对齐；不含 `sign` / `ticket`）。

**置信度**：沿用 CLIP floor（现状约 0.35）。低于 floor 时仅 tags / mundane 命中仍算 food（保守：宁可不进封面，也不漏 demote）。

**建议落点**：`travelogue/layout_contract/subject_tagging.py`（或 `travelogue/curation/food_policy.py` 薄封装，避免循环依赖）。

---

### 4.1 封面 demote（P0）

| 项 | 规格 |
|----|------|
| **改动点** | `effective_cover_score` 与/或 `pick_cover_asset_id_with_meta`（`travelogue/curation/curate_scoring.py`）；v2 路径同步（`cover_scoring_v2`） |
| **默认策略** | `food_cover_policy = demote`：`score *= food_cover_multiplier`（建议默认 **0.15**） |
| **可选硬排除** | `food_cover_policy = exclude`：候选阶段剔除 food；若剔除后池空 → fallback 放行 top food（记 `coverFoodFallback=true`） |
| **用户 override** | `trip.coverAssetId` / Studio repick / Bookends 手工指定 → **跳过** demote/exclude |
| **决策日志** | meta 增加 `foodPolicyApplied: demote|exclude|override|fallback|none` |

**验收直觉**：横构图高清晰美食，在存在任意非美食合格候选时，**不得**成为默认封面。

---

### 4.2 封底 demote（P0）

| 项 | 规格 |
|----|------|
| **改动点** | `build_closing_candidates` / ClosingScorer（`travelogue/cover_engine/closing/`） |
| **默认策略** | 与封面同构：`food_closing_policy = demote|exclude`；默认 **demote**，乘数建议 **0.15** |
| **排除关系** | 维持现有：避开 cover / moment ids；food 策略在其后叠加 |
| **用户 override** | 手工指定 `closingAssetId` 时跳过 |

---

### 4.3 章首 hero demote（P0）

| 项 | 规格 |
|----|------|
| **改动点** | `_pick_chapter_hero`（`screen_planner.py`） |
| **默认策略** | 跳过 `is_food_asset`；仅在 `landscape|panorama` 且非 food 中挑选 |
| **降级** | 若无可选非美食 → **不设章首 hero**（返回 `None`），优于强上美食全幅 |
| **配置** | `food_hero_policy = skip|allow`；默认 `skip` |

> 说明：现状 hero 已偏好 landscape/panorama，竖幅美食通常进不了；本条主要堵住「横幅美食高分抢章首」。

---

### 4.4 Peak Moment / 高光池（P0）

| 项 | 规格 |
|----|------|
| **改动点** | `build_moment_pool` / `_eligible_moment_candidates` / `peak_moment_score`（`moment_scoring.py`） |
| **默认策略** | `allow_food_in_moment = false`：候选阶段排除 `is_food_asset` |
| **打分层双保险** | 若配置为软 demote：`peak_moment_score *= food_moment_multiplier`（建议 **0.05**）；默认硬排除时乘数可不启用 |
| **用户 override** | Studio 指定 `momentAssetId` / 池内手工加入 → 允许 food |
| **与 food-grid** | food-grid 屏 **不**自动写入 `momentPoolIds`；不挂「决定性瞬间」角标 |
| **池为空 fallback** | 若排除 food 后无可选候选：按现有 Phase 23 降级规则扩池；**最后手段**才放行 food，并记 `momentFoodFallback=true` |

---

### 4.5 Food-grid：门槛与软聚合（P0）

#### 4.5.1 门槛调整（修订 Phase 10）

| 项 | Phase 10（现状） | FRP（本 PRD） |
|----|------------------|---------------|
| 最小张数 | ≥3 | **≥2**（`food_grid_min_items=2`） |
| 最大张数 | 9 | 9（不变） |
| 章范围 | 章内 | 章内（不变） |
| pattern | 3→square-4；4→4；6→6；9→9 | **2→双槽或 square-4**；其余不变 |

**2 张 pattern 决议（需评审锁定一项）**：

| 选项 | 说明 | 建议 |
|------|------|------|
| **A. `screen-square-4` 占 2 格** | 与 Phase 10 三图占格一致，实现成本低 | **默认推荐** |
| **B. 既有 2-up landscape/portrait pair** | 更「杂志双联」，但要处理横竖混排 | P1 增强 |

MVP 锁定 **选项 A**；验收以 A 为准。

#### 4.5.2 同餐段软聚合

在 `mundane_run_length` 之外新增（或扩展）收集器：

```text
collect_food_cluster_at_cursor(ids, assets_map, i, *,
  window_seconds,
  max_items=9,
  max_interruptions,
  allowed_buckets=("food",))
```

| 参数 | 默认 | 含义 |
|------|------|------|
| `food_cluster_window_seconds` | **3600**（60 min） | 以游标美食 `takenAt` 为锚，前后落入窗内的美食可入簇 |
| `food_grid_max_interruptions` | **2** | 时间序扫描时允许插入的非美食张数（比现 `tolerance=1` 略宽） |
| `food_grid_min_items` | **2** | 成簇下限 |

**规则**：

1. 游标必须是 food，否则不触发  
2. 向后（主）/ 可选向前微看，收集同章、同窗、同 bucket 的 food ids  
3. 非美食打断累计超过 `max_interruptions` 则停止向该方向扩展  
4. 簇大小 ∈ [min_items, 9] → 生成 food-grid，并从章序中移除这些 id（与现 `_remove_ids_once` 一致）  
5. **不跨章**；无 `takenAt` 时退化为纯游程逻辑（仅靠 interruptions）

#### 4.5.3 与 planner 主循环顺序

维持现有大致顺序，仅替换 `try_mundane_grid` 内部收集逻辑：

```text
collage-solo → mixed-pending → try_mundane_grid(FRP) → mosaic → landscape/portrait runs
```

`stage_flush_remaining_food`：章末剩余 food ≥ `min_items` 时同样走软聚合 flush。

---

### 4.6 配置面

建议挂在 `CurateConfig`（`travelogue/config/curate.py`）及 YAML / runtime 透传：

```yaml
curate:
  enable_food_grid: true
  mundane_grid_buckets: ["food"]

  food_role:
    cover_policy: demote          # demote | exclude | off
    cover_multiplier: 0.15
    closing_policy: demote        # demote | exclude | off
    closing_multiplier: 0.15
    hero_policy: skip             # skip | allow
    allow_food_in_moment: false
    moment_multiplier: 0.05       # 仅 soft 模式使用
    grid_min_items: 2
    cluster_window_seconds: 3600
    grid_max_interruptions: 2
```

| `*_policy = off` / `allow_food_in_moment=true` / `enable_food_grid` 旧门槛 | 行为 |
|----------------------------------------------------------------------------|------|
| 关闭 FRP 选型策略 | 与合入前一致（封面可上美食等） |
| `grid_min_items: 3` + 关软聚合 | 近似 Phase 10 原行为 |

---

### 4.7 决策可观测性（P0 最小）

在既有 decision / curate meta 中增加可调试字段（无需新 UI）：

| 字段 | 含义 |
|------|------|
| `foodPolicy.cover` | demote / exclude / override / fallback / none |
| `foodPolicy.closing` | 同上 |
| `foodPolicy.moment` | excluded / override / fallback / none |
| `foodPolicy.grids[]` | `{assetIds, windowSeconds, pattern, layoutHint}` |

维护者可用现有 debug badge / JSON 抽检；**不**对读者暴露。

---

## 5. UI / UX

| 面 | FRP MVP |
|----|---------|
| Reader | 无新控件；封面更「旅行」、美食更多成桌 |
| Studio | **无**新开关；沿用设封面 / 改签名时刻作为 override |
| 设置页 | MVP **不**暴露；高级用户走 config / 环境（与 Phase 10 一致） |
| 文案 | 不新增 Wait Tips；可选后续在帮助文档加一句「美食默认不成封面」 |

---

## 6. 实施切面与文件

### 6.1 建议模块拆分

| Wave | 内容 | 预估 |
|------|------|------|
| **W0** | `is_food_asset` + `FoodRoleConfig` + 单测 | 0.5d |
| **W1** | 封面 / 封底 / hero demote + override/fallback | 1d |
| **W2** | Moment 池排除 + fallback | 0.5d |
| **W3** | food-grid min=2 + 时间窗软聚合 + flush | 1–1.5d |
| **W4** | fixture / dogfood / acceptance 记录 | 0.5d |

合计约 **3.5–4 人日**（含评审修订缓冲）。

### 6.2 主要改动文件

| 文件 | 改动 |
|------|------|
| `travelogue/layout_contract/subject_tagging.py` | `is_food_asset`；可选扩展 cluster 收集 |
| `travelogue/config/curate.py` + `runtime.py` | `FoodRoleConfig` 字段与默认值 |
| `travelogue/curation/curate_scoring.py` | 封面 demote / exclude |
| `travelogue/cover_engine/closing/gate.py` 与/或 `scorer.py` | 封底 demote / exclude |
| `travelogue/layout_engine/planner/screen_planner.py` | `_pick_chapter_hero` skip food |
| `travelogue/layout_engine/planner/screen_planner_stages.py` | `try_mundane_grid` 软聚合与 min=2 |
| `travelogue/curation/moment_scoring.py` | 高光池排除 food |
| `tests/test_food_grid.py` | 扩 2 张 / 时间窗用例 |
| `tests/test_food_role_policy.py`（新建） | cover/closing/hero/moment 策略 |
| `docs/ACCEPTANCE-PHASE10.md` 或新建 `ACCEPTANCE-FOOD-ROLE-POLICY.md` | 验收清单 |

**尽量不改**：MCS scorer、LTE 模板几何、CLIP 类别表、Phase 23 渲染角标文案。

---

## 7. 测试与验收

### 7.1 自动化

| ID | 用例 | 预期 |
|----|------|------|
| **AC-FRP-01** | 混合相册：非美食 + 高分横幅美食 | 默认封面 ≠ food |
| **AC-FRP-02** | 候选几乎全 food | 允许 food 封面 + `coverFoodFallback` |
| **AC-FRP-03** | 用户指定 food 为封面 | override 生效，不被 demote 打掉 |
| **AC-FRP-04** | 混合相册封底 | 默认封底 ≠ food（有非美食候选时） |
| **AC-FRP-05** | 章内存在横幅美食与非美食 landscape | 章首 hero ≠ food |
| **AC-FRP-06** | 单张 food + 多张风景 | food ∉ `momentPoolIds`；不作 `momentAssetId` |
| **AC-FRP-07** | Studio 指定 food 为 moment | 允许 |
| **AC-FRP-08** | 2 张连续 food | 1 个 food-grid，非 2 个全幅 |
| **AC-FRP-09** | 3 张 food，中间插 1 风景，时间差 < 60min | 仍聚成 1 个 grid（interruptions 内） |
| **AC-FRP-10** | 1 张孤立 food | 单张正文，非 grid，非封面，非 moment |
| **AC-FRP-11** | `food_role.cover_policy=off` 且 `grid_min_items=3` | 行为近似 FRP 前 |
| **AC-FRP-12** | 无 vision、仅 tags=`food` | demote / 组屏仍生效 |

### 7.2 Dogfood / 人工

| ID | 条件 |
|----|------|
| **AC-FRP-D1** | 固定 1 本「旅行+美食混拍」trip：re-curate 前后对比封面 / 单张美食屏数 / grid 数 |
| **AC-FRP-D2** | 封面目视：第一印象是「地方/人/氛围」，不是「菜单」 |
| **AC-FRP-D3** | 同桌菜在成稿中以拼图出现的比例 ≥ 基线（记录 JSON） |

建议基线路径：`docs/acceptance-records/food-role-policy.<trip-id>.json`。

### 7.3 回归

- `pytest tests/test_food_grid.py`  
- Phase 23 moment 相关单测  
- 封面 / closing 既有单测  
- 无美食 demo trip：封面与屏结构无无意义漂移  

---

## 8. 风险与缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| CLIP 把非美食误标为 food | 好图被 demote | 乘数 demote 优于硬排除作默认；override 保留 |
| CLIP 漏标美食 | 仍上封面 | tags / L1 双通道；dogfood 收集漏检样本 |
| 2 张 square-4 留白难看 | 版式空洞 | MVP 用既有占格；P1 评估真·双联 |
| 时间窗过大把两餐拼一起 | 叙事混乱 | 默认 60min；可配；章边界硬切 |
| 全美食相册封面被掏空 | 无封面 | fallback 放行 + meta 标记 |
| 与 TSL 后续双重 demote | 美食永久抬不起头 | TSL 接入时统一权重，本 PRD 乘数可降为语义项 |

---

## 9. 里程碑

| 里程碑 | 交付 | 出口标准 | 状态 |
|--------|------|----------|------|
| **M0 评审** | 锁定 Q1–Q5（见 §10） | 默认策略入库 | ✅ 2026-07-24（按建议默认合入） |
| **M1 选型止血** | W0–W2 | AC-FRP-01–07、12 绿 | ✅ |
| **M2 组屏** | W3 | AC-FRP-08–11 绿 | ✅ |
| **M3 Dogfood** | Fixture 基线 + 真人清单 | AC-FRP-D1 自动绿；D2–D3 产品签 | 🟡 Fixture ✅ · 真人 ☐ |

---

## 10. 开放问题（已决议）

| # | 问题 | 决议 | 状态 |
|---|------|------|------|
| Q1 | 封面默认 `demote` 还是 `exclude`？ | **demote（0.15）** | ✅ Locked |
| Q2 | 2 张美食用 square-4 还是真双联？ | **square-4（选项 A）**；真双联 = P1 | ✅ Locked |
| Q3 | 同餐段时间窗？ | **3600s（60 min）** | ✅ Locked |
| Q4 | food-grid 升格叙事高光 / moment？ | **不做**（避免与 P23 打架） | ✅ Locked |
| Q5 | `sign` / `ticket` 封面 demote？ | **不做**；仅 food | ✅ Locked |

---

## 11. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1.0 | 2026-07-24 | 初稿：封面/封底/hero demote + moment 排除 + food-grid≥2 软聚合；范围对齐实测讨论 |
| v0.1.1 | 2026-07-24 | 落地实现：`FoodRoleConfig` / `food_policy` / planner + cover/closing/moment 接线；验收见 ACCEPTANCE |
| v0.1.2 | 2026-07-24 | 补齐对照缺口：moment 软 demote 接线、`foodPolicy.grids[]`、closing/cover override 落库与真验证、AC-10 补全、config.example / P10 验收同步 |
| v0.1.3 | 2026-07-24 | M3：fixture dogfood 脚本与基线入库；Q1–Q5 决议锁定；真人目视清单待产品签 |
