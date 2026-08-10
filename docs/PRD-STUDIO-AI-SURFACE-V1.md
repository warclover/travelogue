# Travelogue · Studio AI Surface V1 产品需求文档（PRD）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue Studio |
| **文档版本** | **v0.2.1** |
| **状态** | **编码收口 · W1～W3 Done（不含 AC-SAS-08b）** · Conditional Go BLK 已关（[评审纪要](./acceptance-records/sas-studio-ai-surface-v1-review-2026-08-10.md)） |
| **DOC-STATUS** | **active** |
| **主题代号** | 「预览 AI 应用面」— **SAS**（Studio AI Surface） |
| **触发来源** | 2026-08-10 产品狗粮：AI 能力（装帧标题 / Intent / Critic / 杂志文案 / 本机连接）分散且难发现；ACP 偏后端收编、用户面缺一级入口。共识：在画册预览顶栏增加「AI」入口，统一本册 AI 动作与本机连接 |
| **前置条件** | [PRD-AI-CAPABILITY-PLATFORM-V1.md](./PRD-AI-CAPABILITY-PLATFORM-V1.md)（ACP · 门控/预算/观测底座）· [PRD-AI-RETURN-V1.md](./PRD-AI-RETURN-V1.md)（AIR · 杂志文案解冻合同）· [PRD-COVER-CALLIGRAPHY-TITLE-V1.md](./PRD-COVER-CALLIGRAPHY-TITLE-V1.md)（CAL · 装帧标题点按生成）· [PRD-NO-AI-SURFACE-V1.md](./PRD-NO-AI-SURFACE-V1.md)（`aiSurfaceEnabled` 单点门控）· [PRD-DESKTOP-LLM-SETUP-V1.md](./PRD-DESKTOP-LLM-SETUP-V1.md) / [PRD-WRITING-ENGINE-API-HARDENING-V1.md](./PRD-WRITING-ENGINE-API-HARDENING-V1.md)（本机连接）· 预览 Dock v4 可用 |
| **关联文档** | [PRD-PREVIEW-REFINE-V1.md](./PRD-PREVIEW-REFINE-V1.md) · [PRD-PREVIEW-REFINE-UX-V1.1.md](./PRD-PREVIEW-REFINE-UX-V1.1.md) · [PRD-REFINE-FEEDBACK-LOOP-V1.md](./PRD-REFINE-FEEDBACK-LOOP-V1.md) · [AGENT-ARCHITECTURE.md §17](./AGENT-ARCHITECTURE.md) · [adr/019-desktop-user-data-llm-secrets.md](./adr/019-desktop-user-data-llm-secrets.md) |
| **线框** | [wireframes/studio-ai-surface-v1-wireframe.html](./wireframes/studio-ai-surface-v1-wireframe.html)（F0–F6 · 落位以 D-SAS-02 为准） |
| **评审记录** | [acceptance-records/sas-studio-ai-surface-v1-review-2026-08-10.md](./acceptance-records/sas-studio-ai-surface-v1-review-2026-08-10.md)（七席+典型用户 · 8/8 Conditional Go） |
| **验收** | [ACCEPTANCE-STUDIO-AI-SURFACE-V1.md](./ACCEPTANCE-STUDIO-AI-SURFACE-V1.md)（§10 为源）· [W3 狗粮](./acceptance-records/sas-studio-ai-surface-v1-w3-dogfood-2026-08-10.md) |
| **实施清单** | [IMPLEMENTATION-STUDIO-AI-SURFACE-V1.md](./IMPLEMENTATION-STUDIO-AI-SURFACE-V1.md) |
| **更新日期** | 2026-08-10 |

> **定位**
>
> SAS 是 **Studio 预览页的 AI 用户发现面与动作汇聚面**，不是第二套 AI 平台，也不是运维台。  
> 把「会烧模型 / 需显式触发 / 依赖本机连接」的能力收进预览 Dock 一级入口「**AI**」与右侧 Sheet；工程 Agent 名、预算表、unlock-gate **不下沉**主路径。  
> **杂志文案（AIR）在本主题一并解冻整合**：预览侧以 AI Sheet 为权威入口，承接「生成杂志感文案 / 换语气 / 引导配置」，不再灰显、不再仅藏在精修深处。
>
> **一句话目标**：用户打开画册预览，知道「这里有 AI」、能点到该点的动作，且从不被勾选或打开面板自动烧掉额度。
>
> **产品铁律**
>
> 1. **勾选 ≠ 自动生成** — 偏好（如「优先 AI 手写体」）只影响下一次显式点击。  
> 2. **建议只读，采纳才写** — Layout Critic / Intent 等不得静默改结构（继承 ACP advisory-only）。  
> 3. **Fail-open** — 任一 AI 动作失败不影响浏览、精修手工改、导出长图。  
> 4. **门控诚实（分动作）** — 未开闸时入口可发现、Sheet 诚实说明；**各动作门控见 D-SAS-15**，禁止用一句 D-ACP-14 AND 覆盖装帧标题与杂志文案。  
> 5. **与精修分权** — 精修管版式/书衣/分章手工；AI Sheet 管模型动作与本机连接。  
> 6. **本地优先** — 继承 D-AIR-09 / ADR-019；不新造第二套密钥 API。  
> 7. **禁止能力卡硬推** — 继承 D-NAS-20 / D-AIR-03；发现路径 = Dock「AI」，不作首启墙。  
> 8. **W1 不绑 AIR 全量** — 杂志文案解冻 = 现网 narrate 入口（D-SAS-16）；三语气 / 渠道包仍归 AIR 后续切片。

