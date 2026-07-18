# Travelogue · MCS 格式签名路由与图文一体选版 V1（PRD）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue |
| **文档版本** | **v0.2.0** |
| **状态** | **Conditional Go · Ready for Kickoff W0**（shadow only；本轮不写生产硬筛） |
| **特性代号** | **MSR**（MCS Signature Routing） |
| **文档类型** | 版式观感专项优化 PRD（现网 MCS 硬路由层 · 非 LSE 上量） |
| **触发来源** | 工业对标 Shutterfly **US8131114**（Smart photobook creation · 2012）流水线与 LLPP 格式签名匹配；与 [观感提升路线图.md](./观感提升路线图.md)「模板库 / 硬编辑约束」优先级对齐 |
| **前置条件** | Phase 16 LTE 默认路径稳定；Phase 15 MCS `pick_best_window` 为现网权威；asset `aspectKind` / EXIF 时间可用；MGQ D-MGQ-02（禁 runtime 改 rect）已冻结 |
| **纲领上位** | [PRD-LAYOUT-QUALITY-STACK-V1.md](./PRD-LAYOUT-QUALITY-STACK-V1.md)（**LQS** · 统摄 MSR/MGQ/GCS 跨主题合同与排期） |
| **关联文档** | [PRD-MCS-GEOMETRIC-QUALITY-V1.md](./PRD-MCS-GEOMETRIC-QUALITY-V1.md) · [PRD-GENERATIVE-COLLAGE-SURFACES-V1.md](./PRD-GENERATIVE-COLLAGE-SURFACES-V1.md) · [PRD-PHASE16-layout-template-engine.md](./PRD-PHASE16-layout-template-engine.md) · [PRD-USAGE-RULES-LAYOUT-OPTIMIZATION.md](./PRD-USAGE-RULES-LAYOUT-OPTIMIZATION.md) · [P17-LSE-处置建议.md](./P17-LSE-处置建议.md) · [观感提升-业内调研.md](./观感提升-业内调研.md) · [观感提升路线图.md](./观感提升路线图.md) · [acceptance-records/p17-w0-audit-a-active-scoring-chain.md](./acceptance-records/p17-w0-audit-a-active-scoring-chain.md) |
| **评审纪要** | [acceptance-records/mcs-signature-routing-v1-review-2026-07-18.md](./acceptance-records/mcs-signature-routing-v1-review-2026-07-18.md)（**已结案** · Conditional Go · BLK-01～08） |
| **评审模板** | [acceptance-records/mcs-signature-routing-v1-review-TEMPLATE.md](./acceptance-records/mcs-signature-routing-v1-review-TEMPLATE.md)（备查） |
| **验收配套** | 本文 §9；**W1 merge 前**须拆 `ACCEPTANCE-MCS-SIGNATURE-ROUTING-V1.md`（BLK-08） |
| **实施清单** | Kickoff W0 时补 `IMPLEMENTATION-MCS-SIGNATURE-ROUTING-V1.md` |
| **更新日期** | 2026-07-18 |

> **v0.2.0 评审回写摘要（跨职能 Conditional Go）**
>
> - BLK-01：落点 `mosaic.signature_routing` / MosaicConfig；禁默认同步进 LSE  
> - BLK-02：硬过滤序 geometry→signature→URO→eligibility→soft；soft 不得绕过 `signature:*`  
> - BLK-03：**L1 签名序 ≠ 填槽序**（算法关键合同）  
> - BLK-04：L3 方向冲突禁入（`signature:direction_conflict`）  
> - BLK-05：字母表 `L/P/S` + `panorama→L` / `tall→P`  
> - BLK-06：caption SSOT=`captionAreas`；同 level prefer 可测；replan 默认 off  
> - BLK-07：SignatureIndex 生命周期 + reason taxonomy  
> - BLK-08：W1 前拆文；W0=shadow only；page_group 节奏优先  
> - OQ-01～05 **全部关闭**（见 §0.1）  
> - **可 Kickoff W0（shadow）**；生产硬筛另排 W1

> **定位**
>
> US8131114 证明：工业相册书的核心不是「打分更聪明」，而是 **主排序 → 次级分页 → 格式签名硬匹配版式库 → 图文一体填槽** 的可解释路由。  
> Travelogue 已具备更高层能力（HDBSCAN/CLIP 选片、narrate、arc/folio、Playwright 长图），但屏级选版仍是「按 N 枚举 + `try_order_for_pattern` 手写硬规则 + soft 打分」，**没有一等公民的方向签名索引**；narrate 后置、不参与选版。  
> 本 PRD **不**重写 MCS 为 Shutterfly 流水线，**不**解冻 LSE，**不**把 Hungarian 当观感主杠杆；只在现网 MCS 前补一层 **可解释的硬路由契约**，并打通 **caption → 带文案区 pattern 优先**。
>
> **一句话目标**：把专利的 LLPP 做成 LTE/MCS 的签名硬筛；同签名内仍由 MCS/MGQ 软决胜；图文一体选版成为产品差异点。

