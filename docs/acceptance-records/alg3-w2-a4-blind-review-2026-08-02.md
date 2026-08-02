# ALG-V3 · W2-A4 盲评记录

| 属性 | 内容 |
|------|------|
| **日期** | 2026-08-02 |
| **评分人** | 产品（本机狗粮） |
| **alg3Wave** | W2-A4 |
| **experimentalRelax** | true（实验臂） vs false（默认对照） |
| **adaptiveSoftSplit** | false（本轮不评 A3） |
| **visionEffective** | off |
| **Trip** | `demo-3ee2727aea`（与 W1b 同册；clone 条件门保持 On） |
| **模板** | [alg3-blind-review-TEMPLATE.md](./alg3-blind-review-TEMPLATE.md) |
| **狗粮指南** | [alg3-blind-dogfood-GUIDE.md](./alg3-blind-dogfood-GUIDE.md) |
| **状态** | **Pass（持平）** · **不抬默认 on**（自动化 AC-12 已绿；X04 已做人评） |

## 成对样本

| 对 | Off 截图 | On 截图 | 对照拼图 | 问1 假切条 | 问2 跳戏 | 问3 混拼/过碎 | 问4 节奏 |
|----|----------|---------|----------|------------|----------|---------------|----------|
| 1 | [a4-pair1-off.png](./attachments/alg3-blind-2026-08-02/a4-pair1-off.png) | [a4-pair1-on.png](./attachments/alg3-blind-2026-08-02/a4-pair1-on.png) | [compare](./attachments/alg3-blind-2026-08-02/a4-pair1-compare.png) | **平** | **平** | N/A | N/A |
| 2 | | | | | | N/A | N/A |
| 3 | | | | | | N/A | N/A |

全页：`a4-pair1-off-full.png` / `a4-pair1-on-full.png`。

## 漏斗 / 摘要抽查（本机 arm 脚本）

| 项 | Off | On |
|----|-----|-----|
| `cloneGateEffective` | true | true |
| `experimental_relax`（配置） | false | true |
| `rejectFunnelTop.atom_boundary` | 0 | 0 |
| 版式指纹条数 | 20 | 19 |
| 客观差异 | `013`/`014` 各单张 | `media-row:013,014` 合并 |

原始：`attachments/alg3-blind-2026-08-02/a4-{off,on}-algoV3.json` · `*-patterns.json`

## 结论

| 项 | 勾选 |
|----|------|
| W2-A4：问1 On ≥ Off | ☑（**平**） |
| W2-A4：问2 跳戏不差于 Off | ☑（**平**） |
| **总评** | ☑ **Pass（持平）**　□ Conditional　□ Fail |

## 人评原话

> A4（013/014 单张 vs 成对）结果是一样的，所以持平。

## 备注

自动化门：`tests/unit/layout_engine/test_alg3_w2_a4_atom_experimental.py`。人评满足 X04（非仅 funnel）。

**产品决策**：本册实验臂与默认臂观感持平 → **可宣称 A4 盲评过门**，但 **不**据此把 `experimental_relax` 抬为默认 on（与产品锁一致；持平 ≠ 有收益）。
