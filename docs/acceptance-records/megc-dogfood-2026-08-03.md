# MEGC · demo-2019 狗粮记录 · 2026-08-03

| 属性 | 内容 |
|------|------|
| **行程** | `demo-2019` |
| **日期** | 2026-08-03 |
| **分支 / 代码** | `feature/megc-pr-b-selection-gate` @ `362fde2b`（worktree `megc-pr-b-58eba1f4`） |
| **配置样例** | [config-megc-dogfood.example.yaml](../config-megc-dogfood.example.yaml) · `score_mul=0.62` · soft_penalty |
| **本机 config** | 当时临时覆盖后已还原；**事后**仓库默认已转正为 on（见 [默认 on 决策](./megc-default-on-decision-2026-08-03.md)） |
| **关联** | [ACCEPTANCE](../ACCEPTANCE-MOSAIC-EQUAL-GRID-CONTRACT-V1.md) · [IMPL](../IMPLEMENTATION-MOSAIC-EQUAL-GRID-CONTRACT-V1.md) · [PRD v0.2.0](../PRD-MOSAIC-EQUAL-GRID-CONTRACT-V1.md) |

> **历史记录**（转正前）：当时结论是保持默认 off——PR-A 几何已实机绿；PR-B 闸语义对原始等权窗正确，但整册 re-layout 大量走 legacy/classic，软闸胜出率未闭环。随后 PR-B2 + 实册手测后已改默认 on。

---

## 1. 方法

| 步骤 | 做法 |
|------|------|
| A · 闸语义 | 在 **原始** `trip.json`（含既有 5 个 `screen-landscape-4`）上，用 ON 配置调用 `evaluate_megc_gate` |
| B · 整册 off/on | `layout --layout auto --web-layout screens --render --no-validate`（worktree 包优先 import）；对比 pattern 直方图与锚点窗 |
| C · 渲染几何 | 还原原始 trip → worktree `render`（同步 PR-A CSS）→ Playwright 量 `stageH/gridH/bottomOk` 并截图 |
| 禁令核对 | 未改仓库默认 enabled；未用 MSA trackOverride；未新建平行 3:2 YAML |

校验失败注记：本机 trip 含 `curation.coverOrientationByLayout.mobile.preferredCandidateId`，schema 报错；狗粮用 `--no-validate` 完成 render（与选型结论正交）。

---

## 2. 闸语义（原始等权窗 · MEGC ON）

来源：`attachments/megc-dogfood-2026-08-03/gate-on-original-l4.json`

| screenId | native AR 峰 | 期望 | 实测 outcome | score_mul |
|----------|--------------|------|--------------|-----------|
| ch-01-sc-03 | 全 ~1.50 → `three_two` | soft 罚 | **gate_penalize** | 0.62 |
| ch-01-sc-06 | 全 ~1.78 → `sixteen_nine` | 放行 | **gate_allow** | 1.0 |
| ch-01-sc-12 | 峰 `sixteen_nine` | 放行 | **gate_allow** | 1.0 |
| **ch-02-sc-07**（086/088/089/091） | 全 ~1.50 → `three_two` | soft 罚 | **gate_penalize** | 0.62 |
| ch-03-sc-04 | 全 ~1.50 → `three_two` | soft 罚 | **gate_penalize** | 0.62 |

→ AC-04/05 语义在原始锚点上成立；**未误杀电影峰**。

---

## 3. 整册 re-layout · off vs on

| | OFF | ON |
|--|-----|----|
| screens | 22 | 18 |
| `screen-landscape-4` | 1（16:9 峰） | 1（纯 16:9） |
| 锚点 086/088/089 | `screen-landscape-3` | `screen-landscape-3` |
| mosaicDecisionLog | 多数 `plannerPath=legacy` | 同左 |

要点：

1. **3:2 等权四宫在当前 MCS/legacy 重排下本就不稳定复现**（原始冻结册有 3×3:2 L4；re-layout 后锚点改走 landscape-3）。  
2. ON/OFF 均保留 **1 个 16:9 `landscape-4`** → 电影峰不被误杀（与闸表一致）。  
3. ON 屏数 22→18：与 MSA 狗粮类似的 **pacing 漂移**；soft `score_mul` 进入 MCS 时可能间接改窗，但本册多数窗未走 mosaic winner，**不能据此标定 0.62 是否够压 `base_weight≈1.12`**。  
4. 持久化 `mosaicDecisionLog` 为 summary 级，**不含** `megcEnabled/Outcome`（AC-07 仍以 raw `drain_mosaic_capture` / 单测为准）。

附件：`off-relayout-summary.json` · `on-relayout-summary.json`

---

## 4. 渲染几何（PR-A · 原始含 contain 锚点）

Playwright @ 1280×900 · 原始 trip + PR-A CSS 已 sync 到 `trips/demo-2019/journal-screens.css`

| 夹具 | stageH | gridH | gridOk | bottomOk | contain |
|------|--------|-------|--------|----------|---------|
| **anchor-3x2-contain**（086…091 · 右上 contain） | 720 | 720 | ✅ | ✅ | 1 |
| l4-3x2-ch01 | 720 | 720 | ✅ | ✅ | 0 |
| l4-16x9-ch01 | 720 | 720 | ✅ | ✅ | 0 |
| l4-3x2-ch03 | 720 | 720 | ✅ | ✅ | 0 |

对照 PRD F-06 旧 DOM（stage 802 / grid 953 / 下排被裁）：**本轮 `deltaGrid=0`，下排不被裁。**

截图：`attachments/megc-dogfood-2026-08-03/*.png`

---

## 5. 结论与建议

| 项 | 结论 |
|----|------|
| 默认 `enabled` | **当时保持 false**；事后已见 [默认 on 决策](./megc-default-on-decision-2026-08-03.md) |
| `score_mul=0.62` | **暂不调**；需下一批「走 mosaic candidates」的窗或 planner finalize 后再标定胜出率 |
| PR-A CSS | 实机几何 ✅，可视为 demo-2019 contain 锚点收口 |
| PR-B 选型闸 | 单元 + 原始窗 gate 表 ✅；整册视觉「少落 3:2 L4」被 legacy 旁路挡住 |
| 下一 PR 优先 | **planner/legacy finalize 自愈挂 MEGC**（已知风险 #2）；然后再做胜出率狗粮 / 盲评（AC-10） |
| M3 | 仍延期 |

> 注：上表为 **当日** 狗粮结论；PR-B2 + 实册后默认已转正。

**签名**：Agent 狗粮代记录　日期：2026-08-03