> **产品共识（五条铁律）**
>
> 1. **签名硬筛，软分决胜** — `format_signature` / bag-of-mix 在 soft score **之前**过滤；不得用 soft 绕过签名硬拒绝。  
> 2. **落点 = MCS** — 新开关与诊断挂 `MosaicConfig`；**禁止**默认写进 `layout.scoring` / LSE 策略包。  
> 3. **几何铁律不变** — 遵守 D-MGQ-02：禁止 runtime 改 `slots[].rect`；扩拓扑只走 YAML / GCS 离线 admission。  
> 4. **Hungarian ≠ 签名匹配** — 槽内 assignment 仍可选 refine；默认保持 off；不得宣称「匈牙利 = 超越专利主路径」。  
> 5. **确定性** — 同输入 + 同 config → 同 `trip.json` screens；禁默认 shuffle / 依赖 dict 迭代序。

---

## 0. 读者指南

| 章节 | 澄清什么 |
|------|----------|
| §0.1 | 拟冻结决策（D-MSR-*）与待关闭 OQ |
| §1 | 对标结论、现网缺口、问题清单 |
| §2 | 目标 / 非目标 |
| §3 | 与相邻主题边界 |
| §4 | 三层架构与挂点 |
| §5 | 轨 A · 格式签名索引 |
| §6 | 轨 B · 图文一体选版 |
| §7 | 轨 C · 章内 page-group |
| §8 | 配置 / 数据 / 埋点 |
| §9 | 里程碑与验收 |
| §10 | 风险 |
| 附录 | 专利映射 · 版本记录 |

### 0.1 评审决策（D-MSR · **已冻结**）

| # | 决策项 | 冻结结论 |
|---|--------|----------|
| **D-MSR-01** | 落点轨 | 全部新硬筛 / soft 偏好 / 诊断挂 **`MosaicConfig.signature_routing`**；**禁止**默认同步进 `layout.scoring` / LSE（BLK-01） |
| **D-MSR-02** | 签名定义 | 有序字母串；字母表见 §5.1（含 `S` 与 panorama/tall 映射）（BLK-05） |
| **D-MSR-03** | 匹配层级 | **L1 exact → L2 bag → L3 size**；每层记 `signatureMatchLevel` + reason；**L1 ≠ 填槽序**（BLK-03）；L3 **禁止方向冲突**（BLK-04）；混合页 **bag 可为实际主力**（诚实叙事） |
| **D-MSR-04** | 与 `try_order_for_pattern` | W1 起 SignatureIndex = **候选入口权威**；ordering 仅「同签名内 asset↔slot 对齐」；`signature:*` 与 `ordering_failed` **分账** |
| **D-MSR-05** | 图文一体 | caption-active 时优先带文案区；**同 `signatureMatchLevel` 内可观测偏置**（BLK-06）；无文案不强制 caption layout |
| **D-MSR-06** | narrate 时序 | 两阶段友好；`caption_replan_after_narrate` **默认 false**；开启时仅同窗同 asset；**禁止**全册重跑 / 改章序 / 跨屏抽片 |
| **D-MSR-07** | page-group | 章内时间邻近钩子；**节奏配额优先于 page_group**（BLK-08）；Lab → V1.1 |
| **D-MSR-08** | Hungarian | 默认 **off**；仅同签名 refine；非本主题卖点 / 非默认开条件 |
| **D-MSR-09** | 发布门禁 | `enabled=false` 可先 merge；**默认开启**须 **AC-MSR-BLIND ≥55%**（独立 Gate 码） |
| **D-MSR-10** | legacy / self-heal | fallback / self-heal / `replan_screen` / caption replan **不得**产出已被 `signature:*`（及下游 URO/eligibility）拒绝的 pattern（BLK-02） |

| OQ | 冻结结论 |
|----|----------|
| **OQ-MSR-01** | **已关闭 · A** — `square→S`；库无 `S` 槽则 L2 bag |
| **OQ-MSR-02** | **已关闭 · A** — 窗口签名用 `taken_at` 升序（缺则 `asset_id`）；**且**签名序 ≠ 填槽序（BLK-03） |
| **OQ-MSR-03** | **已关闭 · A** — trim 后非空 `asset.caption` **或** 该屏已绑定 lead/hook；章级文案不驱动全章换版；可选记 `captionActiveSource` |
| **OQ-MSR-04** | **已关闭 · B** — V1 不做 Studio 调屏；另 PRD；V1 以匹配级可解释作补偿 |
| **OQ-MSR-05** | **已关闭 · A** — `slots[].role` **派生为主**；显式 `formatSignature` 仅 override + validator fail-loud |

**总案一句话**：抄 Shutterfly 的 **签名硬路由 + 图文一体选版**；落点 **MCS**；软决胜留给 MGQ；SKU 扩库留给 GCS；**诚实承认 bag 主力，不神话 LLPP 精确率**。

---

## 1. 背景与问题

### 1.1 对标结论（US8131114 → Travelogue）