---

## 0. 读者指南

| 章节 | 澄清什么 |
|------|----------|
| §0.1 | 术语 |
| §0.2 | 与相邻主题边界（尤其 AIR / ACP / 精修） |
| §0.3 | 线框帧 ↔ 规格映射 |
| §1 | 背景与问题 |
| §2 | 目标 / 非目标 / 成功画像 |
| §3 | 冻结决策 D-SAS-* |
| §4 | 功能规格 F-SAS-*（含杂志文案解冻整合） |
| §5 | 数据 / API / 门控 |
| §6 | 文案 COPY-SAS-* |
| §7 | 埋点 |
| §8 | 里程碑 |
| §9 | 风险与开放问题 |
| §10 | 验收 AC-SAS-* |
| §11 | 评审拍板清单 |

### 0.1 术语

| 术语 | 含义 |
|------|------|
| **AI Surface / AI Sheet** | 预览顶栏「AI」打开的右侧（窄屏近全高）面板；本主题主交付物 |
| **本册动作** | 针对当前 trip 的显式 AI CTA：装帧标题、意图、排版建议、**杂志文案** |
| **本机连接** | 写作引擎 Provider / Key / ping；WEA/DLLM 合同 |
| **高级** | 链到内部运维台（`/ai-ops-admin` 等）；非普通用户主路径 |
| **杂志文案** | AIR 定义：写入版心的 `meta.title` / `hook` / 章 `lead` / 封底 epilogue 等；**本主题解冻其预览入口并整合进 AI Sheet** |
| **渠道包** | AIR `shareCopyPack`；挂载仍在导出成功面 / 分享面，**不**塞进 AI Sheet 主区（见 NG-SAS-04） |
| **解冻（本主题语境）** | ① 产品开关允许 AI 面可见；② 杂志文案能力在 AI Sheet **完整可用**（非灰显占位） |

### 0.2 与相邻主题边界

| 主题 | 本主题拥有 | 本主题依赖 / 不碰 |
|------|------------|-------------------|
| **AIR** | 预览侧杂志文案 **入口、状态、确认、busy、失败归因** 整合进 AI Sheet；可 supersede「散落工具行 / 精修深处」旧入口为次要或移除 | Prompt / 三语气语义 / 渠道包算法 / 禁编造 → **仍归 AIR**；本主题不重写 narrate Prompt |
| **ACP** | 消费 Intent Brief / Layout Critic 结果的**展示与采纳 UI**；埋点 source=`ai_sheet` | Gateway / Agent / 预算 / unlock_gate → ACP；**禁止**在 Sheet 展示 Agent 工程名 |
| **CAL** | 装帧标题生成 CTA +「优先 AI 手写体」偏好的主入口落在 AI Sheet | 路线 C 生图、失败降级、盲评 → CAL；勾选不自动烧 API（D-CAL-05/22） |
| **NAS** | 当 `aiSurfaceEnabled=false`：诚实门控态（F4） | 不拆除 NAS dark；不恢复能力卡硬推 |
| **精修 / Bookends** | 互斥打开；职责文案边界 | 封面版式、书衣、分章结构、手工改字仍归精修 |
| **WEA / DLLM** | Sheet「本机连接」打开既有设置 Modal | 不平行第二套 secrets API |
| **G1 / 分章面板** | 排版建议可在 AI Sheet 汇总；章级「这章不对」可保留章面板捷径 | 不取消既有 G1 反馈 API |

### 0.3 线框帧映射

| 帧 | 规格 |
|----|------|
| **F0** Dock 落位 | F-SAS-01 |
| **F1** Sheet 默认三层 | F-SAS-02～05 |
| **F2** 建议徽标 | F-SAS-04 |
| **F3** 生成中 | F-SAS-03 / F-SAS-05 busy |
| **F4** 未开闸 | F-SAS-06 |
| **F5** 窄屏 | F-SAS-07 |
| **F6** 拍板 | §3 / §11（杂志文案 = **解冻整合**，已写入 D-SAS-06） |

