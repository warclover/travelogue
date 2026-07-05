# ADR-014：拼图连拍门槛与 MCS 窗口顺序默认值

| 属性 | 内容 |
|------|------|
| **状态** | **Draft · 数据已填（LRG-W1）· 待产品/算法签字** |
| **日期** | 2026-07-05 |
| **决策者** | 产品 + 算法/排版（**待签字** — 本文档"决议"章节为工程基于 dogfood 数据的**建议**，非最终裁定） |
| **关联** | [PRD-LAYOUT-READER-REGRESSION-GUARD.md](../PRD-LAYOUT-READER-REGRESSION-GUARD.md)、[PRD-MOSAIC-CONFIG-RESTORE.md](../PRD-MOSAIC-CONFIG-RESTORE.md)、`travelogue/config/layout.py`、`travelogue/config/mosaic.py` |

## 背景

2026-07 热修将 `layout.mixed_proximity_seconds` 从 **12s** 调整为 **900s（15min）**，显著放宽 1P+4L / 1P+5L 等 mosaic 窗口的连拍门槛；用户侧可能感知「五/六格拼图变多」。该变更与 **overlay CSS 回归（LRG）** 无关，但已与 LRG 同一发布窗口进入 master，**须在 W1 内书面留档**。

同时，MCS `density_budget.window_order` 默认 **`(5, 4, 6, 9)`** 可能导致 4 格窗先于 6 格成功，压制 hero 6 格拼图（见 `demo-815dc906d3` 诊断）。

**术语对照（避免与 ingest 混淆）**：

| 配置项 | 默认 | 作用阶段 | 含义 |
|--------|------|----------|------|
| `layout.mixed_proximity_seconds` | **900** | **curate / 组屏** | 混排/拼图窗口内 `takenAt` 最大跨度 |
| `ingest.burst_seconds` | **3** | **ingest** | 近重复/连拍 ingest 去重 |

## 待决问题

1. **`mixed_proximity_seconds = 900` 是否作为长期全局默认？**
2. 若过松，回滚目标值：**600s / 300s / 60s** 选哪一档？
3. **`window_order` 是否调整为 `(6, 5, 4, 9)`** 以优先 hero 6 格？
4. 是否提供 **相册级 override**（`config.yaml` per-trip 或 Studio 开关）？

## Dogfood 数据（LRG-W1 · 2026-07-05 采集）

> 数据来自 `python scripts/lrg_dogfood_report.py --trip trips/<id>`、`python scripts/mosaic_config_diag.py --trip trips/<id>`、`python scripts/mcr_eval_recurate.py <id>`（后者只读内存 re-curate，不写 `trip.json`）。完整 baseline JSON 见 `docs/acceptance-records/lrg-dogfood.<trip-id>.json`。

### mixed_proximity_seconds 敏感度扫描（1P+4L / 1P+5L burst-pass rate）

| burst_seconds | demo-815dc906d3 · rate（win5 geo/pass, win6 geo/pass） | demo-80301df45c · rate |
|---|---|---|
| 12（原始值） | 0.0（19/0, 18/0） | 0.0（5/0, 5/0） |
| 60 | 0.0（19/0, 18/0） | 0.0（5/0, 5/0） |
| 300 | 0.0541（19/2, 18/0） | 0.0（5/0, 5/0） |
| 600 | 0.4324（19/10, 18/6） | 0.0（5/0, 5/0） |
| **900（当前默认）** | **0.5946（19/12, 18/10）** | 0.0（5/0, 5/0） |

**关键发现**：12s／60s 阈值下两本 trip 的 1P+4L/1P+5L 通过率均为 **0%**——回滚到接近原始值会**完全消灭**当前观测到的 mosaic-5 曝光（与热修前"5/6 格拼图偏少"事故症状一致）。900s 是曲线陡升区（600→900 仍 +16.2pp），600s 是一个有意义的折中点（约为 900s 通过率的 73%）。

### Trip：`demo-815dc906d3`（连拍/拼图边界 · 竖图占比高）

