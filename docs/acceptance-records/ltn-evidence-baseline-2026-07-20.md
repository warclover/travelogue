# LTN 实证基线报告（R1–R4）· 2026-07-20

| 属性 | 内容 |
|------|------|
| **对应调研** | R1 根因实证 / R2 窗供给 / R3 分轨数据源 / R4 分支保护 |
| **方法** | 对 4 本 trip（58/49/121/249 张）以 `log_level=debug` **内存重放 re-curate**（不写 trips/*）；窗签名扫描用 `time_near_chain`（900s）；脚本 `.tmp-ltn-evidence.py`，原始输出 `.cache/ltn-evidence/` |
| **样本** | demo-65db8fd377（凯哥精选4·58）、demo-eb9a45b3c4（黔西南·49）、demo-2025（东澳岛·121）、demo-815dc906d3（张智慧精选2·249） |
| **结论** | **9 项实证发现（E1–E9）；U1/U2 两个未知已当场定位；4 项要求校准 PRD/峰会决议** |

---

## 1. 发现清单

### E1 · demo-65 的拼图≈0 主因是「无合法机会」，不是管线 bug ⚠️ 校准预期

- 4 本 trip 的 `appliedLayoutDensity` **全部为 `balanced`**——demo-65 从未走过 `hero_first`，「hero_first 跳过 MCS」与该 demo 无关。
- demo-65 的窗内聚扫描结果：**win4/win5 时间内聚窗 = 0**（900s 门槛下没有任何一个 4/5 连窗通过 `time_near_chain`）。凯哥精选的照片在时间轴上是散点（精选后间隔远大于 900s）。
- **含义**：对这本 demo，机会 oracle ≈ 0，hero=0 是**正确行为**。它应作为 AC-C-02 的**阴性对照 fixture**（验证「无机会时 used=0 且 Studio 可解释」），而不是「修完必须出 hero」的验收样本。阳性样本应选 demo-2025 / demo-815（见 E2）。

### E2 · 窗供给分布：archive 卷机会充足，curated 卷靠时间内聚而非 burst

| trip | 张数 | win4 内聚窗（top） | win5 内聚窗（top） | 判断 |
|------|------|--------------------|--------------------|------|
| demo-65 | 58 | **0** | **0** | 无机会（阴性对照） |
| demo-eb9a | 49 | 4P0L=6, 2P2L=6, 0P4L=5 | 2P3L=6 | 有少量机会 |
| demo-2025 | 121 | 3P1L=18, 2P2L=17, 4P0L=14, 0P4L=10 | 4P1L=13, 1P4L=1 | 机会充足 |
| demo-815 | 249 | 4P0L=33, 3P1L=27, 0P4L=20 | 3P2L=23, 1P4L=10 | 机会充足 |

- 注意签名分布**竖图偏多**（4P0L / 3P1L 占大头）——4-hero（0P4L）的适用窗存在但不是最大簇；**竖主导签名（3P1L/4P1L）的 hero 需求**值得在剪枝后的空位讨论中重新评估。

### E3 · `burstGroupId` 在全部样本上退化：每资产一组 ⚠️ 校准 C4/C5

- 4 本 trip 的 burst 组数 == 资产数，**groupsGe4 = 0**——不存在任何多张 burst 组。
- **含义**：「burst 链永不切断」「burst 内聚触发 reserve」等设计在现网数据上**取不到信号**；C4 分段与 C5 触发条件必须以 `takenAt` 时间链（`time_near_chain`）为主信号，burstGroupId 仅作未来兼容。峰会方案的伪代码不受影响（time gap 是主判据），但文案要改。

### E4 · 真实活跃候选面 > lte_policy 的 15 个 ID ⚠️ 校准 D-01 剪枝范围

- 重放中实际胜出的模板包括 **`screen-mosaic-4-1l3p-rail`、`screen-mosaic-5-2p3l-rail`**——两者**都不在** `MOSAIC_*_PATTERN_IDS` 的 15 个之内，经 `template_contract`（config 已开 `enabled: true`）的 extras 路径进入候选。
- 日志显示 `candidateSource: "fallback"`、`squareRelaxed: true`（square 图放宽参与）。
- **含义**：峰会 D-01 的「15→11」只覆盖 policy 名单；**真实候选宇宙还有 contract extras（rail 族等）**。剪枝任务必须同时盘点 contract 解锁面，否则「活跃 ≤12」在数字上达标、实际候选面失控。

### E5 · U1 已解：日志混入落选 beam 候选，日志↔成品天然不守恒 ⚠️ AC 口径必修

- 现象：demo-65 日志有 1 个 winner（`mosaic-4-1l3p-rail`，score 0.80），成品 **0 个 mosaic 屏**；demo-815 `2p3l-rail` 胜出 2 次、成品 1 屏。
- 根因（代码确认）：`layout_candidates.py` 对同一章生成**多个候选 plan**（每个都调 `plan_screens_for_chapter` → 触发 MCS hook），日志缓冲（`begin_mosaic_capture`）是**整个 curate 运行共享**的——落选候选的 MCS 决策也进了 `mosaicDecisionLog`。
- **含义**：①`mosaicDecisionLog` 不能直接当「成品解释」用——C6 的 Studio 展示与 AC-C 溯源**必须过滤到胜出 plan**（日志需加 planId/generation 标记，或只在最终 plan 重放时记录）；②此为 H2 的新增需求，不只是保留 rejects。

### E6 · U2 已解：debug 日志有 reject 数据，但暴露「双通道配置」隐患 ⚠️ Wave A 新证据

- 复跑确认：用 `config_override(cfg_dbg)` 包住 re-curate 后，debug 日志**包含完整 `rejectedTemplates`**——demo-65 唯一的 MCS 窗记录了 `contract:infeasible_mix ×3`、`ordering_failed ×3`，最终 `candidatesCount=1`。
- **新隐患（E6b）**：`run_curate(cfg=...)` 传参**不足以**控制日志级别——`drain_mosaic_logs` 内部直接 `get_config().mosaic.log_level`（`hook.py:165`），存在「cfg 参数 vs 进程级 get_config」**双通道**。任何依赖 cfg 传参的调用方（含 Studio per-request override）都可能拿到与预期不符的日志/行为。这是 Wave A fail-loud 主题的又一实证，建议纳入 R-A2 排查范围。

### E9 · MCS 进窗次数极少：stage 抢占定量证据

- debug 重放的 MCS 窗尝试数：demo-65 **1 次**/58 张、demo-eb9a **1 次**/49 张、demo-2025 **4 次**/121 张、demo-815 **7 次**/249 张。
- 绝大多数照片从未进入 MCS——被 collage solo / mixed / landscape run / portrait 流水线在前面消费。「Pipeline 抢占」从推断升级为**定量事实**：改评分只影响这 1–7 个窗，**进窗机会本身才是第一瓶颈**（支持 C1/C4 的优先级排序）。

