# PRD-MCS-GEOMETRIC-QUALITY-V1 · 跨职能专家评审纪要（第二轮）

| 属性 | 内容 |
|------|------|
| **文档** | [PRD-MCS-GEOMETRIC-QUALITY-V1.md](../PRD-MCS-GEOMETRIC-QUALITY-V1.md) |
| **评审版本** | **v0.2.0** → Must-Fix 回写 **[v0.2.1](../PRD-MCS-GEOMETRIC-QUALITY-V1.md)** |
| **日期** | 2026-07-18 |
| **结论** | **有条件通过（Conditional Go）** · **可 Kickoff W0** · **W1 merge 前须消化 BLK-09～14** |
| **相对第一轮** | [mcs-geometric-quality-v1-review-2026-07-18.md](./mcs-geometric-quality-v1-review-2026-07-18.md) 为推荐案结案；**本轮为对照现网代码的正式分席评审** |
| **参评席位** | 算法 · 架构 · 开发 · 测试/QA · 用户体验（含狗粮） |
| **评审方式** | 分席只读 · 对照 `mosaic/scorer` / `candidates` / `selfheal` / `replan` / LTE schema / URO / golden |
| **记录人** | 五席合成纪要 |

---

## 1. 总评（一句话）

> **五席一致 Conditional Go：方向与落点（MCS）站得住，W0 可开工；W1 前必须钉死面积加权口径、堵住现网 self-heal/legacy 硬过滤绕过、写清 eligibility 接线与空候选策略，并把若干 AC/盲评合同改成可判定字面——否则 AC-MGQ-12 与阈值验收会假绿。**

---

## 2. 分席表决

| 席位 | 表决 | 一句话 |
|------|------|--------|
| **算法** | Conditional Go | 阈值形式站得住；面积须按 `col_frac×row_frac`；self-heal/legacy 绕过须进 AC |
| **架构** | Conditional Go | eligibility schema/默认语义未钉；继承 URO 两条真实绕过口；UNDO 优先级未定 |
| **开发** | Conditional Go | 可挂现骨架；W1 前修 self-heal + 钉接线点 + 面积 helper + 原始特征落点 |
| **测试 / QA** | Conditional Go | 阈值可测；AC-12/02/04/05/08/BLIND 字面不足会假绿 |
| **用户体验** | Conditional Go | W0 无用户面风险；W2 评分台须隔离「这页」编辑心智并澄清「不改本书」 |

**汇总**：**五席一致 Conditional Go**。D-MGQ-01～08 / OQ-01～04 **维持采纳**；新增 **BLK-09～14** 阻塞 W1（不阻塞 W0）。

---

## 3. 全场共识

1. **落点 MCS + 固定 SKU + 消费 URO** 经代码交叉核对成立。  
2. **`hero_separation` ≠ prominence** 代码证据充分（`beam_scoring.py`）。  
3. **W0 可 Kickoff**（开关骨架 / 命名 / 落点 CI 断言）。  
4. **现网已存在硬过滤绕过**（非假设）：`selfheal.drop_worst_asset` 未传 `window_ctx`；`replan_screen(legacy)` 不经 `evaluate_reject`。MGQ 上 soft 会放大暴露面。  
5. **面积必须按轨道权重折算**，禁止按 rect 格数裸计。  
6. **评分台对内**；优先独立 debug 路由，勿与「这页」真实编辑语汇混用。

---

## 4. Must-Fix（本轮新增 · 已回写 PRD v0.2.1）

| ID | 议题 | 来源席位 | 冻结要求 | 挡 |
|----|------|----------|----------|----|
| **BLK-09** | 面积/覆盖率计权口径 | 算法 / 架构 / 开发 | 面积 = `slot_display_aspect` 同款 **`col_frac × row_frac`**（按 `layoutGeometry.cols/rows` 权重）；禁止按 rect 格数计数；单测覆盖 `screen-mosaic-5-hero-3-2-plus-4` | W1b |
| **BLK-10** | self-heal / replan-legacy 绕过硬过滤 | 算法 / 架构 / 开发 / QA | W1a 前修复：`drop_worst_asset` 重建 `WindowContext` 并走 `generate_window_candidates_with_rejections`；`replan_screen(legacy)` 须过硬过滤或对 MGQ/URO harness **禁用**；AC-MGQ-12 拆路径验收 | W1a |
| **BLK-11** | eligibility schema 默认语义 | 架构 | 未声明 `constraints.eligibility` ≡ 不参与硬拒绝（moderate、无上限）；schema PR 同批 registry cache 重建 + 全量 validate | W1a |
| **BLK-12** | eligibility 接线与空候选 | 架构 / 开发 | 插入点 = URO `evaluate_reject` **之后**；**不参与** `USAGE_RULE_UNDO_ORDER`；空候选走缩窗/legacy，不撤销 eligibility | W1a |
| **BLK-13** | 原始几何特征落点 | 开发 / QA | `MosaicWindowLog`（或等价）存 raw：`heroProminenceRatio` / `heroCoverageRatio` / `cellAreaCv`，与 penalty 分栏 | W1b |
| **BLK-14** | AC / 盲评可判定合同 | QA / 算法 / UX | 见 §6；含 coverage 边界 `>`、盲评开关矩阵、用例轴最小样本、评分台「不改本书」文案 | W1 merge 前（ACCEPTANCE） |