| 专利能力（FIG.3A / 14 / 6 / 3B） | Travelogue 现状 | 本 PRD 态度 |
|--------------------------------|-----------------|-------------|
| 主准则排序（默认 EXIF 时间） | ingest 排序 | **保留**；签名生成默认跟时间序（OQ-02） |
| 次级准则分页（时间间隔 / 色 / GPS） | curate 分章 + geo；章内窗口由 planner 切 | **加强章内时间邻近 page-group**；色调延后 |
| 版式库 + 槽位 P/L 标注 | LTE YAML `mix` + `slots[].role` | **派生有序签名 + 倒排索引** |
| LLPP 精确选版 | 无；按 N 枚举 + 手写 `try_order_for_pattern` | **本 PRD 主交付** |
| 顺序填槽（FIG.8） | 可选 Hungarian（默认 off） | **不**当主杠杆；可选 refine |
| 图注区与图像一体选版（Claim 12） | `caption` 字段有；选版不读 | **本 PRD 轨 B** |
| 用户拖拽调 page group | Studio 调章序 | **非 V1**（OQ-04） |

### 1.2 现网权威链路与插入点

```text
run_curate
  → ChapterScreenPlanner（节奏 / 窗口）
      → [MSR · 可选] page_group 切刀（时间邻近）     ← 轨 C
      → mosaic.compose.pick_best_window
           → generate_window_candidates
                → [MSR] format_signature 硬筛         ← 轨 A（本 PRD）
                → usage_rules（URO）
                → constraints.eligibility（MGQ）
                → [MSR] caption-aware soft / prefer   ← 轨 B
           → score_candidate（含 MGQ 几何罚）
           → [可选] Hungarian refine（默认 off）
           → MMR/DPP + self-heal / legacy              ← 仍须经 signature 硬筛（D-MSR-10）
  → narrate
      → [MSR] 同窗口 caption re-rank / replan（可选） ← 轨 B 第二阶段
```

审计真值（选版权威链）：`acceptance-records/p17-w0-audit-a-active-scoring-chain.md`。

### 1.3 用户可感知问题（本 PRD 要解决）

| ID | 问题 | 典型表现 | 根因分层 |
|----|------|----------|----------|
| **MSR-P-01** | 横竖混排「塞错页型」 | 2L2P 窗口进了全横/全竖页，大量裁切或空白感 | 无签名硬筛；仅靠事后 `aspectPatternMatchRate` |
| **MSR-P-02** | 同 N 多模板黑盒 | 失败原因只能看到 `ordering_failed`，设计师无法对照库 | YAML `mix` 与 Python 特例双轨 |
| **MSR-P-03** | 有文案仍选「纯图密铺」 | narrate 后 captions 挤在屏外或弱化 | 选版不读 caption；无 textRegion 优先 |
| **MSR-P-04** | 短时连拍被拆到多屏 | 同一场景碎片化 | 章内缺时间邻近 page-group |
| **MSR-P-05** | 扩 SKU 后维护爆炸 | 每加模板就堆 `try_order_for_pattern` 分支 | 缺签名倒排；手写路由不可扩展 |

### 1.4 专利伪代码 → Travelogue 合同（非实施细节）

```python
def bucket_format_signature(assets) -> str:
    """有序：'LLPP' / 'LPP' / 'LLL' / 含 'S' …"""
    ordered = sort_by_taken_at(assets)  # OQ-MSR-02
    return "".join(aspect_letter(a) for a in ordered)

def candidate_patterns(bucket, registry):
    sig = bucket_format_signature(bucket.assets)
    # L1 exact → L2 bag(mix) → L3 size-only
    return signature_index.lookup(sig, n=len(bucket.assets))

def assign_assets_to_slots(assets, pattern):
    # 非本 PRD 默认路径；P17 Hungarian 可选
    return order_for_roles_or_hungarian(assets, pattern.slots)
```

---

## 2. 目标与非目标

### 2.1 目标

| ID | 目标 | 验收口径 | 阶段 |
|----|------|----------|------|
| **G-MSR-01** | 窗口可生成稳定 `formatSignature` | decision_log / 单测 | W0 |
| **G-MSR-02** | LTE 注册表可倒排：`signature → [patternId]`（派生或显式） | validator + 索引单测 | W0–W1 |
| **G-MSR-03** | MCS 候选入口走 L1→L2→L3；reason 可聚合 | `signature:*` taxonomy | W1 |
| **G-MSR-04** | 收敛双轨：新模板无需新增 Python 选版特例即可被签名命中 | ≥1 新模板只靠 YAML 进索引 | W1 |
| **G-MSR-05** | caption-aware：有文案窗口优先带文案区 pattern | 对照 fixture + 诊断率 | W1–W2 |
| **G-MSR-06** | 章内时间邻近 page-group（可开关） | planner 指标 + 盲评子集 | W2 |
| **G-MSR-07** | 默认开启前盲评胜率 **≥ 55%** | **AC-MSR-BLIND** | W3 |
| **G-MSR-08** | `enabled=false` 时与 baseline **逐屏一致** | AC-MSR-01 | W0–W1 |

### 2.2 非目标

