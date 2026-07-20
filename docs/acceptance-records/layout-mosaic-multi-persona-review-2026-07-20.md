# 现有排版 / 拼图多方评审纪要 · 2026-07-20

| 属性 | 内容 |
|------|------|
| **对象** | Travelogue 现行 screens 引擎 + LTE/MCS 拼图 + 三阅读模式（非 HGM） |
| **形式** | 多角色并行评审（两轮） |
| **状态** | **八方完成** · 已落成专项 PRD：[PRD-LAYOUT-TRUST-NARRATIVE-V1.md](../PRD-LAYOUT-TRUST-NARRATIVE-V1.md) |
| **参考 demo** | `demo-65db8fd377`：多为 plate / 单图 / 三叠 / 双竖，**hero mosaic ≈ 0** |

## 参评角色

### 第一轮 · 用户 / 产品 / 设计

| 角色 | 状态 | 结论摘要 |
|------|------|----------|
| 家庭旅行记录者 | ✅ | 干净能发；嫌黏、拼图偶乱；发群偏拆开看清 |
| 旅行摄影爱好者 | ✅ | 骨架对；breath 失效、全屏等权、长图拆拼伤图 |
| UX 体验研究 | ✅ | 版式多、间距单一 → 两头不讨好；拼图要有内聚+hero |
| 产品经理 | ✅ | 高潜力资产、高运维负担；先可信基线，再扩模板 |
| UI/UX 设计 | ✅ | 骨架对、节奏未收敛；冻结扩库，修 breath + 版式角色表 |

### 第二轮 · 架构 / 算法 / 管线

| 角色 | 状态 | 结论摘要 |
|------|------|----------|
| 架构专家 | ✅ | 分层意图清、落地双轨；债在「权威分散 + 静默失败」；要 Narrative Contract |
| 算法专家 | ✅ | 双份评审收敛：局部安全≠叙事节拍；≈0 因几何门+3 槽 legacy 兜底（非 P21 用尽） |
| 管线专家 | ✅ | 最脆 sync/CSS 与 config→curate；fail-open；门禁需闭合 |

---

## 1. 高度共识（两轮合并）

1. **现有游记语法大体正确**：单图大屏、票根分章、不花哨——用户认「这是干净相册/画册」。  
2. **主要短板不是「模板不够」**，而是：  
   - 屏缝 / breath **过弱**（≈9px），节奏扁平；  
   - **拼图出场不稳定**（能力名义有、demo 常近乎 0）；  
   - **三模式不一致**（scroll 合成 / present 保屏 / longshot 拆 slot）；  
   - **修好又弄丢**（config silent default + CSS sync 截断 + 门禁未闭合）。  
3. **拼图应收敛 SKU、强化时机**：有主有次、同场景连拍；反对继续扩 7+/8/9 宫与均等密格默认。  
4. **导出前需要「微信长什么样」预览**：长图拆拼要可预期；架构侧需 Narrative Contract（`exportHints` / `preserveGroup`）。  
5. **下一阶段纪律**：先 **fail-loud 可信基线** → 叙事节拍 / hero 曝光 → 再谈扩库与 HGM。  
6. **拼图≈0 的主因不是 P21 封顶过狠**（算法）：而是进窗前抢占、几何/SKU 硬拒、legacy 回退；P21 在 used≈0 时几乎不生效。

---

## 2. 分角色要点

### 2.1 家庭旅行记录者

- **喜欢**：单图大屏省心；票根能找「第几天」；整体不装。  
- **别扭**：屏缝太黏；节奏平；拼图裁脸。  
- **拼图好看**：同时同地、有主次、2–3 张；**乱**：连拍硬凑、风格混杂、格子太密。  
- **发群**：更偏拆开看清，但别拆到看不出一组；简单并排可保留，四/六宫格宁可拆。  
- **建议**：换章/换地点多喘气；拼图宁少勿凑；导出前微信预览。

### 2.2 旅行摄影爱好者

- **总体**：骨架对，成品仍偏「自动排版」；精选 demo 几乎无 hero mosaic，像只敢安全单张堆叠。  
- **喜欢**：`landscape-1` 基本盘；plate + 票根有杂志感；P21 / `hero_first` 方向对。  
- **讨厌**：breath ≈9px 名存实亡；全屏等权、杰作看不见；拼图要么不出、出了又怕裁伤构图。  
- **屏型建议**：单图默认主力；三叠仅同场同质连拍；双竖给人物成对；多宫必须有 hero，精选集全书 ≤1–2 次；默认 `hero_first`。  
- **微信长图**：接受拆功能，不接受当同一部作品；要导出前双预览。  
- **建议**：先修 rhythm；强制网页 vs 长图双预览；精选相册（如 kept&lt;80）分流排版策略。

