# Travelogue · 版式质量栈纲领 V1（PRD）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue |
| **文档版本** | **v0.1.0** |
| **状态** | **Draft · Ready for Cross-Theme Kickoff**（纲领合同；不替代子 PRD 评审结论） |
| **特性代号** | **LQS**（Layout Quality Stack） |
| **文档类型** | **项目级纲领 PRD**（统摄 MSR · MGQ · GCS；跨主题合同 / 排期 / 禁区） |
| **触发来源** | 2026-07-18 三份子主题 Conditional Go 结案后，需统一心智模型与实施序，避免并行硬筛叠乘与补库失焦 |
| **前置条件** | Phase 16 LTE 默认路径稳定；Phase 15 MCS `pick_best_window` 为现网权威；LSE 默认关闭（见 P17 处置）；URO / BQP 盲评 harness 可复用或可同步 |
| **子主题 SSOT** | [MSR](./PRD-MCS-SIGNATURE-ROUTING-V1.md) · [MGQ](./PRD-MCS-GEOMETRIC-QUALITY-V1.md) · [GCS](./PRD-GENERATIVE-COLLAGE-SURFACES-V1.md) |
| **战略上位** | [观感提升路线图.md](./观感提升路线图.md) · [ROADMAP-PHASE18-BOOK-QUALITY.md](./ROADMAP-PHASE18-BOOK-QUALITY.md) · [P17-LSE-处置建议.md](./P17-LSE-处置建议.md) |
| **现网审计** | [acceptance-records/p17-w0-audit-a-active-scoring-chain.md](./acceptance-records/p17-w0-audit-a-active-scoring-chain.md) |
| **影响评估** | [acceptance-records/layout-quality-stack-v1-impact-review-2026-07-18.md](./acceptance-records/layout-quality-stack-v1-impact-review-2026-07-18.md)（实现前后效果与收益 · 十席联席） |
| **可行性与成本** | [acceptance-records/layout-quality-stack-v1-feasibility-cost-2026-07-18.md](./acceptance-records/layout-quality-stack-v1-feasibility-cost-2026-07-18.md)（落地可行性 · 人日合流 · 砍 scope） |
| **实施清单** | [IMPLEMENTATION-LAYOUT-QUALITY-STACK-V1.md](./IMPLEMENTATION-LAYOUT-QUALITY-STACK-V1.md)（**瘦身版 · 已认可** · S1–S4 + G1/G2 决策门；裁剪登记见其 §5） |
| **替代设计提案** | [PRD-TEMPLATE-CONTRACT-V1.md](./PRD-TEMPLATE-CONTRACT-V1.md)（**TPC** · Draft · 统一模板合同重设计；与本纲领瘦身版二选一，S1/W1 兼容） |
| **相邻业主** | [URO](./PRD-USAGE-RULES-LAYOUT-OPTIMIZATION.md) · [LTE P16](./PRD-PHASE16-layout-template-engine.md) · [LTE Admission](./LTE-ADMISSION-LAYOUT-TEMPLATES.md) · [Output Recipe](./PRD-OUTPUT-RECIPE-V1.md) · [导出门面](./PRD-PREVIEW-EXPORT-FACADE-V1.md) |
| **更新日期** | 2026-07-18 |

> **定位**
>
> 工业相册书赢在 **「库里有合适页型 → 用可解释硬规则进对类 → 同窗内再比几何与文案」**；  
> Travelogue 已有 LTE 固定 SKU + MCS soft + URO，但缺：**格式签名硬路由、屏内几何可标定、离线扩库与海报旁路**。  
> 本纲领将当日三份子 PRD **融为一条版式质量栈**：扩库（GCS）→ 硬路由（MSR）→ 用法/准入（URO/MGQ）→ 几何软决胜（MGQ）→ 旁路海报（GCS-B）。  
> **不**解冻 LSE、**不**把 BRIC 挂 MCS 失败口、**不** runtime 改 `slots[].rect`。
>
> **一句话目标**：在固定 SKU + MCS 权威选窗不变的前提下，用可解释硬层抬「进对页」概率，用几何 soft 与标定抬「同窗更稳」，用离线工厂抬「库天花板」，用隔离海报 Writer 服务「单屏能发」；全部默认开启绑独立盲评 Gate。