| # | 排除项 | 理由 |
|---|--------|------|
| OUT-01 | 用 MSR 替换 MCS soft 打分 / `pick_best_window` | 签名是硬筛，不是唯一决策 |
| OUT-02 | runtime 改 slot rect / 连续分区 solver | D-MGQ-02 / D-GCS-02 |
| OUT-03 | 默认开启 LSE / 新增 LSE 软乘子 | LSE 已冻结 |
| OUT-04 | 默认开启 Hungarian 或宣称其为观感主杠杆 | dogfood 边际低；D-MSR-08 |
| OUT-05 | Lab/主色聚类子分组 | V1.1；抖动风险 |
| OUT-06 | Studio 拖拽调屏序 | OQ-04；另 PRD |
| OUT-07 | 全册 narrate 后重跑 curate/MCS | 成本与抖动；仅同窗口 replan |
| OUT-08 | 选片 subset / DPP 上移 | 观感路线图独立项 |
| OUT-09 | GCS 海报面 / BRIC 挂 `used_legacy` | GCS 禁区 |
| OUT-10 | 另起第二套 usage / eligibility 引擎 | 消费 URO/MGQ，不复制 |
| OUT-11 | 印刷 PDF 相册流水线 | 导出仍走 Output Recipe / longshot |

---

## 3. 与相邻主题边界

| 主题 | 解决什么 | 本文是否改动 | 所有权 |
|------|----------|--------------|--------|
| **MSR（本文）** | 格式签名硬筛 + caption 优先 + 章内时间 page-group | **本 PRD 交付** | **MSR** |
| **MGQ** | `constraints.eligibility` + 屏内几何 soft + 评分台 | **不改**几何公式；签名硬筛 **先于** eligibility | MGQ |
| **URO** | `usage_rules` / UR-01 | **不改引擎**；管道顺序接在签名之后或并列硬层（见 §4.2） | URO |
| **GCS** | 离线扩 SKU + 海报 Writer | 新 SKU **必须**能派生签名入倒排；不碰 runtime BRIC | GCS |
| **LSE / P17** | 策略包 / CAP | **冻结**；Hungarian 保持可选 off | — |
| **Narrate** | 文案生成 | 提供 caption 信号；**不**改 LLM prompt 合同 | Narrate 业主 |
| **ChapterScreenPlanner** | 节奏 / 窗口尺寸 | 轨 C 可挂「邻近合并/切刀」钩子；不重写节奏状态机语义 | Planner |
| **BQP / 盲评** | 代表 trip + harness | Gate **复用 harness**；Gate 码独立 | BQP |

**对外一句话**：MSR 负责「这页该进哪类版式（可解释）」；MGQ 负责「同页几何更稳」；GCS 负责「库里有没有合适 SKU」；URO 负责「别违使用法说明」。

### 3.1 硬过滤顺序（**已冻结** · BLK-02）

```text
geometry 合法
  → signature L1/L2/L3（MSR）        reason: signature:*
  → usage_rules（URO）               reason: usage_rule:*
  → eligibility（MGQ）               reason: eligibility:*
  → soft：caption prefer（MSR）+ MCS/MGQ penalties + diversity
  → pick top
  → fallback / self-heal / replan / caption replan：仍经 signature + URO + eligibility
```

> **铁律**：soft / MMR / diversity / caption prefer **不得**把已产生 `signature:*` 拒绝的 pattern 重新纳入候选集。  
> 若某模板无派生签名（数据坏），记 `signature:invalid_template` 并 **剔除**，不得 silent 进 L3。

---

## 4. 总体方案

### 4.1 三层账本

```text
┌────────────────────────────────────────────────────────────┐
│ 硬路由（MSR 主交付）                                         │
│  format_signature L1/L2 · page_group 时间邻近（可选）         │
└────────────────────────────────────────────────────────────┘
┌────────────────────────────────────────────────────────────┐
│ 软偏好（MSR 次交付）                                         │
│  caption_layout_prefer · （可选）GPS 邻近 facing soft        │
└────────────────────────────────────────────────────────────┘
┌────────────────────────────────────────────────────────────┐
│ 软决胜 / 几何（既有 + MGQ）                                   │
│  score_candidate · geometric_quality · diversity             │
└────────────────────────────────────────────────────────────┘
┌────────────────────────────────────────────────────────────┐
│ 抛光（非默认）                                               │
│  Hungarian slot refine（lse_hungarian_assignment）           │
└────────────────────────────────────────────────────────────┘
```

### 4.2 架构增量

```text
LTE YAML
  └─ slots[].role: portrait|landscape|…  → 派生 formatSignature（SSOT）
  └─ （可选）formatSignature: "LLPP"      → override；须与派生一致（OQ-05）
  └─ captionAreas（SSOT · BLK-06）       → 带文案区；supportsCaption 仅可选别名

SignatureIndex（进程内 · BLK-07）
  └─ 于 registry load / LTE 注册表加载时构建一次（禁 per-window 全量重建）
  └─ exact["LLPP"] → [patternId…]（稳定序：registry 显式序或 pattern_id 字典序）
  └─ bag[(L,P,S) counts] → [patternId…]

MCS candidates
  └─ window assets → signature（taken_at 序）
  └─ lookup L1 → else L2 → else L3(size, 方向冲突剔除) + reason
  └─ caption prefer（同 level 可观测 · §6）
  └─ 既有 scorer / MGQ / pick
```