### 2.3 UX 体验研究

- **读故事**：章界 OK，章内段落不可扫视识别；版式切换≠叙事切换。  
- **看相册**：无展室态；多槽屏抢夺单图纪念权。  
- **拼图降负荷**：同场景 + hero + 稀疏 + 前后缓冲。  
- **拼图增负荷**：跨场景硬拼、flat grid、连续 dense、高光进 mosaic 主槽。  
- **三模式**：叙事 chunk / 代表图 / 段落边界应对齐，像素不必一致。  
- **四原则**：间距表达叙事；稀疏信号>多样皮肤；连作绑紧、杰作离开；三模式同一合同。

### 2.4 产品经理

- **判断**：差异化资产，滑向运维负担——修好又弄丢（config / sync-journal）。  
- **服务叙事**：单图、票根、breath（概念）、hero mosaic（几乎不出）、双竖。  
- **像堆砌**：机械三叠 fallback、full-frame 循环、8/9 宫休眠 SKU。  
- **拼图定位**：收敛 SKU；强化 4/5 槽 hero；预期百张卷 **3–5 次** 高质量 mosaic，不是 0 也不是 15。  
- **P0**：样式静默丢失门禁；配置 silent wrong default。  
- **P1**：安全模板垄断 + mosaic 欠曝光；三模式语义分裂。  
- **P2**：SKU 债；活跃集建议 ≤12。  
- **战略**：排版可信基线 → 叙事节拍优先于模板 SKU；**冻结扩库**直到盲评过线。

### 2.5 UI/UX 设计

- **总评**：骨架 7/10，叙事节奏 5.5/10。  
- **职责**：plate 清晰；1col / 三叠半清晰；双竖弱；mosaic 产品清晰、呈现偏均等网格。  
- **反对**：7+ 槽、均等 dense 默认、第二套 full-bleed 家族、靠增加 breath 屏数凑节奏、卡片阴影/黑底 EXIF。  
- **Top 5**：三级节奏 token（槽缝 / 屏缝 / 语义 pause）；章内 cadence 曲线；mosaic hero-first；统一 Stage-fixed vs Flow-auto；longshot/scroll 双预览。  
- **版式角色表**：plate=章扉；1col=主语；stack-3=时间线；2col=对照；mosaic-4 hero=高潮+证据；均等 mosaic=fallback；breath=语义留白。

---

## 3. 拼图专项共识

| 该强化 | 该收敛 / 禁止 |
|--------|----------------|
| 4/5 槽 **hero + sidebar** | 8/9 宫默认曝光、7+ 槽 |
| 同场景 / burst 内聚 | 跨场景硬拼、连拍重复 2×2 |
| 主槽面积可读（设计建议 ≥55%） | 副槽压成「信息条」 |
| P21 配额作**上限**非 KPI | 「配额没用完就继续塞」 |
| Studio 可解释「为何拼/为何没拼」 | 黑箱 + 静默变 0 |
| hero SKU 进活跃窗族；取消 hero_first 硬跳过 MCS | 用等权 landscape-4 冒充 hero 凑数 |

### 3.1 算法：拼图≈0 根因排序（双份评审合并）

1. **3 槽 legacy / size=3 aux 垄断体感** — MCS 4/5/6 失败后降级三叠；**不记 dense、绕开 P21**，制造「有三叠无 hero」  
2. **Pipeline 抢占 + 窗宽碎片化**（含 `hero_first` 整段跳过 MCS、竖图窗跳过 MCS）  
3. **几何 / eligibility 硬门** — main AR、朝向 mix、hero geometry；部分 hero 模板 `prefers_burst: false` 反而伤 walking 连拍  
4. **4 槽活跃族无 hero SKU** + 评分安全偏置  
5. **配置 / density 放大器**（含 nine_min 与 mosaic 争 narrative 预算）  
6. **P21 配额**（对 used≈0 解释力最弱）

### 3.2 算法：hero 下限守护

- **合理形态** = 机会下限 / 章级 reserve（合法 hero 窗失败则**释放**，**禁止**降级 3 槽凑数），**不是** trip 级 `min_dense` KPI。  
- 精选 / dump / quick-share **应分轨**（limits + beat + 是否启用 size=3 aux）；精选轨是更高门槛+更准时机，不是多拼。

---

## 4. 三模式（scroll / present / longshot）

| 风险 | 谁强调 |
|------|--------|
| 长图拆 slot → 拼图叙事归零 | 产品、UI/UX、UX、家庭、架构、管线 |
| 预览满意、导出失望 | 全员相关 |
| present 跳过票根/辅助屏 | 产品 |
| 需要导出前双预览 + 组屏保留策略 | 共识 |
| 应在 **screens[] 语义合同层** enforce，非像素统一 | 架构、管线 |