| 指标 | 值（900s，当前 render） |
|------|-----------|
| 资产数 / 竖图占比 | 249 / 56.6% |
| 1P+4L(win5) geometry / burst_pass | 19 / 12（63.2%） |
| 1P+5L(win6) geometry / burst_pass | 18 / 10（55.6%） |
| 5 格 `main-portrait-3land` 屏数（trip.json 当前） | 2（`mosaicDecisionLog`：2/2 决策成功，0 fallback） |
| 6 格 hero 屏数 | 0（`mosaic_config_diag` 提示：竖图占多，零 hero 拼图符合预期 · MCR D13） |
| 4 格 landscape 屏数 | 3（`mosaicDecisionLog`：3/3 决策成功，0 fallback） |
| `mcr_eval_recurate` 复核（只读，不改 trip.json） | 与当前 trip.json 一致：`mosaicPatterns=['screen-mosaic-5-main-portrait-3land']`，无 hero |
| 抽样分组合理性 | 2 个 mosaic-5 分组的 5 张资产实际拍摄跨度分别为 **6m04s / 10m21s**（均<900s，且明显是同一场景内连续走动拍摄），非跨场景乱入 |
| ⚠️ 已知问题 | 见文末「附录：本轮已知阻塞项」——本机 `trip.json` 当前有 schema 校验失败（curation 字段 drift），无法完整重新 `render`；现有 `index.html` 相对 `trip.json` 存在 **staleness**（约 25/249 资产未出现在渲染产物中，含本表 2 个 mosaic-5 screen 引用的资产），故 `htmlLayoutScreenCount` 数字虽与 `screenCount` 巧合相等（112=112），但**不构成 mosaic-5 §5.2 目视签字**的有效证据 |

### Trip：`linzhi`（历史稳定基线 · folio 完整）

| 指标 | 值 |
|------|-----|
| trip.json | **本机不可用**——`trips/linzhi/` 按 `.gitignore` 仅保留渲染产物（js/css/html/README），`trip.json` 未随仓库分发（推测为真实个人相册隐私考虑）。无法在本环境 re-curate / 重新 render |
| `htmlLayoutScreenCount`（现有 index.html） | 100 |
| `chapterSeparatorTicketCount`（现有 index.html） | 4 |
| `momentExifBarCount`（现有 index.html） | 0（现有 render 可能早于 P23 EXIF overlay 上线，不能反推当前 overlay 是否生效） |
| burstPassRate / mosaicDecisionSummary | 不可计算（无 `assets[]`/`curation`） |

### Trip：`demo-80301df45c`（PRD 标注"横图 hero 拼图"代表 trip）

| 指标 | 值（900s，重新 render 后） |
|------|-----------|
| 资产数 / 竖图占比 | 164 / **68.9%**（⚠️ 与 PRD 角色描述"横图 hero"不符，见下方发现） |
| 1P+4L(win5) / 1P+5L(win6) geometry / burst_pass | 5/0 · 5/0（**所有阈值下均 0% 通过**，见敏感度表） |
| mosaic 屏数 / hero 屏数 | 0 / 0 |
| `mosaicDecisionLog`（trip.json 当前） | 空——此 trip 未经当前 MCS 决策日志插桩的 curate 跑过，或从未产生候选 |
| `mcr_eval_recurate` 复核 | 与当前一致：`mosaicPatterns=[]`，`heroMosaicScreenCount=0` |

**发现（需团队关注，超出本 ADR 决策范围）**：`demo-80301df45c` 竖图占比 68.9%，且 1P+4L/1P+5L 窗口在任意 `mixed_proximity_seconds` 下通过率均为 0%——这本质是**素材内容限制**（无满足几何+时间条件的连拍序列），不是 window_order 排序问题。该 trip 当前**不能**为"6 格 hero 是否被 4 格压制"提供证据（因为 6 格候选从未进入候选池，与顺序无关）。建议团队重新确认/更换第三本 dogfood trip 为真正有横图连拍素材的相册，否则 window_order 决策将持续缺乏数据支撑。

## 决议（工程基于以上数据的建议 · 待产品/算法签字确认）

<!-- 以下为工程依据 dogfood 数据给出的建议裁定，非最终裁定；请产品+算法评审后勾选/改写 -->

- [x] **建议：维持** `mixed_proximity_seconds: 900` 为全局默认——回滚到 12s/60s 会使两本可用 dogfood trip 的 1P+4L/1P+5L 通过率**归零**，等价于重演"5/6 格拼图偏少"事故；900s 下的实际分组（demo-815dc906d3 两组，跨度 6–10 分钟）经人工核对为同场景连续拍摄，无乱入证据
- [ ] 回滚至 `mixed_proximity_seconds: ___`（不建议；如产品坚持收紧，600s 是数据上"仍保留约 73% 曝光"的折中点，而非 300s/60s）
- [x] **建议：暂不调整** `window_order: (5, 4, 6, 9)`——当前两本 dogfood trip 均**无一个** 6 格候选进入候选池（与顺序无关，是几何/连拍条件不满足），本轮数据**无法**支撑"4 先于 6 压制 hero 6 格"的假设，调整顺序前需要一本真正产生 6 格候选竞争的 dogfood trip
- [ ] 调整为 `window_order: (6, 5, 4, 9)`（或：___）（证据不足，暂缓）
- [ ] **相册级 override**：___（本轮未评估，留待 W2 或下一轮 ADR 修订）

