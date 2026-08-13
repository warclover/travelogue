# Travelogue · 百炼一体连接 V1 产品需求文档（PRD）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue Studio |
| **文档版本** | **v0.2.1** |
| **状态** | **Conditional Go · Must-Fix 已回写 · 可冻结策划** |
| **DOC-STATUS** | **active** |
| **主题代号** | 「一次连接 · 文案与图像」— **BAI**（Bailian AI Integration） |
| **触发来源** | 2026-08-13 产品讨论：工具栏 AI 应拆文案 / 图像，但设置面只允许一把 Key；文案走 DeepSeek、图像走百炼万相+VL，造成「已就绪」只代表文案。共识：用户只配通义百炼一次，应用按任务自动换模型，不感知切换。 |
| **前置条件** | [PRD-STUDIO-AI-SURFACE-V1.md](./PRD-STUDIO-AI-SURFACE-V1.md)（SAS · AI Sheet）· [PRD-DESKTOP-LLM-SETUP-V1.md](./PRD-DESKTOP-LLM-SETUP-V1.md) / [PRD-WRITING-ENGINE-API-HARDENING-V1.md](./PRD-WRITING-ENGINE-API-HARDENING-V1.md)（连接 / ping）· [PRD-COVER-CALLIGRAPHY-TITLE-V1.md](./PRD-COVER-CALLIGRAPHY-TITLE-V1.md)（CAL · 路线 C）· [PRD-AI-RETURN-V1.md](./PRD-AI-RETURN-V1.md)（AIR · 杂志文案）· [PRD-NO-AI-SURFACE-V1.md](./PRD-NO-AI-SURFACE-V1.md)（`aiSurfaceEnabled`）· [adr/019-desktop-user-data-llm-secrets.md](./adr/019-desktop-user-data-llm-secrets.md) |
| **关联** | [PRD-AI-CAPABILITY-PLATFORM-V1.md](./PRD-AI-CAPABILITY-PLATFORM-V1.md)（ACP · 预算/观测）· [PRD-AESTHETIC-ALIGNMENT.md](./PRD-AESTHETIC-ALIGNMENT.md)（审美 MLLM）· [ERROR-CODES.md](./ERROR-CODES.md) |
| **评审记录** | [acceptance-records/bai-bailian-ai-integration-v1-review-2026-08-13.md](./acceptance-records/bai-bailian-ai-integration-v1-review-2026-08-13.md)（八席 · Conditional Go · BLK 已回写） |
| **验收** | Kickoff 后拆 [ACCEPTANCE-BAILIAN-AI-INTEGRATION-V1.md](./ACCEPTANCE-BAILIAN-AI-INTEGRATION-V1.md)；本文 §10 为源 |
| **实施清单** | Kickoff 后拆 [IMPLEMENTATION-BAILIAN-AI-INTEGRATION-V1.md](./IMPLEMENTATION-BAILIAN-AI-INTEGRATION-V1.md) |
| **线框** | W0 补 `wireframes/bailian-ai-integration-v1-wireframe.html`（F0–F6 · 落位以 §4 为准） |
| **更新日期** | 2026-08-13 |

> **定位**
>
> BAI 是 Studio **AI 连接模型与任务路由**的升级，不是第二套 AI 平台，也不重写 narrate Prompt / 封面版式。  
> 把「用户选 DeepSeek 还是通义、再手选模型」收成：**只连通义百炼一把 Key**；文案、识图、封面生图由应用按任务表自动选模型。  
> 预览 Dock 仍是一个「AI」；Sheet 内把动作分成 **文案** 与 **图像** 两块，失败互不影响。
>
> **一句话目标**：配一次百炼，杂志文案和封面字体都能用；用户看不见模型名，也感觉不到切换。
>
> **产品铁律**
>
> 1. **一门多房** — 用户配置的是百炼这扇门；DeepSeek-V4、Qwen-VL/OCR、万相/千问生图是门后的房间。禁止再让用户为文案/图像各选一家「当前服务商」。  
> 2. **L0 永不因缺 Key 失败** — 导入主链仍 stub；无 Key 或单任务失败不影响预览、精修、导出长图。  
> 3. **勾选 ≠ 自动生成** — 继承 D-SAS / D-CAL；点一次才外呼。  
> 4. **分动作诚实** — 「已就绪」只表示 Key 能进百炼；文案通了不冒充封面生图已开通。  
> 5. **用户面不提型号** — Toast / Sheet 不出现 `deepseek-v4-pro`、`wanx*`；型号只进日志与内测开关。  
> 6. **密钥不出本机** — 继承 ADR-019；不进 trip、明文日志、analytics。  
> 7. **NAS 门控不变** — 默认面仍由 `aiSurfaceEnabled` 约束；本文用户面验收在 dark / 开闸包。  
> 8. **生图默认仍是标题贴纸** — 不开放式造假风景封面（CAD 范围）；路线 C 失败 → 字库路线 B。

---

## 0. 读者指南

