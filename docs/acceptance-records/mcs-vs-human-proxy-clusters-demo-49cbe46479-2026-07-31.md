# MCS 实际窗口 vs 人类拼图组代理 · demo-49cbe46479

| 属性 | 内容 |
|------|------|
| 日期 | 2026-07-31 |
| Trip | `demo-49cbe46479` |
| 目的 | 用差距标定是否优先做「簇边界惩罚」 |
| 数据 | `trip.json` 当前 layout（mosaicDecisionLog / shotGrouping / screens） |
| 审阅页 | [HTML](./mcs-vs-human-proxy-clusters-demo-49cbe46479-2026-07-31.html) |
| 原始 JSON | [JSON](./mcs-vs-human-proxy-clusters-demo-49cbe46479-2026-07-31.json) |

> **说明**：代理组 = 同 `shotGroupId` + gap≤300s + size 2–12（页级近似）。SSG scene 组 13–61 张是 episode，不当金标准。  
> **人工金标**：已写入 [mcs-human-cluster-labels-demo-49cbe46479-2026-07-31.json](./mcs-human-cluster-labels-demo-49cbe46479-2026-07-31.json)（§0.H）。

## 0. 标定结论

### 0.A 自动代理（初判）

- **是否优先簇边界惩罚**：`True`
- 证据：污染/拆分 > 对齐；`undercut_series=11`；跨 burst 名义 30 但多为过细 burst。

### 0.H 人工 11 例回写（2026-07-31）→ **确认优先边界，且升级硬约束**

| # | screen | 人工 verdict | 剔除 / 合并 |
|---|--------|--------------|-------------|
| 1 | `ch-01-sc-25` bookends | 去污染 | 去 `asset-082`（黑裙沙滩）；留船甲板 079/081/080 |
| 2 | `ch-01-sc-03` L3 | **整屏不该聚** | 004/005/006 无共同叙事 |
| 3 | `ch-01-sc-09` P3 | 去污染 | 去 `asset-020`（黄衣） |
| 4 | `ch-01-sc-32` P3 | **整屏不该聚** | 042/075/100 跨服+跨景+跨 sg |
| 5 | `ch-01-sc-33` P3 | 去污染 | 去 `asset-092` |
| 6 | `ch-02-sc-05` P3 | 去污染 | 去 `asset-113`（花裙门前） |
| 7 | `ch-02-sc-09` P3 | 去污染 | 去 `asset-128`（廊柱花裙） |
| 8 | `ch-02-sc-10`+`11` | **合并** | 同花裙廊柱系列应一簇 |
| 9 | `ch-02-sc-15` P3 | 去污染 | 去 `asset-142`（实体人像不进影子组） |
| 10 | `ch-03-sc-05/06/08` | **合并 + 去尾污染** | 海滩同服三屏合并；去 `asset-159`（廊柱） |
| 11 | `ch-03-sc-11` L3 | 去污染 | 去 `asset-164`（暮色花裙） |

**统计**：去污染 7 · 整屏打散 2 · 纯合并 1 · 合并并去污 1。**11/11 都是聚类边界错，不是缺模板。**

**信号频次（人工）**：服装突变 ≈7 · 场景突变 ≈7 · 跨 shotGroup ≈5 · 系列被切碎 ≈2 · 强行凑满 3 槽 ≈2。

**落地优先级（人工校准后）**：

1. **硬拒**：同屏跨 `shotGroupId`（本批多次命中污染）。
2. **硬拒 / 强罚**：服装或场景突变后仍为填满 portrait-3/L3/mosaic 而拉入下一张（缺图则降为 pair/单图）。
3. **先合并再切页**：同服同景长系列（例 #8/#10）禁止被游标切成多个互不相关的 3 槽屏。
4. **题材母题**：人像实体 vs 影子等不得混屏（#9）。
5. **跨 burst**：仅 soft；本批不能当主锚。
6. **模板权重 / 新 SKU**：排在上述边界之后。

## 1. 规模

- displayed：178
- 多槽屏：59（命名 mosaic：3）
- 人类代理组：38；尺寸分布 `{2: 20, 3: 5, 4: 3, 5: 2, 7: 4, 8: 2, 10: 1, 11: 1}`
- burst 组(2–12)：0
- MCS log：events=61 winners=5 fallbacks=56