> **与子 PRD 的权威关系**
>
> | 文档 | 权威范围 |
> |------|----------|
> | **本文（LQS）** | 跨主题心智模型、硬过滤序、共享基建、SKU 入轨合同、程序级排期、组合 KPI、禁区 |
> | **MSR / MGQ / GCS** | 各自主题的 D-* 决策、AC、配置草案、里程碑细节、算法阈值 |
> | **冲突时** | 子主题内部细节以子 PRD 已冻结结论为准；跨主题接口以本文为准，冲突须回写双方 |

---

## 0. 读者指南

| 章节 | 澄清什么 |
|------|----------|
| §0.1 | 冻结决策（D-LQS-*） |
| §1 | 为何需要纲领：三主题缺口与组合杠杆 |
| §2 | 目标 / 非目标 / 成功画像 |
| §3 | 统一架构与管道 |
| §4 | 跨主题合同（硬层 · SKU · 面积 · 盲评） |
| §5 | 共享基建（必须先做） |
| §6 | 程序级里程碑与依赖 |
| §7 | 监控看板与诊断叙事 |
| §8 | 风险与故意不做 |
| §9 | Kickoff 清单 |
| 附录 | 子主题映射 · 版本记录 |

### 0.1 纲领决策（D-LQS · **拟冻结 · Kickoff 拍板**）

| # | 决策项 | 结论 |
|---|--------|------|
| **D-LQS-01** | 栈组成 | V1 栈 = **MSR + MGQ + GCS**；URO 为硬层既有业主（消费、不另起引擎） |
| **D-LQS-02** | 落点 | MSR/MGQ 全部挂 **`MosaicConfig`**；GCS **不进** MosaicConfig / 不挂 `used_legacy` |
| **D-LQS-03** | 硬过滤序 | **geometry → signature → URO → eligibility → soft**（一字面；见 §4.1） |
| **D-LQS-04** | 几何铁律 | 遵守 **D-MGQ-02**：禁止 runtime 改 `slots[].rect`；拓扑变更只走 YAML / GCS 离线 admission |
| **D-LQS-05** | LSE | **冻结**：禁止默认同步进 `layout.scoring` / 新 LSE 软乘子上量 |
| **D-LQS-06** | 交付序 | 共享基建 → MSR shadow → MGQ 准入 → MSR 硬筛 → MGQ soft → GCS-B 并行 → GCS-A 按签名空洞补库 → 分主题盲评 |
| **D-LQS-07** | 补库驱动 | GCS 轨 A **必须**以 MSR 诊断的签名空洞为优先队列；禁止「产量 KPI」 |
| **D-LQS-08** | 发布门禁 | 各主题 `enabled=false` 可先 merge；**默认开启**各自绑独立 **AC-*-BLIND ≥55%**；禁止 proxy 单独发布 |
| **D-LQS-09** | 旁路分账 | 杂志面 = MCS/LTE；海报面 = `poster_bric` Writer + export job sidecar；文案「单屏海报」≠ 九宫格 / 用户 collage |
| **D-LQS-10** | 填槽语义 | **L1 签名序 ≠ 填槽序**（继承 MSR BLK-03）；对外叙事诚实承认混合页 **bag 可为主力** |

---

## 1. 背景：三缺口如何合成一条栈

### 1.1 现网权威（不可误映射）

