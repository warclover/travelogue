# PRD-MCS-GEOMETRIC-QUALITY-V1 · 跨职能评审纪要

| 属性 | 内容 |
|------|------|
| **文档** | [PRD-MCS-GEOMETRIC-QUALITY-V1.md](../PRD-MCS-GEOMETRIC-QUALITY-V1.md) |
| **关联** | [观感提升-业内调研.md](../观感提升-业内调研.md) · [观感提升路线图.md](../观感提升路线图.md) · [PRD-USAGE-RULES-LAYOUT-OPTIMIZATION.md](../PRD-USAGE-RULES-LAYOUT-OPTIMIZATION.md) · [p17-w0-audit-a-active-scoring-chain.md](./p17-w0-audit-a-active-scoring-chain.md) |
| **评审版本** | **v0.1.0 Draft** → Must-Fix 已回写 **[PRD v0.2.0](../PRD-MCS-GEOMETRIC-QUALITY-V1.md)** |
| **日期** | 2026-07-18 |
| **结论** | **有条件通过（Conditional Go）** · **可 Kickoff W0**（开关骨架 · 命名清理 · 落点审计） |
| **编码** | **可 Kickoff W0**；W1 前须拆 IMPLEMENTATION / ACCEPTANCE（BLK-08） |
| **参评角色** | 产品 · 算法 · 架构 · 开发 · 测试/QA · 交互/UI（评分台）· 典型用户（狗粮评审者） |
| **评审方式** | 分席只读（PRD §0～§4 + §9；对照现网 MCS / URO / LSE 冻结结论）· 按推荐案结案回写 |
| **记录人** | 产品 / 算法 / 工程联合纪要 |
| **本纪要状态** | **已结案（第一轮）** · BLK-01～08 回写 v0.2.0；**后续以 [专家评审第二轮](./mcs-geometric-quality-v1-expert-review-2026-07-18.md) 为准** |

---

## 0. 会前宣读（主持人 · 3 分钟）

1. **切口**：学 gridwiggle 的「准入声明 + 屏内几何软罚 + pairwise 标定」；**不**换 LTE，**不**上 LSE，**不**做连续分区 solver。  
2. **落点**：现网权威是 **MCS**（`mosaic.scorer` + `combine_utility`），不是 `layout.scoring` beam。  
3. **已冻结的不做清单**：runtime 改 `rect`、生产 shuffle/镜像、DETR、单屏 F-ratio 优化整本。  
4. **本场必拍**：D-MGQ-01～08（见 §6）——**已全部采纳推荐案**。  
5. **与 URO**：MGQ 消费 UR-01；不另起 usage 引擎。

---

## 1. 总评（一句话）

> **方向正确且边界清楚：落点 MCS、固定 SKU + 准入 DSL、pairwise 标定；阻塞在合同钉死（URO 合流、eligibility 挂载、sidecar 分轨、盲评集、fallback 守门）。BLK-01～08 回写 v0.2.0 后可 Kickoff W0；评分台留在 V1·W2，线框随 W2。**

---

## 2. 分席表决

| 席位 | 表决 | 一句话 |
|------|------|--------|
| **产品** | Conditional Go | 对标切口对；评分台对内；与 URO/BQP 须一句话合流 |
| **算法** | Conditional Go | 三 soft 阈值可测；CV 作主特征；章级碎裂靠盲评+诊断 |
| **架构** | Conditional Go | eligibility 挂 `constraints.eligibility`；fallback 必须罩硬过滤 |
| **开发** | Conditional Go | W0 小；W1 前拆 IMPL/AC；rating sidecar 独立更省事 |
| **测试 / QA** | Conditional Go | AC 阈值与「无 main 跳过」须可测；盲评集复用但 Gate 码独立 |
| **交互 / UI** | Conditional Go | W2 双候选够用；线框 W2 再补，不挡 W0 |
| **用户 · 狗粮评审** | Conditional Go | 「不够跳 / 太大 / 太碎」好懂；pairwise 比打分省力 |

**汇总**：**七席一致 Conditional Go**。MF 已回写 v0.2.0 → **可 Kickoff W0**。

---

## 3. 全场共识

1. **观感杠杆在 MCS + 准入 + 标定**，不在解冻 LSE。  
2. **`hero_separation` 名实保留**；屏内用新名。  
3. **固定 SKU 不可 runtime 重排**。  
4. **off 可先 merge**；默认开绑 **AC-MGQ-BLIND ≥55%**。  
5. **评分台 = `alt_topk` pairwise**；独立 `layout-rating.jsonl`。  
6. **W0 ≠ 主题完成**；W1a 第一刀 = UR-01 dogfood（与 URO 合流）+ eligibility DSL。

**会中新增共识**：

- `photoCountScale` 超带 → **硬拒绝**（非仅诊断）。  
- `cell_area_balance` **以面积 CV 为主**；F-ratio 仅作内部可选特征。  
- 评分台线框 **W2 再补**，不挡 W0。

---

## 4. Must-Fix（已成立 · 已回写 PRD v0.2.0）