### 多槽 pattern 分布

| patternId | n |
|-----------|---|
| `screen-portrait-3` | 18 |
| `screen-landscape-1-portrait-1` | 11 |
| `screen-portrait-2` | 9 |
| `screen-portrait-1-landscape-1` | 5 |
| `screen-landscape-3-asymmetric-left` | 4 |
| `screen-landscape-3-asymmetric-right` | 3 |
| `screen-portrait-2-gallery` | 2 |
| `screen-landscape-4` | 2 |
| `screen-landscape-2` | 2 |
| `screen-mosaic-5-3p2l-portrait-hero-lp-stack` | 1 |
| `screen-mosaic-4-2p2l-portrait-bookends` | 1 |
| `screen-mosaic-4-hero-70-sidebar` | 1 |

### 代理组 fate 分布

| fate | n | 含义 |
|------|---|------|
| `exact_window_match` | 14 | 整组恰好等于某一多槽屏 |
| `split_and_polluted` | 10 | 既拆分又混入 |
| `absorbed_with_foreign` | 5 | 整组进同一屏，但混入组外照片 |
| `split_across_screens` | 5 | 一组被拆到多屏（未混外组） |
| `partial_with_foreign` | 2 | 部分成员进屏且混入外组 |
| `not_in_multi_screen` | 1 | 成员未进入任何多槽屏（多为单图/breath） |
| `partial_overlap` | 1 | 部分重叠 |

### 屏幕 verdict 分布

| verdict | n |
|---------|---|
| `boundary_violation_burst` | 30 |
| `aligned` | 12 |
| `undercut_series` | 11 |
| `weak_or_singleton_mix` | 6 |

## 2. 人类代理组 ↔ MCS 屏（污染/拆分优先）