```text
run_curate
  → ChapterScreenPlanner
      → mosaic.compose.pick_best_window     ← 杂志主链（MCS）
           → LTE YAML patterns
           → URO / （本栈补）MSR · MGQ eligibility
           → soft score（本栈补 MGQ 几何罚）
           → used_legacy → legacy 规则屏   ← 现网失败口（非 BRIC）
  → solidify → trip.json screens[]

export / Output Recipe
  → chat_longshot / moments_grid / …
  → （本栈补）poster_bric                 ← 仅 ▾；非 magazinescreens[]
```

权威打分链审计见 P17-W0-A：**默认活跃 = MCS**，`layout.scoring` 默认休眠。

### 1.2 子主题各补哪一块

| 代号 | 全称 | 用户可感知问题（摘要） | 工业对标切口 |
|------|------|------------------------|--------------|
| **MSR** | MCS Signature Routing | 横竖混排塞错页型；有字仍密铺；扩 SKU 后 `try_order` 爆炸 | Shutterfly US8131114 · LLPP + 图文一体 |
| **MGQ** | MCS Geometric Quality | 主图不够跳 / 霸屏 / 小图碎屑；extreme 页误进 | gridwiggle · 准入 + 屏内几何软罚 + pairwise 标定 |
| **GCS** | Generative Collage Surfaces | SKU 空洞进 legacy；聚会缺「一张能发」 | BRIC · 离线轨道枚举 + 海报导出旁路 |

### 1.3 组合杠杆（为何不能只做其中一项）

```text
没有 GCS 扩库     → MSR L1 长期偏低，只能诚实承认 bag 主力，天花板仍在 SKU
没有 MSR 硬筛     → MGQ soft 常在「方向错误」的页型上微调，浪费
没有 MGQ 几何     → 进对类之后仍可能「主图不跳 / 太碎」
没有硬过滤守门    → 任一硬筛 dogfood 严、生产仍经 self-heal/legacy 漏网
把 BRIC 挂 legacy → 破坏杂志哲学（无 hero/文案槽），且违 D-MGQ-02
```

**漏斗隐喻**：

| 层 | 职责 | 抬什么 |
|----|------|--------|
| GCS-A | 扩合法拓扑 | 召回天花板 |
| MSR | 签名硬路由 + caption prefer | 「进对类」精度 |
| URO + MGQ eligibility | 用法与页型准入 | 「少选错」 |
| MGQ soft + MCS | 同窗几何决胜 | 「同窗更稳」 |
| GCS-B | 导出旁路 | Sparse/聚会交付 |

### 1.4 与观感路线图 / BQP 的对齐

| 上位优先级 | LQS 承接 |
|------------|----------|
| P0 感知裁判 | 共用 BQP/URO 代表 trip + harness；Gate 码按主题独立 |
| P2 模板 + 硬约束 | **本纲领主战场**（MSR 硬路由 · MGQ 准入 · GCS 扩库） |
| P4 Solver / LSE | **明确不做**（与 P17 冻结一致） |
| P1 选片 / P3 结构编排 | **非本栈范围**；另轨 |

---

## 2. 目标与非目标

### 2.1 纲领目标（G-LQS-*）

| ID | 目标 | 验收口径 |
|----|------|----------|
| **G-LQS-01** | 冻结跨主题心智与硬过滤序 | 本文 §0.1 / §4；三份子 PRD 交叉引用一致 |
| **G-LQS-02** | 共享硬过滤守门（无绕过） | 见 §5.1；对齐 AC-MGQ-12 / AC-MSR-12 |
| **G-LQS-03** | MSR shadow → 产出签名空洞清单 | 驱动 GCS-A 优先队列（D-LQS-07） |
| **G-LQS-04** | 杂志主链观感：混向少狠裁、主图更稳、有字进带文案区 | 各主题 AC + 独立盲评 |
| **G-LQS-05** | 旁路：▾「单屏海报」可狗粮且不污染 `screens[]` | AC-GCS-05/06；默认露出绑 AC-GCS-BLIND |
| **G-LQS-06** | 设计师扩库主路径 = YAML role/mix/eligibility，非新 Python 选版特例 | MSR G-MSR-04 + GCS admission |

