# Travelogue · 排版可信与叙事合同 需求说明（Layout Trust & Narrative）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue |
| **文档版本** | v1.2.0-LTN |
| **状态** | **Approved · 2026-07-20 项目负责人拍板（v1.1 并入开发评审纠错 + 七方峰会决议；v1.2 并入实证基线校准 E1–E9）** |
| **特性代号** | **LTN**（Layout Trust & Narrative） |
| **一句话代号** | 「先不撒谎，再让拼图该出时出；冻结扩库，勿先松配额」 |
| **前置条件** | Phase 15 MCS、Phase 16 LTE、Phase 21 密度预算已落地；LRG / MCR 有基础但未完全闭合 |
| **依据** | [layout-mosaic-multi-persona-review-2026-07-20.md](./acceptance-records/layout-mosaic-multi-persona-review-2026-07-20.md)、[layout-next-sprint-backlog-2026-07-20.md](./acceptance-records/layout-next-sprint-backlog-2026-07-20.md)、[ltn-dev-feasibility-review-2026-07-20.md](./acceptance-records/ltn-dev-feasibility-review-2026-07-20.md)、[ltn-template-slot-summit-2026-07-20.md](./acceptance-records/ltn-template-slot-summit-2026-07-20.md)、[ltn-evidence-baseline-2026-07-20.md](./acceptance-records/ltn-evidence-baseline-2026-07-20.md) |
| **关联文档** | [PRD-PHASE21-mosaic-density-budget.md](./PRD-PHASE21-mosaic-density-budget.md)、[PRD-LAYOUT-READER-REGRESSION-GUARD.md](./PRD-LAYOUT-READER-REGRESSION-GUARD.md)、[PRD-PHASE15-photo-mosaic-evolution.md](./PRD-PHASE15-photo-mosaic-evolution.md)、[PRD-HIGHLIGHT-GALLERY-MOUNT-V1.md](./PRD-HIGHLIGHT-GALLERY-MOUNT-V1.md)（**后置依赖本 PRD**）、[PRD-FINISH-THIS-TRIP-V1.md](./PRD-FINISH-THIS-TRIP-V1.md)（FTT 纲领 · 将本 PRD A/B 标为 P0、C/D 标为 P1） |
| **参考 demo** | 阴性对照：`demo-65db8fd377`（凯哥精选，实证无内聚窗，hero=0 为正确行为）；阳性样本：`demo-2025` / `demo-815dc906d3`（内聚窗充足） |
| **更新日期** | 2026-07-20 |

---

## 0. 一句话

在**不拆掉现有游记语法**、**不放宽 P21 dense 上限**、**不新增多槽 SKU** 的前提下，先把排版做成**可复现、不静默失败**的可信基线，再对齐 scroll / present / longshot 的**叙事合同**，并让合法的 **hero mosaic 稀疏出场**，使章内节奏可扫视——作为后续高光轻布展（HGM）的前置。

---

## 1. 背景与问题

### 1.1 战略判断（八方评审收敛）

| 判断 | 含义 |
|------|------|
| 语法骨架正确 | 单图大屏、票根分章、不花哨——用户认「干净相册/画册」 |
| 短板不是模板不够 | 债在：可信、三模式、拼图出场、节奏 |
| 拼图≈0 ≠ P21 过狠 | 主因是 3 槽 legacy 兜底、进窗抢占、几何/SKU 硬门；配额常未消耗 |
| 先工程可信，再体验惊喜 | fail-loud 不做，节奏/拼图修了也会「修好又弄丢」 |
| HGM 不插队 | 选型与呈现依赖本 PRD 可信基线 |

### 1.2 用户 / 产品可感知问题

| ID | 问题 | 用户体感 | 根因层 |
|----|------|----------|--------|
| **LTN-P-01** | 修好又弄丢 | 调了样式或配置，成品无感或回退 | sync CSS 截断、config silent default、门禁 FAIL 仍可 merge |
| **LTN-P-02** | 三模式撒谎 | 网页满意，微信长图「不是同一部作品」 | 缺 Narrative Contract；longshot 拆 slot |
| **LTN-P-03** | 拼图该出不出 | 精选像「只敢单图/三叠」；hero mosaic ≈ 0 | MCS→size=3 legacy；`hero_first` 关 MCS；活跃 4 槽无 hero |
| **LTN-P-04** | 节奏扁平 | 屏缝黏、章内不可扫视 | breath≈9px；无语义气口；beat 默认 flat |
| **LTN-P-05** | 拼图黑箱 | Studio 不知为何拼/没拼 | `mosaicDecisionLog` 未产品化 |

### 1.3 拼图≈0 根因排序（算法双份评审）

1. **MCS 失败 → size=3 legacy**（不记 dense、绕开 P21）→「有三叠无 hero」  
2. **Pipeline 抢占 + 窗宽碎片化**（含 `hero_first` 整段跳过 MCS）  
3. **几何 / eligibility 硬门** + 部分 hero 模板对 walking burst 不友好  
4. **活跃 4 槽族无 main 角色** + 评分安全偏置  
5. **配置 / density 放大器**（含 nine_min 争预算）  
6. **P21 配额**（对 used≈0 解释力最弱）

### 1.4 已拍板决策

