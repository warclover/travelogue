# Travelogue · 拼图模板选型与使用优化 V1 产品需求文档（PRD）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue Studio |
| **文档版本** | **v0.2.0** |
| **状态** | **Conditional Go · Must-Fix 已回写**（[七席评审](./acceptance-records/mtso-mosaic-template-selection-v1-review-2026-07-23.md) · **可 Kickoff M1 / PR-A**；M2 合码前关 BLK-03～06） |
| **DOC-STATUS** | **active** |
| **主题代号** | 「拼图模板选型与使用优化 V1」— **MTSO** |
| **调研来源** | 2026-07-23 实机手测反馈 + MCS/LTE/P21/TPC 代码探查 + 七席联评 |
| **审查基线** | 本机 `config.yaml`（含 `template_contract.enabled=true` 狗粮残留）+ 仓库默认 MCS-11 + `lte_policy.yaml` |
| **关联文档** | [P15 MCS](./PRD-PHASE15-photo-mosaic-evolution.md) · [P16 LTE](./PRD-PHASE16-layout-template-engine.md) · [P21 密度预算](./PRD-PHASE21-mosaic-density-budget.md) · [TPC](./PRD-TEMPLATE-CONTRACT-V1.md) · [LTN 峰会](./acceptance-records/ltn-template-slot-summit-2026-07-20.md) · [6 张拼图](./PRD-6张拼图优化.md) · [MGQ](./PRD-MCS-GEOMETRIC-QUALITY-V1.md) · [URO](./PRD-USAGE-RULES-LAYOUT-OPTIMIZATION.md) |
| **验收** | 本文 §9；**M1 暂用本节**；**M2 合码前**补 `ACCEPTANCE-…` + `IMPLEMENTATION-…`（BLK-08） |
| **实施清单** | [IMPLEMENTATION-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1.md](./IMPLEMENTATION-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1.md) **v0.1.0** · Ready for PR-A |
| **评审纪要** | [acceptance-records/mtso-mosaic-template-selection-v1-review-2026-07-23.md](./acceptance-records/mtso-mosaic-template-selection-v1-review-2026-07-23.md)（结案）· [模板](./acceptance-records/mtso-mosaic-template-selection-v1-review-TEMPLATE.md) |
| **实施前调研** | [acceptance-records/mtso-dev-feasibility-2026-07-23.md](./acceptance-records/mtso-dev-feasibility-2026-07-23.md)（SUP 默认已认可 · 2026-07-23） |
| **更新日期** | 2026-07-23 |

> **v0.2.0 相对 v0.1.0（七席回写 · 2026-07-23）**
>
> 1. **资格两段论**：`structurallyQualifiedSix`（段/定向/ordering/gap）与 `admitSixHero`（dense/相邻/机会）分离，消除循环定义。  
> 2. **机会作用域**：armed 仅挡**同 cursor** 抢占该 6 窗的 size4/5，不章内永久禁四宫。  
> 3. **AC-11 双阈值**：有配额时尝试率 ≥0.80 + 转化率相对基线提升；删「显著」模糊词。  
> 4. **孪生六图 canonical**：对外权威 `screen-mosaic-6-main-hero-plus-5`；`…-5-main-hero-plus-4` 为历史孪生，配额/家族去重。  
> 5. **嵌套开关**：`selection_optimization.enabled=false` 时子开关全部无效。  
> 6. **O-2/O-3/O-4 关闭**；O-1 保持开放至 PR-C 几何稿。  
> 7. **M1 可 Kickoff**；M2 合码挡 BLK-03～06。

> **定位**
>
> 现网拼图算法已达到「及格」：活跃集收敛、几何门禁、P21 密度预算能压住明显翻车。但手测暴露三类系统性缺陷——混向叙事弱、六图 hero 被调度饿死、实验模板经 TPC 开关意外复活——使游记拼图停在「整齐」而难到「优秀」。
>
> 本 PRD **不扩库堆模板**，而是在 MCS-11 + 1 空位上，把**选对模板、给合格版式真实机会、隔离实验生命周期**做成可测合同。

