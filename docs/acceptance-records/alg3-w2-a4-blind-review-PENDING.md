# ALG-V3 · W2-A4 盲评记录（脚手架）

| 属性 | 内容 |
|------|------|
| **日期** | 2026-08-01 |
| **评分人** | （待填） |
| **alg3Wave** | W2-A4 |
| **experimentalRelax** | true（实验臂） vs false（默认对照） |
| **adaptiveSoftSplit** | false（本轮不评 A3） |
| **visionEffective** | off / 按样本 |
| **模板** | [alg3-blind-review-TEMPLATE.md](./alg3-blind-review-TEMPLATE.md) |
| **狗粮指南** | [alg3-blind-dogfood-GUIDE.md](./alg3-blind-dogfood-GUIDE.md) · [config 样例](../config-alg3-blind-dogfood.example.yaml) |
| **状态** | **脚手架 · 人评未完成**（自动化 AC-12 funnel+share 已绿；本文件不挡码，挡 **抬默认 on / 宣称 M2·A4 实验过门**） |

## 成对样本

| 对 | Off 截图 | On 截图 | 问1 假切条 | 问2 跳戏 | 问3 混拼/过碎 | 问4 节奏 |
|----|----------|---------|------------|----------|---------------|----------|
| 1 | （待补） | （待补） | | | N/A | N/A |
| 2 | | | | | N/A | N/A |
| 3 | | | | | N/A | N/A |

## 建议语料

1. 同 SG 密连拍但邻接间隔略超 600s（假切条 vs 合法跨隙）  
2. 横竖混拼同场景、多槽占比贴近 observe floor  
3. 窄屏长图导出对照  

## 结论

| 项 | 勾选 |
|----|------|
| W2-A4：问1 On ≥ Off | □ |
| W2-A4：问2 跳戏不差于 Off | □ |
| **总评** | □ Pass　□ Conditional　□ Fail · **当前：Pending human** |

## 备注

自动化门：`tests/unit/layout_engine/test_alg3_w2_a4_atom_experimental.py`（funnel↓≥25% + multi-slot share≥floor + floor 永不自动 widen）。人评完成后把本页状态改为 Pass/Conditional 并链截图路径。**禁止**仅凭 funnel 宣称 AC-12 全绿（X04）。

**相邻狗粮（不计入本表）**：2026-08-02 master 手动走查未开 `experimental_relax`；默认路径观感 ≠ A4 实验臂盲评。