| # | 决策 | 结论 |
|---|------|------|
| D1 | 波次顺序 | **A 可信 → B 三模式 → C 拼图 → D 节奏**；HGM 后置 |
| D2 | 拼图第一刀 | **解耦 MCS→3 槽 legacy**，高于放宽配额 |
| D3 | `hero_first` | **降权 flat dense，不再硬跳过 MCS**；精选允许 1–2 次合法 hero |
| D4 | longshot mosaic | **默认保持组感**（`preserveGroup=true`），非 implicit flatten |
| D5 | hero 下限 | **机会型章级 reserve**；拒绝 trip 级产量 KPI |
| D6 | 节奏 | **与 C 并行轻量启动**设计定标 |
| D7 | 扩库 | **冻结**至盲评过线 |
| D8 | 活跃模板集（峰会 D-01） | **15 → 11**：加 4-hero；剪 `portrait-6` / `landscape-6` / `portrait-9` / `landscape-9` / `grid-8`；留 1 空位 |
| D9 | 分歧定标 | 副槽底线 / L1 屏缝起点交 D1 JND 定标；定标前用保守值 **72px / 10px** |
| D10 | 新硬前置 | **H6–H9**（评分暗礁修复 / 几何审计 / active_set_gate / 合成 fixture）批准插入 |
| D11 | C4 范围（N3） | 采用**简化版粗分段**（burst 链 + takenAt 间隔 + place.city；不发明 `sceneId`） |
| D12 | Fixture（N2） | **脱敏合成 fixture 入库**，CI 可复跑；本机 dogfood 为补充 |

### 1.5 代码事实勘误（开发评审，v1.1 并入）

| # | v1.0 认知 | 代码事实 |
|---|-----------|----------|
| F1 | — | MCS hook 在 `travelogue/layout_engine/mosaic/hook.py`；`curation/screen_layout_state.py` 仅为 shim |
| F2 | 「活跃集 ≤12 只需加 hero」 | 统一集合**已 15 个 ID**；5 槽 hero（`hero-3-2-plus-4`）**已 GA 在列**；缺口 = 4 槽 hero + 剪枝（见 D8） |
| F3 | 「按 sceneId 切窗」 | **`sceneId` 字段不存在**；只有 `burstGroupId` / `takenAt` / `place`（见 D11） |
| F4 | 「Studio 直接消费日志」 | 日志已持久化，但默认 `log_level=window` 会**剥掉完整 `rejectedTemplates`**；Studio 无 mosaic 日志 API（H2 前置） |
| F5 | 「LRG 防护缺失」 | 截断 fail-fast 与 selector 单测**已在 PR 跑**；缺口是 `validate` job（export+diff）**仅 push 后跑**、PR-warn 分支为死代码、分支保护未核实 |
| F6 | 「MCR silent default 待修」 | `enabled_window_sizes` 缩 `[5]` bug **已修**；剩余静默项为 `layoutDensity` 等非法值静默归一 |

### 1.6 峰会新发现（S 系列，动工前必修）

| # | 发现 | 影响 |
|---|------|------|
| **S1** | `_duplicate_density_penalty` 对 burst run≥4 打 0.8 且不看 `prefers_burst` | 4-hero 在设计场景先天背罚，**上线即死** → H6 |
| **S2** | `R_GRID9_LAND` ×1.06 加成与剪 9 宫矛盾；`portrait-9` 无 flat 惩罚 | 剪枝 PR 同步删除 → H6 |
| **S3** | `hero_first` dense ×0.35 **向下取整**，小 trip 预算归零 | C2 必修，否则 curated 轨 hero 恒 0 → H6 |
| **S4** | 4-hero 声明 AR 1.78 vs 实渲 cell ≈1.24（16:9 主图横裁 ~30%）；`portrait-6` 槽 AR 0.375 必裁脸 | GA 前修 YAML；全模板几何审计 → H7 |
| **S5** | 模板权威实为**六写**（YAML status / rollout / lte_policy / LEGACY registry / schema 枚举 / config override） | E1 范围扩大；先修门再删写点 |
| **S6** | hero-3-2 的 [7,3] 分栏、2px/3px gap 等网格杂音 | 纳入几何审计与合同参数 |

### 1.7 实证基线校准（E 系列，v1.2 并入，详见 [实证基线报告](./acceptance-records/ltn-evidence-baseline-2026-07-20.md)）

| # | 实证发现 | 对本 PRD 的校准 |
|---|----------|-----------------|
| **E1** | demo-65 无任何 4/5 时间内聚窗，且 `appliedLayoutDensity=balanced`（从未走 hero_first） | demo-65 改为 **AC-C-02 阴性对照**；阳性验收改用 demo-2025 / demo-815 或 H9 fixture |
| **E3** | 4 本 trip 的 `burstGroupId` 全部退化为每资产一组（groupsGe4=0） | C4/C5 主信号改为 **`takenAt` 时间链**；burstGroupId 仅作兼容 |
| **E4** | 实胜模板 `mosaic-4-1l3p-rail` / `mosaic-5-2p3l-rail` 不在 policy 15 之内（经 template_contract extras 进入） | D8 剪枝范围扩为 **policy ∪ contract 解锁面**；「活跃 ≤12」按并集口径统计 |
| **E5** | `mosaicDecisionLog` 混入落选 beam 候选的决策（胜出≠上屏） | **H2 增加胜出 plan 标记**；C6 展示与 AC 溯源只读胜出 plan 条目 |
| **E6b** | `run_curate(cfg=...)` 与内部 `get_config()` 双通道，cfg 传参不生效于日志级别 | 纳入 **R-A2** 排查范围（fail-loud 主题实证样例） |
| **E7** | demo-2025 存量含 4-hero×2，重放后消失——「名义上线、实际归零」活样本 | 佐证 H8 gate 与 rollout 生命周期规则；golden 基线须锁配置版本 |
| **E9** | MCS 进窗次数：1/58、1/49、4/121、7/249——抢占为定量事实 | **进窗机会是第一瓶颈**，C1/C4 优先级维持最高；评分调优（H6）影响面有限但仍必修 |