### 4.1 架构提案：Narrative Contract（摘要）

Canonical SSOT = `chapters[].screens[]`，每屏带：`narrativeRole` / `groupId` / `preserveGroup` / `exportHints` / `representativeAssetId`。  
三模式是同一合同的三种 View；longshot 默认 mosaic **不 implicit flatten**。

---

## 5. 第二轮 · 技术侧要点

### 5.1 架构专家

- **分层意图 7/10，落地一致性 4/10**（ADR-015 半迁移：LTE / planner 硬编码 / legacy_bridge 三写）。  
- **最大债**：权威源分散 + 静默失败（config / CSS truncate / 三模式 reinterpret）。  
- **边界一句话**：Curate 产出带语义的 `screens[]`；LTE 定义长相；Render 只画；Overlay 只承载读者语义。  
- **P0**：Fail-loud（LRG+MCR 合一）；Narrative Contract。  
- **P1**：LTE 单权威；MCS 曝光策略（活跃 ≤12）。  
- **P2**：Rhythm token 由 planner 产出，禁 CSS 补丁式 breath。  
- **反对**：继续扩 SKU、第五套准入、三模式像素统一、未过门禁的物理大搬迁。

### 5.2 算法专家（两份评审收敛）

- **目标函数错位**：局部 utility + dense 上限 + 安全回退 ≠ 叙事节拍；`beat_profile` 默认 **flat**。  
- **`hero_first` 跳过 MCS** → 应降权而非关管道。  
- **活跃 4 槽族无 main**；3 槽不进 P21 却大量胜出。  
- **工程优先级（算法侧）**：**解耦 size=3 aux** → burst 预分段 → asymmetric quota（有 min 但不强制凑）→ 默认 beat + 真实章进度 → Hero Opportunity Score。  
- **诊断**：先读 `mosaicDecisionLog`，再谈放宽 P21 / 扩 SKU。

### 5.3 管线专家

- **最脆**：sync→render（CSS 截断）与 config→curate（silent wrong default）；共性 = fail-open。  
- **修好又弄丢**三模式：契约碎片化 / 门禁 FAIL 仍可 merge / 可观测 silent。  
- **Enforce 层**：L0 `screens[]` 屏序；L1 多表面 derive；L4 longshot 组策略 ADR；像素不强求一致。  
- **周看板**：窗宽分布、mosaic 曝光、burstPassRate、overlay 覆盖率、screenCount parity、scroll↔longshot slot 守恒。  
- **P0**：闭合 LRG required check；MCR fail-loud + curate 诊断；Type-A/B dogfood 附件。  
- **P1**：三模式语义合同 + 双预览。  
- **冻结扩库**：管线侧 merge 决策树（新 patternId / 槽数&gt;6 → NO）。

---

## 6. 跨角色优先级对齐（建议）

| 优先级 | 主题 | 用户/产品/设计 | 架构/算法/管线 |
|--------|------|----------------|----------------|
| **P0** | 可信基线 / fail-loud | 修好又弄丢 | LRG+MCR 门禁闭合；config/CSS 不再 silent |
| **P0** | 三模式不撒谎 | 双预览、拆拼可预期 | Narrative Contract + longshot 组策略 |
| **P1** | 节奏可读 | breath / 屏缝 | rhythm token；禁 CSS 凑 breath |
| **P1** | 拼图该出时出 | hero 稀疏惊喜 | 修进窗链 + hero SKU + 机会下限；勿先松 P21 |
| **P2** | 收敛 SKU | 活跃集 ≤12 | LTE 单权威；冻结扩库 |

---

## 7. 建议的讨论顺序（更新）

1. 是否认可「**不扩库 → 先 fail-loud 可信基线**」为工程最高优先级  
2. Narrative Contract / longshot `preserveGroup` 默认值如何拍板  
3. 是否取消 `hero_first` 对 MCS 的硬 skip（改为降权）  
4. 是否解耦 **MCS 失败 → size=3 legacy**（切断「假拼图」）  
5. hero mosaic **机会下限 / 章级 reserve**是否接受（非产量 KPI）  
6. breath 语义气口（与屏缝分离）是否进可信基线同期  
7. 排版可信是否作为 HGM 前置（技术侧一致：是）  

---

## 8. 变更

| 日期 | 说明 |
|------|------|
| 2026-07-20 | 初稿：家庭 / UX / 产品 / UIUX 四方汇总 |
| 2026-07-20 | 并入旅行摄影爱好者；五方完成 |
| 2026-07-20 | 第二轮：架构 / 算法 / 管线并入；共识与讨论顺序更新 |
| 2026-07-20 | 并入第二份算法评审：3 槽兜底解耦、asymmetric quota、讨论序补充 |
