# ALG-V3 · 盲评记录模板（W1b+ · FE-ALG3-03）

| 属性 | 内容 |
|------|------|
| **日期** | YYYY-MM-DD |
| **评分人** | |
| **alg3Wave** | W1b / W2 / W3 |
| **cloneGateOn** | true / false（对照臂） |
| **adaptiveSoftSplit** | true / false / n/a |
| **visionEffective** | off / auto_ran / auto_skipped / true |
| **关联 GUIDE** | [ssg-local-dogfood-GUIDE.md](./ssg-local-dogfood-GUIDE.md) · [ACCEPTANCE-ALGORITHM-OPTIMIZATION-V3.md](../ACCEPTANCE-ALGORITHM-OPTIMIZATION-V3.md) §5 |
| **Trip / 语料** | |

## 成对样本

| 对 | Off 截图 | On 截图 | 问1 假切条 | 问2 跳戏 | 问3 混拼/过碎 | 问4 节奏 |
|----|----------|---------|------------|----------|---------------|----------|
| 1 | | | 优/平/差 | 优/平/差 | 优/平/差 / N/A | 优/平/差 / N/A |
| 2 | | | | | | |
| 3 | | | | | | |

## 漏斗 / 摘要抽查

| 项 | Off | On |
|----|-----|-----|
| `curation.algoV3.cloneGateEffective` | | |
| `rejectFunnelTop.near_scene_clone` | | |
| `shotGrouping.stats.softSplitCount` | | |
| `softSplitAdaptive` / `softSplitHoursEffective` | | |
| 切条类跨组硬拒是否出现 | | |

## 结论

| 项 | 勾选 |
|----|------|
| W1b：问1 On ≥ Off | □ |
| W1b：问3 混拼不差于 Off | □ |
| W2：问1+2 ≥ 基线；问3 不差 | □ / N/A |
| **总评** | □ Pass　□ Conditional　□ Fail |

## 备注

…