### 2.2 非目标（纲领级）

| # | 排除项 | 理由 |
|---|--------|------|
| **OUT-01** | 解冻 LSE / 默认开 `layout.scoring` | 已证伪 |
| **OUT-02** | MCS `used_legacy` 默认调 BRIC | GCS 禁区 |
| **OUT-03** | runtime 连续分区 / 改 rect | D-MGQ-02 |
| **OUT-04** | 用 Hungarian 当观感主故事 | MSR D-MSR-08 |
| **OUT-05** | 另起第二套 usage 引擎 | URO 业主 |
| **OUT-06** | 选片 subset / DPP 上移 | 观感 P1 另轨 |
| **OUT-07** | 章级节奏状态机重写 | Planner 业主；MSR page_group 仅钩子 |
| **OUT-08** | 三主题绑成单一「超级开关」一次默认全开 | 必须分主题盲评 |
| **OUT-09** | 以 golden proxy / YAML 产量作发布依据 | 感知裁判优先 |

### 2.3 成功画像（组合）

1. **2 横 2 竖** 稳定进匹配混向页，而不是靠裁切硬撑；  
2. **有明确主图**时主槽跳得出来但不霸屏；**无主次**时更少误进 extreme；  
3. **有图注**更多落在带 `captionAreas` 的版式（replan 默认 off，避免字一出整页改脸）；  
4. **SKU 空洞**可被工厂按签名补齐并经 admission，corpus 上 legacy/miss 相对 baseline ↓；  
5. **聚会/Sparse** 可在 ▾ 导出「单屏海报」，且不与九宫格/长图文案串线；  
6. 调权/扩库时有 **可解释 reject taxonomy + 评分台（MGQ W2）**，而非纯直觉。

---

## 3. 统一架构

### 3.1 总览

```text
                    ┌──────────────────────────────────────┐
                    │  GCS 轨 A · Offline SKU Factory         │
                    │  轨道枚举 → validator → admission YAML  │
                    │  优先队列 ← MSR 签名空洞清单             │
                    └─────────────────┬────────────────────┘
                                      │ GitOps
                                      ▼
┌─────────────────────────────────────────────────────────────┐
│  curate / MCS / LTE（杂志主链）                               │
│                                                               │
│  generate_window_candidates                                   │
│    geometry                                                   │
│    → MSR  format_signature L1/L2/L3     reason: signature:* │
│    → URO  usage_rules                   reason: usage_rule:* │
│    → MGQ  constraints.eligibility       reason: eligibility:*│
│    → soft：caption prefer（MSR）                              │
│           + MCS base + MGQ geometric_quality penalties        │
│    → pick / diversity / self-heal / legacy                    │
│         ★ 仍须经 signature + URO + eligibility（共享守门）     │
└─────────────────────────────────────────────────────────────┘
                                      │
                                      ▼ solidify → screens[]

                    ┌──────────────────────────────────────┐
                    │  GCS 轨 B · poster_bric Writer（旁路）  │
                    │  Output Recipe · export job sidecar    │
                    │  禁止写入 screens[] / 伪 patternId     │
                    └──────────────────────────────────────┘
```

### 3.2 配置根（分账）

| 开关 | 配置路径 | 默认 | 业主 |
|------|----------|------|------|
| 签名硬路由 | `mosaic.signature_routing.enabled` | `false` | MSR |
| 屏内几何 | `mosaic.geometric_quality.enabled` | `false` | MGQ |
| Usage 硬过滤 | `layout.usage_rules.enabled` | 随 URO | URO |
| SKU 工厂工具链 | `features.gcs_sku_factory` | 开发可开 | GCS |
| 海报导出 | `features.gcs_poster_bric` | `false` 至盲评 | GCS |
| LSE beam | `layout.scoring.enabled` | **必须保持 false** | —（禁默认同步） |

### 3.3 术语隔离（跨主题）