---

## 1. 背景与问题

### 1.1 As-Is

| 层 | 现状 | 缺口 |
|----|------|------|
| **ACP** | 后端门控、Intent/Critic、观测已推进 | 用户不知道「册上有 AI」 |
| **CAL** | 精修「这本」内：勾选优先手写体 +「生成装帧标题」 | 发现路径弱；勾选易被误解为自动生成 |
| **AIR** | 合同已写解冻；预览 narrate 多藏于 dark / 精修或旧工具行 | **缺统一、可发现的预览权威入口** |
| **连接** | 首页/设置写作引擎 Modal 可用 | 与「册内 AI 动作」心智割裂 |
| **建议** | G1/章面板可展示 layoutSuggestions | 无 Dock 级「有事可看」信号 |

### 1.2 问题陈述（P-SAS-*）

| ID | 问题 | 严重度 |
|----|------|--------|
| **P-SAS-01** | AI 能力分散在精修、设置、暗门、运维台，预览顶栏无一级入口 | 阻塞 |
| **P-SAS-02** | 用户把「优先 AI 手写体」勾选当成自动生成，产生「没反应 / 偷偷烧钱」恐惧 | 严重 |
| **P-SAS-03** | 杂志文案解冻合同存在，但预览侧无整合面，等于「解冻未完成」 | 阻塞 |
| **P-SAS-04** | Critic 建议产出后用户无发现路径 | 严重 |
| **P-SAS-05** | 若把 ops/Agent 名塞进用户 Sheet，认知负担高于收益 | 中 |
| **P-SAS-06** | AI 与精修双开或职责不清 → 用户不知道改版式找谁 | 中 |

---

## 2. 目标与非目标

### 2.1 目标（In Scope）

| ID | 目标 |
|----|------|
| **G-SAS-01** | 预览 Dock 增加一级「**AI**」入口（桌面带文案；窄屏可图标） |
| **G-SAS-02** | AI Sheet **三层 IA**：本册动作（展开）→ 本机连接（折叠）→ 高级（折叠） |
| **G-SAS-03** | 本册动作卡片位：**装帧标题**、**杂志文案（解冻）**为 W1；**意图**、**排版建议**为 W2（W1 可占位说明「即将开放」或隐藏，不得假接通） |
| **G-SAS-04** | 杂志文案（W1）：有 Key 可生成；无 Key 引导配置；确认框与 AIR 隐私合同一致；导入主链仍 stub；**不含三语气**（D-SAS-16） |
| **G-SAS-05** | （W2）有未读排版建议时 Dock「AI」亮徽标；打开后建议卡片可采纳/忽略/反馈 |
| **G-SAS-06** | 未开闸：入口可见 + Sheet 诚实说明；杂志文案零外呼；分动作门控见 D-SAS-15 |
| **G-SAS-07** | 与精修 Sheet **互斥**；职责边界文案可测 |
| **G-SAS-08** | 全部模型动作 **显式点击** 才外呼；busy 可关面板继续浏览 |

### 2.2 非目标（Out of Scope · V1）

| ID | 不做 | 理由 |
|----|------|------|
| **NG-SAS-01** | 重写 narrate Prompt / 三语气算法 | 归 AIR；SAS W1 **不实现** voice UI/API |
| **NG-SAS-01a** | SAS W1 交付三语气换腔 / 渠道包 v2 | 归 AIR 后续；见 D-SAS-16 |
| **NG-SAS-02** | 在 AI Sheet 内做完整渠道包编辑器 | 渠道挂载成功面；避免 Sheet 变杂物抽屉 |
| **NG-SAS-03** | 把 `/ai-ops-admin`、预算表、unlock-gate 做成用户主功能 | 高级折叠链即可 |
| **NG-SAS-04** | 首启能力卡 / FirstSuccess 主 CTA「去配 Key」 | D-NAS-20 / D-AIR-03 |
| **NG-SAS-05** | 导入主链自动 LLM narrate | D-AIR-04 |
| **NG-SAS-06** | 展示 Intent Brief / Mosaic Judge 等工程名 | 用户语言见 COPY |
| **NG-SAS-07** | 允许建议静默改 `structure_locked` 章节 | ACP advisory-only |
| **NG-SAS-08** | 重做精修 / Bookends / 分章算法 | 边界外 |

### 2.3 成功画像

| 角色 | 成功 |
|------|------|
| **分享者（L0）** | 点开 AI → 看到「可配置连接」；无 Key 仍能导出；不被吓成「整册失败」 |
| **创作者（L1）** | 预览 → AI → 生成杂志感 / 装帧标题 / 看建议，**不必翻精修找暗入口** |
| **产品** | 发现性可测（首次成册后 AI Sheet 打开率）；零「勾选即烧 API」客诉；AC-SAS 绿 |