---

## 5. 轨 A · 格式签名索引（主交付）

### 5.0 L1 语义铁律（**已冻结** · BLK-03）

| 概念 | 定义 |
|------|------|
| **窗口 `formatSignature`** | 窗口资产按 `taken_at` 升序（缺失则 `asset_id`）映射之字母串 |
| **模板签名** | `slots` 按 `index` 升序之 role 字母串 |
| **L1 exact** | **仅**表示两串相等；**不**表示资产按该序填入槽位 |
| **填槽合同** | 独立：同签名候选内由 ordering / role 对齐（及可选 Hungarian）完成 |

decision_log **三件套**（可解释性最低集）：`formatSignature` · `signatureMatchLevel` · 最终 asset 序。

### 5.1 字母表（V1 · BLK-05）

| 字母 | 含义 | `aspectKind` 来源 |
|------|------|-------------------|
| `L` | landscape | `landscape` **或** `panorama` |
| `P` | portrait | `portrait` **或** `tall` |
| `S` | square | `square`（OQ-01·A） |

- 签名长度 **必须**等于窗口照片数 N。  
- **有序**：`LP` ≠ `PL`。  
- Bag 键：`(count_L, count_P, count_S)`，与 YAML `mix` 对齐（square 计入 S；panorama/tall 分别计入 L/P）。  
- **不**新增第四字母（避免索引碎片化）；可选诊断字段 `aspectKindRaw`。

### 5.2 模板侧派生规则

对每个 LTE pattern：

1. 按 `slots` 声明序（index 升序）读取 `role` → 映射为 `L`/`P`/`S`（`main`/`any` 等角色：取 `eligibleAspectKinds` 单值则可确定；多值则 **不进 L1**，仅进 L2/L3，reason `signature:ambiguous_slot`）。  
2. 与 `mix` 交叉校验：bag 计数必须一致，否则 validator fail-loud。  
3. 索引构建失败的模板不得 `lte_rollout_eligible` 静默存活（W1 起）（BLK-07）。  
4. W3 默认开前：核心 N∈{2,3,4,5,6} 的 ga 模板 **L1 可派生率 100%**。

### 5.3 窗口侧签名

1. 取窗口 `asset_ids`。  
2. 按 **拍摄时间升序**（缺失时间则稳定次级键：`asset_id`）（OQ-02·A）。  
3. 映射 `aspectKind` → 字母（§5.1）→ `formatSignature`。  
4. 写入 decision_log：`formatSignature`、`signatureMatchLevel`（`exact|bag|size|none`）、最终 asset 序。

### 5.4 Lookup 合同

| 级别 | 条件 | 行为 |
|------|------|------|
| **L1 exact** | 索引命中有序签名且 `photoCount` 匹配 | 候选集 = 命中列表（稳定序） |
| **L2 bag** | L1 空；mix 计数命中 | 候选集 = bag 列表；reason `signature:bag_fallback` |
| **L3 size** | L2 空 | 自 `patterns_for_window_size` 取同 N，再 **剔除方向冲突**（BLK-04）；reason `signature:size_fallback` |
| **none** | 无任何模板 | 既有 self-heal / legacy；不得伪造签名命中 |

**方向冲突（BLK-04）**：对任一字母，若「窗口计数为 0 而模板 bag 要求 >0」，或等价全 P↔全 L 冲突 → 剔除，reason `signature:direction_conflict`。  
**禁止**：L3 把方向冲突模板「复活」进候选。

**reason taxonomy（BLK-07 · 冻结枚举）**：  
`signature:miss` · `signature:bag_fallback` · `signature:size_fallback` · `signature:direction_conflict` · `signature:invalid_template` · `signature:ambiguous_slot`  
（可增补但须进 ACCEPTANCE）。

### 5.5 与 `try_order_for_pattern` 的收敛（D-MSR-04）

| 阶段 | 合同 |
|------|------|
| W0 | 双轨并存；签名只 **shadow**；`enabled=false`；**零行为差**（BLK-08） |
| W1 | `enabled=true`（dogfood）时：**候选入口权威 = SignatureIndex**；其后才对已入围 pattern 调 ordering |
| ordering 职责 | 仅同签名内 asset↔slot 对齐与既有 burst/hero 启发式；**不得**再充当隐式选版库 |
| 分账 | `signature:*` vs `ordering_failed` 不得混用 |
| W2 | 无签名覆盖的手写分支列入 **可勾选迁移清单**；新 ga 模板 **禁止**只加 Python |
| W3 | 迁移清单为默认开输入；核心 N L1 可派生率 100% |

---

## 6. 轨 B · 图文一体选版（Claim 12 映射）

### 6.1 信号（OQ-03·A）

窗口 **caption-active** 当且仅当：