| 章节 | 澄清什么 |
|------|----------|
| §0.1 | 术语 |
| §0.2 | 与 SAS / WEA / CAL / AIR / ACP 边界 |
| §1 | 矛盾与 As-Is |
| §2 | 目标 / 非目标 |
| §3 | 冻结决策 D-BAI-*（含思考模式、型号升级） |
| §4 | 配置 UI + AI Sheet 信息架构 |
| §5 | 路由表 · secrets · API |
| §6 | 文案 COPY-BAI-* |
| §7 | 埋点 |
| §8 | 里程碑 W0–W3 |
| §9 | 风险与开放问题 |
| §10 | 验收 AC-BAI-* |
| §11 | 附录（型号对照 · 错误矩阵 · 入口收敛） |

### 0.1 术语

| 术语 | 定义 |
|------|------|
| **百炼 / DashScope** | 阿里云模型工作室；用户只配这一家的 API Key |
| **能力槽（capability）** | 内部枚举：`copy`（杂志文案）· `vision`（OCR / 审美看图）· `t2i`（封面字体生图） |
| **任务路由** | 按能力槽选择 model id + 协议；用户不可见 |
| **连接就绪** | 百炼 Key 已保存且最近一次 **文本 ping** 成功（`last_ping_ok=true`） |
| **动作可用** | 该动作允许点击；连接就绪是前提，首次真实调用仍可能因该模型未开通/额度不足而失败并 fail-open |
| **官方 DeepSeek** | `api.deepseek.com` 独立 Key；**Studio 用户面完全隐藏**，不提供接入/切换。工程 CLI / env 可保留，不驱动设置 UI |
| **思考模式** | 百炼 DeepSeek-V4 的 `enable_thinking`；本主题 **默认开**，W0 实测后再决定是否关 |

### 0.2 与相邻主题

| 主题 | 本主题拥有 | 本主题不碰 |
|------|------------|------------|
| **SAS** | 改写 Sheet「本机连接」与动作分区（文案卡 / 图像卡）；`llmAvailable` 拆分 | Dock 落位、与精修互斥、Intent/建议卡片语义 |
| **WEA / DLLM** | 默认连接面改为「只配百炼」；secrets 不再表示全局唯一 provider 抢槽 | coerce / SSRF **继承**；V1 **不**暴露国际站与自定义 URL |
| **AIR** | 文案外呼改走 `copy` 槽路由（可带思考模式） | Prompt、三语气、渠道包 |
| **CAL** | 路线 C / OCR 改走 `t2i` / `vision` 槽；W0 允许换更新生图型号 | 字库路线 B、白名单 Opening、勾选不自动烧 |
| **ACP** | 调用记录带 `capability` + `model`；预算仍按 trip | Gateway / Agent 名不下沉用户面 |
| **NAS** | 开闸后的连接文案 | 默认关闸合同 |
| **CAD** | — | 假风景封面、装帧导演 |

**Supersede（用户面，开闸包）**

| 旧合同 | 本主题之后 |
|--------|------------|
| D-DLLM-05「V1 仅 deepseek / dashscope 平权」 | **Studio 只提供百炼接入面**；官方 DeepSeek 选择器/申请链/模型列表全部隐藏 |
| WEA「一家一配置、切换即当前服务商」 | **无服务商切换 UI**；内部多模型 |
| SAS「配置写作引擎」单一 CTA | 分为配置连接 / 文案动作 / 图像动作 |
| 文本级联默认 `qwen3.7-flash` 且与 VL/万相混谈 | **按能力槽分表**；文案首选百炼托管 DeepSeek-V4 |

工程 CLI / `PROVIDER_PRESETS["deepseek"]` **可保留**供命令行；Studio 设置与 narrate **不**再读官方 DeepSeek Key。

---

## 1. 背景与问题

### 1.1 产品一句话（本主题前提）

旅行照片在本机做成杂志卷轴。AI 是升级：杂志文案 + 封面艺术字。用户不应理解「Chat 模型」和「万相」的差别。

### 1.2 As-Is（2026-08-13）

| 层 | 现状 | 缺口 |
|----|------|------|
| 设置 UI | 单一服务商 + 模型下拉（DeepSeek / 通义平权） | 用户以为配一家就能用全部 AI |
| secrets | 一份 `provider` + 一把 Key；切换覆盖 | 配 DeepSeek 会冲掉百炼，路线 C 读不到 `DASHSCOPE_API_KEY` |
| 文案 | `chat_completion`；DashScope 文本级联 `qwen3.7-flash` → … → `qwen-plus/turbo/max` | 未用百炼上已开通的 `deepseek-v4-*` |
| 封面生图 | `route_c.py` 写死万相异步 + `wanx2.1-t2i-plus` | 与设置页无关；型号偏旧（2025-01） |
| OCR | `qwen-vl-plus`；审美 `qwen-vl-max` | 官方已标「旧版 Qwen-VL」；百炼现推 Qwen3.7/3.8 原生视觉 |
| 就绪灯 | `llmAvailable === last_ping_ok` 同时点亮文案和封面字体 | 文案 ping 成功 ≠ 万相可用 |
| 用户感知 | 切换服务商、选模型、免费级联提示「已自动改用可用模型」 | 与「不感知切换」相反 |

### 1.3 问题清单（P-BAI-*）