---

## 3. 冻结决策（D-SAS-*）

| ID | 决策 | 说明 |
|----|------|------|
| **D-SAS-01** | **Dock 文案 =「AI」** | 不用「AI 应用」（过长）；备选「智能」仅当评审改口 |
| **D-SAS-02** | **落位（对照现网 v4）** | AI 插在 **精修（`.preview-toolbar__menu-wrap`）之后、导出区之前**。现网典型序：`返回 \| 播放 \| 分章 \| 精修 → **AI** → … \| 文件夹 \| 导出`。线框 F0 为示意，**以本决策与 IMPLEMENTATION 相对节点为准**（BLK-SAS-01） |
| **D-SAS-03** | **Sheet 形态** | 桌面右侧 Sheet；窄屏自底向上近全高；单实例 |
| **D-SAS-04** | **与精修互斥** | 开 AI → 关精修面板；开精修 → 关 AI Sheet；与分章面板互斥规则见 SHD-SAS-02 |
| **D-SAS-05** | **装帧标题入口** | **AI Sheet 为主**；精修「这本」可保留次要入口（同 CTA 语义，禁止第二套偏好键） |
| **D-SAS-06** | **杂志文案 = 解冻整合** | AI Sheet **完整交付**现网 narrate 生成/配置引导；**禁止**灰显占位。范围收窄见 **D-SAS-16**（不含三语气/渠道包 UI） |
| **D-SAS-07** | **未开闸策略** | Dock 按钮**可见**；Sheet 展示诚实说明 +「了解如何开启」（不得死链，SHD-SAS-06）；本机连接仍可展开 |
| **D-SAS-08** | **高级** | 默认折叠；链「打开 AI 运维台」；正式对外包可构建旗标隐藏整节（OQ-SAS-02） |
| **D-SAS-09** | **显式触发** | 装帧标题、意图重解析、杂志文案、建议采纳 —— 均需用户动作；无后台自动烧额度 |
| **D-SAS-10** | **建议徽标** | （W2）存在未处理 `layoutSuggestions` 时 Dock「AI」橙点；打开并浏览/处理后清除 |
| **D-SAS-11** | **用户语言** | Sheet 只用「意图 / 排版建议 / 装帧标题 / 杂志文案 / 本机连接」；禁止 Agent 工程名 |
| **D-SAS-12** | **错误归因** | 缺 Key / LLM 失败 → 仅该动作失败；COPY 对齐 AIR，禁止「制作失败」整单语义 |
| **D-SAS-13** | **（废止混写）** | ~~一切动作 = D-ACP-14 AND~~ → 以 **D-SAS-15** 分动作矩阵为准 |
| **D-SAS-14** | **旧入口收敛** | W1：杂志文案以 AI Sheet 为权威；精修深处 narrate 可深链。W2：对照表完成降级/移除（F-SAS-08） |
| **D-SAS-15** | **分动作门控矩阵**（BLK-SAS-03） | 见 §5.1 表；**禁止**给 title-art 强行加 NAS 403（除非另 OQ 拍板） |
| **D-SAS-16** | **SAS↔AIR 切片**（BLK-SAS-04） | SAS W1 杂志文案 = 现网 `POST /__travelogue/narrate` 入口解冻（确认、busy、失败归因、配置引导、`source=ai_sheet`）。**不含** `voice` UI/API、**不含**渠道包编辑。AIR 仍拥有 Prompt/渠道/语气产品语义 |

---

## 4. 功能规格

### 4.1 F-SAS-01 · Dock「AI」按钮

- **位置（相对节点）**：在 `.preview-toolbar__menu-wrap`（精修）之后插入 AI 按钮容器；不得假设「播放在精修右侧」（现网播放/分章在精修左侧）。见 D-SAS-02。  
- **形态**：桌面 `✦ AI`（或设计系统等价图标 + 文案）；窄屏可仅图标，`aria-label="AI"`。  
- **状态**：
  - `idle` / `active`（Sheet 打开）
  - `badge`（D-SAS-10 · W2）
  - 不因未开闸而隐藏（D-SAS-07）
- **点击**：toggle AI Sheet；若精修打开则先关精修（D-SAS-04）。  
- **埋点**：`ai_sheet_open` / `ai_sheet_close`（§7 · 须进 allowlist）。

### 4.2 F-SAS-02 · Sheet 壳与三层 IA

```text
┌ AI ──────────────────── × ┐
│ 副标题：本册智能动作 · 不自动消耗额度
├───────────────────────────┤
│ 【本册动作】默认展开
│   · 装帧标题            ← W1
│   · 杂志文案            ← W1 解冻（D-SAS-06/16）
│   · 意图 / 排版建议     ← W2（W1 可隐藏或「即将开放」）
│ 【本机连接】details 折叠
│ 【高级】details 折叠（可旗标隐藏）
└───────────────────────────┘
```