---

## 2. 产品原则

| ID | 原则 | 说明 |
|----|------|------|
| **LTN-PR-01** | 游记语法为底 | 不借机全书换肤；单图 / 票根 / 双竖基本盘保持 |
| **LTN-PR-02** | Fail-loud 优先 | 读者可见样式与关键 curate 配置不得 silent wrong；违规阻断发布 |
| **LTN-PR-03** | 语义合同 > 像素统一 | 三模式对齐叙事角色与组边界，不要求像素一致 |
| **LTN-PR-04** | P21 上限哲学不变 | dense 配额是天花板，不是 KPI；禁止「没用完就塞」 |
| **LTN-PR-05** | Hero 宁缺毋滥 | 仅 burst+几何+主槽合格时 emit；禁止等权 grid 冒充 hero |
| **LTN-PR-06** | 冻结扩库 | 新 patternId / 槽数&gt;6 默认拒；活跃集目标 ≤12 |
| **LTN-PR-07** | 可解释 | Studio 必须能说清「为何拼 / 为何没拼」Top3 |
| **LTN-PR-08** | HGM 前置 | 本 PRD 验收前，不启动完整高光轻布展实现 |

---

## 3. 目标与非目标

### 3.1 目标

| ID | 目标 | 验收口径 |
|----|------|----------|
| **G-LTN-01** | 读者可见样式 / 关键 config **零静默丢失** | LRG+MCR 门禁闭合；Type-A/B dogfood 附件必过 |
| **G-LTN-02** | 三模式叙事不撒谎 | 同 trip：scroll 中的 mosaic 组在 longshot **仍可辨「一组」**；导出前双预览可用 |
| **G-LTN-03** | Hero mosaic 稀疏回归 | curated（机会合法）：**1–2** 次含 `main` 的 hero；archive 百张卷：**3–5** 次高质量 dense（P21 max 内） |
| **G-LTN-04** | 切断假拼图 | `portrait3_after_failed_mcs5_rate` 相对基线 **↓≥50%** |
| **G-LTN-05** | 节奏可扫视 | 小样本盲评节奏 **5.5→≥7**；语义 pause 与屏缝分离 |
| **G-LTN-06** | Studio 可解释 | 用户可见 reject / fallback Top3 |
| **G-LTN-07** | 可观测 | 周看板：窗宽、mosaic 曝光、burstPass、screenCount parity、scroll↔longshot 守恒 |

### 3.2 非目标

| 不做 | 原因 |
|------|------|
| 新增多槽 SKU（7+/8/9、第二套 full-bleed） | 扩库增债、不治根因 |
| 放宽 P21 `dense_collage_max` | used≈0 时无效；先修进窗 |
| trip 级强制 `min_dense` | 会硬凑，伤杂志感 |
| 三模式像素级统一 | 错误目标 |
| HGM 完整轻布展 / 凝视模式 | 依赖本 PRD + P23 选型 |
| 改写全书装裱分级皮肤 | 已验证有害（见 HGM 背景） |

---

## 4. 范围与分波交付

```text
Wave A 可信基线（含 H8 active_set_gate、H9 fixture）
   │
   ├──► B3 双预览（提前，2–4 天）＋ B1 合同 ADR 起草
   │        └──► B2 longshot 保组感（独立大项，新 ADR 推翻 ADR-003）
   │
   ├──► H6 评分暗礁修复 + H7 几何审计
   │        └──► C1 → C2 → C3（剪枝+转正同 PR）→ C5
   │                  └── C6 Studio 解释（可并行，先做 H2 日志保留）
   │                  └── C4 简化粗分段（视 C1–C3 后指标决定是否完整化）
   │
   └──► Wave D 节奏（D2 beat 默认 1–2 天可先行；D1 JND 定标并行）

Wave E 收敛与看板（贯穿 / 不阻塞 A–C）

HGM ── 本 PRD 验收后另开
```

预估节奏（开发评审修正后）：**A 压缩为 3–5 人日**（含 H8/H9 约 +2 人日）→ H6/H7 约 2–3 人日 → C 主链 约 2 周 → **B2 独立 1.5–2.5 周**（最大单项，不与 C 抢人）→ D 3–6 人日（多数可并行）。

---

## 5. Wave A · 可信基线（P0）

### 5.1 需求

| ID | 需求 | 说明（v1.1 按代码事实改写） |
|----|------|------|
| **R-A1** | 闭合 LRG merge 门 | 将 `export --sync-journal` + `git diff --exit-code` **挪进 PR job**（现仅 push 后跑）；删除死代码 PR-warn 分支；分支保护勾选 `lint` / `test-pr` / sync 步骤所属 job |
| **R-A2** | 关键 config fail-loud | `layoutDensity` 等关键键**非法值 → `ConfigError`**（替代静默归一 `balanced`）；复用 `template_contract` 的 fail-loud 模式；`[5]` bug 已由 MCR 修复，勿重复。**v1.2 增**：排查 `cfg` 传参 vs `get_config()` 双通道不一致（E6b，`drain_mosaic_logs` 为实证样例） |
| **R-A3** | 冻结扩库纪律 | PR / merge 决策树：新 `patternId` 或槽数&gt;6 → 默认 **NO**（豁免须书面）；validator 现只挡 &gt;9，需新规则并处理 8/9 存量豁免 |
| **R-A4** | 诊断基线 | 基于 `layout_debt_report.py` / `mosaic_config_diag.py` 薄封装聚合脚本；基线跑在 **H9 fixture** 上（demo trips 不入 git，CI 不可复跑） |
| **R-A5（H8）** | active_set_gate | `lte_policy` ↔ codegen（`--sync-python` 产物）↔ schema 枚举 ↔ golden **四处对账进 PR job**，drift → FAIL |
| **R-A6（H9）** | 合成 fixture 入库 | 脱敏合成 trip（`log_level=debug` re-curate）入库；AC-C 基线与机会 oracle 以此为准 |

