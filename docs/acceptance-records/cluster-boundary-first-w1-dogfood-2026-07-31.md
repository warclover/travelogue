# Cluster-Boundary-First · W1 狗粮验收 · demo-49cbe46479

| 属性 | 内容 |
|------|------|
| 日期 | 2026-07-31 |
| 分支 | `feat/cluster-boundary-first-v1` |
| 方案 | [PLAN-CLUSTER-BOUNDARY-FIRST-MOSAIC-V1.md](../PLAN-CLUSTER-BOUNDARY-FIRST-MOSAIC-V1.md)（已审定稿） |
| Trip | `demo-49cbe46479` |
| 配置 | 本机 `shotGrouping.mosaic.atom.enabled=true`；三列等分实验 SKU 暂出 allowlist |

---

## 1. 出口结论

**W1 Go：通过**（污染/灾难回归达标；碎度偏高，交 W2 回收系列密度）。

| 检查 | 结果 |
|------|------|
| #1 #3 #5 #6 #7 #9 污染成员不得同屏 | ✅ |
| #2 #4 灾难屏不得再成 | ✅ |
| #10 尾 `asset-159` 不得并入海滩组 | ✅ |
| #11 已知残差 | ✅ 本轮亦未再污染（加分） |
| #8/#10 合并（非 Go） | 未测为门槛；交 W2 |
| 跨 2h 屏 | ✅ 0（#4 类已灭） |

---

## 2. 碎度观察（相对改前定性）

改前（对照 HTML / 代理导出）：多槽屏约 59，其中 `portrait-3`×18 等，脏屏多。

改后（本次 layout）：

| 指标 | 值 |
|------|-----|
| 内容多槽屏 | 10 |
| 内容单图屏 | 14 |
| 多槽占比 | **0.417** |
| `portrait-3` | 5 |
| `portrait-2` | 2 |
| MCS mosaic 命名 | 1（3P2L lp-stack） |

解读：干净优先已达成；多槽密度明显下降，符合「宁碎勿脏」。W2 应在 **同 atom 内** 提高切页利用率（系列合并后再按容量成屏），不得靠跨 atom 回填。

---

## 3. 配置注意

- 本机 SSG 段名为 camelCase **`shotGrouping`**；loader 优先读它。蛇形 `shot_grouping` 若并存会被忽略。
- 样例：[config-cluster-boundary-first-dogfood.example.yaml](../config-cluster-boundary-first-dogfood.example.yaml)

---

## 4. 下一步

1. 开 PR 合入 W0+W1。  
2. **W2**：atom → page packs（同系列可多屏，但优先吃满契约容量）。  
3. 碎度护栏：相对本验收基线，后续改动若多槽占比再腰斩需告警。
