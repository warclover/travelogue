# ALG-V3 · W1b 盲评记录

| 属性 | 内容 |
|------|------|
| **日期** | 2026-08-02 |
| **评分人** | 产品（本机狗粮） |
| **alg3Wave** | W1b |
| **cloneGateOn** | true（条件门） vs false 对照 |
| **adaptiveSoftSplit** | false（本轮不评 A3） |
| **visionEffective** | off（本轮 arm 配置强制） |
| **Trip** | `demo-3ee2727aea`（夏睿彤年度精选） |
| **模板** | [alg3-blind-review-TEMPLATE.md](./alg3-blind-review-TEMPLATE.md) |
| **狗粮指南** | [alg3-blind-dogfood-GUIDE.md](./alg3-blind-dogfood-GUIDE.md) |
| **状态** | **Pass**（pair1 人评完成；自动化 AC-10 已绿） |

## 成对样本

| 对 | Off 截图 | On 截图 | 对照拼图 | 问1 假切条 | 问2 跳戏 | 问3 混拼/过碎 | 问4 节奏 |
|----|----------|---------|----------|------------|----------|---------------|----------|
| 1 | [w1b-pair1-off.png](./attachments/alg3-blind-2026-08-02/w1b-pair1-off.png) | [w1b-pair1-on.png](./attachments/alg3-blind-2026-08-02/w1b-pair1-on.png) | [compare](./attachments/alg3-blind-2026-08-02/w1b-pair1-compare.png) | **On 优** | N/A | **平**（两者可接受） | N/A |
| 2 | | | | | | | N/A |
| 3 | | | | | | | N/A |

全页：`w1b-pair1-off-full.png` / `w1b-pair1-on-full.png`（高度 Off≈17803 · On≈16119）。

## 漏斗 / 摘要抽查（本机 arm 脚本）

| 项 | Off | On |
|----|-----|-----|
| `cloneGateEffective` | false | true |
| `visionEffective` | off | off |
| `rejectFunnelTop.near_scene_clone` | 0 | 0 |
| 版式指纹条数 | 19 | 20 |
| 开篇差异（客观） | `media-row:001,002,003` 密拼 | `001/002/003` 拆成单张 |

原始：`attachments/alg3-blind-2026-08-02/w1b-{off,on}-algoV3.json` · `*-patterns.json`  
复现：`python scripts/alg3_blind_dogfood_arm.py w1b-off …/cfg-w1b-off.yaml`

## 结论

| 项 | 勾选 |
|----|------|
| W1b：问1 On ≥ Off | ☑（On 优；合影不宜挤进一行） |
| W1b：问3 混拼不差于 Off | ☑（两者都可接受 → 平） |
| **总评** | ☑ **Pass**　□ Conditional　□ Fail |

## 人评原话

> Off 开篇把 001–003 收成一行；On 拆成单张。两者都可以接受，我更喜欢后者，因为照片是合影。

## 备注

自动化门：`tests/unit/layout_engine/test_alg3_w1b_clone_gate.py`。  
产品含义：条件 clone 门（现网默认 On）在本册合影连拍段上更符合「单张看清合影」的偏好；不禁止 Off 的密拼，但 On 更优。