> **一句话目标**：**混向有主次；合格六图 hero 能上场；experimental 不再借 TPC 偷跑；每个「没选中」都可解释。**

> **完成定义**
>
> | 门 | 含义 | 不等于 |
> |----|------|--------|
> | **M1 Go** | 生命周期隔离 + 六图漏斗日志 + 合成 fixture 基线 | 新模板转 GA |
> | **M2 Go** | 两段资格 + 机会保护 + 1P4L 双分支 + 2P3L 主从（experimental） | 放宽 P21 dense 上限 |
> | **M3 Go** | 狗粮/盲评通过 → 转正或归档；acceptance-records 闭环 | 「六图更多」KPI |

---

## 0. 读者指南与边界

### 0.1 与相邻主题

| 主题 | 关系 | 本主题做什么 |
|------|------|--------------|
| [P21](./PRD-PHASE21-mosaic-density-budget.md) | **继承硬上限** | 不放宽 `dense_collage_max`、相邻 dense 禁令、`max_mosaic_slots=6`；只修正「合格六图被 4/5 抢死」 |
| [TPC](./PRD-TEMPLATE-CONTRACT-V1.md) | **合同求值权威** | TPC 只管 mix/eligibility；**不再**因 `enabled=true` 解锁全部 experimental |
| [LTN 峰会](./acceptance-records/ltn-template-slot-summit-2026-07-20.md) | **活跃集 11+1** | 空位专用于有主次的 2P3L 继任；不恢复等权平铺 |
| [P15/P16](./PRD-PHASE15-photo-mosaic-evolution.md) | MCS/LTE 骨架 | 候选·打分·YAML SSOT 不变；补选型策略与生命周期门 |
| [6 张拼图](./PRD-6张拼图优化.md) | 主图 AR 红线 | 保留 `main_ar_guard`；不为曝光放松 AR/face/near-scene |
| [URO](./PRD-USAGE-RULES-LAYOUT-OPTIMIZATION.md) | usage 语义 | 把 YAML `whenNotToUse` 升为可测拒选（至少 1P4L 竖强） |
| [QFX](./PRD-QUALITY-FIXPACK-V1.md) | **正交** | 日更合入/NAS/导出事务；**本主题不碰** |

### 0.2 代码事实（2026-07-23 探查 · 不可重议）

| ID | 事实 |
|----|------|
| **F-01** | 仓库 YAML ≈30；MCS 默认活跃 **11**（`lte_policy.yaml`）；8/9 平铺与旧 2P3L equal 为 deprecated |
| **F-02** | `2p3l-equal` deprecated → `mosaic_pattern_disabled=True`；同拓扑 `2p3l-rail` 为 experimental/`rollout=0` |
| **F-03** | `_contract_unlocks_experimental()`：`template_contract.enabled=true` 时 **放行全部** experimental+percent=0 → 本机 registry 膨胀到 21；trips 可见 `2p3l-rail` / `1l3p-rail` |
| **F-04** | 「主图+右二+底三」= `screen-mosaic-5-main-hero-plus-4` / `…-6-main-hero-plus-5`（几何孪生、**photoCount=6**、均 ga）；本地 trips HTML **曝光 0** |
| **F-05** | `window_order=(5,4,6)`；全横且 remaining≠6 时 size5 失败 → **size4（landscape-4）先胜** → size6 永不尝试（合成仿真已复现） |
| **F-06** | `large_mosaic_min_slots=5` + 每章 1 次：任意 5 槽 mosaic 吃掉六图章配额 |
| **F-07** | 小册 dense 上限 ≈1；`landscape-4` 计 dense；先发四宫即可锁死后续六图 |
| **F-08** | `main-portrait-3land` 结构是 **横主 2×2 + 右竖辅 + 底三横**；YAML 已写「竖最强时勿用」，评分侧未等同强硬 |
| **F-09** | 粗分段 `seg_cap<6` 禁止凑六图跨段（正确）；须记为「无机会」而非「选版失败」 |
| **F-10** | `main-hero-plus-4` 与 `main-hero-plus-5` 几何孪生、双进 MCS-6（评审新增） |
| **F-11** | `SIGNATURE_WHITELIST` 无 `(0,6,*)`；现靠 fallback 全集（评审新增） |
| **F-12** | `legacy` 可构造 deprecated 6/8/9，append 靠 `mosaic_pattern_disabled` 挡（评审新增） |