| proxy | n | P/L | fate | 触达屏 | 顶屏 pattern | inter/foreign |
|-------|---|-----|------|--------|--------------|---------------|
| `cohesive-run-026` | 11 | 10P1L | `split_and_polluted` | 4 | `screen-portrait-3` (ch-03-sc-05) | 3/0 |
| `cohesive-run-020` | 10 | 9P1L | `split_and_polluted` | 3 | `screen-portrait-2` (ch-02-sc-06) | 2/0 |
| `cohesive-run-022` | 7 | 7P0L | `split_and_polluted` | 3 | `screen-portrait-3` (ch-02-sc-11) | 3/0 |
| `cohesive-run-035` | 7 | 4P3L | `split_and_polluted` | 4 | `screen-landscape-1-portrait-1` (ch-03-sc-23) | 2/0 |
| `cohesive-run-028` | 5 | 3P2L | `split_and_polluted` | 2 | `screen-portrait-3` (ch-03-sc-12) | 3/0 |
| `cohesive-run-014` | 4 | 2P2L | `split_and_polluted` | 2 | `screen-landscape-1-portrait-1` (ch-01-sc-24) | 2/0 |
| `cohesive-run-031` | 4 | 2P2L | `split_and_polluted` | 2 | `screen-portrait-2` (ch-03-sc-16) | 2/0 |
| `cohesive-run-032` | 3 | 3P0L | `split_and_polluted` | 2 | `screen-portrait-2` (ch-03-sc-20) | 2/0 |
| `cohesive-run-004` | 2 | 2P0L | `split_and_polluted` | 2 | `screen-portrait-2-gallery` (ch-01-sc-11) | 1/1 |
| `cohesive-run-021` | 2 | 2P0L | `split_and_polluted` | 2 | `screen-portrait-3` (ch-02-sc-09) | 1/2 |
| `cohesive-run-010` | 3 | 2P1L | `absorbed_with_foreign` | 1 | `screen-mosaic-5-3p2l-portrait-hero-lp-stack` (ch-01-sc-18) | 3/2 |
| `cohesive-run-001` | 2 | 0P2L | `absorbed_with_foreign` | 1 | `screen-landscape-3-asymmetric-left` (ch-01-sc-03) | 2/1 |
| `cohesive-run-011` | 2 | 1P1L | `absorbed_with_foreign` | 1 | `screen-mosaic-5-3p2l-portrait-hero-lp-stack` (ch-01-sc-18) | 2/3 |
| `cohesive-run-025` | 2 | 2P0L | `absorbed_with_foreign` | 1 | `screen-portrait-3` (ch-02-sc-15) | 2/1 |
| `cohesive-run-030` | 2 | 2P0L | `absorbed_with_foreign` | 1 | `screen-portrait-3` (ch-03-sc-15) | 2/1 |
| `cohesive-run-024` | 3 | 2P1L | `partial_with_foreign` | 1 | `screen-portrait-3` (ch-02-sc-15) | 1/2 |
| `cohesive-run-003` | 2 | 1P1L | `partial_with_foreign` | 1 | `screen-portrait-2` (ch-01-sc-06) | 1/1 |
| `cohesive-run-012` | 8 | 3P5L | `split_across_screens` | 2 | `screen-landscape-4` (ch-01-sc-20) | 4/0 |
| `cohesive-run-017` | 8 | 3P5L | `split_across_screens` | 3 | `screen-mosaic-4-hero-70-sidebar` (ch-01-sc-30) | 4/0 |
| `cohesive-run-013` | 7 | 0P7L | `split_across_screens` | 2 | `screen-landscape-4` (ch-01-sc-22) | 4/0 |
| `cohesive-run-019` | 7 | 5P2L | `split_across_screens` | 3 | `screen-portrait-3` (ch-02-sc-02) | 3/0 |
| `cohesive-run-009` | 5 | 4P1L | `split_across_screens` | 2 | `screen-portrait-3` (ch-01-sc-17) | 3/0 |
| `cohesive-run-029` | 4 | 0P4L | `partial_overlap` | 1 | `screen-landscape-3-asymmetric-left` (ch-03-sc-14) | 3/0 |
| `cohesive-run-018` | 3 | 0P3L | `exact_window_match` | 1 | `screen-landscape-3-asymmetric-left` (ch-01-sc-31) | 3/0 |
| `cohesive-run-033` | 3 | 0P3L | `exact_window_match` | 1 | `screen-landscape-3-asymmetric-right` (ch-03-sc-21) | 3/0 |
| `cohesive-run-002` | 2 | 2P0L | `exact_window_match` | 1 | `screen-portrait-2` (ch-01-sc-04) | 2/0 |
| `cohesive-run-005` | 2 | 1P1L | `exact_window_match` | 1 | `screen-landscape-1-portrait-1` (ch-01-sc-12) | 2/0 |
| `cohesive-run-006` | 2 | 1P1L | `exact_window_match` | 1 | `screen-portrait-1-landscape-1` (ch-01-sc-13) | 2/0 |
| `cohesive-run-007` | 2 | 1P1L | `exact_window_match` | 1 | `screen-landscape-1-portrait-1` (ch-01-sc-14) | 2/0 |
| `cohesive-run-008` | 2 | 1P1L | `exact_window_match` | 1 | `screen-landscape-1-portrait-1` (ch-01-sc-15) | 2/0 |
| `cohesive-run-015` | 2 | 1P1L | `exact_window_match` | 1 | `screen-landscape-1-portrait-1` (ch-01-sc-26) | 2/0 |
| `cohesive-run-016` | 2 | 0P2L | `exact_window_match` | 1 | `screen-landscape-2` (ch-01-sc-27) | 2/0 |
| `cohesive-run-027` | 2 | 1P1L | `exact_window_match` | 1 | `screen-portrait-1-landscape-1` (ch-03-sc-09) | 2/0 |
| `cohesive-run-034` | 2 | 1P1L | `exact_window_match` | 1 | `screen-landscape-1-portrait-1` (ch-03-sc-22) | 2/0 |
| `cohesive-run-036` | 2 | 1P1L | `exact_window_match` | 1 | `screen-landscape-1-portrait-1` (ch-03-sc-27) | 2/0 |
| `cohesive-run-037` | 2 | 1P1L | `exact_window_match` | 1 | `screen-landscape-1-portrait-1` (ch-03-sc-28) | 2/0 |
| `cohesive-run-038` | 2 | 2P0L | `exact_window_match` | 1 | `screen-portrait-2` (ch-03-sc-31) | 2/0 |
| `cohesive-run-023` | 2 | 2P0L | `not_in_multi_screen` | 0 | `—` (—) | — |