| ID | 问题 | 用户感知 | 严重度 |
|----|------|----------|--------|
| **P-BAI-01** | 一把「当前服务商」无法同时服务 DeepSeek 文案与百炼图像 | 配了文案，封面字体静默走字库 | P0 |
| **P-BAI-02** | 就绪灯绑死文本 ping | 「已就绪」点封面仍失败 | P0 |
| **P-BAI-03** | 型号写死旧 VL / 万相 2.1 / 旧 `qwen-plus` 兜底 | 担心停服；新用户控制台找不到 | P1 |
| **P-BAI-04** | 模型下拉暴露内部级联 | 非开发者劝退 | P1 |
| **P-BAI-05** | 官方 DeepSeek 与百炼托管 DeepSeek 抢心智 | 「我不是已经有 DeepSeek 了吗」 | P1 |
| **P-BAI-06** | 思考模式未定义 | 延迟/费用/JSON 稳定性未知 | P1（W0 钉） |

### 1.4 核心判断

**不**再找一个全能模型。百炼托管的 `deepseek-v4-pro` 解决的是「文案要 DeepSeek 味、但 Key 仍是百炼」。图像仍是 VL/OCR + 生图，同一把 Key、不同 model id。

---

## 2. 目标与非目标

### 2.1 目标

| ID | 目标 |
|----|------|
| **G-BAI-01** | 开闸用户只配 **一次** 百炼 Key，即可触发杂志文案与封面字体（后者仍受 CAL 旗标与 fail-open） |
| **G-BAI-02** | Studio **只出现** 通义百炼接入面：无服务商二选一、无模型下拉、无官方 DeepSeek 配置（含高级） |
| **G-BAI-03** | AI Sheet 文案 / 图像分区；失败局部化 |
| **G-BAI-04** | 内部按能力槽路由；日志有型号，UI 无型号 |
| **G-BAI-05** | 三款阿里侧默认型号迁到现行世代（见 D-BAI-04），W0 狗粮通过才切生图默认 |
| **G-BAI-06** | 已有官方 DeepSeek Key 的用户：设置里看不到 DeepSeek；引导改配百炼后文案+图像才齐。Studio **不再**用官方 DeepSeek 出杂志文案 |

### 2.2 非目标

| ID | 非目标 |
|----|--------|
| **NG-BAI-01** | 跨云自动 failover（百炼挂了改打官方 DeepSeek / Gemini） |
| **NG-BAI-02** | 官方 Gemini / Codex / OpenAI 一等公民；正式包自定义 base_url / 中转 |
| **NG-BAI-03** | 重写 AIR Prompt、三语气、渠道包 |
| **NG-BAI-04** | 开放式文生封面风景（CAD） |
| **NG-BAI-05** | 为万相再做一套用户可见「图像 Key」 |
| **NG-BAI-06** | 用 VL 聊天接口冒充文生图 |
| **NG-BAI-07** | 导入主链自动 LLM narrate |
| **NG-BAI-08** | Studio 内任何官方 DeepSeek 接入 UI（含高级折叠、服务商下拉、DeepSeek 申请链） |

### 2.3 成功画像

- 新用户：控制台复制百炼 Key → 保存并测试 → Sheet 上文案与封面字体都可点。  
- 老用户（只配过官方 DeepSeek）：打开设置 **看不到** DeepSeek；须改填百炼。改配前杂志文案按未连接（本机 stub），封面走字库。  
- 老用户（已配百炼）：无需重填；路由表切换后文案可能改走 V4-Pro，体感是「更像杂志」，不是「换了家」。

---

## 3. 体验合同与冻结决策

### 3.1 能力分层（相对 DLLM 的修订）

| 层级 | 名称 | 用户一句话 | 本主题 |
|------|------|------------|--------|
| **L0** | 本机核心 | 无 Key 也能出长图 | **不变** |
| **L1** | 百炼一体 | 一把百炼 Key，文案+图像 | **唯一用户升级路径** |
| **L2** | 审美 MLLM 等 | 看图打分 | 同一把百炼 Key + `vision` 槽；默认仍跟 ACP 旗标 |

### 3.2 冻结决策（D-BAI-*）