| 概念 | 正确指称 | 禁止混用 |
|------|----------|----------|
| 用户自制拼图素材 | `mediaClass=collage` → full-frame | 称「GCS 拼贴」 |
| GCS 海报导出 | `exportSurface=poster_bric` / 「单屏海报」 | 「九宫格」「moments_grid」 |
| GCS 工厂模板 | YAML `generator: gcs-track-v1` | 伪 `patternId` 进 `screens[]` |
| `hero_separation` | 跨屏 hero 复用（既有） | 当作屏内 prominence |
| 屏内几何 | `hero_prominence` / `hero_coverage` / `cell_area_balance` | 塞进 `hero_separation` |
| L1 exact | 签名串相等 | 断言填槽序 = taken_at 序 |

---

## 4. 跨主题合同（SSOT）

### 4.1 硬过滤顺序（一字面 · D-LQS-03）

```text
geometry 合法
  → signature L1/L2/L3（MSR）     signature:*
  → usage_rules（URO）            usage_rule:*
  → eligibility（MGQ）            eligibility:*
  → soft：
       caption prefer（MSR，同 signatureMatchLevel 内可观测）
       + MCS score_candidate
       + MGQ geometric_quality penalties
       + diversity / MMR
  → pick top
  → fallback / self-heal / replan / caption replan
       ★ 不得产出已被 signature:* / usage_rule:* / eligibility:* 拒绝的 pattern
```

**铁律**：soft / MMR / diversity / caption prefer **不得**把硬拒 pattern 拉回候选集。

### 4.2 SKU 入轨最低字段（GCS → MSR/MGQ/URO）

经 LTE validator + admission 的新 YAML **必须**满足：

| 字段 / 能力 | 要求 |
|-------------|------|
| 轨道几何 | 可映射 `stage.cols/rows`；不重叠、不越界；gap 一致 |
| 签名可派生 | slots role → `L/P/S` 可派生或诚实进 L2；与 `mix` bag 一致 |
| `generator` + `enum_params` | 可复现（GCS D-GCS-08） |
| `usage` / eligibility | 非空壳；可被 URO/MGQ 消费 |
| V1 禁止 | 伪 hero 面积带 SKU；BRIC 连续 rect 硬塞 YAML |

**不合格 → 丢弃**（discard 报表），不得放宽 V-P16 硬约束「为了填满」。

### 4.3 面积口径（全栈统一）

槽面积占比 = `col_frac × row_frac`（复用 `geometry.slot_display_aspect` 权重折算）。  
**禁止**按 `slot.rect` 跨越格数裸计。  
MGQ 三罚、eligibility 面积带、工厂规范化 **同源**。

### 4.4 盲评与代表集

| 项 | 合同 |
|----|------|
| 样本 | 与 BQP/URO **共用代表 trip 集 + harness**（先统一「8/9 本」口径） |
| Gate | **AC-MSR-BLIND / AC-MGQ-BLIND / AC-GCS-BLIND** 独立计票、独立默认开决策 |
| 开关矩阵 | 两臂**只翻**被测主题开关；其余硬层同态 |
| MSR 子集 | 必须含 **混向窗 + 有图注**；图文子集不得显著劣于 off |
| GCS 海报 | 独立「可发」≥55%；与杂志 Gate 分账 |
| 禁止 | 仅用 proxy / golden 微涨充当默认开依据 |

### 4.5 decision_log 最低可解释集

| 字段 | 业主 |
|------|------|
| `formatSignature` · `signatureMatchLevel` · 最终 asset 序 | MSR |
| `rejectReasons[]`（`signature:*` / `usage_rule:*` / `eligibility:*`） | 硬层 |
| raw 几何：`heroProminenceRatio` / `heroCoverageRatio` / `cellAreaCv` | MGQ（与 penalty 分栏） |
| `captionActive` / `captionPreferApplied` | MSR |
| 导出：`exportSurface=poster_bric`（job sidecar，非 screens） | GCS-B |

---

