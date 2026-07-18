# PRD-MCS-SIGNATURE-ROUTING-V1 · 跨职能评审纪要

| 属性 | 内容 |
|------|------|
| **文档** | [PRD-MCS-SIGNATURE-ROUTING-V1.md](../PRD-MCS-SIGNATURE-ROUTING-V1.md) |
| **模板** | [mcs-signature-routing-v1-review-TEMPLATE.md](./mcs-signature-routing-v1-review-TEMPLATE.md) |
| **对标** | Shutterfly US8131114 · Smart photobook creation（LLPP · Claim 12） |
| **相邻挡门** | [MGQ](../PRD-MCS-GEOMETRIC-QUALITY-V1.md) · [GCS](../PRD-GENERATIVE-COLLAGE-SURFACES-V1.md) · [URO](../PRD-USAGE-RULES-LAYOUT-OPTIMIZATION.md) · [LTE P16](../PRD-PHASE16-layout-template-engine.md) · [LSE 处置](../P17-LSE-处置建议.md) · [观感提升路线图](../观感提升路线图.md) |
| **评审版本** | **v0.1.0 Draft** → Must-Fix 已回写 **[PRD v0.2.0](../PRD-MCS-SIGNATURE-ROUTING-V1.md)** |
| **日期** | 2026-07-18 |
| **结论** | **有条件通过（Conditional Go）** · **可 Kickoff W0**（开关骨架 · 派生规则 · shadow_log；本轮不写生产硬筛） |
| **编码** | **可 Kickoff W0（shadow only）**；W1 硬筛合入前须拆 IMPLEMENTATION / ACCEPTANCE（BLK-08） |
| **参评角色** | 产品 · 算法 · 架构 · 开发 · 测试/QA · 用户体验/交互 · 典型用户（旅行厚册读者 · 图文叙事册作者） |
| **评审方式** | 分席只读（PRD §0.1 D/OQ · §2 · §5–§7 · OUT）· 对照现网 MCS / `try_order_for_pattern` / MGQ·GCS·LSE 纪律 · 跨职能模拟联评结案 |
| **记录人** | 产品 / 算法 / 架构 / 工程 / UX 联合纪要 |
| **本纪要状态** | **已结案** · BLK-01～08 成立并回写 PRD v0.2.0 |

---

## 0. 会前宣读（主持人 · 3 分钟）

1. **切口**：学 Shutterfly 的 **签名硬路由 + 图文一体**，不是整段重写成印刷相册流水线。  
2. **勿重开**：MCS 权威选窗；LSE 冻结；禁 runtime 改 `rect`；Hungarian 默认 off、非卖点。  
3. **三轨**：A=有序签名索引；B=caption-aware；C=章内时间 page-group（Lab 色调不做 V1）。  
4. **本场必拍**：D-MSR-01～10；关闭 OQ-MSR-01～05。  
5. **本轮默认**：评审 + 文档回写；W0 仅 shadow，不写生产硬筛。

---

## 1. 总评（一句话）

> **方向正确、落点与非目标干净；最大算法漏洞是「把有序签名当成填槽契约」——现网填槽是 bag+role，混合页 bag 才是主力。BLK-01～08（含 L1≠填槽序、L3 方向冲突禁入、captionAreas SSOT、page_group 节奏优先）回写 v0.2.0 后可 Kickoff W0 shadow；W1 前拆文；默认开绑独立盲评。**

---

## 2. 分席表决

| 席位 | 表决 | 一句话 |
|------|------|--------|
| **产品** | Conditional Go | 对标切口对；对外叙事锁「签名硬筛 + 图文优先」，勿吹 LLPP 精确率或 Hungarian |
| **算法** | Conditional Go | 切口对；须冻结 L1≠填槽序、L3 方向冲突、panorama/tall 字母表、page_group vs 节奏 |
| **架构** | Conditional Go | 与 MGQ/URO/GCS 纪律对齐；钉挂载点、Index 生命周期、taxonomy、replan 边界 |
| **开发** | Conditional Go | W0/W1 估时合理、W2 偏紧；最大风险 try_order 双轨与硬层枯竭；同意 W0 shadow only |
| **测试 / QA** | Conditional Go | AC/BLIND 协议须可测；AC-06/08/12 字面加固，防 prefer 假绿 |
| **用户体验 / 交互** | Conditional Go | 有字进带文案版须可感知；caption 跳变默认关；解释作 V1 无拖拽的补偿 |
| **用户 · 旅行厚册** | Conditional Go | 要少狠裁、连拍别碎；术语不必见，观感要稳 |
| **用户 · 图文叙事册** | Conditional Go | 有字别密铺；字一出整页改脸不可接受（默认不 replan） |

**汇总**：**八席一致 Conditional Go**。MF 已回写 v0.2.0 → **可 Kickoff W0（shadow）**；未回写前不批无条件 Go。

---

## 3. 全场共识

