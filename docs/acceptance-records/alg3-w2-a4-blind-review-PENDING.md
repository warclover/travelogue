# ALG-V3 · W2-A4 盲评记录（脚手架）

| 属性 | 内容 |
|------|------|
| **日期** | 2026-08-02 |
| **评分人** | （待填 · 请打乱 Off/On 标签后打分） |
| **alg3Wave** | W2-A4 |
| **experimentalRelax** | true（实验臂） vs false（默认对照） |
| **adaptiveSoftSplit** | false（本轮不评 A3） |
| **visionEffective** | off |
| **Trip** | `demo-3ee2727aea`（与 W1b 同册；clone 条件门保持 On） |
| **模板** | [alg3-blind-review-TEMPLATE.md](./alg3-blind-review-TEMPLATE.md) |
| **狗粮指南** | [alg3-blind-dogfood-GUIDE.md](./alg3-blind-dogfood-GUIDE.md) |
| **状态** | **材料已备 · 等人评**（自动化 AC-12 已绿；本文件不挡码，挡 **抬默认 on / 宣称 M2·A4 实验过门**） |

## 成对样本

| 对 | Off 截图 | On 截图 | 对照拼图 | 问1 假切条 | 问2 跳戏 | 问3 混拼/过碎 | 问4 节奏 |
|----|----------|---------|----------|------------|----------|---------------|----------|
| 1 | [a4-pair1-off.png](./attachments/alg3-blind-2026-08-02/a4-pair1-off.png) | [a4-pair1-on.png](./attachments/alg3-blind-2026-08-02/a4-pair1-on.png) | [compare](./attachments/alg3-blind-2026-08-02/a4-pair1-compare.png) | | | N/A | N/A |
| 2 | | | | | | N/A | N/A |
| 3 | | | | | | N/A | N/A |

全页：`a4-pair1-off-full.png` / `a4-pair1-on-full.png`。中段裁切：`a4-{off,on}-mid.png`。

## 漏斗 / 摘要抽查（本机 arm 脚本）

| 项 | Off | On |
|----|-----|-----|
| `cloneGateEffective` | true | true |
| `experimental_relax`（配置） | false | true |
| `rejectFunnelTop.atom_boundary` | 0 | 0 |
| 版式指纹条数 | 20 | 19 |
| 客观差异 | `013`/`014` 各单张 | `media-row:013,014` 合并 |

原始：`attachments/alg3-blind-2026-08-02/a4-{off,on}-algoV3.json` · `*-patterns.json`  
复现：`python scripts/alg3_blind_dogfood_arm.py a4-on …/cfg-a4-on.yaml`

## 结论

| 项 | 勾选 |
|----|------|
| W2-A4：问1 On ≥ Off | □ |
| W2-A4：问2 跳戏不差于 Off | □ |
| **总评** | □ Pass　□ Conditional　□ Fail · **当前：Pending human（材料 Ready）** |

## 备注

自动化门：`tests/unit/layout_engine/test_alg3_w2_a4_atom_experimental.py`。**禁止**仅凭 funnel↓ 宣称 AC-12 过门（X04）。

本册 A4 差异偏局部（013/014 是否成对）；若观感「平」，可再补一对「邻接间隔略超 600s」语料后再结案。