- 窗口内任一 asset 存在非空 `caption`（**trim** 后），或  
- 该屏规划已绑定非空 lead/hook（若 curate 阶段尚无，则阶段 2 再判）。

可选诊断：`captionActiveSource` ∈ {`asset`,`lead`,`hook`}。章级文案 **不**单独驱动全章换版。

### 6.2 Pattern 能力标记（BLK-06）

| 优先级 | 合同 |
|--------|------|
| **SSOT** | YAML 非空 **`captionAreas`** ⇒ 带文案区 |
| **别名** | `usage.supportsCaption: true` 可选；若存在须与 `captionAreas` **validator 双向一致** |
| **兼容期** | editorial 白名单须 **有限列举 + sunset**；**禁止**无限 `kind`/`displayName` 字符串匹配作主路径 |

### 6.3 行为分层

| 模式 | 行为 | 阶段 |
|------|------|------|
| **prefer（默认）** | caption-active 时，**同 `signatureMatchLevel` 内**带文案区候选须可观测优先：胜出 `patternId` ∈ 带文案区集合，**或** score **严格大于**无文案区最佳候选（阈值 IMPLEMENTATION 钉死；AC-MSR-06） | W1 |
| **require（可选）** | 同签名存在带文案区 SKU 时硬滤无文案区；否则降级 prefer | W2 · 另 AC |

竖图 + caption：元数据可表达时优先「portrait 槽与 caption 区相邻」；否则退化为任意带文案区。  
无文案时 **不**强制 caption layout（纯图册不变稀）。

### 6.4 与 narrate 的两阶段合同（D-MSR-06）

```text
阶段 1 · curate
  └─ 若上游已有用户/导入 caption → 直接 caption-aware 选版
  └─ 否则按无文案路径选版（可标记 screen.flags.captionFlexible=true）

阶段 2 · narrate 后（mosaic.signature_routing.caption.replan_after_narrate）
  └─ 默认 false（产品：跳变不扰民）
  └─ 开启时：仅 captionFlexible 且现已 caption-active 的目标屏
  └─ 复用 replan_screen / score_window_candidates（薄封装）；alt 仍经硬过滤
  └─ 同 asset 集合；禁止改章序、跨屏抽片、改非目标屏
```

---

## 7. 轨 C · 章内 page-group（FIG.14 次级准则 · 子集）

### 7.1 V1 范围

| 准则 | V1 | 说明 |
|------|----|------|
| 时间短间隔同组 | **做** | 章内序列上，相邻照片间隔 ≤ `page_group.max_gap_seconds` 倾向同一窗口 |
| GPS 邻近 | **soft / 可选** | 已有 geo 章级；屏级仅 soft prefer facing，不强制 |
| Lab 色调 | **不做** | V1.1 / tone_continuity |
| 用户拖拽调页 | **不做** | OQ-04 |

### 7.2 与 ChapterScreenPlanner（BLK-08）

- MSR **不**替换节奏状态机（3/4/5/6/8/9 配额）。  
- 提供钩子：`propose_page_groups(chapter_assets) → groups[]`，planner 在切窗时 **优先不拆组**。  
- **冲突优先级（冻结）**：**节奏配额 / 合法 N 集合优先**；page_group 不得强行破配额；破组记 `page_group:split`。  
- 默认 `page_group.enabled=false`；与 `signature_routing.enabled` **可分可合**（见 §8.1）。

---

## 8. 配置、数据与埋点

### 8.1 配置（冻结草案）

```yaml
mosaic:
  signature_routing:
    enabled: false                    # 总开关；false = 与 baseline 逐屏一致（BLK-01）
    match:
      exact: true
      bag_fallback: true
      size_fallback: true             # L3；须剔除 direction_conflict（BLK-04）
    square_letter: S                  # OQ-01·A
    signature_asset_order: taken_at   # OQ-02·A；≠ 填槽序（BLK-03）
    caption:
      mode: prefer                    # prefer | require | off
      replan_after_narrate: false     # 默认 off（D-MSR-06）
    page_group:
      enabled: false                  # 节奏配额优先（BLK-08）
      max_gap_seconds: 120
      gps_soft: false
    shadow_log: true                  # W0：enabled=false 仍写签名与本可命中集；零副作用
```

**W0 编码范围（冻结）**：开关骨架 + 字母表/派生 + shadow_log + AC-MSR-01/11/13。  
**W0 禁止**：硬筛进候选入口、caption prefer 改分、page_group 改窗、caption replan、写入 `layout.scoring`、runtime 改 rect。

### 8.2 decision_log / 诊断字段（建议）

| 字段 | 含义 |
|------|------|
| `formatSignature` | 窗口有序签名 |
| `signatureMatchLevel` | `exact\|bag\|size\|none` |
| `signatureCandidateCount` | 硬筛后候选数 |
| `captionActive` | bool |
| `captionPreferApplied` | bool |
| `pageGroupId` / `pageGroupSplit` | 轨 C |
| `rejectReasons[]` | 含 `signature:*` |

### 8.3 确定性