1. **签名 = 硬路由契约**，不是第二套 MCS soft；软决胜留给 MGQ。  
2. **L1 有序签名 ≠ 填槽序**；填槽仍由同签名内 ordering / role（及可选 Hungarian）完成。  
3. **混合页诚实叙事**：bag 可为实际主力；勿对外假装「处处 LLPP 精确」。  
4. **L3 size 兜底**须剔除方向冲突模板（`signature:direction_conflict`）。  
5. **caption prefer** 须同 `signatureMatchLevel` 内可观测优先；replan **默认 off**；禁全册重跑。  
6. **page_group**：节奏配额优先；仅「优先不拆」合法 N。  
7. **Hungarian / LSE 非本主题卖点**。  
8. **W0 ≠ 主题完成**：W0=shadow+开关；W1=硬筛挂候选；W2=page-group/replan；W3=盲评。  
9. **本轮只做评审/文档回写**；生产硬筛另排 W1。

**会中新增共识**：

- `panorama→L`、`tall→P`（不新增第四字母）。  
- caption SSOT 字段钉死为 **`captionAreas`**（`supportsCaption` 仅可选别名）。  
- SignatureIndex 于 registry load 时构建一次；禁 per-window 全量重建。  
- decision_log 三件套：`formatSignature` / `signatureMatchLevel` / 最终 asset 序。  
- 盲评须含「混向窗 + 有图注」子集；图文子集不得显著回退。

---

## 4. Must-Fix（已成立 · 已回写 PRD v0.2.0）

