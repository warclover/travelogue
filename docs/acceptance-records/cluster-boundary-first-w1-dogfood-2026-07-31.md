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

1. 开 PR 合入 W0+W1+W2。  
2. **W3**：look 细分攻坚 #11（本册 look 信号仍弱）。  
3. 碎度护栏：相对 W2b 基线，后续改动若多槽占比再腰斩需告警。  
4. #8 廊柱系列仍未进本章选片（curation 95/223），属选片而非排版边界问题。

---

## 5. W2 系列切页初版（同日）

| 改动 | 说明 |
|------|------|
| `pack_atom_page_sizes` | atom 内按 3/2/1 切页；`n%3==1` 反孤儿（4→2+2） |
| 人物竖图 | 先取满 atom，再按 page packs 成屏 |
| MCS | `prefer_window_sizes_for_atom`：优先吃满 / 可再切的余量 |

| 指标 | W1 | W2a |
|------|----|-----|
| 内容多槽屏 | 10 | 12 |
| 内容单图屏 | 14 | 11 |
| 多槽占比 | 0.417 | 0.522 |
| 污染/灾难 | 过 | 仍过 |

---

## 6. W2b · atom 内禁止 person/scenery 分流（同日续）

**根因**：`_flush_portrait_pending` 先按 `asset_has_person` 拆人/景，把同 atom 海滩系列拆成 2+3+2+2；展示序里 154/155 还排在 158 后。

**修复**：atom ON 时整段 pending 按 atom 切页；页内 `sort_ids_by_taken_at`；MCS 日志增加 `atomCap` 字段。

| 指标 | W2a | W2b |
|------|-----|-----|
| 内容多槽 / 单图 | 12 / 11 | **11 / 11** |
| 多槽占比 | 0.522 | **0.500** |
| `portrait-3` | — | **5** |
| #10 海滩 | 4 屏 | **3 屏** `150-152 \| 153-155 \| 156-158` |
| #10 尾污染 | 干净 | **仍干净** |
| 污染/灾难 11 例 | 过 | **仍过** |

解读：#10 over-split 明显改善（加分项）；多槽占比略降因竖三列合并减少了碎双列屏，属预期。

---

## 7. PRD 补漏（统一门收口）

对照 PLAN §3 / §4 补齐：

| 缺口 | 处理 |
|------|------|
| attach 尾部 portrait-1 合并 | 过 atom 门；`allowTailCrossAtom=false` 时拒跨 atom |
| mixed 1P1L / 1P2L | 成屏前过 atom 门 |
| legacy / replan | `build_legacy_screen` 多槽过 atom 门 |
| P0-2 fail-loud | `resolve` 默认 warning + 计数器 |
| 类别软惩罚 | scorer `category_jump_soft` |
| §5 配置字段 | `strongTemplate*` / `mosaicShareFloorObserve` |
| coarse_segments | 注明 atom ⊆ segment |

仍缓：§6.3 三册抽检、§6.1 指标产品化、W3 look、开 PR（本机无 gh）。

---

## 8. 弱 SSG 册 time_bridge（demo-d6697c8dca）

**问题**：双侧无 `shotGroupId` 时旧逻辑一律 `shot_group_mismatch` → 全单张（多槽≈0.03）。

**修复**：`missingShotGroupMode: time_bridge`（默认）——双侧缺 sg 时改靠 gap + 半硬 sc；有/无混装仍硬拒；双侧均有 sg 仍必须相同。

| 册 | 改前多槽占比 | 改后 |
|----|-------------|------|
| demo-d6697c8dca | ~0.03 | **~0.57** |
| demo-49cbe46479 | ~0.48–0.50 | 仍多槽为主；#1–#10 污染/灾难过；**#11 已知残差**（同 sg 近时换装）可再现 |