- 索引遍历、候选排序键必须稳定（`pattern_id` 字典序或 registry 显式序）。  
- Shadow 日志不得影响选版结果。  
- `enabled=false`：跳过硬筛与 caption prefer、page_group；允许 shadow_log。

### 8.4 埋点 / 实验

| 指标 | 用途 |
|------|------|
| `signature_exact_rate` | L1 命中率 |
| `signature_bag_rate` | L2 占比（过高 → 库缺有序 SKU） |
| `signature_size_fallback_rate` | L3；与 `used_legacy` 分账 |
| `caption_prefer_apply_rate` | 轨 B 覆盖 |
| `ordering_failed_rate` | 应随双轨收敛下降 |
| `aspectPatternMatchRate` | 既有；期望 ↑（非 Gate） |

---

## 9. 里程碑与验收

### 9.1 工作包

| 里程碑 | 内容 | 预估 | Go | No-Go |
|--------|------|------|----|-------|
| **W0** | 字母表 + 派生 + shadow_log；开关骨架；IMPLEMENTATION 任务卡（可同开） | 1–1.5d | 默认 off；AC-MSR-01/11/13；**零硬筛** | 争议改 LSE；写生产硬筛 |
| **W1** | SignatureIndex + L1/L2/L3 挂候选；caption prefer；taxonomy | 1.5w | AC-MSR-01～07、12～14 | soft 绕过签名；runtime 改 rect |
| **W2** | caption replan 可选；page_group（节奏优先）；ordering 迁移清单；≥3 模板 `captionAreas` | **1～1.5w** | AC-MSR-08～10 | 全册重跑；Lab 进 V1 |
| **W3** | 盲评（含混向+图文子集）+ 默认开启决策 | 3–5d | **AC-MSR-BLIND ≥55%** 或保持 off | 仅用 proxy 微涨当发布依据 |

**拆文节奏**：W0 可以本文 §9 为工程挡门；**任何 W1 代码合入 master 前**必须存在：

- `IMPLEMENTATION-MCS-SIGNATURE-ROUTING-V1.md`
- `ACCEPTANCE-MCS-SIGNATURE-ROUTING-V1.md`

### 9.2 工程验收

| ID | 条款 |
|----|------|
| **AC-MSR-01** | `signature_routing.enabled=false` 时，固定 fixture 与 baseline 逐屏一致（patternId + asset 序 + 固化几何） |
| **AC-MSR-02** | 同一窗口资产集，签名对 `taken_at` 序确定性可复现；缺时间时 `asset_id` 次键稳定 |
| **AC-MSR-03** | ≥5 个 ga 模板可从 slots 派生签名，并通过 validator 与 `mix` bag 一致 |
| **AC-MSR-04** | 窗口签名 `LLPP` 时，L1 候选仅含模板签名为 `LLPP` 的模板（**不**断言填槽序=taken_at 序） |
| **AC-MSR-05** | L1 空且 bag 命中时，`signatureMatchLevel=bag`，且不出现方向计数冲突模板 |
| **AC-MSR-06** | caption-active + `prefer`：存在同 `signatureMatchLevel` 带文案区候选时，胜出 `patternId` ∈ 带文案区 **或** score 严格大于无文案区最佳（BLK-06） |
| **AC-MSR-07** | decision_log 含 `formatSignature`、`signatureMatchLevel`、最终 asset 序 |
| **AC-MSR-08** | `replan_after_narrate=true` 时仅改目标屏；非目标屏 patternId+asset_ids 不变；目标屏 asset 集合不变 |
| **AC-MSR-09** | `page_group.enabled=true` 时，间隔 ≤ 阈值的连拍优先同窗；与节奏冲突时记 `page_group:split` 且合法 N 不被破坏 |
| **AC-MSR-10** | curate P95 增幅 ≤ +10%（相对 MSR off；固定数据集/命令进 ACCEPTANCE） |
| **AC-MSR-11** | 默认配置下 `layout.scoring.enabled is false`；MSR 字段仅出现在 `MosaicConfig` 路径（BLK-01） |
| **AC-MSR-12** | 启用硬筛时，legacy / self-heal / `replan_screen` / caption replan 各 ≥1 负例：不得包含 `signature:*` 已拒 pattern（BLK-02） |
| **AC-MSR-13** | Shadow：`enabled=false` ∧ `shadow_log=true` → screens 哈希不变，且诊断含「本可 L1」列表 |
| **AC-MSR-14** | L3：全 P 窗口不得选出全 L（或方向冲突）模板；断言 `signature:direction_conflict` 或候选集不含冲突项（BLK-04） |

### 9.3 产品门禁

| ID | 条款 |
|----|------|
| **AC-MSR-BLIND** | 与 BQP/MGQ/URO **共用代表 trip 集 + harness**；on vs off **仅差** `signature_routing`；胜率 **≥ 55%**；Gate 码独立；ACCEPTANCE 须钉：计票单位、平局/弃权、样本量；须含 **混向窗 + 有图注** 子集，且图文子集 **不显著劣于 off** |
| **AC-MSR-DIAG** | exact/bag/size/direction_conflict 比率报表可读；**不**以 proxy 单独作为 merge / 默认开依据 |