| ID | 议题 | 来源席位 | 要求（冻结一字面） | 成立 |
|----|------|----------|-------------------|------|
| **BLK-01** | 落点写死 MCS | 架构 / 产品 | 唯一配置根 `mosaic.signature_routing`（`MosaicConfig`）；禁默认同步进 LSE / `layout.scoring`；AC-MSR-11 | ✅ |
| **BLK-02** | 硬过滤顺序 + 守门 | 架构 / 算法 | 顺序：geometry → **signature** → URO → eligibility → soft；soft/MMR/diversity/**caption prefer** 不得把 `signature:*` 已拒 pattern 拉回；fallback/self-heal/replan 同效（AC-MSR-12） | ✅ |
| **BLK-03** | L1 语义：签名序 ≠ 填槽序 | 算法 / 开发 | 窗口签名=taken_at 字母串；模板签名=slots index 序字母串；**L1 仅两串相等**；填槽合同独立 | ✅ |
| **BLK-04** | L3 方向冲突禁入 | 算法 / QA | `size` 级候选 bag 不得与窗口方向冲突；reason `signature:direction_conflict`；负例进 AC | ✅ |
| **BLK-05** | 字母表扩展 | 算法 / UX | `L/P/S`；**`panorama→L`，`tall→P`**；方图=`S`（OQ-01·A） | ✅ |
| **BLK-06** | caption SSOT + prefer 可测 | 架构 / UX / QA | SSOT=`captionAreas`；同 level 有文案区候选时胜出须 ∈ 带文案区（或 score 严格优于无文案区最佳）；replan 默认 off | ✅ |
| **BLK-07** | Index 生命周期 + taxonomy | 架构 / 开发 | registry load 构建；稳定序；reason 枚举冻结（含 `direction_conflict` / `ambiguous_slot` / `invalid_template`） | ✅ |
| **BLK-08** | 拆文 + W0 范围 + page_group | 开发 / QA / 算法 | W1 merge 前拆 ACCEPTANCE+IMPLEMENTATION；W0=shadow only；**节奏配额优先于 page_group** | ✅ |

---

## 5. Should-Fix（不单独挡 Kickoff）

1. 监控 `signature_exact_rate`；exact≪bag 时对内改叙事为「bag 硬匹配为主」。  
2. GCS 轨 A 按签名空洞补有序 SKU；禁用 BRIC/`used_legacy` 补洞。  
3. W2 `require` 模式与 prefer 分 AC；防几何罚系统性打没 caption SKU（诊断计数）。  
4. 轨 B 兼容白名单有限列举 + sunset；禁无限 `displayName` 匹配。  
5. W2 估时调为 **1～1.5w**，或拆「replan 先 / page_group 后」。  
6. Studio 调屏另立 PRD；V1 提供只读匹配级人话解释作补偿。  
7. AC-MSR-BLIND：trip 集 SSOT、计票单位、平局规则写入 ACCEPTANCE；图文子集不劣于 off。  
8. MGQ/URO 文档侧交叉引用硬过滤前插序（实现期）。

---

## 6. D-MSR / OQ 拍板汇总

### 6.1 决策

| 决策 | 本场决议 |
|------|----------|
| **D-MSR-01** | **采纳** — 全部挂 `MosaicConfig`；禁默认进 LSE |
| **D-MSR-02** | **修订采纳** — 有序 `P/L/S`；+ panorama→L / tall→P（BLK-05） |
| **D-MSR-03** | **修订采纳** — L1→L2→L3；+ L1≠填槽序（BLK-03）；+ L3 方向冲突禁入（BLK-04）；承认 bag 可为混合页主力 |
| **D-MSR-04** | **修订采纳** — W1 起 SignatureIndex=候选入口权威；ordering 仅同签名内对齐；`signature:*` 与 `ordering_failed` 分账 |
| **D-MSR-05** | **修订采纳** — caption 优先；同 level 可观测偏置（BLK-06） |
| **D-MSR-06** | **修订采纳** — 两阶段友好；replan 默认 off；仅同窗；禁全册重跑/改章序/跨屏抽片 |
| **D-MSR-07** | **修订采纳** — 时间邻近钩子；**节奏配额优先**（BLK-08） |
| **D-MSR-08** | **采纳** — Hungarian 默认 off；非卖点 |
| **D-MSR-09** | **采纳** — off 可先 merge；默认开须 AC-MSR-BLIND≥55% |
| **D-MSR-10** | **采纳** — fallback 不得复活 `signature:*` 已拒 pattern |

### 6.2 开放问题

| OQ | 决议 |
|----|------|
| **OQ-MSR-01** | **关闭·A** — `square→S`；库无 S 槽则 L2 |
| **OQ-MSR-02** | **关闭·A** — 窗口内 `taken_at` 升序；缺时 `asset_id`；**且**签名序≠填槽序 |
| **OQ-MSR-03** | **关闭·A** — asset.caption（trim）或屏已绑定 lead/hook；章级文案不驱动全章换版；`captionActiveSource` 可记 |
| **OQ-MSR-04** | **关闭·B** — V1 不做 Studio 调屏；另 PRD |
| **OQ-MSR-05** | **关闭·A** — `slots[].role` 派生为主；显式 `formatSignature` 仅 override + validator fail-loud |

---

## 7. 分席要点摘要

### 7.1 产品
- 用户痛点 MSR-P-01/03 成立；对外主故事：「少选错方向页型 + 有字进带文案版」。  
- 禁止宣传「已工业级处处 LLPP」直至 L1 覆盖可信；禁止 Hungarian 当卖点。

### 7.2 算法
- 最大风险：有序签名神话化 vs 现网 bag+role 填槽。  
- W1 第一刀=签名硬筛；caption prefer 作探针；`require` 排 W2。

### 7.3 架构
- 边界清晰：MSR / URO / MGQ / GCS 不抢轨。  
- W0 批准范围：开关 + 派生 + shadow；禁硬筛进主路径。

### 7.4 开发
- 挂点：`generate_window_candidates` 前/内接 Index；caption replan 薄封装复用 `replan_screen`。  
- 例：模板槽序 `PLLP` vs 窗口 `LLPP` → L1 空、L2 bag 命中属预期。

### 7.5 测试 / QA
- AC-06 须胜出断言或严格分差；AC-12 负例矩阵；BLIND 协议进 ACCEPTANCE。  
- Shadow：screens 哈希不变 + 诊断含「本可 L1」。

### 7.6 用户体验 / 交互
- 有字优先须盲评子集可感知；跳变默认不扰民。  
- V1 无拖拽 → 匹配级人话解释作补偿。

### 7.7 典型用户
- 厚册：裁切/连贯；叙事册：字进版、勿静默换脸。

---

## 8. 会后动作

| # | 动作 | 负责人 | 状态 |
|---|------|--------|------|
| 1 | 回写本纪要结论与拍板一字面 | 记录人 | ✅ |
| 2 | BLK-01～08 合入 PRD → **v0.2.0** | 产品 / 算法 / 架构 | ✅ |
| 3 | Kickoff W0：补 `IMPLEMENTATION-…` 任务卡（可与 W0 同开） | 开发 | □ |
| 4 | W1 merge 前拆 `ACCEPTANCE-MCS-SIGNATURE-ROUTING-V1.md` | 测试 / 开发 | □ |
| 5 | README 状态行更新为 Conditional Go | 产品 | ✅ |
| 6 | MGQ/URO 交叉引用硬过滤前插（实现期） | 架构 | □ |

---

## 9. 签名栏（模拟联评 · 结案）

| 角色 | 态度 | 日期 |
|------|------|------|
| 产品 | Conditional Go | 2026-07-18 |
| 算法 | Conditional Go | 2026-07-18 |
| 架构 | Conditional Go | 2026-07-18 |
| 开发 | Conditional Go | 2026-07-18 |
| 测试 / QA | Conditional Go | 2026-07-18 |
| 用户体验 / 交互 | Conditional Go | 2026-07-18 |
| 用户 · 旅行厚册 | Conditional Go | 2026-07-18 |
| 用户 · 图文叙事册 | Conditional Go | 2026-07-18 |

---

## 附录 · 分席详细意见出处

本场为跨职能模拟联评；详细论证归档于会话评审输出，结案效力以本文 §4～§6 一字面与 PRD v0.2.0 为准。