| ID | 决策 | 说明 |
|----|------|------|
| **D-BAI-01** | **用户面仅百炼接入** | Studio 设置 / AI Sheet 连接 **只** 提供通义百炼：Key + 保存并测试。标题统一 **「模型API 配置」**（D-BAI-17）。**禁止** DeepSeek 服务商选项、申请链、模型列表（主路径与高级皆无）。V1 **无** 国际站选择、**无** 自定义 URL（D-BAI-18/19）。 |
| **D-BAI-02** | **按能力槽路由，不按用户选模型** | 见 §5.1。用户选的「模型」字段默认空；正式包 **不** 提供手填覆盖。内测包可用 config 旗标覆盖 `copy` 槽。 |
| **D-BAI-03** | **文案首选百炼 `deepseek-v4-pro`** | 同一兼容端点 `dashscope.aliyuncs.com/compatible-mode/v1`（已探通 `deepseek-v4-flash-0731`）。Pro 若 404 / 必须 Workspace MaaS 地址，W0 回退 Flash 为默认并记 OQ-BAI-02。 |
| **D-BAI-04** | **三款阿里默认型号升级（目标世代）** | 见 §3.3。生图默认 **W0 对比通过前仍用 `wanx2.1-t2i-plus`**（D-CAL-18 字形实证），不得未测切换。 |
| **D-BAI-05** | **级联按槽，禁止一条全球名单** | 文案额度错误只换文本模型；万相失败只降级路线 B；OCR 失败只判校验未过。 |
| **D-BAI-06** | **Ping 只证 Key** | 一次短超时文本 ping（可用 Flash，避免 Pro 思考烧 ping）。不在 ping 里打万相/VL。 |
| **D-BAI-07** | **就绪拆灯** | `connectionOk`（Key ping）≠ `copyReady` ≠ `imageReady`。V1：`copyReady = connectionOk`；`imageReady` 乐观等于 `connectionOk`，**首次 t2i/vision 鉴权失败后**该动作改诚实态，不关文案灯。禁止再用单一 `llmAvailable` 点亮封面字体。 |
| **D-BAI-08** | **思考模式默认开** | 文案槽 DeepSeek-V4 **`enable_thinking=true` 为默认**。是否关闭 **以 W0 实测为准**（OQ-BAI-01）。Ping **强制关思考**。若百炼要求思考必须 **stream** 而现网 client 非流式，W0 须先验证非流式能否开思考；**不能则 W1 生产默认改为关思考**，流式作为独立增量，不得假装已开（D-BAI-14）。 |
| **D-BAI-09** | **UI 不宣布切换** | 槽内 fallback 成功：不 Toast「已改用 xx」。仅当整槽失败才人话错误（额度/未开通）。 |
| **D-BAI-10** | **Studio 密钥槽只有百炼** | `secrets.json` 用户可写槽 = `dashscope`。旧文件里的官方 `deepseek` Key **不进 UI、不驱动 Studio narrate/ping**（可保留磁盘字段以免误删，升级时 `active` 强制百炼）。图像与文案都只读百炼 Key。CLI / `DEEPSEEK_API_KEY` env 仍可供开发者命令行，与 Studio 设置脱钩。 |
| **D-BAI-11** | **协议两套，对用户仍是一家** | Chat Completions（copy/vision）+ 万相/图像异步（t2i）。不把生图塞进 chat。 |
| **D-BAI-12** | **Sheet 分区** | 本册动作至少两张卡：「杂志文案」「封面字体」（识图不单独做第三张用户卡；OCR 是封面字体的内部门槛）。连接区改名，不再叫「写作引擎」为主标题。 |
| **D-BAI-13** | **继承 fail-open** | 文案失败 → 保留本机/旧文案；封面失败 → 路线 B；导出永不因 BAI 失败而禁。 |
| **D-BAI-14** | **思考不得假绿** | 现网 `llm/client.py` 为非流式 `urlopen`。W0 必须用真实百炼调用证明：非流式 + `enable_thinking` + 杂志 JSON 可解析。失败则生产默认关思考，并记 OQ-BAI-01=关。 |
| **D-BAI-15** | **生图升级先验协议** | W0 对 `wan2.7-image-pro` / `qwen-image-3.0-pro` / `wan2.2-t2i-plus` 除字形外必须记录：是否仍走现网万相异步 URL。协议不同则 **不得** 当 drop-in 替换，须单独立项改 `route_c.py`。 |
| **D-BAI-16** | **OCR 升级先验多模态合同** | `qwen3.5-ocr` 必须在现网 `vision_chat_completion`（`image_url` + JSON）上打通；否则默认改 `qwen3.7-flash`，旧 `qwen-vl-plus` 仅链尾。 |
| **D-BAI-17** | **用户可见主名 =「模型API 配置」** | Modal 标题、首页设置入口、Sheet 连接区、帮助 H7 统一此名。不再使用「智能连接」「写作引擎」作主标题。 |
| **D-BAI-18** | **V1 只中国站** | 正式包不提供国际站选择；`region` 固定 `cn`。国际站（OQ-BAI-06）推迟 W2+。 |
| **D-BAI-19** | **正式包无自定义 URL** | 不暴露 base_url 输入。中转 / 自定义端点为非目标（NG-BAI-02）。内测/dark 可用 config 覆盖，不进用户面。 |
| **D-BAI-20** | **思考开关正式包隐藏** | 用户不可见。W0 若证明非流式无法开思考：**V1 关思考交货**，不为此做流式客户端（流式另立项）。 |

### 3.3 型号升级合同（D-BAI-04 展开）

用户担心的「三个阿里模型」对应现网：**万相 2.1 文生图**、**qwen-vl-plus（OCR）**、**qwen-vl-max（审美）**。百炼已将 Qwen-VL 标为旧版，万相 2.1 文生图停在 2025-01，后续有 2.2 / 2.6 / 2.7 与千问生图。

| 能力槽 | 现网（As-Is） | **目标默认（本主题）** | 槽内兜底 | 不得作为默认的原因 |
|--------|---------------|------------------------|----------|---------------------|
| **copy** | `qwen3.7-flash` 级联到 `qwen-plus/turbo/max` | **`deepseek-v4-pro`** | `deepseek-v4-flash-0731` → `qwen3.7-flash` → `qwen3.7-plus` → `qwen3.8-max` | 旧名 `qwen-plus/turbo/max` 仅作 **最后兼容别名**（控制台仍有则留在链尾，不进 UI） |
| **vision · OCR** | `qwen-vl-plus` | **`qwen3.5-ocr`** | `qwen3.7-flash`（原生视觉）→ `qwen-vl-plus` | 专用 OCR 优先于通用 VL；旧 VL 只防停服前的兼容 |
| **vision · 审美** | `qwen-vl-max` | **`qwen3.7-plus`** | `qwen3.8-max` → `qwen-vl-max` | 3.8-max 更强但更贵；审美短名单用 plus 级 |
| **t2i** | `wanx2.1-t2i-plus` | **W0 冠军**（候选见下） | 现网 `wanx2.1-t2i-plus` 必须留在链上直到冠军稳定 | 未测切换会毁掉 CAL 字形门（「光」字教训） |