### 0.3 用户可感知问题 → 落点

| 审查 ID | 问题 | 严重度 | 落点 |
|---------|------|--------|------|
| **Q1** | 混向「及格不优秀」；竖强仍塞横主竖辅 | **P0** | §4 D-03 · S-MTSO-02 |
| **Q2** | 「两竖三横」以为退役仍常见 | **P0** | §4 D-01 · S-MTSO-01（实为 `2p3l-rail`） |
| **Q3** | 六图 hero（主+右二+底三）消失 | **P0** | §4 D-05/D-07 · S-MTSO-03 |
| **Q4** | 无有主次的 2P3L 继任 | **P1** | §4 D-02/D-04 · S-MTSO-04 |
| **Q5** | 拒因不可解释 / 曝光归零难归因 | **P1** | §4 D-11 · S-MTSO-05 |
| **Q6** | deprecated 旁路仍可构造（靠门禁挡） | **P2** | §4 D-01 · AC 负例 |

---

## 1. 背景与及格线诊断

### 1.1 为什么现在是「及格」

| 能力 | 作用 |
|------|------|
| MCS 统一候选打分 | 几何非法、主 AR、脸裁切有门禁 |
| P21 密度预算 | 抑制「整章全是拼盘」 |
| 活跃集剪到 11 | 去掉易裁脸的 6/8/9 平铺噪声 |
| LTE YAML + usage 文案 | 模板意图可文档化 |

### 1.2 为什么到不了「优秀」

```text
素材结构 → 窗宽贪心(5→4→6) → 配额/分段 → 签名缩窄 → 合同/打分 → 落屏
                 ↑ 全横被 4 饿死六图
                 ↑ 5 槽吃掉 large 章配额
混向唯一强 SKU = 横主竖辅 → 竖强时叙事错误
TPC ON = 实验族整批进 registry → 与「退役」产品叙事冲突
```

**产品判断**：继续微调 `base_weight` **不能**修复结构性饿死与生命周期泄漏；必须改**调度合同 + 生命周期隔离 + 混向主次 SKU**。

---

## 2. 目标与非目标

### 2.1 目标

| ID | 目标 | 衡量 |
|----|------|------|
| **G-01** | 实验/退役生命周期与生产候选解耦 | TPC ON 且实验开关 OFF → experimental 曝光 **0**；deprecated **永远 0** |
| **G-02** | 合格六图 hero 获得真实尝试 | 资格窗漏斗：`qualified → attempted → won` 可测；本地基线从 0 提升机会转化率 |
| **G-03** | 1P4L 按「谁是主角」分支 | 强竖 fixture **不**落 `main-portrait-3land`；横强可继续落 |
| **G-04** | 2P3L 有主次继任（非等权双竖） | 新模板主槽面积 ≥0.55、主从 ≥3:1；狗粮通过后才占活跃集空位 |
| **G-05** | 拒选可解释 | 每窗可归为：未尝试 / 分段 / 配额 / 资格不足 / 合同 / 评分落败 / 胜出 |
| **G-06** | 不破坏 P21「少而精」 | dense 总额、相邻禁令、跨段限制 **零放宽** |

### 2.2 非目标

| ID | 非目标 |
|----|--------|
| **NG-01** | 不提高卷级 `dense_collage_max`、不取消相邻 dense 禁令 |
| **NG-02** | 不恢复 `2p3l-equal` / 6·8·9 等权平铺为 GA |
| **NG-03** | 不以「六图屏数」为成功 KPI（防强塞） |
| **NG-04** | 不重开 MSR 有序签名体系；轻路由仅缩窄合同候选 |
| **NG-05** | 不做用户手动选模板 UI |
| **NG-06** | 不改 LSE/Hungarian/选片子集/叙事；不 runtime 改 `slots[].rect` |
| **NG-07** | 不纳入 QFX / NAS / 导出事务 |

---

## 3. 术语