- 副标题固定传达「不自动消耗」。  
- 各动作卡片：标题 + 一句说明 + 状态徽章 + 主/次按钮。

### 4.3 F-SAS-03 · 装帧标题（CAL）

| 元素 | 规格 |
|------|------|
| 偏好 | 「优先 AI 手写体」checkbox；**仅**影响下一次点击路由偏好；**不**触发生成 |
| 主 CTA | 「生成装帧标题」/ 已有结果时「重新生成」 |
| Busy | 进度条或状态「生成中」；按钮 disabled；可关 Sheet；完成 toast + 可选轻徽标 |
| 失败 | fail-open；toast/卡片内错误；不挡预览 |
| 与精修 | 次要入口共享同一 API/偏好键（D-SAS-05） |

### 4.4 F-SAS-04 · 意图与排版建议（ACP 消费面）

**意图**

- 展示可读摘要（例：「已就绪 · 偏少章」），**不**展示 raw JSON / Agent 名。  
- CTA「重新解析」→ 显式触发 Intent Brief 刷新（门控满足时）；busy/失败 fail-open。  
- 文案说明：影响后续选片/分章**建议**，不直接改已锁定结构。

**排版建议**

- 无建议：空态说明「成册后若有可改点会出现在这里」。  
- 有建议：卡片列表（章定位 + 短说明 + **采纳 / 忽略** + 可选「这章不对」走既有 `layoutFeedback`）。  
- **采纳**才写入；`structure_locked` 时遵循现网保护（不可静默覆盖）。  
- Dock 徽标与「未处理」计数联动（D-SAS-10）。  
- 打开 Sheet 且存在未读建议时，可自动滚到本卡片（增强，非阻塞）。

### 4.5 F-SAS-05 · 杂志文案（AIR 解冻整合）★

> 本主题将 AIR 预览侧合同**收编进 AI Sheet**，作为解冻最小包的预览权威触点（对齐 D-AIR-02「Sheet/预览 narrate CTA」，并升级为统一入口）。

#### 4.5.1 能力矩阵

| 状态 | Sheet 表现 |
|------|------------|
| 表面未开闸 | 整卡落入 F-SAS-06 诚实态（不单独伪装） |
| 开闸 + 无有效 Key | 状态「未配置」；主 CTA「配置写作引擎」→ 打开既有 LLM 设置 Modal（`source=ai_sheet_narrate`）；次文案 COPY-AIR-01 / COPY-SAS-N01 |
| 开闸 + 已配 Key | 状态「可生成」或「已是杂志感」；主 CTA「生成杂志感文案」 |
| 生成中 | busy；可关面板；完成后刷新预览文案 |
| 失败 | COPY-AIR-03 / COPY-SAS-N03；提供重试 +「去检查连接」 |

#### 4.5.2 交互（W1 = 现网 narrate；对齐 AIR 隐私/归因）

1. **W1 无语气选择器**（BLK-SAS-02 / D-SAS-16）。三语气待 AIR `voice` API 落地后启用 **AC-SAS-08b**。  
2. 点击生成 → **确认**（COPY-AIR-02 / COPY-SAS-N02，含手改覆盖提示 COPY-SAS-N06）→ `POST /__travelogue/narrate`（body：`tripId`；与现网一致）。  
3. **不**触发 curate/layout。  
4. **导入主链仍 stub**（D-AIR-04）；仅本 CTA 写 LLM。  
5. `structure_draft`：CTA 禁用或说明「请先在分章确认」（SHD-SAS-01；后端 409）。  
6. 作用域、禁编造、SFI/禁词：继承 D-AIR-09～13；本主题不放宽。

#### 4.5.3 与渠道包

- AI Sheet **不**内嵌完整渠道包 UI（NG-SAS-02）。  
- 可选一行次链：「导出成功后可复制朋友圈/群文案」→ 不打断；渠道逻辑仍归 AIR F-AIR-03。

### 4.6 F-SAS-06 · 未开闸诚实态

- 标题/副标题可改为「本环境未开启智能能力」。  
- 本册动作区合并为一张说明卡 +「了解如何开启」（帮助锚点或内测说明，IMPLEMENTATION 定）。  
- 「本机连接」仍可展开配置（方便内测先配 Key，再开闸）。  
- **禁止**对未开闸动作发出外呼（门控矩阵测试）。

### 4.7 F-SAS-07 · 窄屏

- Dock：图标「AI」；与精修互斥不变。  
- Sheet：近全高；卡片按钮可缩短文案（「生成」）。  
- 遵守现网 preview narrow-gate：若整页为诚实门面，不另开平行 AI 幻想态（与 PMX 合同一致）。