## 5. 共享基建（Program P0 · 必须先做）

> 下列项是三主题 W1 硬行为的公共前置；**归 LQS 程序拥有**，任务可落在任一子 IMPL，但验收跨主题共享。

### 5.1 硬过滤绕过修复（对齐 MGQ BLK-10）

| 路径 | 要求 |
|------|------|
| `selfheal.drop_worst_asset` | 重建 `WindowContext`，走 `generate_window_candidates_with_rejections` |
| `replan_screen(legacy)` | 结果强制过硬过滤，**或** harness/评分台禁止调用 legacy 策略 |
| legacy append / caption replan | 同效：不得 emit 硬拒 pattern |

对应 AC：**AC-MGQ-12**、**AC-MSR-12**（分路径负例）。

### 5.2 开关骨架与落点 CI

- `MosaicConfig.signature_routing` / `geometric_quality` 进 fail-loud；默认 `enabled=false`。  
- CI 断言：默认 `layout.scoring.enabled is false`；MGQ/MSR 字段不出现在 LSE 默认路径（AC-MGQ-11 / AC-MSR-11）。  
- GCS：compose/legacy 路径静态/单测无 `bric_compose`（AC-GCS-01）。

### 5.3 Reject taxonomy 与看板

统一前缀命名空间；可联合展示，但 **不得**合并撤销顺序：

- `signature:*` — 不进 URO UNDO  
- `usage_rule:*` — URO 业主  
- `eligibility:*` — **不参与** `USAGE_RULE_UNDO_ORDER`（MGQ BLK-12）

### 5.4 盲评 SSOT

Kickoff 时钉死：代表 trip 列表、计票单位、平局/弃权、veto/脚本扩展方式；写入各 ACCEPTANCE 或共享附录，本文只引用。

---

## 6. 程序级里程碑（融合排期）

> 子主题内部 W0/W1/W2/W3 细节以子 PRD 为准。下表是 **跨主题依赖序**；W0 文档/开关可并行，**生产硬行为勿三主题同周齐开**。

| 程序波次 | 内容 | 主要依赖 | 出口 |
|----------|------|----------|------|
| **LQS-P0** | 共享基建：绕过修复 · 双开关骨架 · taxonomy · 盲评 SSOT · 本文合同拍板 | 无 | AC-MGQ-12 路径可测；落点 CI 绿 |
| **LQS-P1** | **MSR W0 shadow**：字母表 · 派生 · shadow_log · 零行为差 | P0 | AC-MSR-01/13；产出 **签名空洞清单 v0** |
| **LQS-P2** | **MGQ W0 + W1a**：命名锁 · eligibility · 消费 UR-01 | P0 | AC-MGQ-03/05/12；准入可看板 |
| **LQS-P3** | **MSR W1**：SignatureIndex 挂候选入口 + caption prefer | P1 + P0 守门 | AC-MSR-01～07、12～14 |
| **LQS-P4** | **MGQ W1b**：三 soft + 面积 helper + raw 特征 | P2 | AC-MGQ-01～06、13～15 |
| **LQS-P5** | **GCS 轨 B**（可与 P3 **并行**）：`poster_bric` Writer · flag=false | Output Recipe 合同 | AC-GCS-05/06/08/09；狗粮 |
| **LQS-P6** | **GCS 轨 A**：按 P1/P3 空洞清单枚举 → ≥3 experimental | P1 空洞清单；LTE admission | AC-GCS-02～04；miss/legacy 方向对 |
| **LQS-P7** | 标定与默认开：MGQ 评分台（W2）· 各主题独立盲评 | P3–P6 | 各 AC-*-BLIND ≥55% 或保持 off |

### 6.1 资源紧张时的砍法

| 优先级 | 保留 | 可延后 |
|--------|------|--------|
| **P0** | 共享守门 + MSR shadow + MGQ eligibility（W1a） | — |
| **P1** | MSR 硬筛 + GCS-B 海报 | MGQ soft、GCS-A、评分台 |
| **P2** | MGQ soft + GCS-A 按空洞补库 | page_group、caption replan、海报默认露出 |