| 术语 | 定义 |
|------|------|
| **MCS-11** | 现网默认统一候选集（3×3 + 4×4 + 5×2 + 6×2） |
| **六图 hero 家族** | 几何孪生：`screen-mosaic-6-main-hero-plus-5`（**canonical**）与 `screen-mosaic-5-main-hero-plus-4`（历史孪生）；主 2×2 + 右 2 + 底 3；配额/机会按家族去重 |
| **结构合格六图（structurallyQualifiedSix）** | 同粗分段连续 6 张：全横或 ≤1 竖；`_order_hero_six`（含 main_ar）成功；hero gap ≥ 阈值。**不含** dense/配额判断 |
| **可接纳六图（admitSixHero）** | 在结构合格之上：dense/相邻/track 允许再发一张 dense，且机会状态允许尝试 |
| **横主竖辅 1P4L** | 现役 `screen-mosaic-5-main-portrait-3land` |
| **竖主横辅 1P4L** | 本案新增（或强竖单图 rescue）分支 |
| **2P3L 主从继任** | 一竖为 main、次竖为辅、三横为细节带；**禁止**两满高竖栏等权 |
| **实验狗粮开关** | `mosaic.template_experiments.*`；与 TPC `template_contract` **正交** |
| **六图机会（hero_six_opportunity）** | 状态机：结构合格时 **armed** → 同 cursor 禁 size4/5 抢占 → 胜出 consumed / 失效 released；**不**增加 dense 总额 |

---

## 4. 已拍板决策（七席锁定 · 2026-07-23）

| 决策 | 锁定结论 |
|------|----------|
| **D-MTSO-01 生命周期隔离** | `deprecated`：任意路径（candidate / self-heal / legacy fallback）**不可 emit**。`experimental`：**不得**因 `template_contract.enabled` 解锁；仅当 `mosaic.template_experiments.enabled=true` **且** allowlist 命中 **且** trip∈dogfood cohort 时可见。TPC 只做合同求值。 |
| **D-MTSO-02 活跃集** | 保持 **11 GA + 1 空位**。空位专用于 2P3L **主从**继任；等权 `2p3l-rail` **永不转 GA**（留 YAML + 文首标非继任；默认不进 allowlist）。 |
| **D-MTSO-03 1P4L 双分支** | 窗内唯一竖图若为最佳主图或 hero gap≥阈值 → **禁止**横主竖辅（`mixed_portrait_is_hero`）；走竖主横辅新模板，不足则 **单图 hero rescue**。仅横图具备合格 main 且竖适合窄槽时保留 `main-portrait-3land`。 |
| **D-MTSO-04 2P3L 继任几何** | **方案 A**：第一竖图为唯一 main，第二竖为辅助叙事槽，三横为细节带；主槽面积 ≥0.55，主从面积比 ≥3:1。禁止「双满高竖 + 三横等分」冒充 hero。建议 id：`screen-mosaic-5-2p3l-portrait-hero-rail`（视觉冻结前可改名）。 |
| **D-MTSO-05 窗宽序** | 默认仍 **5→4→6**（继承 P21）。仅当 cursor 上 **结构合格**且将尝试六图时，该次改为 **6→5→4**。禁止全局抬升所有六图优先级。 |
| **D-MTSO-06 重排明确性** | 日志必含 `base_window_order` / `effective_window_order` / `reorder_reason`（`structurally_qualified_six` \| `exact_tail_fit` \| `single_portrait_tail` \| …）。 |
| **D-MTSO-07 配额与机会** | **不增加** dense 总额；相邻 dense 禁令不变。`hero_six_opportunity`：结构合格 → armed → **仅同 cursor** 阻止 size4/5 抢占该 6 窗；胜出 consumed；段尽/资格失效/章结束/配额不足 → released。large 章配额对家族去重计数。 |
| **D-MTSO-08 粗分段** | **禁止**为凑六图跨段。`seg_cap<6` → 记 `six_hero_blocked:segment_cap`（无机会）。 |
| **D-MTSO-09 签名轻路由** | 扩展白名单覆盖 1P4L 双分支与 2P3L 主从；miss 或空交集 → **回落合同全集**。路由不替代 TPC。 |
| **D-MTSO-10 六图构建红线** | 保留 `_order_hero_six`：≤1 竖、≥4 横、横向 main + main_ar。补原因码：`six_hero_portrait_overflow` / `six_hero_no_main` / `six_hero_insufficient_landscape`。不放松 AR/face/near-scene。 |
| **D-MTSO-11 可观测性前置** | 原始窗口日志为挡门：须含 `structurallyQualifiedSix`、`admitSixHero`、`sixHeroOpportunityState`、窗宽序、拒因漏斗、配额快照、winner。AC **禁止**只读格式化展示日志。 |
| **D-MTSO-12 转正门槛** | 新模板先 experimental+allowlist；合成 fixture + 代表 trip compare + 盲评均过，且无 deprecated 回潮，才转 GA 占空位。不通过则归档，空位不强填。 |
| **D-MTSO-13 成功指标** | **主指标** = 转化率 `won / attempted`（仅统计 admit 后尝试）；**辅指标** = 有配额时结构合格窗的尝试率 `attempted / structurallyQualified`。**不设**全局最低六图屏数。另：混向错误落位 ≤ 基线、deprecated leak=0、dense 违规=0。 |
| **D-MTSO-14 孪生 canonical** | 对外/文档/漏斗权威 id = `screen-mosaic-6-main-hero-plus-5`；`screen-mosaic-5-main-hero-plus-4` 保留渲染与历史兼容，机会与 large 配额按**家族**去重，避免双计。 |