| ID | 议题 | 来源席位 | 要求（冻结一字面） | 成立 |
|----|------|----------|-------------------|------|
| **BLK-01** | 落点轨写死 MCS | 架构 / 算法 | 新维度只进 `MosaicConfig`；AC-MGQ-11 断言 `layout.scoring.enabled` 默认 false | ✅ |
| **BLK-02** | 与 URO 开关/排期合流 | 产品 / 算法 | UR-01 / `usage_rules` 引擎归属 **URO**；MGQ W1a **消费**之；MGQ 另交 `constraints.eligibility` | ✅ |
| **BLK-03** | eligibility 挂载点 | 架构 / 开发 | SSOT = **`constraints.eligibility`**；不把完整 DSL 塞进 `usage.signals` | ✅ |
| **BLK-04** | soft 公式可测边界 | 算法 / 测试 | ceiling=0.50、prominence_min_ratio=1.35、cv_start=0.35；无 main → 跳过；写入 AC | ✅ |
| **BLK-05** | fallback 不得绕过硬过滤 | 架构 / 开发 | legacy / self-heal / replan 仍经 UR + eligibility；AC-MGQ-12 | ✅ |
| **BLK-06** | sidecar 分轨 | 开发 / 产品 | **独立** `runs/layout-rating.jsonl`；不扩展 `layout-feedback` editType | ✅ |
| **BLK-07** | 盲评集复用 | 产品 / QA | 与 BQP/URO **共用代表 trip 集 + harness**；Gate 码 **AC-MGQ-BLIND 独立** | ✅ |
| **BLK-08** | 拆文节奏 | 开发 / QA | W0 可以 PRD §9 为挡门；**W1 merge 前**必须拆 ACCEPTANCE + IMPLEMENTATION | ✅ |

---

## 5. Should-Fix（不单独挡 Kickoff）

1. W2 评分台默认 **内部/dogfood 开关**。  
2. `uncoveredPenalty` 保持 **P2 可选**。  
3. 诊断指标进 `layoutMetrics`（非 Gate）。  
4. 估时：W0 0.5–1d；W1 1–1.5w；W2 1–1.5w；W3 3–5d。  
5. 评分台线框 **W2 再补**。  
6. `cell_area_balance` 首期 CV；F-ratio 不进默认公式。

---

## 6. D-MGQ / OQ 拍板汇总

| 决策 | 本场决议 |
|------|----------|
| **D-MGQ-01** | **采纳** — 全部挂 `MosaicConfig`；禁止默认进 LSE / `layout.scoring` |
| **D-MGQ-02** | **采纳** — 固定 SKU + 准入 DSL；禁止 runtime 改 `rect` |
| **D-MGQ-03** | **采纳** — 保留 `hero_separation`；新增三几何维 |
| **D-MGQ-04** | **采纳** — P0 硬过滤 + reject 看板；P1 soft；硬不被 soft 绕过 |
| **D-MGQ-05** | **采纳** — pairwise（`alt_topk`）+ 分层用例；禁生产 shuffle |
| **D-MGQ-06** | **采纳** — off 可先 merge；默认开须 AC-MGQ-BLIND ≥55% |
| **D-MGQ-07** | **采纳** — 消费 URO；不另起 usage 引擎 |
| **D-MGQ-08** | **采纳** — 不引入 DETR；可加强 focal / face_crop / retention |

| OQ | 决议 |
|----|------|
| **OQ-MGQ-01** | **A** — 评分台为 V1·W2 必做（对内开关） |
| **OQ-MGQ-02** | **A** — W1a 第一刀 = UR-01 dogfood（与 URO 合流）+ eligibility DSL |
| **OQ-MGQ-03** | **A** — `photoCountScale` 超带 → **硬拒绝** |
| **OQ-MGQ-04** | **B** — 可 Kickoff W0 编码（开关 + 命名 + 落点审计） |

---

## 7. 分席要点摘要

### 7.1 产品
- 用户痛点成立；对外叙事：「少选错页型 + 主图更稳 + 可标定」。  
- 评分台不对全体用户；另立用户文案合同不在本波。

### 7.2 算法
- 阈值冻结见 BLK-04；权重各 ≤0.25 起步。  
- 章级碎裂：盲评看整本 + dense streak / hero 复用诊断。

### 7.3 架构
- `constraints.eligibility` 为 SSOT；与 URO `usage` 分层。  
- 默认权重变更时由算法负责人裁定是否 bump algorithm lock。

### 7.4 开发
- W0：`MosaicConfig.geometric_quality` 骨架 + 注释/单测锁 `hero_separation`。  
- W1 前拆 IMPLEMENTATION / ACCEPTANCE。

### 7.5 测试 / QA
- AC-MGQ-11/12 进 v0.2；盲评 Gate 码独立、样本可共用。

### 7.6 交互 / UI
- W2 一屏双候选 + 标签足够；线框不挡 W0。

### 7.7 用户 · 狗粮评审
- 标签词表可读；支持 pairwise。

---

## 8. 会后动作

| # | 动作 | 负责人 | 状态 |
|---|------|--------|------|
| 1 | 回写本纪要结论与拍板一字面 | 记录人 | ✅ |
| 2 | BLK-01～08 合入 PRD → **v0.2.0** | 产品 / 算法 | ✅ |
| 3 | Kickoff W0：补 `IMPLEMENTATION-…` 任务卡（可与 W0 同开） | 开发 | □ |
| 4 | W1 merge 前拆 `ACCEPTANCE-…` | QA | □（BLK-08） |
| 5 | PRD 状态 → Conditional Go · Ready for Kickoff W0 | 产品 | ✅ |
| 6 | 通知 URO / BQP 业主：BLK-02 / BLK-07 合流点 | 产品 | □ |

---

## 9. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| 会前稿 | 2026-07-18 | 预填共识候选、BLK 候选、D-MGQ/OQ 拍板表 |
| 结案 | 2026-07-18 | 七席 Conditional Go；D-MGQ/OQ 采纳推荐案；BLK-01～08 成立并回写 PRD v0.2.0 |