若只能做一条主线：**LQS-P0 → P1 → P2（eligibility）**；GCS-B 作并行旁路；GCS-A 与 MGQ soft 紧随。

### 6.2 拆文纪律（继承子主题 BLK-08）

| 波次 | 文档要求 |
|------|----------|
| 本纲领 Kickoff | 本文 v0.1+；可选 `IMPLEMENTATION-LAYOUT-QUALITY-STACK-V1.md`（任务卡级） |
| 各子主题 W1 merge 前 | 各自 `ACCEPTANCE-…` + `IMPLEMENTATION-…` 必须存在 |
| GCS | 实现 **先 B 后 A**（子 PRD 已冻） |

---

## 7. 监控看板（组合诊断叙事）

四张看板分账；**禁止**合成单一「观感分」作发布依据。

| 看板 | 关键指标 | 叙事规则 |
|------|----------|----------|
| **路由** | `signature_exact_rate` / `bag_rate` / `size_fallback_rate` / `direction_conflict` | exact≪bag → 优先 GCS 补有序 SKU，勿加压 MGQ 权重 |
| **准入** | `usage_rule:*` · `eligibility:*` reject 聚合 | 枯竭 → 查守门与 UNDO 边界，勿用 soft 绕过 |
| **几何** | 三罚触发率 + raw 特征分位 | exact 已高但盲评仍输 → MGQ/caption 主战场 |
| **库与旁路** | `used_legacy` / pattern-miss vs baseline；海报导出成功率 | 轨 A KPI = miss/legacy ↓；轨 B = 成功率 + 盲评可发 |

**决策树（运维）**：

```text
bag ≫ exact 且 miss 高     → GCS-A 按空洞补库
exact 高 · 混向仍狠裁      → 查 L3 direction_conflict 是否生效 / ordering 分账
exact 高 · 主图不稳        → MGQ soft / eligibility
有字仍密铺                 → caption prefer / captionAreas 覆盖
Sparse 抱怨多屏            → GCS-B 发现性（▾），不改杂志主 CTA
legacy 飙升                → 硬筛过严或绕过未修；先看板分账再回调
```

---

## 8. 风险与缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| 三主题同开硬行为 → 候选枯竭 | legacy 飙升、观感回退 | §6 串行硬行为；分开关 dogfood |
| BRIC 被当成 MCS 救场银弹 | 哲学冲突 | D-LQS-02/09；AC-GCS-01；产品话术禁「拼贴救场」 |
| 工厂产无 usage/签名的 YAML | 降不了 miss | §4.2 入轨硬门 |
| L1 被误解为填槽契约 | 算法/调试串线 | D-LQS-10；decision_log 三件套 |
| MGQ soft 与 caption prefer 互打 | 带文案 SKU 被几何罚打没 | 分账诊断；prefer 写成可观测 AC |
| 评分台与「这页」混用 | 用户以为改了本书 | MGQ 独立路由 +「不改本书」固定句 |
| 误挂 LSE | 默认路径零感知或意外开启 | AC-MGQ-11 / AC-MSR-11 |
| 单一超级盲评一次全开 | 无法归因 | D-LQS-08；Gate 码独立 |

---

## 9. Kickoff 清单（本纲领）

### 9.1 会前必读

1. 本文 §0.1 · §3 · §4 · §6  
2. MSR / MGQ / GCS 各自 §0 冻结决策（已结案）  
3. P17-W0-A 活跃打分链  

### 9.2 会中必拍

- [ ] 采纳或修订 **D-LQS-01～10**  
- [ ] 确认硬过滤序一字面（§4.1）与 URO/MGQ/MSR 文档交叉引用  
- [ ] 确认 GCS-A 补库优先级 = MSR 空洞清单（D-LQS-07）  
- [ ] 确认 LQS-P0 共享基建 Owner 与目标日  
- [ ] 确认盲评 trip 集 SSOT Owner（与 URO/BQP 合流）  