### 5.2 验收（AC-A）

| ID | 验收项 |
|----|--------|
| **AC-A-01** | Type-A（样式/sync）变更：LRG 必过，附件进 CI 或发布清单 |
| **AC-A-02** | Type-B（curate/config）变更：MCR / 诊断可指出错误 intent，不得 silent 落到错误密度档 |
| **AC-A-03** | 故意截断 overlays 的回归用例必须失败 |
| **AC-A-04** | 诊断脚本可复跑，输出落入周看板起点 |

### 5.3 依赖与约束

- 复用并加强 [PRD-LAYOUT-READER-REGRESSION-GUARD.md](./PRD-LAYOUT-READER-REGRESSION-GUARD.md)，本 Wave **闭合其未闭环项**，不另起平行门禁体系。  
- 读者可见、非 LTE 生成样式仍只维护在 overlays 约定路径。

---

## 6. Wave B · 叙事合同与三模式（P0/P1）

### 6.1 Narrative Contract（最小字段集）

Canonical SSOT = `chapters[].screens[]`。每屏（或组）须能表达：

| 字段 | 含义 | 备注 |
|------|------|------|
| `narrativeRole` | plate / hero_single / stack / pair / mosaic_hero / mosaic_flat / breath / … | 枚举可迭代，须文档化 |
| `groupId` | 连作 / 拼图组 ID | 同组共享 |
| `preserveGroup` | 导出/长图是否保持组感 | **mosaic 默认 `true`**（D4） |
| `exportHints` | 表面特定提示（可拆/代表图优先等） | 不得与 `preserveGroup` 冲突而不自知 |
| `representativeAssetId` | 组代表作 | present / 缩略 / 长图折叠时用 |

**合同语义**：scroll / present / longshot 是同一合同的三种 View；允许像素与版式密度不同，**不允许无提示地抹掉组边界**。

### 6.2 需求

| ID | 需求 | 说明 |
|----|------|------|
| **R-B1** | ADR：Narrative Contract | 字段、默认值、迁移策略、与现有 `screens[]` 对齐 · **已落地** [ADR-020](./adr/020-narrative-contract.md) |
| **R-B2** | longshot 尊重 `preserveGroup` | **改合同非修 bug**：新 ADR 推翻 ADR-003「按 slot 展平」。窄幅（~428px）三级降级：① **保组换排**（竖向组排+组标记，默认）→ ② **代表图 + N**（`representativeAssetId` + 徽标）→ ③ 拆屏（仅显式 `preserveGroup=false`）。**已落地** `screens_to_longshot_items` |
| **R-B3** | 导出前双预览（**提前交付**） | MVP：iframe 双面（`index.html` vs `index-longshot.html` 同宽模拟），并排或一键切换；不依赖 B2，先让差异诚实可见 |
| **R-B4** | present 不偷叙事 | 现状：`chapter-separator` 不在幻灯 selector 内**已被静默跳过**（与 `skipAuxBlocks` 无关）；须补产品规则，不得 silent 丢章界。**已落地**：`screenplay.js` AUX 含章界（仍受 `skipAuxBlocks` 约束） |

### 6.3 验收（AC-B）

| ID | 验收项 |
|----|--------|
| **AC-B-01** | ADR 评审通过并入库 |
| **AC-B-02** | 固定 dogfood：scroll 中含 hero mosaic 的 trip，longshot 仍可辨「一组」（目视 + 可选 slot 守恒断言）。**机器项已落地**：`ltn_dogfood.py` / `scripts/ltn_dogfood_ac.py` + fixture；目视见验收记录 |
| **AC-B-03** | 双预览在导出/分享主路径可达，家庭用户能说清差异 |
| **AC-B-04** | `preserveGroup=false` 仅显式场景使用，有日志 |

---

## 7. Wave C · 拼图「该出时出」（P1）

### 7.1 产品定位（沿用评审）

| 屏型 | 角色 |
|------|------|
| 单图 `landscape-1` / 竖单 | 主语 |
| `portrait-2` | 对照 / 成对人物 |
| stack-3 | 同场时间线（合法时） |
| **mosaic-4/5 hero + sidebar** | **高潮 + 证据**（稀疏） |
| 等权 mosaic / 机械三叠 | fallback，不得冒充高潮 |

预期：

- **Curated**（kept&lt;80 或精选心智）：全书 **≤1–2** 次高质量 hero mosaic。  
- **Archive**（百张级 dump）：P21 表内 **3–5** 次高质量 dense（优先 hero，非等权密格）。

### 7.2 硬前置（v1.1 新增，C3 动工前完成）

| ID | 前置 | 说明 |
|----|------|------|
| **H2** | 日志保留 Top3 reject + 胜出 plan 标记 | 修 `format_log_entry`：window 级保留 rejected Top3（或 explain 字段），控制体积；AC 指标**禁止**读裁剪后日志。**v1.2 增（E5）**：日志须带胜出 plan 标记（planId/generation）或仅最终 plan 记录——beam 候选决策混入是实证事实，否则日志↔成品不守恒 |
| **H6** | 评分暗礁修复 | S1：`prefers_burst:true` 模板豁免 duplicate_density（cap 0.2）；S2：删 `R_GRID9_LAND` ×1.06；S3：dense 缩放 `max(1, floor(...))` 保底。各配回归锁单测 |
| **H7** | 模板几何审计 | 全活跃模板「声明 AR vs 实渲 cell AR」对账；修 4-hero：`targetDisplayAspect: 1.30`、`preferLadder: [1.3333, 1.5, 1.7778]` |