### 4.1 配置合同

```yaml
mosaic:
  template_contract:
    enabled: false          # 仅合同；不解锁 experimental
  template_experiments:
    enabled: false          # 显式狗粮总开关
    allowlist: []           # patternId 白名单
    cohort_trip_ids: []     # 默认空=无人可见
  selection_optimization:
    enabled: false          # 父开关；false 时下列子项全部无效
    hero_six_opportunity:
      enabled: true         # 仅父 ON 时生效
    mixed_hero_routing:
      enabled: true
    # 默认共用 layout.usage_rules.hero_gap_threshold；若设置则覆盖
    # hero_gap_threshold: 0.15
```

仓库默认：`template_experiments.enabled=false`，`selection_optimization.enabled=false`，直至 **M3 盲评后另决策**默认 on（O-2 已关）。

---

## 5. 功能规格

### 5.1 S-MTSO-01 · 生命周期单一判定

**行为**

1. 统一函数（建议 `lifecycle_admit(pattern_id, cfg, trip_id) -> AdmitResult`）覆盖：`mosaic_registry`、`mosaic_pattern_disabled`、legacy `append`、self-heal。
2. 删除/改写「TPC ON ⇒ experimental 可见」耦合；TPC 路径只过滤合同匹配。
3. LTE OFF 硬禁列表补齐历史缺口（至少含 `2p3l-equal`），与 YAML deprecated 对齐。

**拒因码（稳定）**：`lifecycle_deprecated` · `lifecycle_experimental_gated` · `lifecycle_allowlist_miss` · `lifecycle_cohort_miss`

### 5.2 S-MTSO-02 · 1P4L 主角判定

**输入**：窗内 1 竖 + ≥4 横（或签名 (1,4,*)）。

**规则**

| 条件 | 动作 |
|------|------|
| 竖图 hero/sharp 为窗内最优，或相对最强横 gap≥阈值 | **拒** `main-portrait-3land`（`mixed_portrait_is_hero`）；候选 ∈ {竖主横辅新模板, `portrait-1` rescue, 可选 `p1-l2` 若 size3 开} |
| 横图具备 main_ar 合格且竖适合窄槽 | 允许现役横主竖辅 |
| 主横不合格 | 不硬塞 5 槽；拆窗 / 单图 |

现役 YAML `whenNotToUse` 必须与上述拒选 **同测**（URO 可复用或本主题最小硬规则）。

### 5.3 S-MTSO-03 · 六图机会保护（两段资格）

**A. 结构合格 `structurallyQualifiedSix`（全部满足）**

