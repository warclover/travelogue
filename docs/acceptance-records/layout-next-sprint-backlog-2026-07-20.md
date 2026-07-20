# 排版 / 拼图下一阶段任务清单（供审核）· 2026-07-20

| 属性 | 内容 |
|------|------|
| **依据** | [layout-mosaic-multi-persona-review-2026-07-20.md](./layout-mosaic-multi-persona-review-2026-07-20.md)（八方） |
| **关联** | HGM 单独轨；本清单假定 **排版可信是 HGM 前置** |
| **状态** | **已拍板 · 正式 PRD：** [PRD-LAYOUT-TRUST-NARRATIVE-V1.md](../PRD-LAYOUT-TRUST-NARRATIVE-V1.md) |
| **纪律** | **冻结扩库**（新 patternId / 槽数&gt;6 → NO）直至盲评过线 |

---

## 0. 战略结论（技术对齐）

| 判断 | 含义 |
|------|------|
| 问题不是「模板不够」 | 语法骨架可用；债在可信、节奏、拼图出场、三模式合同 |
| 拼图≈0 ≠ P21 过狠 | 主因：3 槽 legacy 兜底、进窗抢占、几何/SKU 硬门；配额未消耗 |
| 先工程可信，再体验惊喜 | fail-loud 不做，节奏/拼图修了也会「修好又弄丢」 |
| HGM 不插队 | 选型与呈现依赖可信基线；本阶段不排 HGM 实现 |

---

## 1. 优先解决的问题（按影响排序）

| ID | 问题 | 用户可感症状 | 根因层 | 不修的后果 |
|----|------|--------------|--------|------------|
| **Q1** | 静默失败 / 修好又弄丢 | 调了样式或配置，成品无感或回退 | 管线 fail-open（CSS truncate、config silent default、门禁 FAIL 仍可 merge） | 一切体验优化不可复现 |
| **Q2** | 三模式语义分裂 | 网页满意、微信长图「不是同一部作品」 | 缺 Narrative Contract；longshot 拆 slot | 分享链路信任崩 |
| **Q3** | 拼图该出不出（hero≈0） | 精选像「只敢单图/三叠」 | MCS→size=3 legacy；hero_first 关 MCS；4 槽无 hero SKU | 差异化资产名存实亡 |
| **Q4** | 节奏扁平 | 屏缝黏、章内不可扫视 | breath≈9px；无语义气口；beat 默认 flat | 「自动排版感」压过杂志感 |
| **Q5** | 拼图黑箱 | Studio 不知为何拼/没拼 | 日志有、产品未消费 | 无法调参、无法信任 |

**刻意后置**：扩 7+/8/9 SKU、放宽 P21 max、全书换肤式 HGM、凝视模式。

---

## 2. 需要优化的功能（能力地图）

| 能力 | 现状 | 目标态（本阶段） |
|------|------|------------------|
| Fail-loud 门禁 | LRG/MCR 未闭合 | 违规阻断 merge / 发布；错误可见 |
| 三模式合同 | 各表面各自 reinterpret | `screens[]` + `preserveGroup` / `exportHints`；双预览 |
| MCS 进窗与 fallback | 失败→三叠假拼图 | 解耦 size=3 aux；合法 hero 窗禁止 silent legacy |
| Density / 分轨 | 一套参数伤精选 | curated / archive 分 limits；hero_first=降权非关管 |
| Hero SKU 曝光 | 活跃 4 槽无 main | 4/5 hero 进活跃族；活跃集 ≤12 |
| 节奏 | CSS 级缝隙 | L0/L1/L2 token；语义 pause 与屏缝分离 |
| 可解释性 | mosaicDecisionLog 沉底 | Studio「为何拼/为何没拼」Top3 |

---

## 3. 任务清单（建议波次）

### Wave A · P0 可信基线（建议 1–2 周，阻塞一切体验债）

| 任务 | 负责侧重 | 交付物 | 验收 |
|------|----------|--------|------|
| **A1** 闭合 LRG required check | 管线 | CI/门禁：截断/缺样式 → FAIL | dogfood Type-A 附件必过 |
| **A2** MCR + config fail-loud | 管线 | silent wrong default → 显式错误/诊断 | curate 日志可定位错误 intent |
| **A3** 冻结扩库纪律落地 | 全员 | PR 检查清单 / merge 决策树 | 新 patternId / 槽&gt;6 默认拒 |
| **A4** demo 诊断基线固化 | 算法+产品 | 对 `demo-65db8fd377` 聚合 `fallbackReason` / `rejected_templates` | 周看板起点可复跑 |