### 7.3 需求（实现序：H2/H6/H7 → C1→C2→C3→C5；C6 并行；C4 视指标后置）

| ID | 需求 | 说明 |
|----|------|------|
| **R-C1** | 解耦 MCS→size=3 legacy | 删 aux-3 拼接（`hook.py` size=3 直连 + `runtime.py` pack_aux）；降级序：**降窗宽（5→4→6 内建）→ 单图 hero 救场**（仅 main-eligible 且 hero gap 显著；advance=1 余照重进循环）**→ 显式 pending**（fail-loud 日志 `mcs_all_sizes_failed`）。parity / portrait tiler 显式 3 槽路径**原样保留** |
| **R-C2** | `hero_first` 改降权 | 删 hook 早退 + 修 S3 取整归零（**两处都要动**）；对 flat dense 强降权；hero 族仍可在合法窗尝试 |
| **R-C3** | 活跃集 15→11 + 4-hero 转 GA | 按 D8 清单剪 5 加 1；4-hero：`status: ga`、`rollout: 100`、进 `MOSAIC_4_PATTERN_IDS` + schema 枚举 + `--sync-python` codegen + `LEGACY_MOSAIC_REGISTRY_IDS` 补 hero-3-2；竞争用**条件化 hero-gap prior**（有主角 hero ×1.10、等权背 `wasted_hero` 0.35；均势反向），不硬抬 base_weight |
| **R-C4** | 简化粗分段（可降级项） | **主信号 = `takenAt` 时间链**（E3：现网 burstGroupId 退化为每资产一组，不可依赖）；时间豁口 = min(900s, max(120s, 3×中位间隔))；换 city 切；时间戳缺失贴前段；segment 为 planner 内存对象。**签名路由**：`(nP,nL,burst内聚)` → pattern 白名单缩窄，未命中回落全量 registry，路由结果写日志 `candidate_source`。视 C1–C3 后指标决定是否完整化 |
| **R-C5** | 机会 reserve 状态机 | `planner_state` 加 `hero_reserve: idle/armed/consumed/released`；armed 期间等权 dense 让位 hero 窗；失败/章尽/资产被占 → released；**不加额度**，P21 max / 相邻禁 / 章级上限照常 |
| **R-C6** | Studio 解释 | 前置 H2；消费原始 `mosaicDecisionLog` 展示 fallbackReason / rejected Top3（叙事语言）；签名路由的 `candidate_source` 一并展示 |
| **R-C7** | 分轨参数表 | 文档化 curated / archive / quick-share：limits、是否启用 size=3 aux、beat、min_score（实现可配置，不必三套代码） |
| **R-C8** | 槽位角色参数（峰会 D-03） | 新增窗内相对软惩罚 `main_not_window_best`(0.4)、`main_clone_in_sidebar`(0.3)；主从面积比 ≥3:1、主槽 AR 失配 ≤1.4× 进闸门；副槽最小短边保守值 72px（JND 定标后更新）；模板合同补最小槽宽 / 出血 / gap token / visualWeight 校验带 / caption 锚 |

### 7.4 红线

- 不为凑 reserve 放宽 `main_ar` / burst gate / face_crop 硬线；新机制只做条件化加成/占位，不碰硬门阈值。  
- 不把 featured / moment 图塞进无 main 的 flat-4。  
- 不连续两屏 dense（P21 相邻禁令保留）。  
- **不**为提升 used 而提高 `dense_collage_max`（本阶段）。  
- 签名路由必须白名单缩窄 + 未命中回落全量，禁止路由表成为新静默失败点。  
- 九宫独立配额逻辑（`nine_grid_limits_for_trip`）与 parity/tiler 显式 portrait-3 不受剪枝影响。

### 7.5 验收（AC-C，v1.1 补防钻空口径）

| ID | 验收项 |
|----|--------|
| **AC-C-01** | `portrait3_after_failed_mcs5_rate` ↓≥50%。**口径**：分母 = fixture 上离线隔离重放（配额/rhythm 无关）中「size≥4 有 hard_valid 候选但无 winner」的窗数；分子 = 成品三叠屏中与失败窗**共享 ≥1 assetId 且序位紧邻**者；parity/tiler 产物不计入；**只读原始日志** |
| **AC-C-02** | **机会 oracle**（配额无关：main 角色 pattern 硬门全过 ∧ 隔离评分 ≥ min_candidate_score 的窗数）≥1 ⇒ 成品 hero ∈ [1,2]；oracle=0 ⇒ used=0 可接受且 Studio 可解释。计入的 hero 屏须 `main ∈ roles` 且 main 面积占比 ≥0.55（防换标签冒充）。**样本口径（E1）**：demo-65 为阴性对照（oracle=0 → used=0 + 可解释）；阳性断言跑在 demo-2025 / demo-815 同分布的 H9 fixture 上 |
| **AC-C-03** | archive dogfood（≥100 kept）：hero/dense 落在 P21 max 内，目标 3–5 高质量（盲评「有主次」+ 计数硬门：裁脸数 / AR 失配数） |
| **AC-C-04** | `cross_scene_window_rate` &lt;5%（简化分段下由构造保证） |
| **AC-C-05** | Studio 可见「为何没拼」Top3 |
| **AC-C-06** | P21：`dense_collage_used ≤ max`；相邻 dense = 0 |
| **AC-C-07** | 防回潮单测齐备：no_aux3 / parity_tail / hero_first_attempts_mcs / dense_floor / burst_no_dup / no_grid9_boost / reserve_release / metric_reads_raw_log + golden 重录（与剪枝同 PR） |