### 9.3 会后动作

| # | 动作 | 产出 |
|---|------|------|
| 1 | 回写 D-LQS 拍板 → 本文升 v0.2.0（若有修订） | 纲领冻结 |
| 2 | 拆或更新三份子 IMPLEMENTATION 任务卡，挂 LQS-P* 依赖 | 可排期 |
| 3 | 更新 [docs/README.md](./README.md) LQS 状态行 | 可发现 |
| 4 | MSR shadow 跑一轮 corpus → 空洞清单 v0 | GCS-A 输入 |
| 5 | **本轮不强制编码**；编码按 LQS-P0 另排期 | 纪律 |

### 9.4 子主题评审状态（输入基线 · 2026-07-18）

| 主题 | PRD | 评审 | 状态 |
|------|-----|------|------|
| MSR | v0.2.0 | [纪要](./acceptance-records/mcs-signature-routing-v1-review-2026-07-18.md) | Conditional Go · W0 shadow |
| MGQ | v0.2.1 | [第一轮](./acceptance-records/mcs-geometric-quality-v1-review-2026-07-18.md) · [专家](./acceptance-records/mcs-geometric-quality-v1-expert-review-2026-07-18.md) | Conditional Go · W0；W1 前 BLK-09～14 |
| GCS | v0.2.0 | [纪要](./acceptance-records/generative-collage-surfaces-v1-review-2026-07-18.md) | Conditional Go · Kickoff W0；实现先 B 后 A |

---

## 10. 所有权一览

| 主题 | 交付 | 不改 |
|------|------|------|
| **LQS（本文）** | 跨主题合同、排期、共享基建定义、组合 KPI 叙事 | 子主题内部阈值细节 |
| **MSR** | SignatureIndex · caption prefer · page_group 钩子 | MGQ 公式 · GCS Writer |
| **MGQ** | eligibility DSL · 三 soft · 评分台 | usage 引擎 · 签名字母表 |
| **GCS** | 轨道工厂 · `poster_bric` | MosaicConfig 评分路径 |
| **URO** | `usage_rules` / UR-01 | — |
| **LTE / Admission** | validator · lifecycle | — |
| **BQP** | 代表 trip + 盲评 harness | 各 Gate 码独立 |

**对外一句话**：

> **GCS 抬库天花板；MSR 决定进哪类版式；URO/MGQ 决定别进错用法与几何带；MGQ soft 在同窗决胜；海报旁路服务单屏分享——杂志主链始终是固定 SKU + MCS。**

---

## 附录 A · 子主题能力映射（速查）

| 能力 | 子 PRD 章节 | LQS 挂点 |
|------|-------------|----------|
| format_signature L1/L2/L3 | MSR §5 | §3.1 硬层 |
| caption-aware prefer / replan | MSR §6 | soft 层；replan 默认 off |
| page_group 时间邻近 | MSR §7 | 节奏配额优先 |
| constraints.eligibility | MGQ §4.3.1 | 硬层 |
| hero_prominence / coverage / cell_area_balance | MGQ §4.3.2 | soft 层 |
| layout-rating.jsonl | MGQ §4.4 | LQS-P7 |
| 轨道 SKU 工厂 | GCS §5 | LQS-P6；输入=空洞清单 |
| poster_bric Writer | GCS §6 | LQS-P5；旁路 |
| 禁 BRIC@legacy / 禁改 rect | GCS §4.2 · MGQ D-MGQ-02 | D-LQS-02/04 |

## 附录 B · 版本记录

| 版本 | 日期 | 说明 |
|------|------|------|
| **v0.1.0** | 2026-07-18 | 初稿：融会 MSR/MGQ/GCS 为版式质量栈；跨主题合同与 LQS-P0～P7 排期；待 Kickoff 拍板 D-LQS-01～10 |