1. `seg_cap ≥ 6` 且 cursor 起 6 张同段  
2. 定向：全横或恰好 1 竖  
3. `_order_hero_six` 预跑成功（含 main_ar）  
4. hero gap ≥ 阈值（主图相对配图；默认 `usage_rules.hero_gap_threshold`）

**B. 可接纳 `admitSixHero`（在 A 之上）**

5. 当前 `dense_collage` / 相邻 dense / track cap **允许**再发一张 dense  
6. 机会状态非「本章已 consumed 且无新结构合格窗」等冲突

**状态机**

```text
idle → armed（结构合格）→ consumed（六图家族胜出）
                ↘ released（段尽/结构失效/章结束/dense 不可用）
```

**armed 作用域（BLK-04）**：仅在**当前 cursor** 阻止 size4/size5 **抢先 emit 该 6 窗资产**；`effective_window_order=6,5,4`。  
**不**章内永久禁止 `landscape-4`（后续 cursor 若无结构合格六图，恢复默认 5→4→6）。  
**非结构合格**：保持 `5,4,6`，与今日及格线一致。

### 5.4 S-MTSO-04 · 2P3L 主从继任模板

| 项 | 要求 |
|----|------|
| mix | portrait:2 · landscape:3 · photoCount:5 |
| 几何 | 竖 main 主导面积；次竖可读；三横细节带；**无**双满高等权 |
| 合同 | eligibility / usage / siblings 齐；validator + 声明 AR vs 实渲 AR 对账 |
| 生命周期 | 先 experimental + allowlist；M3 转 GA 才写入 `MOSAIC_5_PATTERN_IDS` |
| 禁令 | 不得把 `2p3l-rail` 改 ga 充数 |

### 5.5 S-MTSO-05 · 可观测漏斗

每窗原始字段（最低集）：

| 字段 | 含义 |
|------|------|
| `baseWindowOrder` / `effectiveWindowOrder` / `reorderReason` | 窗宽策略 |
| `structurallyQualifiedSix` / `admitSixHero` | 两段资格 bool |
| `sixHeroOpportunityState` | idle/armed/consumed/released |
| `sixHeroFamilyId` | canonical 家族 id（去重用） |
| `candidateSource` | legacy_size / contract / signature / signature_fallback |
| `rejectFunnel[]` | `{stage, patternId?, reason}` 分层 |
| `quotaSnapshot` | dense_used/max · large_chapter_used/max · last_was_dense |
| `winnerPatternId` / `fallbackReason` | 结果 |

提供脚本（可扩 `layout_debt_report` / `layout_compare`）：按 trip 输出六图漏斗与混向落位表。

### 5.6 S-MTSO-06 · 签名轻路由扩展（示意）

| 签名 (nP,nL,cohesive) | 优先族 |
|----------------------|--------|
| (1,4,*) + 竖强 | 竖主横辅 / portrait-1 |
| (1,4,*) + 横强 | `main-portrait-3land` |
| (2,3,*) | 2P3L 主从继任（实验可见时） |
| (0,6,*) + 合格 | 六图 hero 孪生 |
| miss | 合同全集 |

---

## 6. 系统解法映射

| 解法 | 收口问题 | 关键决策 |
|------|----------|----------|
| **S-MTSO-01** 生命周期隔离 | Q2, Q6 | D-01 |
| **S-MTSO-02** 混向主角分支 | Q1 | D-03, D-09 |
| **S-MTSO-03** 六图机会保护 | Q3 | D-05, D-07, D-08, D-10 |
| **S-MTSO-04** 2P3L 主从 SKU | Q4 | D-02, D-04, D-12 |
| **S-MTSO-05** 漏斗可观测 | Q5 | D-06, D-11, D-13 |

---

## 7. 里程碑

| 里程碑 | 交付 | 出口标准 |
|--------|------|----------|
| **M1 · 门禁可证** | lifecycle 单一判定；六图漏斗日志；合成 fixture；本机 TPC 狗粮配置与仓库默认叙事对齐说明 | AC-01～03；TPC ON≠实验全开 |
| **M2 · 策略可用** | hero_six_opportunity；1P4L 双分支；2P3L 继任 YAML+CSS（experimental）；路由扩展 | AC-04～09；P21 红线零违规 |
| **M3 · 产品可发** | compare + 盲评；转正或归档；acceptance-records；开关默认策略决策 | AC-10～12；回滚演练通过 |