---

## 8. Wave D · 节奏可读（P1，与 C 并行轻量）

### 8.1 三级节奏模型

| 层级 | 名称 | 含义 | 注意 |
|------|------|------|------|
| **L0** | 槽缝 | 屏内图片间隙 | 保持现有拼图内聚 |
| **L1** | 屏缝 | 普通屏与屏之间 | 解决「黏」的主杠杆之一 |
| **L2** | 语义 pause | 换章 / 换地点 / 高潮前后 | **≠** 多塞 breath 空屏凑数 |

中期：rhythm hint 宜由 planner 写入合同字段；**禁止**仅靠永久 CSS 补丁冒充叙事气口（架构约束）。

### 8.2 需求

| ID | 需求 | 说明（v1.1 并入峰会值带） |
|----|------|------|
| **R-D1** | Token 定标 | 起点带（JND 小样在带内定标，家庭侧宁小勿大）：**L0 ≈ 3px**（贴片感）；**L1 = clamp(10–12px, 1.6vh, 20px)**（现 8px 起步偏黏）；**L2 = clamp(36px, 6vh, 64px)**；比例 **L0:L1:L2 ≈ 1:4:16**。职责：票根管**章界**、L2 管**章内场景界**，不叠加。Token 只放 **preamble / overlays 源文件**（`@lte-generated` 段会被 sync 冲掉）。**已落地**：`--rhythm-l*` + `rhythmGap`/`data-rhythm-gap` |
| **R-D2** | Beat 接线 | 默认 `flat` → `classic_magazine`，**峰位 0.60–0.65 章进度**；章进度用真实/可靠估计。连续同 pattern 容忍：单图 ≤3、组合屏 ≤2、mosaic ≤1；章内 pattern 熵参考带 0.55–0.75。**已落地**：资产序进度 + 峰窗 0.55–0.70；pack 默认 classic（quick_share 仍 flat） |
| **R-D3** | 版式角色表 | 产品/渲染注释统一：plate / 1col / stack-3 / 2col / mosaic-hero / breath（+ mosaic-flat）。**已落地**：`layout_roles.py` 映射表；DOM `data-layout-role` / `data-narrative-role`；`rhythm_signoff.py` 闸门（改 `--rhythm-l*` 须 bump `RHYTHM_SIGNOFF`） |

### 8.3 验收（AC-D）

| ID | 验收项 |
|----|--------|
| **AC-D-01** | 小样本盲评节奏分 ≥7（基线 ~5.5）。工程 proxy 仅提示；人评清单见 [ltn-dogfood-ac](./acceptance-records/ltn-dogfood-ac-2026-07-20.md) |
| **AC-D-02** | 语义 pause 出现在章界/地点界，而非均匀加大所有屏缝。**代理已进** `ltn_dogfood`（禁全 L1/全 L2） |
| **AC-D-03** | 有样本时：hero mosaic 中章占比 ≥60%（与 beat 一致）。**已落地** fixture + 脚本（中章带 `[0.35, 0.80]`） |

---

## 9. Wave E · 收敛与可观测（P2，贯穿）

| ID | 需求 | 验收 |
|----|------|------|
| **R-E1** | LTE 单权威收束 | 活跃 pattern 唯一清单；收敛**六写**（YAML status / rollout / lte_policy / LEGACY registry / schema 枚举 / config override）；顺序：先修门（H8）→ 再删写点 → 最后建新抽象。生命周期规则：**rollout=0 超 4 周强制 review**（转正或归档）。**已落地（第一步）**：`active_set.py` 清单 + 六写表；`LEGACY_MOSAIC_REGISTRY_IDS` **改为派生** codegen unified（删手写第四表）；gate 对账含 LEGACY↔policy；`rollout.zeroSince` + 28 天逾期 FAIL |
| **R-E2** | 周看板 | 窗宽分布、mosaic 曝光、§12 指标包；脚本 `scripts/ltn_weekly_dashboard.py`（只读 trip.json，默认不 re-curate）。实现：`travelogue/layout_engine/mosaic/ltn_weekly.py` |
| **R-E3** | 分轨表产品化 | curated / archive / quick-share 写入 `config.yaml.example` + §11.1（权威：`mosaic_track.py`） |
| **R-E4** | Asymmetric quota（可选） | max 不变；opportunity 维度可观测；**无合法窗不强制 emit**。**已落地**：`asymmetric_quota.py` + planner soft min/`denseOpportunitySeen`；周看板字段；`should_force_dense_emit()≡False` |

---

## 10. 版式角色表与活跃集（产品合同）

工程映射：`travelogue/layout_contract/layout_roles.py`（产品别名 ↔ `narrativeRole`；渲染 `data-layout-role`）。

| 角色 | pattern 族（示意） | 叙事职责 | 密度 |
|------|-------------------|----------|------|
| 章扉 | plate | 章界 / 找「第几天」 | 低 |
| 主语 | landscape-1 / portrait-1 | 纪念权、情绪锚点 | 低 |
| 对照 | portrait-2 | 成对人物 / 左右对照 | 低 |
| 时间线 | stack-3 / 混三 | 同场推进 | 中（须同质） |
| **高潮证据** | **mosaic-4/5/6 hero** | 同场景证据墙 | **稀** |
| 等权密格 | landscape-4 / portrait-4（仅此二） | 仅 fallback / 显式签名位 | 应↓ |
| 语义留白 | breath / L2 pause | 换气 | 稀 |

### 10.1 MCS 活跃集 11（D8 拍板）