**收益**：止住「修好又弄丢」；后续 A/B 可归因。  
**风险若不做**：B/C 波次全部不可靠。

---

### Wave B · P0/P1 三模式不撒谎（建议与 A 尾部重叠，1.5–2 周）

| 任务 | 负责侧重 | 交付物 | 验收 |
|------|----------|--------|------|
| **B1** Narrative Contract ADR（字段最小集） | 架构 | `narrativeRole` / `groupId` / `preserveGroup` / `exportHints` / `representativeAssetId` | ADR 评审通过 |
| **B2** longshot 组策略（默认不 implicit flatten mosaic） | 架构+渲染 | 导出路径尊重 `preserveGroup` | 同 trip：scroll 拼图组在 longshot 仍可辨「一组」 |
| **B3** Studio / 导出前双预览（网页 vs 微信长图） | 产品+前端 | 并排或一键切换预览 | 家庭/摄影角色可说清差异 |

**收益**：分享链路信任；拼图叙事不在导出层归零。  
**依赖**：B1 先于 B2；B3 可先做「诚实预览」再接完整合同。

---

### Wave C · P1 拼图「该出时出」（建议 2–3 周，勿先松 P21）

| 任务 | 负责侧重 | 交付物 | 验收 |
|------|----------|--------|------|
| **C1** 解耦 MCS 失败 → size=3 legacy | 算法 | 4/5/6 全失败：优先单图 hero / 降窗宽；3 槽仅 parity/tiler | `portrait3_after_failed_mcs5_rate` ↓≥50% |
| **C2** `hero_first`：关 MCS → 降权 flat dense | 算法 | 精选集仍可尝试 hero 族 | curated demo：`mosaicWindowDecisions`&gt;0 且含 main |
| **C3** Hero SKU 进活跃 4/5 窗族 | 算法+LTE | `screen-mosaic-4-hero-*` 等进 `MOSAIC_*_PATTERN_IDS`（活跃≤12） | 含 `main` 角色屏占比可测 |
| **C4** Burst 预分段（禁跨 scene 滑窗） | 算法 | MCS 前按 burst/地点切窗 | `cross_scene_window_rate` &lt;5% |
| **C5** 机会下限 / 章级 reserve（非 KPI） | 算法 | 合法 hero 窗失败则释放；**禁止** 3 槽凑数 | 合法机会 used=0 → 告警；非法不强制 emit |
| **C6** Studio 可解释 reject Top3 | 产品+前端 | 消费 `mosaicDecisionLog` | 用户可见「为何没拼」 |

**收益**：hero mosaic 从≈0 回到「稀疏惊喜」；P21 上限哲学保留。  
**红线**：不为凑数放宽 main_ar / 跨场景硬拼；不把 landscape-4 等权当 hero。

**建议实现序**：C1 → C2 → C3 → C4 → C5；C6 可与 C1 并行。

---

### Wave D · P1 节奏可读（可与 C 并行轻量启动，1–2 周）

| 任务 | 负责侧重 | 交付物 | 验收 |
|------|----------|--------|------|
| **D1** 三级节奏 token（槽缝 / 屏缝 / 语义 pause） | 设计+渲染 | CSS/token 规范；pause ≠ 多塞 breath 屏 | 盲评节奏分 5.5→≥7（小样本） |
| **D2** 默认 beat profile + 真实章进度 | 算法 | 非 flat；progress 不用启发式糊弄 | hero mosaic 中章占比 ≥60%（有样本时） |
| **D3** 版式角色表写进产品/渲染注释 | 设计+产品 | plate / 1col / stack-3 / 2col / mosaic-hero / breath | 评审用语统一 |

**收益**：章内可扫视；「黏」感下降。  
**注意**：D1 禁纯 CSS 补丁式永久方案；中期应由 planner 产出 rhythm hint（架构 P2）。

---

### Wave E · P2 收敛与可观测（持续）

