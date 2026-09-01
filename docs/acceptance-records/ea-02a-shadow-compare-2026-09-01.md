# EA-02a 横版 series vs mosaic 影子对照

| 属性 | 内容 |
|------|------|
| 日期 | 2026-09-01 |
| 任务 | [收敛任务清单.md](../收敛任务清单.md) `EA-02a` |
| 口径 | [成册指标口径定义.md](../成册指标口径定义.md) |
| comparisonRunId | `ea02a-20260901-203246` |
| surface | `landscape-16x9` · `measurementStage=compose` |
| 计时 | 预热 1 + 正式 3 · `perf_counter_ns` · 主值 planMsMedian |
| tieTolerance | 0.02（跑前声明，见结果不得改） |
| 代码 | `9efa02ff+dirty` |
| dataRowsHash | `72a02a3e9e1beacc6ee982c076005202115e69e5db219a789e73be0baaf2ffbd` |
| 结论 | **已完成 · 有阻断性发现 · 非质量通过** |

## 怎么读

1. **这不是谁更好看的排名。** coverage / 失败 / 耗时按 EA-00 采集；density、页数、emptySlotRate 只记录，不评分。
2. 每趟旅行从同一份 compose 前快照深拷贝，两臂交替。采集时点是 `compose_trip` / `compose_portfolio_trip` 刚返回的内容屏。
3. series 的 overflowCapped 与 placementGap 用口径 §3 公式拆开，不用 `overflow.resolution`。
4. **两套覆盖率不得混用**：`all-valid` 纳入全部有效输入（`outputInvalid` 仍算 coverage，完整性失败另报）；`paired-ok` 只纳入两侧均为 `ok` 的配对，专供 Δ 与 win/tie/loss。总览主表是 all-valid。
5. **mosaic 的 planMs 只覆盖 `compose_trip` 二次 beam**。窗级 MCS 发生在公共快照的 `build_chapters_from_buckets`，两边共享，不计进 planMs。series 的 planMs 才是选系列 + 装填全过程。因此 planMs 不能解释成「谁排一整本更快」。
6. 任务清单量级按**磁盘资产文件数**分组；行内 `folderN` 是 `trip.assets` 图片记录数，两者不必相等。
7. 对照行的 `tripId` 使用 `trips/<id>/` 目录名，避免克隆旅行共用 JSON `tripId` 把两趟合并作废。

## 阻断性发现（不是门槛，禁止当排名）

行级数据足以改变阶段 5 顺序；本页 **不是** series 或 mosaic 的质量通过证明。

- **容量策略 vs 装填失败必须拆开。** 阶段 5 不从 `SE-01` 三种性格起手：先 `SE-00a` 收敛容量内 `placementGap`，再 `SE-00b` 拍板超量容量策略（舍弃 / 拆卷 / 扩容），最后才进入均衡、人物、风景。
- **纯 placement gap**（`overflowCapped=0`，容量几乎没用尽）：`_bai_w1b_titleart`（gap 44）、`demo-3ee2727aea`（gap 36）。
- **gap 主导的混合原因**：`demo-65db8fd377`（overflowCapped=2 + placementGap=30）。不要当成干净容量内失败。
- **capped 不可忽略的混合原因**：`demo-1d4f92d534`、`demo-0ebda73294`。不要和纯 gap 捆成同一个修复。`demo-005` 是稀疏档小缺口，适合当回归样例。
- **mosaic 可作覆盖参照，不能当健康基线。** 最小修复：要么注册 `screen-square-1`，要么禁止规划器产出；compose 边界加全册 asset ID 唯一性断言。
- mosaic `planMs≈0` 不能读成「游记排版零成本」——重活在共享快照的窗级 MCS。

## 总览

### all-valid coverage（正式验收主表 · 同一有效输入队列）

`outputInvalid` 的 coverage 仍计入分子分母；完整性失败只出现在 pipelineFailureRate。