**禁止**单 PR 塞满 M1–M3。建议列车：PR-A 生命周期+日志 → PR-B 六图机会 → PR-C 混向模板 → PR-D 转正。

---

## 8. 实施落点（预览）

| 路径 | 改动 |
|------|------|
| `travelogue/layout_engine/mosaic/lte_adapter.py` | 拆 TPC↔experimental 耦合；lifecycle_admit |
| `travelogue/layout_engine/mosaic/hook.py` | 资格序、机会保护、拒因 |
| `travelogue/layout_contract/planner_state.py` | `hero_six_opportunity` 状态 |
| `travelogue/layout_engine/mosaic/builders.py` | 六图/混向 ordering 原因码 |
| `travelogue/layout_engine/mosaic/coarse_segments.py` | 签名白名单扩展 + miss 回落 |
| `travelogue/layout_engine/mosaic/log.py` | 漏斗字段 |
| `travelogue/config/mosaic.py` + 样例 YAML | 实验开关 / selection_optimization |
| `travelogue/layout_templates/lte_policy.yaml` | 仅转正时登记新 GA |
| `…/screen-mosaic-5-main-portrait-3land.yaml` | usage 与拒选对齐 |
| `…/screen-mosaic-5-main-hero-plus-4.yaml`（及孪生） | 命名/usage 澄清 photoCount=6 |
| **新增** `…/screen-mosaic-5-2p3l-portrait-hero-rail.yaml` | 2P3L 主从 |
| **新增** 竖主 1P4L YAML（id 视觉冻结） | 强竖分支 |
| `templates/visual-journal/journal-screens.css` | 新几何 |
| `tests/unit/layout_engine/test_mtso_*.py` + fixtures | 负例/正例/回滚 |
| `scripts/layout_compare.py` / debt report | 漏斗报告 |
| `docs/acceptance-records/mtso-*-2026-*.md` | 基线·狗粮·转正 |

---

## 9. 验收（AC）

| AC | 条件 |
|----|------|
| **AC-MTSO-01** | `template_contract.enabled=true` 且 `template_experiments.enabled=false` → 所有 experimental **不可见**；deprecated **永远不可见** |
| **AC-MTSO-02** | `2p3l-equal`、`2p3l-rail` 在 candidate / fallback / self-heal / legacy 各 ≥1 负例不可 emit（rail 仅 allowlist+cohort 可例外） |
| **AC-MTSO-03** | 任意 6 图窗口日志可唯一归类：未尝试 / 分段 / 配额 / 资格不足 / 合同 / 评分落败 / 胜出 |
| **AC-MTSO-04** | 结构合格且 admit 通过的 fixture：`effective_window_order` 为 `6,5,4` 且 **至少尝试** size=6 |
| **AC-MTSO-05** | 非结构合格 fixture：保持默认 `5,4,6`；不因保护策略空耗 dense/large |
| **AC-MTSO-06** | 全 corpus：dense 总额、无相邻 dense、large 章上限、不跨 coarse segment —— **违规=0** |
| **AC-MTSO-07** | 强竖 1P4L → 不落横主竖辅；横强 1P4L → 可落横主竖辅 |
| **AC-MTSO-08** | 新 2P3L：validator 过；主槽面积≥0.55；主从≥3:1；声明 AR vs 实渲对账通过；截图签核 |
| **AC-MTSO-09** | 签名 miss / 空交集 → 回落合同全集；无静默空候选 |
| **AC-MTSO-10** | `selection_optimization.enabled=false` 时固定 corpus 与基线逐屏一致（patternId、asset 序、几何）；嵌套子开关无效 |
| **AC-MTSO-11** | 狗粮双阈值：（a）dense/相邻允许时，`attempted/structurallyQualified ≥ 0.80`；（b）`won/attempted` 相对基线提升；（c）deprecated leak=0；混向错误落位 ≤ 基线；dense 违规=0。**禁止**用全局六图屏数作通过条件 |
| **AC-MTSO-12** | 转 GA 前独立盲评记录；未达标则归档且不占空位 |
| **AC-MTSO-13** | 六图家族去重：同窗孪生二选一时 large/机会计数 +1；日志 `sixHeroFamilyId` = canonical |