**生图 W0 候选（必须实机比字形，不是看发布日）：**

1. `wan2.7-image-pro`（2026-04 · 官方强调文字渲染）  
2. `qwen-image-3.0-pro`（2026-07 · 小字/多字体渲染，与书法贴纸同向）  
3. `wan2.2-t2i-plus`（2.1 的直接世代升级）  

评分对齐 CAL：地名生僻字、短标题、标点/数字；OCR 回读通过率；延迟；审核拒绝率。 **冠军未出前，生产默认禁止改 D-CAL-18。**

**文本旧链：** `qwen-plus` / `qwen-turbo` / `qwen-max` 不再作为「付费兜底」主叙事；付费兜底改为 Qwen3.7/3.8。若 W0 发现某账号只有旧名能打通，链尾保留旧名。

### 3.4 思考模式（D-BAI-08 细则）

| 调用 | 默认 |
|------|------|
| 文案 narrate（`copy` + DeepSeek-V4） | **开思考** |
| 文案 fallback 到 Qwen3.x | 跟该模型百炼默认；不额外强开 |
| Ping | **关思考** |
| OCR / 审美 | 关思考（要短 JSON） |
| 生图 | 不适用 |

W0 记录至少：n≥10 次 narrate（含开/关思考对照，或先全开再抽 3 次关闭对照）。关闭条件（满足任两条建议关）：JSON 解析失败率开 > 关 +10pt；P95 > 产品可接受阈值（建议 45s，OQ-BAI-01 可改）；费用显著高于 Flash 无思考且文风无差异。 **未完成 W0 不得在生产关思考。**

---

## 4. 功能规格（F-BAI-*）

### 4.1 F-BAI-01 · 配置 Modal（主路径）

**标题：** 模型API 配置（D-BAI-17；替代「写作引擎」「智能连接」）。

**主路径字段（仅这些默认可见）：**

1. 说明：只读「通义百炼」（**无**服务商 `<select>`）。申请 Key 外链仅百炼控制台 / 官方说明。  
2. API Key。  
3. 主按钮：「保存并测试」。  
4. 状态：未填写 / 已保存未测 / 已连接 / 失败人话。

**禁止出现（主路径、高级、正式包皆无）：** DeepSeek 选项与申请链、模型下拉、服务商切换确认、**国际站选择**、**自定义 API 地址**、思考模式开关。

**正式包无「高级」折叠。** 内测/dark 可用 config 覆盖地域/base_url/思考，不进设置 UI。

### 4.2 F-BAI-02 · 保存并测试

- 写入百炼槽 Key；文本 ping（无思考）。  
- 成功：`last_ping_ok=true`；文案「已连接通义百炼」。  
- 失败：沿用 WEA 错误矩阵，用户面服务商名统一「通义百炼」，不要说 DeepSeek。  
- **不**把「已自动改用可用模型」作为主路径成功文案（D-BAI-09）。若 ping 首选 Pro 失败而 Flash 成功，静默记实际 ping 模型，UI 仍「已连接」。

### 4.3 F-BAI-03 · AI Sheet 分区

继承 SAS 壳（Dock「AI」、与精修互斥、未开闸诚实态）。

**开闸后主区顺序：**

1. **杂志文案**（AIR 现网 narrate CTA / 确认 / busy / 覆盖提示）  
   - 未连接：CTA「去连接」→ Modal（`source=ai_sheet_copy`）  
   - 已连接：现网生成/再生成  
2. **封面字体**（CAL 现网 resolve + 优先 AI 手写体勾选）  
   - 未连接百炼：说明「封面手写体需要通义百炼」+「去连接」；字库路线仍可用时诚实写「将使用本机字库」  
   - 已连接但 t2i 调用失败：Toast 局部失败 + 自动路线 B，不关文案卡  
3. **模型API 配置**（沉底）  
   - 已连接：折叠，「模型API 配置 · 已连接」  
   - 未连接：置顶展开（继承现网「未就绪置顶」）  
4. Intent / 建议（W2 SAS 已有则保持；调用走 copy 或独立 Agent 配置，不在本主题扩模型）

**禁止：** 一张「AI 全能」按钮同时烧文案+生图。

### 4.4 F-BAI-04 · 首页设置入口

首页设置手风琴与 Modal 同源。标签 **「模型API 配置」**；描述 COPY-BAI-12。

### 4.5 F-BAI-05 · 旧入口与兼容

| 入口 | 策略 |
|------|------|
| 官方 DeepSeek 已配、无百炼 | **不**再驱动 Studio 文案；连接区引导填百炼；设置里 **无** DeepSeek 控件。磁盘旧 Key **留着不管**，不删 |
| 百炼已配 | 自动吃新路由表；无需重填；`region` 视为 cn |
| 模型下拉里选过 `qwen-plus` | 忽略用户模型，走 D-BAI-02 默认路由 |
| 自定义 base_url / 国际站 | 正式包忽略用户面；磁盘里若有 intl/custom，W1 可继续用于请求但 **不展示、不可改**；W2 再决定是否清 |