**第一轮 BLK-01～08**：本轮复核 **维持成立**，不重开。

---

## 5. Should-Fix（不单独挡 W0）

1. `hero_coverage` 判定用 **`> 0.50`**（加权后 `hero-3-2-plus-4` 主槽恰 0.50，避免误伤）。  
2. `photoCountScale` 硬拒绝走 `candidates._reject`，勿复制 `main_ar_ineligible` 双轨 soft。  
3. `cell_area_balance`：content 槽 **n&lt;3 跳过或衰减**；不读 `visualWeight`。  
4. 诊断指标按 `patternId` 分层；与 dense streak / hero 复用联动对账。  
5. `geometric_quality` 未知子 key **fail-loud**（勿学顶层 penalties 静默丢键）。  
6. decision log：复用 `usageRuleRejects`（reason=`eligibility:*`）或新增字段——IMPLEMENTATION 二选一写死。  
7. 估时：W0 **1–1.5d**；W1 **1.5–2w**（含 BLK-10 修复）；用例集构建另计产品/QA 2–3d。  
8. AC-MGQ-09 P95：明确脚本或挪到 W3。  
9. **UX**：评分台优先独立路由；文案钉「不改变当前书任何一页」；`wasted-space` 标签标注「暂未接入调权」或 W2 首发不放；P-05/P-06 移出「用户可感知」表。  
10. W1 跑三罚项**触发覆盖率**基线，判断故事强度再进 W3。  
11. 分层用例补轴：**均匀网格 / 加权轨道**。  
12. URO 文档 vs 代码：`usage_rules.enabled` 默认与 `URO_GOLDEN_TRIP_IDS`「8 vs 9」口径先核对再共用盲评集。

---

## 6. AC / 盲评合同补丁（BLK-14 明细）

| 项 | 要求 |
|----|------|
| AC-MGQ-02 | 改可执行断言：面积分布变而 `hero_separation` 不变；仅 `hero_asset_ids` 重叠态变化时才变 |
| AC-MGQ-04 | 钉死 breakdown key + raw 特征字段（BLK-13） |
| AC-MGQ-05 | fixture：heroScore/featured 持平窗；`extreme` 拒 / `moderate` 放行对照 |
| AC-MGQ-06/14 | 面积口径 BLK-09；coverage 用 `>`；临界样本含 `hero-3-2-plus-4` |
| AC-MGQ-08 | 每轴每档最小样本 **≥3** |
| AC-MGQ-12 | 拆测：legacy 路径 / self-heal 三分支（含 drop）/ replan |
| AC-MGQ-BLIND | 两臂只翻 `geometric_quality`；`usage_rules` 同态；复用 `URO_GOLDEN_TRIP_IDS`（先统一本数口径）；声明 veto/脚本扩展方式；平局计分规则写死 |
| photoCountScale | 映射独立 AC 或并入 AC-MGQ-05 |
| 评分台 UX | ACCEPTANCE/线框含「不改本书」固定文案 |

---

## 7. D-MGQ / OQ 复核

| 决策 | 本轮 |
|------|------|
| D-MGQ-01～03、05～08 | **维持采纳** |
| D-MGQ-04 | **维持采纳**，执行依赖 **BLK-10** |
| OQ-MGQ-01、03、04 | **维持采纳** |
| OQ-MGQ-02 | **维持采纳**，顺序微调：先 **BLK-10** 再开 UR-01 dogfood |

---

## 8. 分席要点（摘要）

### 8.1 算法
- 复用 `geometry.py::slot_display_aspect` 的 frac 原语。  
- soft 插在乘性链前段，须与节奏诊断联动。  
- 新 soft 放大 self-heal 触发 → 与绕过口复合风险。

### 8.2 架构
- schema `additionalProperties:false` → eligibility 全有全无迁移窗口。  
- AC-MGQ-01 比较口径钉 `patternId`+`assetIds`+几何（非浮点 score）。  
- sidecar 分轨对；建议统一 reader 分派 schema。

### 8.3 开发
- W0 文件清单：`config/mosaic.py`、注释/单测、IMPLEMENTATION。  
- W1：`eligibility.py`、`candidates.py`、`selfheal.py`、`legacy.py`、`scorer.py`、面积 helper、log。  
- W2：预览复用纯函数 `_pick_alt_topk`，**禁止**误用会 mutate 的 `replan_screen`。

### 8.4 测试 / QA
- 假绿最高危：AC-MGQ-12。  
- 盲评「同场」缺开关矩阵与脚本常量名。

### 8.5 用户体验
- P-04 真且最重；P-05/P-06 非用户问题。  
- 狗粮故事强度依赖罚项触发率，建议 W1 先统计。

---

## 9. 会后动作

| # | 动作 | 状态 |
|---|------|------|
| 1 | 本纪要结案 | ✅ |
| 2 | BLK-09～14 回写 PRD → **v0.2.1** | ✅ |
| 3 | Kickoff W0 + 开 IMPLEMENTATION | □ |
| 4 | W1 merge 前拆 ACCEPTANCE（含 §6 合同） | □ |
| 5 | 通知 URO 业主：BLK-10 共修 + 盲评口径 8/9 | □ |

---

## 10. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| 专家评审结案 | 2026-07-18 | 五席 Conditional Go；新增 BLK-09～14；回写 PRD v0.2.1 |