### 4.8 F-SAS-08 · 旧入口收敛

| 现网入口（示例） | V1 策略 |
|------------------|---------|
| 精修 → 这本 → 重新生成文案 / 杂志感 | **降级**：移除或改为「在 AI 中打开」深链 |
| 精修 → 装帧标题 | **可保留**次要 CTA（D-SAS-05） |
| 首页写作引擎设置 | **保留**；Sheet「本机连接」复用同一 Modal |
| dark 工具行 narrate | 开闸后不再作为默认发现路径 |

IMPLEMENTATION 须附「入口收敛对照表」并配回归用例。

### 4.9 F-SAS-09 · 本机连接与高级

**本机连接（折叠）**

- 状态徽章：未测通 / 已就绪 / 失败码人话（WEA）。  
- CTA「配置 / 测试」→ 既有 `openLlmSettings`。  
- 脚注：本地 Key；失败不影响出图。

**高级（折叠）**

- 「打开 AI 运维台 →」`/ai-ops-admin`（或现网等价）。  
- 对外正式包默认隐藏整节（OQ-SAS-02；开发/内测包显示）。

---

## 5. 数据 / API / 门控

### 5.1 分动作门控矩阵（D-SAS-15）

| 动作 | `aiSurfaceEnabled` | `ai_capability` / Agent 旗标 | 有效 Key | 备注 |
|------|--------------------|------------------------------|----------|------|
| Dock「AI」按钮可见 | 不要求（始终可发现） | — | — | D-SAS-07 |
| Sheet 本册动作区（开闸） | **要** true，否则 F-SAS-06 | — | — | |
| **杂志文案** 外呼 | **要**（后端 403） | — | **要**（否则引导配置） | 现网 `handle_narrate` |
| **装帧标题** 外呼 | **不**强制（现网无 NAS 403） | CAL `title_art` / routeC 旗标 | route C 可能需图像模型 Key | 精修次入口同口径 |
| **意图 / 建议** 外呼 | 要（用户面） | **要**（D-ACP-14 对 `ai/agents/*`） | **要**（Agent 路径） | W2；前端不得绕过服务端 fallback |
| 本机连接配置 | 不要求 surface | — | — | 可先配后开闸 |

```text
surfaceOn = aiSurfaceEnabled === true
if !surfaceOn → Sheet 主区 F-SAS-06（连接区仍可配）；杂志文案按钮不可外呼
装帧标题：即使 surface 关，精修次入口行为保持 CAL 现网（本主题不新加 NAS 403）
```

### 5.2 API（复用，不平行造轮）

| 能力 | 复用 |
|------|------|
| 杂志文案 | 既有 `POST /__travelogue/narrate`（W1 **无** `voice`） |
| 装帧标题 | 既有 `POST .../title-art/resolve` |
| 意图 | 既有 Intent Brief API（ACP · W2） |
| 排版建议 | 既有 suggestions + accept / `layoutFeedback`（W2） |
| 连接 | 既有 settings + ping（WEA） |
| 配置投影 | `aiSurfaceEnabled` 等既有 studio config |

**禁止**为 SAS 新建第二套密钥或 narrate 业务端点；若需 `source` 查询参数仅用于埋点/日志。

### 5.3 隐私

- 完整继承 D-AIR-09、D-ACP-07、ADR-019。  
- 确认框展示 COPY-AIR-PRIVACY / COPY-SAS-N02。

---

## 6. 文案（COPY-SAS-*）

| ID | 场景 | 文案（冻结方向） |
|----|------|------------------|
| **COPY-SAS-01** | Sheet 副标题 | 「本册智能动作 · 不自动消耗额度」 |
| **COPY-SAS-02** | 装帧·说明 | 「点一次才生成。勾选只表示优先走 AI 手写体，不会自动开跑。」 |
| **COPY-SAS-03** | 意图·说明 | 「重新理解这趟旅行的节奏与篇幅偏好（影响后续建议，不直接改已锁定结构）。」 |
| **COPY-SAS-04** | 建议·说明 | 「只读建议；采纳后才写入。」 |
| **COPY-SAS-05** | 建议·空态 | 「成册后若有可改点，会出现在这里；届时顶部 AI 会亮提示点。」 |
| **COPY-SAS-06** | 未开闸 | 「本环境未开启智能能力。出图与导出不受影响。」 |
| **COPY-SAS-07** | 连接·脚注 | 「本地 Key · 失败不影响出图与导出。」 |
| **COPY-SAS-08** | 精修互链（可选） | 「版式与书衣请用「精修」；智能生成请用「AI」。」 |
| **COPY-SAS-N01** | 杂志·L0 | 对齐 COPY-AIR-01 |
| **COPY-SAS-N02** | 杂志·确认 | 对齐 COPY-AIR-02 |
| **COPY-SAS-N03** | 杂志·失败 | 对齐 COPY-AIR-03 |
| **COPY-SAS-N04** | 杂志·卡片标题 | 「杂志文案」 |
| **COPY-SAS-N05** | 杂志·说明 | 「重写封面钩子与章节导语等版心文字；照片仍留在本机。导入默认仍用本机文案。」 |
| **COPY-SAS-N06** | 杂志·覆盖提示（SHD-SAS-04） | 确认框须含：「将重写版心文案（可能包括你改过的句子）。」 |