### 4.6 F-BAI-06 · 窄屏

Sheet 两张卡可缩按钮为「生成文案」「生成封面字」。连接区一行状态。

---

## 5. 数据 / 路由 / API

### 5.1 任务路由表（实现源）

代码落点建议：`travelogue/util/llm_presets.py` 扩展为 **capability registry**（或新 `travelogue/llm/router.py`，layer-0 不向上引用）。前端 **不**复制一份型号表；status API 只下发连接态，不下发完整级联（防泄漏与漂移）。

| capability | protocol | primary | fallbacks | 调用方 |
|------------|----------|---------|-----------|--------|
| `copy` | OpenAI-compat chat | `deepseek-v4-pro` | 见 §3.3 | `chat_completion` / narrate |
| `vision_ocr` | OpenAI-compat chat + image_url | `qwen3.5-ocr` | §3.3 | `ocr_verify.py` |
| `vision_aesthetic` | 同上 | `qwen3.7-plus` | §3.3 | `aesthetic_mllm_adapter.py` |
| `t2i` | 万相/图像异步 API | W0 冠军或暂 `wanx2.1-t2i-plus` | 现网 2.1 plus | `route_c.py` |

`model_failover=true` 仅在 **同槽同协议** 内生效。Vision 调用 **禁止** 走 copy 级联。Copy **禁止** 走 VL/OCR 模型（贵且文风差），除非 copy 链全部 404。

### 5.2 secrets 形状（D-BAI-10）

`user_data/secrets.json` 以百炼为唯一 Studio 槽：

```json
{
  "dashscope": {
    "api_key": "sk-…",
    "region": "cn",
    "base_url": null,
    "last_ping_ok": true
  }
}
```

- 读旧版扁平 `{provider, api_key, …}`：若 `provider=dashscope` 迁入上式；若 `provider=deepseek` **不**写入 Studio 活跃槽、**不**用于 ping/narrate；可把旧字段留在文件注释性备份或忽略。  
- GET status：`maskedKey`（百炼）、`connectionOk`、`hasDashscope`；**不要**下发 `hasDeepseek` 给前端做第二套 UI。  
- 注入 env：仅 `DASHSCOPE_API_KEY`。路线 C 与文案都读百炼。  
- POST settings：忽略客户端传来的 `provider=deepseek`（视为 400 或强制改写为 dashscope），防止旧前端残留。

### 5.3 API（复用 + 增量）

| 能力 | 合同 |
|------|------|
| 杂志文案 | 现网 `POST /__travelogue/narrate`；服务端改走 `copy` 槽 |
| 装帧标题 | 现网 `POST .../title-art/resolve`；Key 来自百炼槽 |
| 连接读写 | 现网 `/llm/settings` `/llm/ping` `/llm/status`；**只接受 dashscope**；status 增 D-BAI-07 字段 |
| **禁止** | 新建第二套密钥业务端点；为每个模型各做 ping API |

思考模式：由服务端按 D-BAI-08 / D-BAI-20 附加；**不要**让前端传 `enable_thinking`。

### 5.4 错误与 fail-open

| 场景 | 用户面 | 工程 |
|------|--------|------|
| Key 无效 | 连接失败；两张卡都去连接 | `E_LLM_AUTH` |
| 仅免费额度 / 某模型额度尽 | 「通义百炼额度不足…」；槽内 fallback，全失败再报 | `E_LLM_QUOTA_FREE_TIER` / `E_LLM_QUOTA` |
| 生图模型未开通 | 封面字体走字库；文案不受影响 | 记 `E_CAL_C_*` / 新码可选 `E_LLM_IMAGE_UNAVAILABLE`（W1 登 ERROR-CODES） |
| Pro 不存在 | 静默 Flash；UI 仍已连接 | 日志 `E_LLM_MODEL` |
| 思考导致非 JSON | 现网 json 降级；W0 计入 OQ-BAI-01 | 解析失败重试一次关思考（**仅当次**，不改默认） |

当次关思考重试：允许。改全局默认：不允许，除非 OQ-BAI-01 关闭。

---

## 6. 文案（COPY-BAI-*）

| ID | 场景 | 文案（冻结方向） |
|----|------|------------------|
| **COPY-BAI-01** | Modal / 设置 / Sheet 连接标题 | 模型API 配置 |
| **COPY-BAI-02** | Modal 副标题 | 使用通义百炼 API Key。杂志文案和封面字体都会用到，无需选择模型。 |
| **COPY-BAI-03** | 主按钮 | 保存并测试 |
| **COPY-BAI-04** | 成功 | 已连接通义百炼 |
| **COPY-BAI-05** | Sheet 连接已就绪 | 模型API 配置 · 已连接 |
| **COPY-BAI-06** | 文案未连接 | 连接通义百炼后可生成杂志文案 |
| **COPY-BAI-07** | 图像未连接 | 封面手写体需要通义百炼；未连接时使用本机字库 |
| **COPY-BAI-08** | 图像调用失败 | 封面字体暂时改用本机字库，不影响文案和导出 |
| **COPY-BAI-09** | 额度 | 通义百炼额度不足。请到控制台关闭「仅使用免费额度」或充值后再试。 |
| **COPY-BAI-10** | 旧 DeepSeek 用户 | 请改用通义百炼 API Key。杂志文案和封面字体都在这一把 Key 上。 |
| **COPY-BAI-11** | 脚注 | 密钥只保存在本机。失败不影响出图与导出。 |
| **COPY-BAI-12** | 首页设置摘要 | 一把通义百炼 Key，用于文案和封面字体 |