| 管线 | 有效输入 | ok | coverage N | microCoverage | macroCoverage | tripFailRate | pipelineFailureRate | planMs 中位 | planMs P90 |
|------|----------|----|------------|---------------|---------------|--------------|---------------------|-------------|------------|
| mosaic | 20 | 15 | 20 | 98.7% | 98.0% | 0.0% | 25.0% | 0.0 | 0.0 |
| series | 20 | 20 | 20 | 55.0% | 70.5% | 0.0% | 0.0% | 86.7 | 103.7 |

### series 资产守恒（all-valid）

`eligible 1849 = placed 1017 + overflowCapped 611 + placementGap 221 + intakeLoss 0`

未入册 832 张中： overflowCapped 73.4%（产品策略）， placementGap 26.6%（工程鲁棒性）。

### paired-ok coverage（仅两侧均为 ok · Δ 与胜负）

15 对。win / tie / loss（series 相对 mosaic，容差 0.02）： **5** / **2** / **8**

配对 coverage 差（series − mosaic）：中位 -17.9% · Q1 -48.8% · Q3 2.6%

| 管线 | N | microCoverage | macroCoverage |
|------|---|---------------|---------------|
| mosaic | 15 | 98.9% | 98.0% |
| series | 15 | 60.4% | 78.6% |

### 量级分组（all-valid）

| 量级 | mosaic micro | series micro | mosaic macro | series macro | mosaic N | series N |
|------|--------------|--------------|--------------|--------------|----------|----------|
| sparse-60-140 | 96.3% | 95.7% | 96.4% | 100.0% | 7 | 7 |
| regular-196-326 | 97.2% | 60.7% | 98.0% | 56.1% | 5 | 5 |
| overflow-424-1000 | 99.3% | 48.3% | 99.4% | 50.0% | 8 | 8 |

## 分旅行配对

Δ 仅两侧 `status=ok` 时填写；`outputInvalid` 等配对显示 —（与 paired-ok 同一谓词）。

| trip | 量级 | mosaic cov | series cov | Δ | mosaic 状态 | series 状态 | mosaic planMs | series planMs | series overflowCapped | series placementGap | mosaic placementGap |
|------|------|------------|------------|---|-------------|-------------|---------------|---------------|----------------------|---------------------|---------------------|
| `demo-album` | sparse-60-140 | 92.9% | 92.9% | 0.0% | ok | ok | 0.0 | 69.2 | 0 | 1 | 0 |
| `demo-20ecc928d6` | sparse-60-140 | 95.7% | 100.0% | 4.3% | ok | ok | 0.0 | 59.1 | 0 | 0 | 0 |
| `demo-d21946c6a9` | sparse-60-140 | 96.4% | 100.0% | 3.6% | ok | ok | 0.0 | 73.3 | 0 | 0 | 0 |
| `demo-03ca76b26d` | sparse-60-140 | 96.4% | 100.0% | 3.6% | ok | ok | 0.0 | 78.9 | 0 | 0 | 0 |
| `demo-49551086fe` | sparse-60-140 | 96.8% | 100.0% | 3.2% | ok | ok | 0.0 | 83.3 | 0 | 0 | 0 |
| `demo-005` | sparse-60-140 | 96.4% | 78.6% | -17.9% | ok | ok | 0.0 | 73.3 | 0 | 6 | 0 |
| `demo-1b67b06546` | sparse-60-140 | 97.1% | 97.1% | — | outputInvalid | ok | 0.0 | 76.0 | 0 | 1 | 0 |
| `demo-817f1f8801` | regular-196-326 | 98.0% | 100.0% | 2.0% | ok | ok | 0.0 | 87.6 | 0 | 0 | 0 |
| `demo-65db8fd377` | regular-196-326 | 95.6% | 28.9% | — | outputInvalid | ok | 0.0 | 90.7 | 2 | 30 | 1 |
| `demo-1bfe89d31c` | regular-196-326 | 98.0% | 100.0% | 2.0% | ok | ok | 0.0 | 92.0 | 0 | 0 | 0 |
| `_bai_w1b_titleart` | regular-196-326 | 94.8% | 24.1% | — | outputInvalid | ok | 0.0 | 72.7 | 0 | 44 | 2 |
| `demo-3ee2727aea` | regular-196-326 | 98.8% | 56.1% | -42.7% | ok | ok | 0.0 | 85.8 | 0 | 36 | 0 |
| `demo-81d3442e92` | overflow-424-1000 | 99.1% | 76.1% | — | outputInvalid | ok | 0.0 | 85.1 | 21 | 7 | 0 |
| `demo-e52494839a` | overflow-424-1000 | 99.3% | 64.9% | -34.3% | ok | ok | 0.0 | 102.5 | 38 | 9 | 0 |
| `demo-0ebda73294` | overflow-424-1000 | 99.3% | 51.1% | -48.1% | ok | ok | 0.0 | 98.4 | 39 | 27 | 0 |
| `demo-6395848778` | overflow-424-1000 | 99.4% | 50.0% | -49.4% | ok | ok | 0.1 | 99.5 | 84 | 6 | 0 |
| `demo-9a32512fea` | overflow-424-1000 | 99.4% | 50.0% | -49.4% | ok | ok | 0.0 | 105.4 | 84 | 6 | 0 |
| `demo-de855740dc` | overflow-424-1000 | 99.4% | 50.0% | -49.4% | ok | ok | 0.0 | 104.4 | 84 | 6 | 0 |
| `demo-2019` | overflow-424-1000 | 99.5% | 47.3% | -52.2% | ok | ok | 0.0 | 103.6 | 105 | 1 | 0 |
| `demo-1d4f92d534` | overflow-424-1000 | 99.2% | 22.0% | — | outputInvalid | ok | 0.1 | 100.6 | 154 | 41 | 1 |