禁词：默认可达面禁止把缺 Key / 单动作失败写成整单「生成失败」「制作失败」（继承 AIR/NAS）。

---

## 7. 埋点

| 事件 | 属性 | 备注 |
|------|------|------|
| `ai_sheet_open` | source=`dock` \| `deep_link`；`has_badge` | **W1 须写入** `analytics.js` allowlist（BLK-SAS-05） |
| `ai_sheet_close` | reason；`dwell_ms` | 同上 |
| `ai_sheet_action_click` | action=`title_art` \| `narrate` \| `open_settings` \| `open_ops`（W2 再加 intent/suggestion_*） | 同上 |
| `ai_sheet_action_result` | action；ok；latency_ms；error_code? | 同上 |
| `ai_sheet_gate_view` | surfaceOn；keyOk | 可选；若打点则须进 allowlist |
| 复用 | `llm_narrate_click` / `llm_narrate_result` | **须带** `source=ai_sheet` |
| 复用 | `title_art_*` | 从 Sheet 触发时标注 source |

KPI（本主题）：成册后 7 日内 AI Sheet 打开率、杂志文案点击率、装帧标题从 Sheet 触发占比；（W2）建议采纳率。  
**不**替代 ACP unlock_gate 的工程指标。

---

## 8. 里程碑

| 里程碑 | 交付 | 门禁 |
|--------|------|------|
| **W0** | 七席+1 Conditional Go；BLK 回写 v0.2；§11 拍板 | ✅ 2026-08-10 |
| **W1** | Dock + Sheet 壳 + 三层 IA + 未开闸态 + 本机连接 + **杂志文案现网解冻** + 装帧标题主入口 + allowlist | AC-SAS-01～07、08（无 voice）、12～14、17 |
| **W2** | 意图卡 + 排版建议 + Dock 徽标 + 旧入口收敛 + 窄屏打磨 | AC-SAS-09～11、15～16 |
| **W3** | 狗粮 N≥5；埋点核对；ACCEPTANCE 勾选；精修互链文案 | 主题 Done（**不**要求 AC-SAS-08b） |

> 编码 Kickoff 以 W0 Go 为准。本文件落地 ≠ `aiSurfaceEnabled` 正式发版默认开（仍受 OQ-AIR-01 / 发版说明约束）。

---

## 9. 风险与开放问题

### 9.1 风险

| 风险 | 缓解 |
|------|------|
| Dock 拥挤 | 短文案「AI」；窄屏图标 |
| 用户以为打开 Sheet 就收费 | 副标题 + 勾选说明 + 确认框 |
| 杂志文案与装帧标题同时 busy | 分动作 busy；互不阻断导出 |
| 与 AIR 双源文案漂移 | COPY-SAS-N* 对齐 COPY-AIR-*；AIR 改文案时同步 |
| 精修用户找不到旧按钮 | F-SAS-08 深链「在 AI 中打开」+ 狗粮 |

### 9.2 开放问题（OQ-SAS-*）

| ID | 问题 | 默认倾向 |
|----|------|----------|
| **OQ-SAS-01** | Dock 文案是否改「智能」 | 默认 **AI**（D-SAS-01） |
| **OQ-SAS-02** | 正式包是否隐藏「高级」整节 | **已收**：frozen 默认隐藏；dev / `TRAVELOGUE_AI_OPS=1` / `?aiOps=1` 显示 |
| **OQ-SAS-03** | 精修装帧标题次要入口是否 W1 就删 | 默认 **W1 保留、W2 评估删除** |
| **OQ-SAS-04** | 建议徽标是否包含「杂志文案已就绪未查看」 | 默认 **仅排版建议**；杂志用 toast |
| **OQ-SAS-05** | AI Sheet 是否提供「同步渠道文案到封面钩子」 | 默认 **否**（仍归 AIR 成功面 F-AIR-05） |

---

## 10. 验收（AC-SAS-*）