| 组 | patternId | 动作 |
|----|-----------|------|
| 3 槽 | portrait-3 / landscape-3 / portrait-1-landscape-2 | 保（parity / 显式路径） |
| 4 槽 | portrait-2-landscape-2 / portrait-4 / landscape-4 / **mosaic-4-hero-70-sidebar** | 保 ×3 + **新增转 GA** |
| 5 槽 | main-portrait-3land / hero-3-2-plus-4 | 保 |
| 6 槽 | main-hero-plus-4 / main-hero-plus-5 | 保（hero 型） |
| **剪除** | ~~portrait-6~~ / ~~landscape-6~~ / ~~portrait-9~~ / ~~landscape-9~~ / ~~grid-8~~ | 剪（同 PR 删 `R_GRID9_LAND`、重录 golden） |
| 余量 | 1 空位 | 留给盲评过线的新版面 |

> **v1.2 口径修正（E4）**：上表只覆盖 `lte_policy` 名单；实证显示 `template_contract` extras（`mosaic-4-1l3p-rail`、`mosaic-5-2p3l-rail` 等 rail 族）是**现网真实胜出者**。C3 剪枝 PR 须同步盘点 contract 解锁面，「活跃集 ≤12」按 **policy ∪ contract** 并集统计与门禁（H8 对账范围含 contract extras）。

---

## 11. 分轨策略（Curated / Archive / Quick）

| 轨道 | 条件（示意） | dense max | MCS | size=3 aux | hero 期望 |
|------|--------------|-----------|-----|------------|-----------|
| **Curated** | kept&lt;80 或强精选心智 | 0–2（机会型） | 开；flat dense 降权 | 默认关或极严 | 1–2 合法 hero |
| **Archive** | kept≥100 | P21 现表 | 开；burst 5→4→6 | 仅显式路径 | 3–5 高质量 |
| **Quick share** | 快速分享意图 | 低 | 可降级 | 允许安全三叠 | 可不拼 |

> 分轨是**参数与策略**差异，优先共用 MCS 代码路径。

### 11.1 运行时参数表（R-C7 · v1.2.9）

权威实现：`travelogue/layout_contract/mosaic_track.py`（curate 时叠在 `MosaicConfig` 上）。

| track | 解析条件 | `dense_collage_max` 额外上限 | `min_candidate_score` | `beat_profile` | `enable_size3_aux` |
|-------|----------|-------------------------------|------------------------|----------------|--------------------|
| curated | `intent.mode≠quick_share` 且 kept&lt;100 | **2** | 0.35 | classic_magazine | false |
| archive | kept≥100（且非 quick_share） | 无（沿用 P21） | 0.35 | classic_magazine | false |
| quick_share | `intent.mode=quick_share` | **1** | 0.40 | flat | false |

`enable_size3_aux=true` 时仅追加 size=3 为 MCS 末档（默认全轨关闭，守 C1）。

---

## 12. 指标与周看板

只读聚合入口：`compute_ltn_weekly_metrics` → `scripts/ltn_weekly_dashboard.py`（输出 `.cache/ltn-weekly/report.json`）。

| 指标 | 定义 | 健康方向 |
|------|------|----------|
| `silent_ship_count` | 静默丢失样式/错误 config 上线次数（CI/过程指标；周看板脚本不产出） | → 0 |
| `hero_mosaic_count` | 含 main/hero 角色的 dense 屏 | curated 1–2；archive 3–5 / 百张 |
| `portrait3_after_failed_mcs5_rate` | MCS 5 失败后立刻三叠占比（看板为 MVP 代理；门禁用 AC-C-01 隔离重放口径） | ↓≥50% |
| `cross_scene_window_rate` | 跨 scene MCS 窗占比（日志无 flag 时记 0；C4 构造本即段内） | &lt;5% |
| `dense_quota_utilization` | used/max（P21 + 分轨 cap） | 健康带约 0.4–0.8（非 0 非 1 硬凑） |
| `dense_opportunity_min` / `seen` / `fill_rate` | E4 soft 机会维（相对 max）；`denseForcedEmit` 恒 false | fill 观察用；无合法窗不得硬凑 |
| `preserve_group_honor_rate` | longshot 尊重 mosaic 组 | → 高 |
| `studio_reject_explain_rate` | 有 Top3 解释的决策占比 | → 100%（有决策时） |
| `windowSizeDistribution` | 胜出 plan 窗宽直方图 | 观察 4/5/6 结构 |
| `mosaic5ExposureRate` / `mcsUnifiedExposureRate` | 内容屏曝光率 | 见既有 MCS 健康带 |

---

## 13. 风险与缓解

| 风险 | 缓解 |
|------|------|
| 解耦 3 槽后奇数图「挂住」 | parity / tiler 显式路径保留；单测覆盖 |
| hero SKU 进活跃后 clutter 反弹 | P21 max + 相邻禁 + flat 降权；盲评门槛 |
| `preserveGroup` 使长图过长 | 双预览诚实展示；允许显式 `false` + 文案提示 |
| 节奏加大导致「空洞」 | JND 小样；宁小勿大；暂停≠空屏堆砌 |
| 与 HGM 抢节奏资源 | HGM 后置；本 PRD 验收为闸门 |

---

## 14. 推出与回滚

| 项 | 说明 |
|----|------|
| 特性开关 | 建议：`layout.trust_narrative.*` 或分项 flag（fallback 解耦 / hero_first 降权 / preserve_group / beat） |
| Dogfood | 固定 curated demo + 至少一本 archive dump；Type-A/B 附件 |
| 回滚 | 单 flag 回滚优先于整包；P21 行为保持可独立关闭（既有） |
| 合并纪律 | Wave A 门禁未绿，B/C 体验 PR **不得**以「先合并再补门禁」上岸 |