**决议摘要（一句话）**：

> 维持 `mixed_proximity_seconds=900` 与 `window_order=(5,4,6,9)` 现状不变；window_order 调整因缺乏 6 格候选竞争的 dogfood 证据而暂缓，待补充一本真实横图连拍相册后再评审。

## 后果

### 维持 900s

- 利：demo-815dc906d3 保留 2 个 mosaic-5 screen（1.9%/107 内容屏），对应"张智慧精选2"里两段海边连续行走场景，符合直觉；不维持则完全消失，复现原事故症状
- 弊：900s 跨度较大（15 分钟），理论上仍存在"同地点不同事件被误判为一组"的风险，但本轮抽样未发现实例；建议后续 dogfood 扩容时持续抽查分组的时间跨度分布

### 维持 window_order 现状

- 利：无变更风险；避免在缺乏证据情况下改变全局打分候选顺序
- 弊：若确实存在"4 格抢先于 6 格"的压制，本决议不会解决它——但本轮数据表明当前两本 trip 的 6 格候选池本就是空的，调整顺序不会改变结果，需先解决候选生成而非候选排序

## 附录：本轮已知阻塞项（供后续修复参考，非本 ADR 决策内容）

1. `trips/demo-815dc906d3/trip.json`（本机本地文件，未纳入版本控制）当前 `render` 会报两类 schema 错误：① `chapters[1].screens` 中 5 个条目缺 `screenId`（已在本机补齐 `ch-02-sc-gap-NN` 占位 ID，仅本地文件，不影响任何已提交内容）；② 补齐后仍报 `curation` 存在 schema 未声明的字段（`aestheticAlignment`、`albumProfile`），阻止完整 `render` 跑通。这是 **schema/数据版本漂移**，与 LRG overlay 门禁无关，但导致目前 `trips/demo-815dc906d3/index.html` **落后于** 当前 `trip.json`（约 25/249 资产未出现在渲染产物里，含两个 mosaic-5 screen 引用的资产）。建议单独排期修复 schema 或补齐 trip.json，之后重新 `render` 才能拿到 demo-815dc906d3 的**当前**渲染产物，用于 §5.2 完整目视签字（尤其 mosaic-5 底行不裁切一项，本轮**未能**验证）。
2. `trips/linzhi/trip.json` 按 `.gitignore` 规则不随仓库分发，本环境无法 re-curate/render，只能对现有静态 `index.html` 做只读指标提取；EXIF/ticket 等指标可能反映的是**早于**当前 overlay 版本的历史渲染。
3. `demo-80301df45c` 实测竖图占比 68.9%，与 PRD 描述的"横图 hero 拼图代表 trip"角色不符，且无法提供 6 格候选证据；建议后续更换或新增一本真正含横图连拍的 dogfood trip。

## 验证计划

- [x] 3 本 dogfood trip 指标采集（`demo-815dc906d3`、`demo-80301df45c` 已 render+采集；`linzhi` 因 `trip.json` 本机不可用，仅 HTML 只读指标）
- [x] `docs/acceptance-records/lrg-dogfood.*.json` baseline 已写入（3 个文件）
- [ ] 产品目视 §5.2 checklist —— **未完成**：`demo-815dc906d3` 因附录阻塞项 #1（render 落后于 trip.json）无法验证 mosaic-5 底行不裁切；`demo-80301df45c` 当前无 mosaic/hero 屏可供目视；需附录问题解决后补做
- [ ] MCR-RELEASE-NOTE 用户须知更新（本轮维持默认值，暂不需要；若产品最终裁定与本建议不同则需要）

## 参考

- commit `22c1767` · `travelogue/config/layout.py` L185
- `travelogue/config/mosaic.py` · `DensityBudgetConfig.window_order` 默认 `(5, 4, 6, 9)`
- `scripts/mosaic_config_diag.py`