---

## 10. 风险与回滚

| 风险 | 缓解 | 回滚 |
|------|------|------|
| 六图保护让 4/5 变稀 | 仅同 cursor 挡抢占；机会可释放 | 关 `hero_six_opportunity`（父开关 OFF 亦可） |
| 新 2P3L 仍像假拼图 | 主从比例+截图硬门槛；不过即归档 | 不进 `lte_policy` |
| 实验隔离过严无狗粮样本 | 显式 cohort，不借 TPC | — |
| 路由与 TPC 冲突 | 只缩窄；空交集回落 | 关 `mixed_hero_routing` |
| 开关组合复杂 | 三开关独立默认 off；各有一致性测 | 先关 experiments → 再关 selection_optimization |

**回滚顺序**：`template_experiments` OFF → `hero_six_opportunity` OFF → `mixed_hero_routing` / `selection_optimization` OFF → **保持 P21 ON**。

---

## 11. 狗粮与对照语料（建议）

| 语料 | 关注 |
|------|------|
| 合成：全横 12 / 10 / 6 | 六图机会 vs landscape-4 饥荒 |
| 合成：1 强竖 + 4 横；1 弱竖 + 4 横 | 1P4L 分支 |
| 合成：2 竖 + 3 横（人物对照） | 2P3L 主从 |
| 合成：段长 4–5 的连拍 | `segment_cap` 记无机会 |
| 实册：曾开 TPC 的 demo（815/2025 等） | experimental leak=0（实验关时） |
| 实册：风景横图密集行程 | 合格六图转化率 |

对照命令：同一 trip `selection_optimization` on/off + `layout_compare`；手记写入 `docs/acceptance-records/`。

---

## 12. 开放项

| # | 问题 | 状态（七席 2026-07-23） |
|---|------|-------------------------|
| O-1 | 竖主 1P4L 几何轨道 | **已关（合同冻结）**：PR-C2 落地左满高竖 + `cols:[11,9]`；截图盲评归 PR-D |
| O-2 | `selection_optimization` 默认 true 时机 | **已关**：保持默认 false 至 M3 盲评后另决策；父 OFF 则子无效 |
| O-3 | hero gap 与 URO | **已关**：默认共用 `usage_rules.hero_gap_threshold`；MTSO 可覆盖须单测锁 |
| O-4 | `2p3l-rail` 去留 | **已关**：留 YAML + 文首标非继任；默认不进 allowlist；禁止转 GA |

---

## 13. Must-Fix 跟踪（评审）

| ID | 挡 | 状态 |
|----|----|------|
| BLK-MTSO-01 TPC↔experimental | M1 | ⬜ PR-A |
| BLK-MTSO-02 deprecated 全路径 | M1 | ⬜ PR-A |
| BLK-MTSO-03 资格两段论 | M2 | ✅ 合同已回写本文；实现待 PR-B |
| BLK-MTSO-04 机会作用域 | M2 | ✅ 合同已回写本文；实现待 PR-B |
| BLK-MTSO-05 AC-11 双阈值 | M2 | ✅ 合同已回写本文；测待 PR-B |
| BLK-MTSO-06 SKU/孪生/O-1 稿 | M2/PR-C | ✅ 合同冻结 SKU 已落；截图签核 → PR-D |
| BLK-MTSO-07 漏斗 fixture | M1 | ⬜ PR-A |
| BLK-MTSO-08 拆 ACCEPTANCE/IMPL | M2 | ⬜ M1 豁免 · M2 前必拆 |

---

## 14. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| **v0.1.0** | 2026-07-23 | 首稿：手测 + 代码探查；D-01～13 Draft Ready for Review |
| **v0.2.0** | 2026-07-23 | 七席 Conditional Go 回写：两段资格 · 机会作用域 · AC-11 双阈值 · 孪生 canonical · O-2/3/4 关闭 · 可 Kickoff M1 |