---

## 15. 与 HGM / P21 / LRG 的边界

| 文档 | 关系 |
|------|------|
| **P21** | 本 PRD **保留** dense 上限与相邻禁令；**不**放宽 max；修正「进不了管道」 |
| **LRG** | Wave A **闭合**其 fail-loud / dogfood 缺口 |
| **HGM** | **消费**本 PRD 的可信基线与节奏；本阶段不实现完整轻布展 |
| **MCS / LTE** | 改策略与活跃族、fallback；冻结扩库 |

---

## 16. 实施任务索引（与 backlog 对齐）

详见 [layout-next-sprint-backlog-2026-07-20.md](./acceptance-records/layout-next-sprint-backlog-2026-07-20.md) 与 [ltn-template-slot-summit-2026-07-20.md](./acceptance-records/ltn-template-slot-summit-2026-07-20.md)。

| Wave | 任务 ID |
|------|---------|
| A | A1–A4 + **H8 / H9** |
| 前置 | **H1**（schema 演进）/ **H2**（日志保留）/ **H3**（codegen 同步）/ **H6**（评分暗礁）/ **H7**（几何审计） |
| B | B1–B3（+ R-B4）；B3 提前、B2 独立排期 |
| C | C1–C3 → C5；C6 并行；C4 简化版可降级 |
| D | D1–D3（D2 可先行） |
| E | E1–E4 |

---

## 17. 变更记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.2.17-LTN | 2026-07-20 | Dogfood AC：B-02/D-02/D-03 机器可复跑（fixture+脚本）；D-01 人评清单；验收记录入库 |
| v1.2.16-LTN | 2026-07-20 | 实施落地：E1 第一步 — active_set SSOT、LEGACY 派生自 codegen、rollout.zeroSince 生命周期进 H8 gate |
| v1.2.15-LTN | 2026-07-20 | 实施落地：E4 asymmetric quota（hard max + soft opportunity；无合法窗不强制 emit；看板字段） |
| v1.2.14-LTN | 2026-07-20 | 实施落地：D3 版式角色表（产品别名↔narrativeRole、渲染 data-*）+ `rhythmSignOff` CSS 漂移闸门 |
| v1.2.13-LTN | 2026-07-20 | 实施落地：E2 周看板（`ltn_weekly.py` + `ltn_weekly_dashboard.py`）；E3 分轨说明补齐 `config.yaml.example` |
| v1.0.0-LTN | 2026-07-20 | 首版：依据八方评审与已拍板 backlog，专项解决可信 / 三模式 / 拼图出场 / 节奏 |
| v1.1.0-LTN | 2026-07-20 | 并入开发可实现性评审（F1–F6 勘误、工期修正、H 系列前置）与七方峰会决议（D8–D12、S1–S6、活跃集 11、节奏值带、longshot 三级降级、AC 防钻空口径） |
| v1.2.0-LTN | 2026-07-20 | 并入 4 trip debug 重放实证基线（§1.7 E 系列）：demo-65 改阴性对照、C4/C5 主信号改 takenAt、活跃集口径扩 contract extras、H2 增胜出 plan 标记、R-A2 增双通道排查 |
| v1.2.12-LTN | 2026-07-20 | 实施落地：D1 三级节奏 token + `rhythmGap` hint；D2 资产真进度 + classic_magazine 峰位 0.55–0.70 |
| v1.2.11-LTN | 2026-07-20 | 实施落地：B2 longshot 尊重 preserveGroup（三级降级）+ B4 present 纳入 chapter-separator |
| v1.2.10-LTN | 2026-07-20 | 实施落地：B1 Narrative Contract — [ADR-020](./adr/020-narrative-contract.md)、schema 五字段、`ensure_narrative_contract`、修订 ADR-003 长图默认展平 |
| v1.2.9-LTN | 2026-07-20 | 实施落地：C7 分轨参数表（curated/archive/quick_share）；C8 槽位软惩罚 + AR/副槽短边闸门（面积比软罚以免误杀 3land） |
| v1.2.8-LTN | 2026-07-20 | C4 补齐：签名路由叠在模板合约之上（TC∩signature；命中写 signature，未命中保留 exact/fallback） |
| v1.2.7-LTN | 2026-07-20 | 实施落地：C4 简化粗分段（takenAt/city 切分 + 跨段截窗）与签名路由（signature / signature_fallback） |
| v1.2.6-LTN | 2026-07-20 | 实施落地：B3 导出前双预览 MVP（同宽 428 iframe 网页 vs 长图） |
| v1.2.5-LTN | 2026-07-20 | 实施落地：C6 Studio「为何没拼」— mosaicExplain API + chapter-layout + 预览抽屉 |
| v1.2.4-LTN | 2026-07-20 | 补齐遗漏：C1 单图救场+mcs_all_sizes_failed；C3 hero-gap prior/wasted_hero；H8 golden+contract 并集；C5 占位 release；AC-C-02/07 缺测 |
| v1.2.3-LTN | 2026-07-20 | 实施落地：C5 hero_reserve 状态机（armed 等权 dense 让位；章尽 unused→released） |
| v1.2.2-LTN | 2026-07-20 | 实施落地：H2 window 保留 rejected Top3；metrics 读 raw；beam 暂停 capture；isWinnerPlan 标注 |
| v1.2.1-LTN | 2026-07-20 | 实施落地：H7 几何审计 + 4-hero AR 校正；H9 合成 fixture；C1 解耦 MCS aux-3；C3 活跃集 11（剪 6/8/9 平铺 + 4-hero GA） |
