# ALG-V3 · W1b 盲评记录（脚手架）

| 属性 | 内容 |
|------|------|
| **日期** | 2026-08-01 |
| **评分人** | （待填） |
| **alg3Wave** | W1b |
| **cloneGateOn** | true（条件门默认） vs false 对照 |
| **adaptiveSoftSplit** | false（本轮不评 A3） |
| **visionEffective** | off（无 vision / SSG empty 路径） |
| **模板** | [alg3-blind-review-TEMPLATE.md](./alg3-blind-review-TEMPLATE.md) |
| **状态** | **脚手架 · 人评未完成**（自动化 AC-10 已绿；本文件不挡码，挡 **M1b 宣称**） |

## 成对样本

| 对 | Off 截图 | On 截图 | 问1 假切条 | 问2 跳戏 | 问3 混拼/过碎 | 问4 节奏 |
|----|----------|---------|------------|----------|---------------|----------|
| 1 | （待补） | （待补） | | | | N/A |
| 2 | | | | | | N/A |
| 3 | | | | | | N/A |

## 建议语料（从 SSG dogfood / 自有相册抽）

1. 无 vision、无 `shotGroupId` 的密连拍步行段（假切条高发）  
2. 横竖混拼同场景  
3. 窄屏长图导出对照  

## 结论

| 项 | 勾选 |
|----|------|
| W1b：问1 On ≥ Off | □ |
| W1b：问3 混拼不差于 Off | □ |
| **总评** | □ Pass　□ Conditional　□ Fail · **当前：Pending human** |

## 备注

自动化门：`tests/unit/layout_engine/test_alg3_w1b_clone_gate.py`（合成窗 funnel / ↓≥40% 或硬可见）。人评完成后把本页状态改为 Pass/Conditional 并链截图路径。