禁词：模型 id、万相、VL、思考链、token、failover、「已自动改用」。  
继承：缺 Key 不得写成整单生成失败（NAS/AIR/SAS）。

SAS COPY-SAS-N01「配置写作引擎」在开闸包 **改为** COPY-BAI-06 方向（「去连接」）。

---

## 7. 埋点

| 事件 | 属性 | 备注 |
|------|------|------|
| 复用 `llm_settings_save` / `llm_ping_*` | `provider=dashscope`；**无** key | 须带 `source`；**禁止**再打 `llm_provider_change` 到 deepseek |
| 复用 `llm_narrate_*` / `title_art_*` / `ai_sheet_*` | 增 `capability`=`copy\|t2i\|vision_ocr` | 无 model 在 **用户可关联** 的前端事件 |
| **`bai_route_result`**（服务端/管道） | `capability`；`model`；`fallback`；`thinking`；ok；latency_ms；error_code? | **仅后端/本地日志**；analytics 载荷 **禁止 model** 除非已是内部 allowlist 且无 PII |
| `ai_sheet_action_click` | action 保持；source | 连接 CTA 用 `open_settings` |

W1：`analytics.js` allowlist 只加前端需要的新事件名；型号留服务端。

---

## 8. 里程碑

| 波次 | 范围 | Go / No-Go |
|------|------|------------|
| **W0** | 实机狗粮：Pro ping+narrate（开思考，含非流式验证 D-BAI-14）；Flash 对照；`qwen3.5-ocr` 的 `image_url`；生图三候选 **协议+字形** vs `wanx2.1`；线框 F0–F6 | 无 Pro 则默认改 Flash（OQ-BAI-02）。思考非流式失败则生产默认关。生图冠军未出 **不挡** 连接 UI，但 **挡** 改生产 t2i 默认 |
| **W1** | secrets 仅百炼槽 + 旧文件迁移；Modal **「模型API 配置」** 无 DeepSeek/国际站/自定义 URL；status 拆灯；copy 路由；ping 无思考；Sheet 文案/图像/连接文案；OCR 换目标型号（可留 VL 链尾） | 无百炼 = Studio 文案未连接；图像诚实走字库。**可与 W0 并行**；开思考/换生图默认/换 OCR 默认以 W0 记录为准 |
| **W2** | t2i 切冠军（或书面保留 2.1）；审美换 `qwen3.7-plus`；COPY 全替换；OQ-BAI-01 关闭思考与否；国际站另议 | 封面字形不得劣于现网盲评底线 |
| **W3** | 狗粮清单 + 错误码登记 + 帮助 H7 改「模型API 配置」 | 真人走通：只填一次百炼，文案+封面字 |

W0 可与 W1 部分并行（UI 不依赖生图冠军）。

---

## 9. 风险与开放问题

| ID | 项 | 默认倾向 | 关闭波次 |
|----|----|----------|----------|
| **OQ-BAI-01** | 文案思考开还是关 | **先开**；非流式失败则 **V1 关思考交货**（D-BAI-20），不做流式客户端 | W0–W2 |
| **OQ-BAI-02** | `deepseek-v4-pro` 是否可在现网 `compatible-mode/v1` 调用（无需 Workspace MaaS URL） | 先假设可以（Flash 已通）；不行则默认 Flash | W0 |
| **OQ-BAI-03** | 生图冠军 | 未测不切默认 | W0–W2 |
| **OQ-BAI-04** | `qwen3.5-ocr` 对书法贴纸是否优于 `qwen3.7-flash` | OCR 专用优先；若误识印章/飞白则改 3.7-flash | W0 |
| **OQ-BAI-05** | 正式包是否露出思考开关 | **关闭：藏**（D-BAI-20） | **已关** |
| **OQ-BAI-06** | 国际站是否进 V1 | **关闭：V1 只中国站**（D-BAI-18）；intl 推迟 | **已关 · 推迟** |
| **OQ-BAI-07** | 正式包自定义 URL / 中转 | **关闭：不提供**（D-BAI-19） | **已关** |

**风险**

| 风险 | 缓解 |
|------|------|
| Pro 思考让 narrate 超时 | ping 关思考；当次 JSON 失败可关思考重试；超时沿用现网 E_LLM_TIMEOUT |
| 生图新模型字形回退 | 冠军门 + 保留 2.1 链尾 + 路线 B |
| 旧 VL 停服发生在 W2 前 | W1 先把 OCR 切到 3.5-ocr / 3.7-flash |
| 双 Key 迁移写坏 secrets | 原子写 + 单测旧扁平格式 + 失败则只读不写 |
| 用户以为「已连接」= 万相已开通 | COPY-BAI-08；分灯 D-BAI-07 |

---

## 10. 验收（AC-BAI-*）