| 任务 | 负责侧重 | 交付物 | 验收 |
|------|----------|--------|------|
| **E1** LTE 单权威收束 | 架构 | 减少 planner 硬编码 / legacy_bridge 三写 | 活跃 pattern 唯一清单 |
| **E2** 周看板 | 管线 | 窗宽分布、mosaic 曝光、burstPass、screenCount parity、scroll↔longshot 守恒 | 每周一页 |
| **E3** curated / archive / quick-share 分轨表 | 产品+算法 | limits + 是否 size=3 aux + beat | 精选 demo 策略文档化 |
| **E4** asymmetric quota（可选） | 算法 | max 不变；opportunity min 不强制凑 | utilization 0.4–0.8 健康带 |

---

## 4. 优化收益分析

### 4.1 按波次（投入 vs 收益）

| 波次 | 相对投入 | 用户可感收益 | 工程收益 | 建议 |
|------|----------|--------------|----------|------|
| **A 可信** | 中 | 间接（稳定） | **极高**：止损、可归因 | **必做 / 最先** |
| **B 三模式** | 中高 | **极高**（发群/导出） | 高：合同清晰 | **必做 / 紧随 A** |
| **C 拼图出场** | 高 | **高**（差异化回归） | 高：目标函数纠偏 | **必做 / 勿先松 P21** |
| **D 节奏** | 中 | **高**（杂志感） | 中 | 与 C 并行轻量；忌单独堆 CSS |
| **E 收敛** | 持续低 | 低直接 | 高：降运维债 | 跟进，不阻塞 A–C |
| ~~扩 SKU~~ | 高 | 低/负 | 负 | **本阶段不做** |
| ~~HGM 完整~~ | 高 | 条件收益 | 依赖选型 | **排版可信后再开** |

### 4.2 收益假设（审核用目标，非承诺 KPI）

| 指标 | 现状（demo 体感） | Wave A–C 后目标 |
|------|-------------------|-----------------|
| 样式/配置静默丢失 | 偶发「修好又弄丢」 | 门禁阻断；0 silent ship |
| hero mosaic（含 main） | ≈0 | curated：机会合法时 **1–2**；百张 archive：**3–5** 高质量 |
| MCS 失败→portrait-3 率 | 高 | 相对基线 ↓≥50% |
| 长图仍可辨「一组」 | 常拆散 | mosaic `preserveGroup` 默认遵守 |
| 盲评节奏 | ~5.5 | ≥7（小样本） |
| Studio 可解释 | 无 | reject Top3 可见 |

### 4.3 依赖与并行

```text
A1–A3 ──┬──► B1 → B2 → B3
        │
        └──► C1 → C2 → C3 → C4 → C5
                    │
                    └── C6（可并行）
        │
        └──► D1（设计定标）→ D2
                    │
E2 看板贯穿全程；E1/E3 在 C 稳定后加速
```

---

## 5. 明确不做 / 暂缓（本阶段）

| 项 | 原因 |
|----|------|
| 新增多槽 SKU（7+/8/9、第二套 full-bleed） | 评审一致：扩库增债、不治根因 |
| 放宽 P21 `dense_collage_max` | used≈0 时无效；先修进窗 |
| trip 级强制 `min_dense` | 会硬凑，伤杂志感 |
| HGM 完整轻布展 / 凝视模式 | 选型与可信基线前置未满足 |
| 三模式像素级统一 | 错误目标；应对齐语义合同 |

---

## 6. 拍板结果（2026-07-20）

| # | 议题 | 结论 |
|---|------|------|
| 1 | Wave 顺序 | **同意** A→B→C→D；HGM 后置 |
| 2 | C1 解耦 3 槽 | **同意** 作为拼图第一刀 |
| 3 | hero_first 降权 | **同意**；精选 1–2 次合法 hero |
| 4 | preserveGroup | **默认保持组感** |
| 5 | 机会下限 | **同意**章级 reserve；拒产量 KPI |
| 6 | 节奏 D1 | **与 C 并行轻量定标** |
| 7 | 正式背书 | **已落成 PRD-LAYOUT-TRUST-NARRATIVE-V1** |

---

## 7. 变更

| 日期 | 说明 |
|------|------|
| 2026-07-20 | 初稿：项目负责人视角任务清单 + 收益分析，供审核 |
| 2026-07-20 | 拍板通过；指向正式 PRD LTN v1.0 |