| ID | 断言 |
|----|------|
| **AC-SAS-01** | 预览 Dock 可见「AI」；顺序符合 D-SAS-02 |
| **AC-SAS-02** | 点击打开 Sheet；再点或 × 关闭 |
| **AC-SAS-03** | 精修与 AI Sheet 互斥（D-SAS-04） |
| **AC-SAS-04** | Sheet 含三层：本册动作 / 本机连接 / 高级（或旗标隐藏高级） |
| **AC-SAS-05** | 「优先 AI 手写体」勾选**不**产生网络请求；仅点击生成才请求 |
| **AC-SAS-06** | 装帧标题可从 AI Sheet 完整走通（成功或 fail-open） |
| **AC-SAS-07** | **杂志文案**：无 Key → 配置引导可打开设置；有 Key → 确认后 narrate 成功写版心；失败不挡导出；不触发 curate |
| **AC-SAS-08** | （W1）杂志文案**无**语气选择器；确认框含覆盖提示 COPY-SAS-N06 |
| **AC-SAS-08b** | （AIR 依赖 · 不挡 SAS Done）`voice` API 落地后：Sheet 可选语气并传入 narrate | 
| **AC-SAS-09** | （W2）有未处理建议时 Dock 亮点；处理后熄灭 |
| **AC-SAS-10** | （W2）建议采纳/忽略符合只读→写入；structure_locked 不被静默破坏 |
| **AC-SAS-11** | （W2）意图「重新解析」为显式触发；UI 无 Agent 工程名 |
| **AC-SAS-12** | `aiSurfaceEnabled=false`：按钮可见；Sheet 诚实态；**杂志文案**零外呼（装帧标题按 D-SAS-15，不要求精修次入口一并消失） |
| **AC-SAS-13** | 本机连接打开既有设置 Modal；无第二套密钥 API |
| **AC-SAS-14** | 导入主链无 Key 仍可出长图（回归 NAS/AIR） |
| **AC-SAS-15** | 窄屏可打开 AI Sheet 并完成至少「配置或生成」一条路径 |
| **AC-SAS-16** | （W2）旧权威入口已收敛或深链至 AI Sheet（对照表勾选） |
| **AC-SAS-17** | `analytics.js` allowlist **含** `ai_sheet_open` / `ai_sheet_close` / `ai_sheet_action_click` / `ai_sheet_action_result`；且 `llm_narrate_click` 带 `source=ai_sheet` 可查 |

---

## 11. 评审拍板清单

| # | 议题 | 本文默认 | 评审 |
|---|------|----------|------|
| D1 | Dock 文案 | **AI** | ✅ 七席维持 |
| D2 | 落位 | 精修之后、导出之前（现网相对节点） | ✅ BLK-SAS-01 |
| D3 | 装帧标题双入口 | Sheet 主 + 精修次 | ✅ |
| D4 | 未开闸按钮 | 可见 + 诚实 Sheet | ✅ |
| D5 | 高级/运维台 | 折叠；正式包可隐藏 | ✅ |
| D6 | **杂志文案** | **解冻整合；W1 = 现网 narrate（无 voice）** | ✅ D-SAS-16 |
| D7 | 与精修互斥 | 是 | ✅ |

---

## 12. 与 AIR / ACP 的合同关系（摘要）

```text
NAS 门控（aiSurfaceEnabled）
    └─ SAS：预览发现面与动作壳
           ├─ 杂志文案 CTA  ──W1 复用现网 narrate──► AIR 隐私/归因；voice/渠道仍归 AIR 后续
           ├─ 装帧标题 CTA ──复用──► CAL（门控独立，见 D-SAS-15）
           ├─ 意图/建议 UI ──W2 消费──► ACP Agents（advisory）
           └─ 本机连接     ──复用──► WEA/DLLM
ACP：平台与观测；不替代 SAS 用户面
AIR：文案产品语义；预览入口权威迁移至 SAS（D-SAS-06 / D-SAS-16 / F-SAS-05）
```

**AIR 指针**：`PRD-AI-RETURN-V1.md` §4.1 已增补「预览权威 CTA = AI Sheet」。

---

## 13. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.2.1 | 2026-08-10 | W1～W3 编码收口：挂 ACCEPTANCE/IMPLEMENTATION/狗粮纪要；状态改为编码收口 Done（仍不含 AC-SAS-08b / 正式默认开闸） |
| v0.2.0 | 2026-08-10 | 七席+1 Conditional Go 回写 BLK-SAS-01～05：Dock 现网落位 · W1 去掉 voice 假绿 · 分动作门控 D-SAS-15 · AIR 切片 D-SAS-16 · 埋点 allowlist AC-SAS-17；里程碑 W1/W2 切开 |
| v0.1.0 | 2026-08-10 | 初稿：线框 F0–F6 产品化；杂志文案按解冻整合写入 D-SAS-06 / F-SAS-05 / AC-SAS-07～08 |