| ID | 断言 | 波次 |
|----|------|------|
| **AC-BAI-01** | 配置 UI **无** DeepSeek 控件、**无** 模型下拉、**无** 国际站选择、**无** 自定义 URL、**无** 思考开关；标题为「模型API 配置」 | W1 |
| **AC-BAI-02** | 只填百炼 Key，保存并测试成功 → 杂志文案可确认生成（dark/开闸） | W1 |
| **AC-BAI-03** | 同上条件下点封面字体：若 t2i 可用则路线 C；若不可用则路线 B 且 Toast 不指责文案、导出仍可用 | W1–W2 |
| **AC-BAI-04** | 仅官方 DeepSeek 旧 secrets、无百炼：Studio 文案视为未连接（COPY-BAI-10）；设置无法再填 DeepSeek；磁盘旧 Key 仍在；导出仍可用 | W1 |
| **AC-BAI-05** | 旧版扁平 `secrets.json`：百炼 Key 迁入后仍可用；DeepSeek-only 不驱动 Studio | W1 |
| **AC-BAI-06** | Ping 请求不含思考；文案默认含思考（直到 OQ-BAI-01 关闭为关） | W1 |
| **AC-BAI-07** | 文案槽额度失败不调用万相；万相失败不改写已生成文案 | W1 |
| **AC-BAI-08** | 用户可见字符串不含 model id /「已自动改用」 | W1 |
| **AC-BAI-09** | `llmAvailable` 不再单独点亮封面字体 CTA（测试锁 status 字段） | W1 |
| **AC-BAI-10** | OCR 默认不是 `qwen-vl-plus`（除非 W0 判定新模型不可用并书面豁免） | W1 |
| **AC-BAI-11** | 生产 t2i 默认若离开 `wanx2.1-t2i-plus`，须附 W0 字形对比记录 | W2 |
| **AC-BAI-12** | 无 Key：L0 导入→预览→长图仍通；Sheet 不报整单失败 | W1 |
| **AC-BAI-13** | NAS 关闸：连接 API 行为不弱于现网 NAS 合同 | W1 |
| **AC-BAI-14** | 帮助 H7 / 设置摘要使用「模型API 配置」+ COPY-BAI-12 | W3 |
| **AC-BAI-15** | POST `/llm/settings` 带 `provider=deepseek` 不得写成官方 DeepSeek 活跃连接（400 或强制百炼） | W1 |
| **AC-BAI-16** | W0 记录：非流式思考是否可解析 JSON；生图候选协议是否与 `route_c.py` 同构；`qwen3.5-ocr` 是否吃 `image_url` | W0 |
| **AC-BAI-17** | 保存百炼连接后 `region` 为 cn（或不写 intl） | W1 |

---

## 11. 附录

### 11.1 现网 → 目标型号速查

| 用途 | 现网 | 目标 | 备注 |
|------|------|------|------|
| 文案 | `qwen3.7-flash` + 旧 plus/turbo/max | `deepseek-v4-pro` | 百炼托管，不是官方 DeepSeek 域名 |
| 文案 ping | 同级联 | Flash 或 Pro **无思考** | D-BAI-06 |
| OCR | `qwen-vl-plus` | `qwen3.5-ocr` | 旧 VL 链尾 |
| 审美 | `qwen-vl-max` | `qwen3.7-plus` | W2 |
| 封面生图 | `wanx2.1-t2i-plus` | W0 冠军 | 未测不切 |

### 11.2 实现锚点（As-Is）

| 模块 | 路径 |
|------|------|
| Preset / 级联 | `travelogue/util/llm_presets.py` |
| Chat / ping | `travelogue/llm/client.py` |
| secrets | `travelogue/llm/user_settings.py` |
| 设置 API | `travelogue/web/studio_handlers/llm_settings_handlers.py` |
| 设置 UI | `templates/studio/js/llm-settings.js` |
| AI Sheet | `templates/studio/preview-toolbar/ai-sheet.js` |
| 万相 | `travelogue/cover_engine/title_art/route_c.py` |
| OCR | `travelogue/cover_engine/title_art/ocr_verify.py` |
| 审美 | `travelogue/ai/agents/aesthetic_mllm_adapter.py` |

### 11.3 评审拍板清单

产品 2026-08-13 **全部认可**；同日拍板写回 v0.2.1：

- [x] **D-BAI-01 / 17** 用户面仅百炼；主名 **「模型API 配置」**  
- [x] **D-BAI-18** V1 只中国站  
- [x] **D-BAI-19** 正式包无自定义 URL  
- [x] **D-BAI-20** 思考开关藏；非流式失败则 V1 关思考，不做流式客户端  
- [x] 旧官方 DeepSeek Key **留盘不驱动**  
- [x] W1 与 W0 **并行**（开思考/换生图/换 OCR 等 W0）  
- [x] **D-BAI-08 / 04** 思考先开、生图未测不切  
- [x] COPY 禁型号 · secrets 仅百炼槽 · NAS 不回退  

### 11.4 版本记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.2.1 | 2026-08-13 | 产品拍板：主名「模型API 配置」；V1 只中国站；正式包无自定义 URL / 思考开关；旧 DeepSeek Key 留盘；W1∥W0；流式思考失败则关思考交货（D-BAI-17～20） |
| v0.2.0 | 2026-08-13 | 八席评审 Conditional Go：隐藏全部 DeepSeek 接入面；D-BAI-14～16（思考/生图协议/OCR 合同）；AC-BAI-15/16 |
| v0.1.0 | 2026-08-13 | 初稿：一门多房、Sheet 分区、V4-Pro 文案、思考默认开、三款阿里型号升级合同 |