### 9.4 主题 Go / No-Go

| 里程碑 | Go | No-Go |
|--------|-----|-------|
| W0 | D-MSR/OQ 已冻结；开关默认 off；shadow 零副作用；**不写生产硬筛** | 未决落点仍改 LSE；硬筛进主路径 |
| W1 | AC-MSR-01～07、11～14；ACCEPTANCE+IMPLEMENTATION 已存在 | soft 绕过硬筛；无迁移合同 |
| W2 | AC-MSR-08～10；节奏优先可证 | 全册重跑；Lab 进 V1 |
| W3 默认开 | AC-MSR-BLIND（含子集合同） | 仅有单元测试绿 / 仅有 proxy |

---

## 10. 风险与缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| 库缺有序 SKU → L2/L3 过高 | 签名层形同虚设 | GCS 轨 A 按签名空洞补库；监控 bag/size rate |
| 硬筛过严 → legacy 飙升 | 观感回退 | 默认保留 L3；reject 看板；BLK 对齐 AC-MSR-12 |
| 方图 / ambiguous role 过多 | L1 覆盖差 | OQ-01；ambiguous 仅 L2；validator 推模板修 role |
| caption replan 抖动 | 用户感知「文案后版式跳变」 | 默认 replan off；仅 captionFlexible；盲评单独切片 |
| 与 MGQ/URO 硬层叠乘 | 候选枯竭 | 分账 reason；权重保守；管道顺序写死 |
| 误把 Hungarian 当主故事 | 预期管理失败 | D-MSR-08；对外叙事锁定「签名 + 图文」 |
| 手写 ordering 债务反弹 | 双轨永久化 | W2 迁移清单作 W3 门禁输入 |

---

## 11. 实施顺序建议

| 顺序 | 包 | 依赖 | 备注 |
|------|----|------|------|
| 1 | 跨职能评审冻结 D-MSR / OQ | ✅ 2026-07-18 | 见评审纪要 |
| 2 | W0 开关 + 派生 + shadow | 无 | **可 Kickoff（shadow only）** |
| 3 | 拆 IMPLEMENTATION | — | W0 同开 |
| 4 | W1 索引挂候选入口 + caption prefer | W0 | **拆 ACCEPTANCE（BLK-08）** |
| 5 | W2 page_group + caption replan | W1 | 可选；估时 1～1.5w |
| 6 | W3 盲评与默认开启决策 | W1+W2 | 未过 Gate 则保持 off |

若只能完成一项：优先 **W1（SignatureIndex 硬筛挂 MCS 候选入口）**；叙事锁定「签名硬筛 + 图文优先」，勿吹 LLPP 精确率或 Hungarian。

---

## 12. 成功画像

1. **2 横 2 竖** 窗口稳定进入 `LLPP` / `PPLL` 等匹配页型，而不是靠事后裁切硬撑；  
2. **有图注** 的屏更多落在「图 + caption 区」版式，而不是密铺后再挤字；  
3. **短时连拍** 更少无故拆屏；  
4. 设计师加模板时 **主要改 YAML role/mix**，不必再开一条 Python 选版特例；  
5. 失败可解释：`signature:miss` / `bag_fallback` / `size_fallback` 可看板。

---

## 附录 A · US8131114 映射表（备查）

| 专利步骤 | Travelogue 落点 | MSR 轨 |
|----------|-----------------|--------|
| 1415 主准则排序 | ingest / taken_at | 签名序（OQ-02） |
| 1420 次级分页 | curate 章 + 轨 C 时间组 | C |
| 1427 版式库 | LTE YAML | A |
| 1430 槽数 + 格式签名选版 | SignatureIndex L1/L2 | A |
| 1435 图 + 文填入 | narrate + 轨 B | B |
| 1440 完成相册 | render / Output Recipe / longshot | 非本 PRD |
| Claim 12 图注一体 | caption-aware prefer/replan | B |
| FIG.8 顺序填槽 | 非目标；Hungarian 可选 | — |
| FIG.9/10 决策树 | 签名索引 + 有限 SKU 路由 | A |

| 专利弱项 | Travelogue 已有/规划 | 本 PRD 态度 |
|----------|---------------------|-------------|
| 无 AI 选片 | HDBSCAN + CLIP + Phase 9 | 不重复建设 |
| 无语义叙事 | narrate + arc | 只接 caption 信号 |
| 顺序填槽 | Hungarian（默认 off） | 不当主杠杆 |
| 印刷终点 | Playwright longshot 等 | 不改导出主链 |

---

## 附录 B · 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1.0 | 2026-07-18 | 初稿；待跨职能评审拍板 D-MSR-01～10 与 OQ-MSR-01～05 |
| v0.2.0 | 2026-07-18 | 跨职能 Conditional Go；BLK-01～08 回写；OQ 全关；L1≠填槽序；L3 方向冲突；captionAreas SSOT；可 Kickoff W0 shadow |