### E7 · 重放揭示模板曝光漂移：4-hero 曾经出现过、现在选不中了

- demo-2025 **存量** trip.json 里有 `screen-mosaic-4-hero-70-sidebar × 2`（历史 curate 产物）；本次重放后变成 `mosaic-4-1l3p-rail × 2` + `mosaic-5-main-portrait-3land × 1`。
- **含义**：①4-hero 在某个历史配置下**赢过**（其可行性有实证）；②某次变更后它从候选中消失/失利——这正是「名义上线、实际归零」的活样本，佐证 H8 active_set_gate 与 rollout 生命周期规则的必要性；③re-curate 不幂等（同数据不同结果），golden 基线须锁配置版本。
- 另 demo-815 重放中 `screen-landscape-4`（等权）经 MCS 胜出 2 次——等权 4 与 hero 4 的竞争关系（hero-gap prior）有真实战场。

### E8 · rhythm post-check 现网 fail-open 实录

- 重放日志：demo-2025 `full_bleed_portrait_consecutive=3`、demo-815 `=4`、两本 `portrait_pair_streak=1`——**mode=log 只记不管**。佐证 Wave A fail-loud 方向；这些违规量也可直接进周看板。

---

## 2. R3 答案：分轨判定数据源

- `assets[]` **无** keep/cull 字段；判定源是 `curation.displayedAssetIds`（kept 数）与 `curation.excludedByCullAssetIds` + `cullSummary`。
- 样本 kept：43 / 42 / 107 / 203 → curated 判据「kept<80」以 `len(displayedAssetIds)` 计算即可落地；demo-65、demo-eb9a 落 curated 轨，demo-2025、demo-815 落 archive 轨，分布合理。

## 3. R4 状态：分支保护

- 本机无 `gh`，API 查保护规则需 admin token。**需负责人在 GitHub 网页确认**：`warclover/travelogue` → Settings → Branches → main 是否有 required status checks（应勾 `lint`、`test-pr`）。或安装 `gh` 后由我核验。

---

## 4. 对 PRD / 峰会决议的校准建议

| 原表述 | 校准为 |
|--------|--------|
| AC-C-02 以 demo-65 为 hero≥1 验收样本 | demo-65 = **阴性对照**（oracle=0 → used=0 + 可解释）；阳性验收改用 demo-2025 / demo-815 或 H9 合成 fixture |
| C4/C5「burst 链/burst 内聚」为主信号 | **`takenAt` 时间链为主**；burstGroupId 现网退化，仅作兼容 |
| D-01 剪枝=policy 15→11 | 增加**contract extras 盘点**（rail 族等），「活跃集」定义 = policy ∪ contract 解锁面 |
| C6/H2 直接展示 rejected Top3 | U2 已解：debug 级数据可用；H2 只需把 window 级保留 Top3；另修 E6b 双通道配置 |
| AC 溯源假设日志↔成品守恒 | U1 已解：日志含落选 beam 候选的决策；H2 增加胜出 plan 标记，AC-C-07 只对胜出 plan 断言守恒 |
| R-A2 范围 | 增加 E6b：`cfg` 传参与 `get_config()` 双通道一致性排查（`drain_mosaic_logs` 为实证样例） |

## 5. 建议下一步

1. **H2 需求扩充**（U1 已定位）：`mosaicDecisionLog` 加胜出 plan 标记（planId/generation），或仅最终 plan 记录；C6/AC 溯源只读胜出 plan 条目。
2. H9 合成 fixture 设计时**必须包含**：≥900s 内聚簇、0P4L 与 3P1L 两类签名窗、阴性段（散点时间）——本报告的分布就是配方。
3. R4 请负责人网页确认（或授权装 gh）。
4. 本脚本可在 Wave A 转正为 `scripts/ltn_evidence_baseline.py`（即 A4 交付物）。

## 6. 变更

| 日期 | 说明 |
|------|------|
| 2026-07-20 | 初稿：4 trip debug 重放 + 窗签名扫描；E1–E8、U1–U2、校准建议 |