### Registry 未知模板（mosaic 内容屏）

按 EA-00，最终 `patternId` 必须能在同次 Registry 查到 `len(template.slots)`。下列 ID 仍被 mosaic 产出，但不在源码 `screen-*.yaml` / `page-*.yaml` 中，故记 `outputInvalid`。

- `screen-square-1` × 6

## 失败与完整性（分列，不可相加）

| trip | pipeline | status | tripFail | integrityFail | chapterFail | emptyRenderedPages | omittedPlannedPages | pageDegraded | invalidReason |
|------|----------|--------|----------|---------------|-------------|--------------------|---------------------|--------------|---------------|
| `demo-1b67b06546` | mosaic | outputInvalid | False | True | 0 | 0 | — | 0 | unknownTemplate;identity:pagePartition |
| `demo-65db8fd377` | mosaic | outputInvalid | False | True | 0 | 0 | — | 0 | duplicatePlacements;unknownTemplate;identity:pagePartition |
| `_bai_w1b_titleart` | mosaic | outputInvalid | False | True | 0 | 0 | — | 0 | duplicatePlacements;unknownTemplate;identity:pagePartition |
| `demo-81d3442e92` | mosaic | outputInvalid | False | True | 0 | 0 | — | 0 | unknownTemplate;identity:pagePartition |
| `demo-2019` | series | ok | False | False | 1 | 0 | 0 | 8 | — |
| `demo-1d4f92d534` | mosaic | outputInvalid | False | True | 0 | 0 | — | 0 | duplicatePlacements |
| `demo-1d4f92d534` | series | ok | False | False | 2 | 0 | 4 | 20 | — |

## 复跑

```text
python scripts/ea02a_shadow_compare.py --write-markdown docs/acceptance-records/ea-02a-shadow-compare-2026-09-01.md
python scripts/ea02a_shadow_compare.py --from-jsonl docs/acceptance-records/ea-02a-shadow-compare-2026-09-01.jsonl
```

`--from-jsonl` 只重算汇总与 Markdown，不重跑 compose；数据行按原文拷贝，`dataRowsHash` 校验行级未改。密度与页数列刻意不进总览排名。