## 3. 污染/跨簇多槽屏（verdict≠aligned）

| screen | pattern | n | P/L | verdict | shotGroups | best Jaccard |
|--------|---------|---|-----|---------|------------|--------------|
| `ch-01-sc-18` | `screen-mosaic-5-3p2l-portrait-hero-lp-stack` | 5 | 3P2L | `boundary_violation_burst` | sg-scene-0c | 0.6 |
| `ch-01-sc-20` | `screen-landscape-4` | 4 | 0P4L | `boundary_violation_burst` | sg-scene-0c | 0.5 |
| `ch-01-sc-22` | `screen-landscape-4` | 4 | 0P4L | `boundary_violation_burst` | sg-scene-0c | 0.571 |
| `ch-01-sc-25` | `screen-mosaic-4-2p2l-portrait-bookends` | 4 | 2P2L | `boundary_violation_burst` | sg-scene-0c, sg-scene-0d | 0.333 |
| `ch-01-sc-30` | `screen-mosaic-4-hero-70-sidebar` | 4 | 0P4L | `boundary_violation_burst` | sg-scene-0d | 0.5 |
| `ch-01-sc-03` | `screen-landscape-3-asymmetric-left` | 3 | 0P3L | `boundary_violation_burst` | sg-weak-0 | 0.667 |
| `ch-01-sc-09` | `screen-portrait-3` | 3 | 3P0L | `boundary_violation_burst` | sg-scene-0b | — |
| `ch-01-sc-10` | `screen-portrait-3` | 3 | 3P0L | `boundary_violation_burst` | sg-scene-0b | 0.25 |
| `ch-01-sc-17` | `screen-portrait-3` | 3 | 3P0L | `boundary_violation_burst` | sg-scene-0b | 0.6 |
| `ch-01-sc-21` | `screen-portrait-3` | 3 | 3P0L | `boundary_violation_burst` | sg-scene-0c | 0.375 |
| `ch-01-sc-23` | `screen-landscape-3-asymmetric-right` | 3 | 0P3L | `boundary_violation_burst` | sg-scene-0c | 0.429 |
| `ch-01-sc-31` | `screen-landscape-3-asymmetric-left` | 3 | 0P3L | `boundary_violation_burst` | sg-scene-0d | 1.0 |
| `ch-01-sc-32` | `screen-portrait-3` | 3 | 3P0L | `boundary_violation_burst` | sg-scene-0b, sg-scene-0c, sg-scene-0d | — |
| `ch-01-sc-33` | `screen-portrait-3` | 3 | 3P0L | `boundary_violation_burst` | sg-scene-0c, sg-scene-0d | — |
| `ch-02-sc-02` | `screen-portrait-3` | 3 | 3P0L | `boundary_violation_burst` | sg-scene-0d | 0.429 |
| `ch-02-sc-05` | `screen-portrait-3` | 3 | 3P0L | `boundary_violation_burst` | sg-scene-0d, sg-scene-0e | 0.182 |
| `ch-02-sc-09` | `screen-portrait-3` | 3 | 3P0L | `boundary_violation_burst` | sg-scene-0e, sg-scene-2a | 0.25 |
| `ch-02-sc-10` | `screen-portrait-3` | 3 | 3P0L | `boundary_violation_burst` | sg-scene-2a | 0.25 |
| `ch-02-sc-11` | `screen-portrait-3` | 3 | 3P0L | `boundary_violation_burst` | sg-scene-2a | 0.429 |
| `ch-02-sc-12` | `screen-portrait-3` | 3 | 3P0L | `boundary_violation_burst` | sg-scene-1b, sg-scene-2a | 0.25 |
| `ch-02-sc-15` | `screen-portrait-3` | 3 | 3P0L | `boundary_violation_burst` | sg-scene-1b | 0.667 |
| `ch-03-sc-05` | `screen-portrait-3` | 3 | 3P0L | `boundary_violation_burst` | sg-scene-1c | 0.273 |
| `ch-03-sc-06` | `screen-portrait-3` | 3 | 3P0L | `boundary_violation_burst` | sg-scene-1c | 0.273 |
| `ch-03-sc-08` | `screen-portrait-3` | 3 | 3P0L | `boundary_violation_burst` | sg-scene-1c | 0.167 |
| `ch-03-sc-11` | `screen-landscape-3-asymmetric-right` | 3 | 0P3L | `boundary_violation_burst` | sg-scene-1c | 0.333 |
| `ch-03-sc-12` | `screen-portrait-3` | 3 | 3P0L | `boundary_violation_burst` | sg-scene-1c | 0.6 |
| `ch-03-sc-14` | `screen-landscape-3-asymmetric-left` | 3 | 0P3L | `boundary_violation_burst` | sg-scene-1c | 0.75 |
| `ch-03-sc-15` | `screen-portrait-3` | 3 | 3P0L | `boundary_violation_burst` | sg-scene-1c | 0.667 |
| `ch-03-sc-18` | `screen-landscape-3-asymmetric-left` | 3 | 0P3L | `boundary_violation_burst` | sg-scene-1c | 0.167 |
| `ch-03-sc-21` | `screen-landscape-3-asymmetric-right` | 3 | 0P3L | `boundary_violation_burst` | sg-scene-1c | 1.0 |
| `ch-01-sc-16` | `screen-portrait-1-landscape-1` | 2 | 1P1L | `undercut_series` | sg-scene-0b | 0.4 |
| `ch-01-sc-24` | `screen-landscape-1-portrait-1` | 2 | 1P1L | `undercut_series` | sg-scene-0c | 0.5 |
| `ch-01-sc-28` | `screen-portrait-2` | 2 | 2P0L | `undercut_series` | sg-scene-0d | 0.25 |
| `ch-01-sc-29` | `screen-portrait-1-landscape-1` | 2 | 1P1L | `undercut_series` | sg-scene-0d | 0.25 |
| `ch-02-sc-03` | `screen-landscape-1-portrait-1` | 2 | 1P1L | `undercut_series` | sg-scene-0d | 0.286 |
| `ch-02-sc-04` | `screen-landscape-1-portrait-1` | 2 | 1P1L | `undercut_series` | sg-scene-0d | 0.286 |
| `ch-02-sc-06` | `screen-portrait-2` | 2 | 2P0L | `undercut_series` | sg-scene-0e | 0.2 |
| `ch-03-sc-16` | `screen-portrait-2` | 2 | 2P0L | `undercut_series` | sg-scene-1c | 0.5 |
| `ch-03-sc-23` | `screen-landscape-1-portrait-1` | 2 | 1P1L | `undercut_series` | sg-scene-1c | 0.286 |
| `ch-03-sc-24` | `screen-portrait-1-landscape-1` | 2 | 1P1L | `undercut_series` | sg-scene-1c | 0.286 |
| `ch-03-sc-25` | `screen-portrait-2` | 2 | 2P0L | `undercut_series` | sg-scene-1c | 0.286 |
| `ch-01-sc-06` | `screen-portrait-2` | 2 | 2P0L | `weak_or_singleton_mix` | sg-scene-1a | 0.333 |
| `ch-01-sc-11` | `screen-portrait-2-gallery` | 2 | 2P0L | `weak_or_singleton_mix` | sg-scene-0b | 0.333 |
| `ch-03-sc-03` | `screen-portrait-2-gallery` | 2 | 2P0L | `weak_or_singleton_mix` | sg-scene-1b, sg-scene-1c | 0.083 |
| `ch-03-sc-19` | `screen-portrait-2` | 2 | 2P0L | `weak_or_singleton_mix` | sg-scene-1c | 0.25 |
| `ch-03-sc-20` | `screen-portrait-2` | 2 | 2P0L | `weak_or_singleton_mix` | sg-scene-1c | 0.667 |
| `ch-03-sc-26` | `screen-landscape-2` | 2 | 0P2L | `weak_or_singleton_mix` | sg-scene-1c | 0.125 |

## 4. 人工下一步

1. 打开 HTML，对 `pollution_candidate` / `absorbed_with_foreign` 用眼睛确认外来图是否破坏整体。
2. 错代理组标 `false_proxy`，避免假阳性推高惩罚权重。
3. 若人工确认污染 ≥ 对齐，则落地跨 burst / 跨 cohesive-series 的簇边界硬拒/重罚，再调模板权重。
