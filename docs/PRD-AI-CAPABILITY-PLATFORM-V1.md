# Travelogue · AI 能力平台 V1 产品需求文档（PRD）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue Studio |
| **文档版本** | **v0.3.0** |
| **状态** | **Conditional Go · 开发负责人技术可行性核查已回写 · W1 排期已按代码事实调整** |
| **DOC-STATUS** | **active** |
| **主题代号** | 「编辑智能收编」— **ACP**（AI Capability Platform） |
| **触发来源** | 2026-08-10 AI 能力现状架构评审：LLM/VLM 调用分散在 `services/llm_narrate.py`（叙事）、`cover_engine/title_art/route_c.py`（生图艺术字）、`vision/aesthetic_mllm.py`（审美 MLLM）三处，各自实现重试/缓存/降级，且已有明确的 import-linter 债务（`vision.aesthetic_mllm → curation.*` 三条 `ignore_imports`，标注「aesthetic MLLM relocation pending P2」）；同时 `AGENT-ARCHITECTURE.md` §17 设计的 Intent Brief / Layout Critic / Mosaic Judge 均未落地。本主题把「LLM 能力」收编为一个独立系统，并承接既往架构评审给出的 P0–P2 路线图 |
| **前置条件** | 不推翻、不重做：[PRD-DESKTOP-LLM-SETUP-V1.md](./PRD-DESKTOP-LLM-SETUP-V1.md)（L0/L1 铁律 · secrets）· [PRD-WRITING-ENGINE-API-HARDENING-V1.md](./PRD-WRITING-ENGINE-API-HARDENING-V1.md)（服务商隔离）· [adr/019-desktop-user-data-llm-secrets.md](./adr/019-desktop-user-data-llm-secrets.md)（密钥落盘）· [PRD-NO-AI-SURFACE-V1.md](./PRD-NO-AI-SURFACE-V1.md)（默认关用户面门控） |
| **关联文档** | [AGENT-ARCHITECTURE.md §17](./AGENT-ARCHITECTURE.md)（策展四子系统 LLM 增强策略，本主题的落地母文档）· [PRD-AI-RETURN-V1.md](./PRD-AI-RETURN-V1.md)（AIR · 用户面解冻，本主题为其提供解冻门槛数据）· [PRD-COVER-CALLIGRAPHY-TITLE-V1.md](./PRD-COVER-CALLIGRAPHY-TITLE-V1.md)（CAL · 路线 C 生图迁移方）· [PRD-COVER-TYPESETTING-CONTINUITY-V1.md](./PRD-COVER-TYPESETTING-CONTINUITY-V1.md)（CTS · G-CTS-05 埋点依赖本平台）· `docs/aesthetic-alignment/`（PA-MLLM 迁移方）· `TECH-ARCHITECTURE.md` §18（分层约束） |
| **评审记录** | [acceptance-records/acp-ai-capability-platform-v1-review-2026-08-10.md](./acceptance-records/acp-ai-capability-platform-v1-review-2026-08-10.md)（七席+典型用户 · 8/8 Conditional Go） |
| **技术可行性核查** | 2026-08-10 开发负责人对照现网代码逐项核查（无代码改动），发现 §4/§5/§7/§8 多处方案与实际调用时机/性能预算不符，已回写本版（详见各节标注） |
| **验收** | Kickoff 后拆 `ACCEPTANCE-AI-CAPABILITY-PLATFORM-V1.md`；本文 §10 为源 |
| **实施清单** | Kickoff 后拆 `IMPLEMENTATION-AI-CAPABILITY-PLATFORM-V1.md` |
| **更新日期** | 2026-08-10 |

> **定位**
>
> ACP 不新增一个「更聪明的功能」，而是把**已经存在、正在规划**的所有 LLM/VLM 能力（叙事文案、生图艺术字、审美 MLLM、意图理解、排版评审、拼图裁决）统一到**一个独立系统**里：统一网关、统一预算、统一观测、统一缓存、统一评测。四个策展子系统（筛选/聚类/拼图/排版）与 Agent 2 叙事师、封面装帧，**都是这个平台的消费者**，不再各自维护一份 LLM 调用逻辑。
>
> **一句话目标**：新增一个 AI 能力时，只需要写一个 Agent 适配器；不需要重新发明重试、预算、缓存、隐私审计与观测。
>
> **战略原则（继承 + 新增）**
>
> 1. **不做群聊多 Agent** — 继承 `AGENT-ARCHITECTURE.md` §12 反模式；ACP 内的 Agent 之间不互相调用，只由上层子系统各自读写结构化字段。
> 2. **执行引擎不变** — 继承 §17.1；LLM 只做「理解意图 → 调参 → 消歧 → 解释」，四子系统的确定性算法主路径不动。
> 3. **本地优先、白名单上云** — 继承 D-AIR-09；新增 Agent 默认禁止发送原图像素，需求逐条过审。
> 4. **Fail-open 铁律** — 任意 ACP 调用失败/超预算 = 该建议不存在，绝不影响主链产出。
> 5. **架构方向单向** — ACP 只能被上层（`curation`/`layout_engine`/`cover_engine`/`services`）依赖，不得反向依赖它们；这是解决现有 `vision.aesthetic_mllm → curation.*` 债务的强制约束。

---

## 0. 读者指南

| 章节 | 澄清什么 |
|------|----------|
| §1 | 现状三孤岛、已知架构债务、问题陈述 |
| §2 | 目标 / 非目标 |
| §3 | 冻结决策 D-ACP-* |
| §4 | 系统架构设计（模块清单、分层契约、迁移前后对照） |
| §5 | 功能规格 P0–P2（承接既往架构评审建议） |
| §6 | 数据 / API / 隐私 |
| §7 | 迁移计划（三个现有调用点如何切入，不回归） |
| §8 | 里程碑 |
| §9 | 埋点 |
| §10 | 验收标准 AC-ACP-* |
| §11 | 风险与开放问题 OQ-ACP-* |
| §12 | 与既有 AI 主题的关系 |
| §13 | 变更记录 |

### 0.1 术语

| 术语 | 含义 |
|------|------|
| **Gateway 层** | 现有 `travelogue/llm/`；模型级 HTTP 客户端、密钥解析、重试；本主题**保留不重构** |
| **Capability 层** | 新增 `travelogue/ai/`；能力编排（Agent、预算、缓存、观测、评测），本主题主体 |
| **Agent** | Capability 层内一个具体能力单元（如 `intent_brief`），输入结构化摘要、输出结构化 JSON + `confidence` + `source` |
| **消费者（Consumer）** | 调用某个 Agent 的上层模块（`curation.*` / `layout_engine.*` / `cover_engine.*` / `services.*`） |
| **Advisory 字段** | Agent 写入 `trip.json` 的建议性字段（如 `curation.layoutSuggestions`），消费者可读可忽略，不自动覆盖已锁定结构 |

---

## 1. 背景与问题

### 1.1 现状：三个各自为战的 LLM/VLM 调用点

| 调用点 | 文件 | 能力 | 重试/降级 | 缓存 | 预算控制 |
|--------|------|------|-----------|------|----------|
| 叙事文案 | `travelogue/services/llm_narrate.py` | 章/卡文案填槽 | 自实现 | `llm/narrate_cache.py`（brief hash） | 无显式上限 |
| 封面生图艺术字（路线 C） | `travelogue/cover_engine/title_art/route_c.py` + `ocr_verify.py` | DashScope 万相文生图 + OCR 校验 | 自实现（异步轮询） | 无 | 无 |
| 审美 MLLM（PA-MLLM） | `travelogue/vision/aesthetic_mllm.py` | 高价值候选（封面/hero/瞬间）打分 | 自实现 | 独立 `aesthetic-mllm.json` | 有 shortlist 门控，但与其它两处不共享阈值语义 |

三处都各自解决同一批问题（provider 解析、JSON 解析容错、fail-open、缓存 key 设计），但互不共享代码，也没有一个地方能回答「这个 trip 这次一共调了几次 LLM/VLM、花了多久、成功率多少」。

### 1.2 已确认的架构债务（不是猜测，是仓库里已登记的债务）

`pyproject.toml` 第 121～126 行的 import-linter 契约里已经显式记录（`[[tool.importlinter.contracts]]` → `ignore_imports`）：

```toml
# master CI debt · aesthetic MLLM relocation pending P2
"travelogue.vision.aesthetic_mllm -> travelogue.curation.aesthetic_blind_review",
# master CI debt · aesthetic MLLM relocation pending P2
"travelogue.vision.aesthetic_mllm -> travelogue.curation.album_profile",
```

即 `vision.aesthetic_mllm` 反向依赖了 `curation` 层（违反 `travelogue.curation : ... → travelogue.media : travelogue.vision : travelogue.llm` 的分层方向），项目已经知道这是债务、标了「pending P2」，但一直没有专项承接。本主题就是那个「P2」。

### 1.3 问题陈述（P-ACP-*）

| ID | 问题 | 严重度 |
|----|------|--------|
| **P-ACP-01** | 三处调用点重复实现 provider 解析、JSON 容错、fail-open，改一处 Bug 不代表另两处也修了 | 中 |
| **P-ACP-02** | `vision.aesthetic_mllm → curation.*` 反向依赖是已登记债务，长期挂着会持续腐蚀分层契约的可信度 | 中高 |
| **P-ACP-03** | 无跨调用点的统一预算：`AGENT-ARCHITECTURE.md` §17.6 提出的 `maxLlmCallsPerTrip` 从未真正实现为一个共享计数器 | 中 |
| **P-ACP-04** | 无统一观测面：`pipeline.runs[].agent` 枚举里没有任何 LLM/VLM 相关值（当前仅 `media_lab/curator/layout/storyteller/storyteller-lite/publisher`），无法从 trip 侧看出这次 AI 调了几次、花了多久 | 中高 |
| **P-ACP-05** | Intent Brief / Layout Critic / Mosaic Judge 均停留在 `AGENT-ARCHITECTURE.md` §17 文档层面，四子系统仍各自消费不到「用户意图」 | 高（ROI 最高但未落地） |
| **P-ACP-06** | `PRD-AI-RETURN-V1.md` 的默认开关 `OQ-AIR-01` 悬而未决，没有量化的 go/no-go 依据 | 中 |
| **P-ACP-07** | LLM 文案质量目前只能人工盲评（如 CAL 的 `AC-CAL-BLIND`），没有与算法侧（SRCC、Jaccard）对齐的统一评测方法论 | 中 |

---

## 2. 目标与非目标

### 2.1 目标（In Scope）

| ID | 目标 |
|----|------|
| **G-ACP-01** | 新建独立包 `travelogue/ai/`，作为**唯一**的 AI 能力编排层；新增能力必须走这里，不得再各自实现 |
| **G-ACP-02** | 统一预算/重试/降级/缓存/观测：一次 trip 内所有 LLM/VLM 调用可在一处查看（延迟、成功率、降级原因、估算成本） |
| **G-ACP-03** | 落地 **Intent Brief Agent** 最小版（P0），四子系统开始共享同一份「编辑意图」 |
| **G-ACP-04** | 落地 **Layout Critic** 与 **Mosaic Judge** 最小版（P1），复用 PA-MLLM 已验证的「仅对候选小样本调用」模式 |
| **G-ACP-05** | 为 `PRD-AI-RETURN-V1.md` 的 `OQ-AIR-01`（默认开关）提供量化解冻门槛计算器（P1） |
| **G-ACP-06** | 落地 G1 反馈闭环最小版：用户「这章不对」的信号可回写为下次调参依据（P2） |
| **G-ACP-07** | 建立统一的 LLM/VLM 输出**盲评 + 满意度评测框架**，与算法侧方法论对齐（P2） |
| **G-ACP-08** | 迁移既有三处调用点（narrate / route C / PA-MLLM）到新平台，**不改变**其外部契约与现有验收（AC-AIR-* / AC-CAL-* / AA 系列） |
| **G-ACP-09** | 解决 §1.2 的 import-linter 债务：迁移后可从 `pyproject.toml` 的 `ignore_imports` 中删除对应三行 |

### 2.2 非目标（Out of Scope · V1）

| ID | 非目标 | 理由 |
|----|--------|------|
| **NG-ACP-01** | 重写叙事文案的 Prompt / 语气逻辑本身 | 归 AIR；本主题只搬运调用方式，不动业务逻辑 |
| **NG-ACP-02** | 多 Agent 群聊 / 自由对话式交互 | §12 反模式；ACP 内 Agent 互不通信 |
| **NG-ACP-03** | 推翻 NAS 默认关闭用户面门控 | 门控是产品决策，不是本主题范围 |
| **NG-ACP-04** | 直接拍板「默认开启 AI」 | 本主题只**提供**量化依据，决策权仍在 AIR/产品 |
| **NG-ACP-05** | 云端托管、多租户、跨设备同步 | 与章程「本地优先」冲突 |
| **NG-ACP-06** | 新增第三方模型 provider（除 DeepSeek / DashScope） | 沿用 WEA 既有白名单 |
| **NG-ACP-07** | LLM 直接输出 `chapters[].items[]` 或改写 HTML | §12 反模式；Agent 只写 advisory 字段 |
| **NG-ACP-08** | 不强制同一迭代周期内完成 P0–P2 全部内容 | 七席+1 评审 BLK-ACP-02：M1–M4（基础设施 + 零回归迁移）可独立结项**并允许长期停留**；新增能力（M5 起）按需再评审时间线，避免变成第 6 个悬置主题（对齐 AIR/CTS 现状教训） |

---

## 3. 冻结决策（D-ACP-*）

| ID | 决策 | 说明 |
|----|------|------|
| **D-ACP-01** | **分层边界** | 新建 `travelogue/ai/`，与 `media : vision : llm` 同层（import-linter 第 6 层）；只能被 `curation/layout_engine/layout_templates/cover_engine/services` 等上层依赖，**禁止**反向导入它们的类型 |
| **D-ACP-02** | **Gateway 与 Capability 分离** | `travelogue/llm/`（模型级 HTTP 客户端、密钥解析）保留不动；`travelogue/ai/` 只依赖 `travelogue/llm/`，不重复实现 HTTP/重试。**修订（开发核查回写）**：`services/llm_narrate.py` **不物理迁入** `travelogue/ai/`——它对 `curation.asset_caption`/`services.narrative_brief`/`narrative_scope`/`narrative_validate` 的依赖是合法的 services 层业务逻辑，反向搬进 `ai` 层会立即违反 D-ACP-01 的分层方向；`narrate` 与 `ai` 的关系是「上层调用下层的横切设施」，不是「迁移」，见 D-ACP-17 |
| **D-ACP-03** | **Agent 统一签名** | 所有 Agent 输入为 dict/dataclass 摘要（不含原图路径/像素，除非显式白名单字段），输出为 `{"data": {...}, "confidence": float, "source": "llm"\|"cache"\|"fallback"}` |
| **D-ACP-04** | **统一预算** | `ai.budget.TripLlmBudget`：trip 级调用计数器，读 `config.ai_capability.max_calls_per_trip`；超限后续调用直接走 `fallback`，不报错 |
| **D-ACP-05** | **统一观测** | 扩展 `schemas/trip.schema.json` 的 `pipelineRun.agent` 枚举，新增 `intent_brief` / `layout_critic` / `mosaic_judge` / `title_art_route_c` / `aesthetic_mllm`；每次 Agent 调用写一条 `pipeline.runs[]` |
| **D-ACP-06** | **统一缓存** | `ai.cache`：`contentSig`/`briefHash` + `promptVersion` → 磁盘缓存，合并现有 `narrate_cache.py` 与 `aesthetic-mllm.json` 的模式为一套实现 |
| **D-ACP-07** | **隐私白名单不变且集中审计** | 继承 D-AIR-09；新增一个 CI 断言点：`travelogue/ai/` 目录下任意 Agent 的请求体构造函数必须过「无 `file://`、无原图 base64」静态检查（可复用 AIR §5.3 的审计思路） |
| **D-ACP-08** | **Fail-open 铁律** | 任意 Agent 调用异常/超时/超预算 → 捕获在 `travelogue/ai/` 内部，返回 `confidence=0, source="fallback"`；**不得**向上抛出阻断主链的异常 |
| **D-ACP-09** | **Advisory 字段位** | `intent.intentBrief` / `curation.layoutSuggestions` / `curation.mosaicJudgeLog` 与 `AGENT-ARCHITECTURE.md` §17.9 保持字段名一致；`structure_locked` 之后 Agent 不得自动覆写 `chapters[]` |
| **D-ACP-10** | **迁移零回归** | 迁移 narrate / route C / PA-MLLM 后，既有 API 请求/响应字段、`AC-AIR-*`、`AC-CAL-*`、AA 系列验收必须全部保持通过；新增能力可增量开关，不得默认改变现有行为 |
| **D-ACP-11** | **主题收编不等于推翻** | AIR / CTS / CAL / CAD / HIT 各自的产品决策（语气、白名单、风格）不受本主题影响；本主题只统一它们底下的 LLM/VLM 调用基础设施 |
| **D-ACP-01a** | **`cover_engine` 分层补齐**（BLK-ACP-01 回写） | 现网 `pyproject.toml` 的 `layers` 契约**不含** `cover_engine`；实施时一并将 `cover_engine` 补入 `layers`（置于 `render:export` 与 `media:vision:llm:ai` 之间），消除「新增 forbidden 契约建在未分层模块上」的治理假象 |
| **D-ACP-13** | **延迟预算 · 不拖慢首屏**（BLK-ACP-04 回写；**适用范围收窄，开发核查回写**） | 继承 `AGENT-ARCHITECTURE.md` §17.6「异步不阻塞」：**仅适用于 Intent Brief / Layout Critic**——两者均可挂载到既有 `travelogue/web/studio_jobs.py` 后台任务阶段（ingest/curate job 的一个 stage），天然异步、不阻塞 HTTP 首屏；单次调用超时保护默认 **8s**，超时直接返回 `fallback`。**Mosaic Judge 不适用本条的「同步 8s 超时」模型**，改用 D-ACP-15 |
| **D-ACP-14** | **三方 AND 门控语义**（BLK-ACP-05 回写 · 典型用户席提出） | `ai_capability.enabled` × `aiSurfaceEnabled` × 「provider 非 stub 且有效 Key」为 **AND** 语义；任一为否，`ai/agents/*` 全部直接走 `fallback`，**不发出任何外部请求**；隐私确认文案复用既有 D-AIR-09 / `COPY-AIR-PRIVACY`，不新造第二套说法 |
| **D-ACP-15** | **Mosaic Judge 二阶段设计**（开发核查回写 · 取代原「beam 内实时 tie-break」） | 核查 `layout_contract/search_budget.py` 发现 `search_timeout_ms=2000`、`max_evaluations_per_trip=500`——整章排版预算是 **2 秒**，`try_mosaic_window` 在 beam 热路径内被同步反复调用（`layout_engine/planner/screen_planner_stages.py`），塞入任何网络调用都会打穿 SearchBudget。改为**两阶段**：① beam search 按现有确定性逻辑完整跑完出结果，**不等待** Mosaic Judge；② 排版结束后，仅对分差 `< tie_epsilon` 且被判定为「值得复核」的少量窗口，异步补一次 Judge 调用；调用结果在该章渲染前到达则可覆盖为 Judge 建议的候选（仍须在原候选集合内），未到达则维持 beam 的确定性结果。Judge 的角色从「决策者」降级为「事后可能否决的复核」 |
| **D-ACP-16** | **aesthetic_mllm 迁移边界**（开发核查回写 · 取代「包一层」描述） | 核查 `vision/aesthetic_mllm.py` 发现仅 `score_image_with_mllm`（单图 vision LLM 调用）是纯粹的能力层逻辑；`build_mllm_shortlist`/`_rank_mllm_candidates`（依赖 `curation.aesthetic_score.purpose_overall`、`curation.aesthetic_blind_review.review_stratum_for_asset`）、`apply_aesthetic_mllm_scores`（依赖 `curation.aesthetic_score.refresh_aesthetic_ml_blend`）、`_write_mllm_fields`、`apply_mllm_oracle_from_labels` 均为审美打分/分层选片的 curation 业务逻辑。迁移边界冻结为：仅 `score_image_with_mllm` 核心调用下沉至 `ai/agents/aesthetic_mllm_adapter.py`；其余函数**搬迁至** `curation/aesthetic_mllm_shortlist.py`，由其调用 `ai.agents.aesthetic_mllm_adapter.score_image(...)`。这是「拆分搬家」，不是「包一层」，工作量按此重估 |
| **D-ACP-17** | **narrate 接入方式**（开发核查回写 · 呼应 D-ACP-02） | `services/llm_narrate.py` 物理位置不变；仅新增对 `travelogue.ai.budget`/`ai.cache`/`ai.telemetry` 的调用（services 层调用 ai 层，方向合法）。`ai/agents/` 下**不设** `narrate_adapter.py` 文件；§4.3/§7 对应描述已更正 |
| **D-ACP-18** | **budget 与 shared_backoff 分工**（开发核查回写） | `ai/budget.py`（`TripLlmBudget`）只管「trip 级调用**次数上限**」；`travelogue/llm/shared_backoff.py`（既有）继续管「429/502/503 **限流退避**」；两者是不同维度，`ai/budget.py` 内部调用 `shared_backoff`获取退避许可，不重新实现退避逻辑，也不合并成一个配置项 |

---

## 4. 系统架构设计

### 4.1 现状（三孤岛）

```text
services/llm_narrate.py ──┐
cover_engine/title_art/   ├──> travelogue/llm/client.py ──> DeepSeek / DashScope
route_c.py + ocr_verify.py┤        (各自处理重试/解析/缓存)
vision/aesthetic_mllm.py ─┘        └── aesthetic_mllm.py 还反向 import curation.*（债务）
```

三处各自维护 prompt、JSON 解析、fail-open、缓存 key；无共享预算与观测。

### 4.2 目标架构

```text
curation / layout_engine / cover_engine / services（消费者，不变）
        │  读写 advisory 字段（intentBrief / layoutSuggestions / mosaicJudgeLog）
        ▼
travelogue/ai/                         ← 本主题新增，唯一能力编排层
  ├── agents/
  │   ├── intent_brief.py              新增（P0）· 挂载 studio_jobs.py 既有后台任务
  │   ├── layout_critic.py             新增（P1）· 同上
  │   ├── mosaic_judge.py              新增（P1）· 二阶段调用，不进 beam 热路径（D-ACP-15）
  │   ├── title_art_adapter.py         适配现有 cover_engine/title_art/route_c.py（唯一「纯包一层」迁移）
  │   └── aesthetic_mllm_adapter.py    仅 score_image_with_mllm 核心下沉（D-ACP-16 · 拆分非整体迁移）
  ├── gate.py                          §4.6 统一前置检查（门控 AND + 延迟/超时）
  ├── budget.py                        TripLlmBudget（统一计数/降级，复用 llm/shared_backoff.py 做限流，D-ACP-18）
  ├── cache.py                         统一 contentSig+promptVersion 缓存
  ├── telemetry.py                     统一 pipeline.runs 写入 + 汇总视图
  └── eval/
      ├── blind_review.py              统一盲评框架（复用 AA/CAL 方法论）
      └── unlock_gate.py               AIR 解冻门槛计算器
        │
        ▼
travelogue/llm/（Gateway 层，不变）── client.py / user_settings.py / presets.py / errors.py / shared_backoff.py
        │
        ▼
DeepSeek / DashScope（chat + vision-chat + 文生图）

curation/aesthetic_mllm_shortlist.py（新增，非 ai/ 内）── 承接 D-ACP-16 拆出的 shortlist/blend 业务逻辑，调用 ai.agents.aesthetic_mllm_adapter
services/llm_narrate.py（物理位置不变）── 新增对 ai.budget / ai.cache / ai.telemetry 的调用（D-ACP-17）
```

### 4.3 模块清单

| 模块 | 职责 | 对应现有能力 |
|------|------|--------------|
| `ai/agents/intent_brief.py` | 1 次/trip，抽取 `titleHint/tone/peakMoments/cullPolicy/clusterHints/layoutHints/narrativeHints`；挂载既有 `studio_jobs.py` 后台任务 stage，天然满足 D-ACP-13 异步要求 | 新增（AGENT-ARCHITECTURE §17.4） |
| `ai/agents/layout_critic.py` | G1 前 1 次/trip，读章级屏摘要给排版建议；同样挂载 `studio_jobs.py` | 新增（§17.3.4） |
| `ai/agents/mosaic_judge.py` | **不在 beam 循环内调用**；排版结束后对少量近似打平的窗口做事后异步复核（D-ACP-15） | 新增（§17.3.3，设计已按开发核查修订） |
| `ai/agents/title_art_adapter.py` | 包一层 `cover_engine/title_art/route_c.py` + `ocr_verify.py`（零 curation/services 依赖，核查确认为唯一「纯包一层」迁移） | 迁移（低风险） |
| `ai/agents/aesthetic_mllm_adapter.py` | **仅**下沉 `score_image_with_mllm` 的纯 vision LLM 调用；`build_mllm_shortlist`/`apply_aesthetic_mllm_scores`/`_write_mllm_fields`/oracle 函数**不进本文件**，见 D-ACP-16 | 迁移 + 解债务（工作量按拆分重估，非「包一层」） |
| `ai/gate.py` | 统一前置检查入口（§4.6）：门控 AND 语义 + 异步/超时保护，所有 Agent 必经 | 新增 |
| `ai/budget.py` | trip 级调用**次数**预算，读 `max_calls_per_trip`；限流退避委托给既有 `llm/shared_backoff.py`（D-ACP-18），不重复实现 | 新增（复用退避基础设施） |
| `ai/cache.py` | 统一缓存（合并 `narrate_cache.py` 思路 + `aesthetic-mllm.json` 思路） | 新增（合并） |
| `ai/telemetry.py` | 写 `pipeline.runs[]` + Studio 观测面数据源 | 新增 |
| `ai/eval/blind_review.py` | 统一盲评抽样/打分导出（对齐 `pa_acceptance.py` 的 SRCC 方法论） | 新增 |
| `ai/eval/unlock_gate.py` | 读 telemetry 计算配置转化率/成功率/满意度，给 AIR 解冻建议 | 新增 |
| `curation/aesthetic_mllm_shortlist.py` | **新增位置**（不在 `ai/` 内）：承接 D-ACP-16 从 `vision/aesthetic_mllm.py` 拆出的 shortlist 排序、`album_profile`/`review_stratum` 消费、`refresh_aesthetic_ml_blend` 调用、结果写回 `quality.aesthetic`；调用 `ai.agents.aesthetic_mllm_adapter.score_image(...)` | 新增（M4 拆分产物） |
| `services/llm_narrate.py` | **物理位置不变**；新增对 `ai.budget`/`ai.cache`/`ai.telemetry` 的调用（D-ACP-17），Prompt/brief/校验逻辑不动 | 接入（非迁移） |

### 4.4 与四子系统 / Agent 的消费关系（对齐 AGENT-ARCHITECTURE §17.4.1）

| Advisory 字段 | 写入者（ai/agents/*） | 消费者 |
|----------------|------------------------|--------|
| `intent.intentBrief.cullPolicy` | `intent_brief.py` | `curation/photo_cull.py` |
| `intent.intentBrief.clusterHints` | `intent_brief.py` | `curation/clustering.py` |
| `intent.intentBrief.layoutHints` | `intent_brief.py` | `layout_engine`（beam `arc_mode`/`intent_peak_chapters`）· `mosaic/hook.py` scorer 权重 |
| `curation.layoutSuggestions` | `layout_critic.py` | G1 UI（Studio），仅展示，不自动改 `chapters[]` |
| `curation.mosaicJudgeLog` | `mosaic_judge.py` | `mosaic/compose.py` 事后异步复核（D-ACP-15；候选必须来自已有集合） |
| `meta.*` narrate 结果 | `services/llm_narrate.py`（不变，仅接入 ai.budget/cache/telemetry） | Agent 3 出版人（不变） |
| `curation.cullHints` 之外的封面标题图 | `title_art_adapter.py` | `render/cover_opening.py` |
| 审美候选打分 | `curation/aesthetic_mllm_shortlist.py`（shortlist/blend）→ `ai.agents.aesthetic_mllm_adapter`（单图打分） | `curate_scoring.py`（U-COVER/U-HERO blend，不变） |

### 4.5 与 import-linter 契约的更新

> **事实更正（七席+1 评审 BLK-ACP-01）**：核查现网 `pyproject.toml` 发现 `cover_engine` **当前不在** `layers` 列表内（该列表止于 `media : vision : llm`，`cover_engine` 是被 `render/assemble.py`、`render/cover_opening.py` 调用的未分层模块）。这意味着下面第 2 条新增的 forbidden 契约虽然能独立生效（import-linter 允许约束未列入 `layers` 的模块），但**解决不了「`cover_engine` 该在分层图哪一层」这个更根本的问题**——必须按 D-ACP-01a 一并补齐，否则会造成「看起来治理了、实际留了一块空白」的假象。

迁移完成后：

1. 按 **D-ACP-01a** 把 `cover_engine` 补入 `layers`（置于 `render:export` 与 `media:vision:llm:ai` 之间），再新增 `travelogue.ai` 至第 6 层（与 `media : vision : llm` 并列）：
   ```toml
   "travelogue.media : travelogue.vision : travelogue.llm : travelogue.ai",
   ```
2. 新增 forbidden 契约，防止 `travelogue.ai` 反向依赖上层：
   ```toml
   [[tool.importlinter.contracts]]
   name = "AI capability layer must not import upward (ACP D-ACP-01)"
   type = "forbidden"
   source_modules = ["travelogue.ai"]
   forbidden_modules = [
       "travelogue.curation", "travelogue.layout_engine", "travelogue.layout_templates",
       "travelogue.cover_engine", "travelogue.services", "travelogue.render",
       "travelogue.export", "travelogue.web", "travelogue.orchestrator",
   ]
   ```
3. 删除 §1.2 引用的三行 `ignore_imports`（`vision.aesthetic_mllm → curation.*`），因为该逻辑迁移进 `ai/agents/aesthetic_mllm_adapter.py` 后不再需要读 `curation` 类型——由消费者（`curation/aesthetic_score.py`）在调用前把所需字段整理成 dict 传入。

### 4.6 调用前置检查（D-ACP-13 / D-ACP-14 · 七席+1 评审回写）

任意 `ai/agents/*` 被调用前，`travelogue/ai/` 内部统一执行两道前置检查，检查不通过直接返回 `fallback`，**不进入** Gateway 层：

1. **门控检查**（D-ACP-14）：`ai_capability.enabled AND aiSurfaceEnabled AND (provider != "stub" AND 有效 Key)`；三者任一为否 → `source="fallback"`，零外呼。
2. **延迟检查**（D-ACP-13）：调用必须在异步任务中执行、不阻塞首屏预览渲染；单次调用设 8s 超时（可配 `ai_capability.timeout_sec`），超时即 `fallback`，不做同步重试。

两道检查在 `ai/budget.py` 与新 `ai/gate.py` 中实现，所有 Agent 适配器共用同一入口，不允许单个 Agent 自行绕过。

> **范围说明（开发核查回写）**：本节的「延迟检查」对 Intent Brief / Layout Critic 成立（两者可挂载 `studio_jobs.py` 后台任务，天然异步）。**Mosaic Judge 不走本节流程**——它的调用时机在排版结束之后，遵循 D-ACP-15 的独立两阶段设计，不受 `ai.capability.timeout_sec` 单一超时值约束，而是与 `SearchBudget`（`search_timeout_ms=2000`）解耦运行。

---

## 5. 功能规格（P0–P2）

> 编号延续既往架构评审的优先级分级；每条给出功能点、输入输出契约、与既有文档的关系、验收锚点。

### 5.1 P0-1 · Intent Brief Agent（最高 ROI）

- **触发**：Agent 0 ingest 完成后，`structure_draft` 之前，1 次调用/trip（用户可手动「重新解析意图」重跑）。
- **输入**：`userNotes`（备注原文）、`voice.transcript` 摘要、`assets[]` 的时间/地点/标签统计（不含像素）、可选 `intent.plan` 文件。
- **输出**：写入 `trip.intent.intentBrief`（结构与 `AGENT-ARCHITECTURE.md` §17.4 示例一致：`titleHint/tone/peakMoments/cullPolicy/clusterHints/layoutHints/narrativeHints`）。
- **消费方式**：`intent_hints.py` 扩展为优先读 `intentBrief`，读不到（无 Key / 关闭 / 解析失败）时回落现有正则规则——**零回归**。
- **异步落地方式（开发核查回写）**：直接挂载既有 `travelogue/web/studio_jobs.py` 后台任务（ingest job 的后续 stage），不新建异步机制；`StudioJob.stage`/`stageHint` 复用现有 Task Dock 展示模式。
- **门控与延迟**：受 §4.6 前置检查约束（异步执行、8s 超时、三方 AND 门控）。
- **验收锚点**：AC-ACP-01～03、15、16（见 §10）。

### 5.2 P0-2 · 统一 LLM Ops 观测面

- **形态**：Studio 内部路由 `/ai-ops-admin`（对齐现有 `/templates-admin`、`/lse-flags-admin` 的「治理控制台」形态，internal，不进主链 UI）。
- **数据源**：`ai/telemetry.py` 汇总 `pipeline.runs[]` 中 `agent ∈ {intent_brief, layout_critic, mosaic_judge, narrate, title_art_route_c, aesthetic_mllm}` 的记录。
- **展示**：每个 Agent 的调用次数、成功率、平均耗时、降级次数、（可选）估算 token 成本；按 trip 与按天两个视角。
- **意义**：这是 CTS 的 `G-CTS-05`（读 D-CAL-27 漏斗）与本主题 `unlock_gate.py`（§5.5）共同依赖的底座，目前是分别在各主题里零散建，本功能把它收编成一处。

### 5.3 P1-1 · Layout Critic

- **触发**：G1（结构确认）之前，1 次调用/trip；输入为每章「屏摘要」（`patternId`、张数、横竖比、是否 mosaic），**不传原图**。
- **输出**：`curation.layoutSuggestions[]`（如「第 2 章 5 张全竖图建议改用 gallery 横滑」），仅展示在 G1 UI，用户可采纳（触发对应章节 `apply_layout_to_trip` 重跑）或忽略。
- **约束**：不得输出完整 `screens[]`；建议必须引用已存在的 `patternId` 白名单，不得发明新版式；建议文案遵循 SHD-ACP-02（优先 ≤28 字，硬顶 36）。
- **异步落地方式**：同 §5.1，挂载 `studio_jobs.py` curate 阶段之后的独立 stage。
- **门控与延迟**：受 §4.6 前置检查约束；同受 SHD-ACP-03 确定性回归覆盖（未采纳建议时 `chapters[]` 不变）。
- **验收锚点**：AC-ACP-06～07、15、16。

### 5.4 P1-2 · Mosaic Judge（设计已按开发核查修订 · D-ACP-15）

> **原设计已废弃**：v0.1/v0.2 曾设想「beam 排版循环内实时 tie-break」；核查 `layout_engine/planner/screen_planner_stages.py`（`try_mosaic_window` 在同步热路径内被反复调用）与 `layout_contract/search_budget.py`（`search_timeout_ms=2000`、`max_evaluations_per_trip=500`）后确认：单次网络调用足以打穿整章排版预算，且 beam 搜索本身倾向保留近似分数的候选，触发频率可能远超预期。改为下述二阶段设计。

- **第一阶段（不变）**：beam search 按现有确定性逻辑跑完，产出章节排版结果；**不等待、不调用** LLM。`mosaic/scorer.py` 记录 top1/top2 候选分差 `< tie_epsilon` 的窗口列表（仅记录，不阻塞）。
- **第二阶段（异步复核）**：该章排版结束后，对第一阶段记录的候选窗口（数量应很少，见下方阈值统计要求），异步调用 Mosaic Judge；输入为低分辨率五联候选缩略图。若结果在该章最终渲染前到达，**且**建议候选在原集合内，则采纳；否则维持第一阶段的确定性结果。
- **输出**：`chosenCandidateId` **必须**在已有候选集合内；写 `curation.mosaicJudgeLog`（含 `overriddenFromFirstPass: bool`，供埋点区分「复核生效」与「复核未赶上」）。
- **阈值与调用量**：`tie_epsilon` 默认值须在实施前用现网 mosaic 候选分数分布单独统计一次（SHD-ACP-01），且必须同时统计「触发次数/trip」的分布（不能只看单窗口分差），确认改造后调用量可控（建议先设 `max_calls_per_trip` 独立于全局 `ai_capability.max_calls_per_trip` 的更严格上限，如 3～5 次/trip）。
- **门控与延迟**：门控 AND 语义（D-ACP-14）仍适用；延迟约束改用 D-ACP-15，不套用 §4.6 的同步 8s 模型。
- **验收锚点**：AC-ACP-08、09、16、17（见 §10）。

### 5.5 P1-3 · AIR 解冻门槛量化器

- **动机**：回应 `PRD-AI-RETURN-V1.md` 的 `OQ-AIR-01`（默认开关悬而未决）。
- **做法**：`ai/eval/unlock_gate.py` 读 §5.2 的观测数据，计算「配置转化率 / narrate 成功率 / 渠道复制率」（AIR §7 已定义埋点），按 AIR/CTS 商定阈值输出 `go` / `no-go` / `insufficient-data` 三态建议，写入一份可读报告（不自动改配置）。
- **意义**：把「以后再看数据」变成一个可重复运行的计算器，而不是无限期悬置的开放问题。

### 5.6 P2-1 · G1 反馈闭环最小版

- **交互**：G1 界面「这章不对」→ 弹出极简原因分类（如「图太多/太少」「顺序不对」「风格不搭」）。
- **落地**：写入 `curation.layoutFeedback[]`（trip 级，非全局学习，V1 不做跨 trip 学习模型）；下次同 trip 重跑 Layout Critic / beam 时读取，作为一次性调参输入。
- **明确不做**：不做跨用户/跨 trip 的学习或微调；V1 范围仅「当次可读」。

### 5.7 P2-2 · 统一盲评 + 满意度评测框架

- **做法**：`ai/eval/blind_review.py` 提供统一的抽样导出/打分收集接口，方法论对齐 `pa_acceptance.py`（Spearman SRCC）与 CAL 的 `AC-CAL-BLIND` 流程，覆盖对象扩展到 narrate 文案与 Layout Critic 建议。
- **产出**：每个 Agent 有一份可重复运行的盲评报告模板，而不是各主题各写一次性脚本。

### 5.8 P2-3 · 既有并行 AI 主题收编为消费者

- **做法**：不重开新功能，而是把 AIR / CTS / CAL 中「需要统一观测/预算/评测」的部分，明确指向本平台对应模块（见 §12），减少重复造轮子。

---

## 6. 数据 / API / 隐私

### 6.1 `trip.json` 新增字段（草案，Kickoff 时冻结进 `schemas/trip.schema.json`）

```json
{
  "intent": {
    "intentBrief": {
      "titleHint": "雨后京都",
      "tone": "quiet documentary",
      "peakMoments": ["祇园夜雨"],
      "cullPolicy": { "dropScreenshots": true, "keepEmotionalBlur": true },
      "clusterHints": { "preferFewerChapters": true },
      "layoutHints": { "arc": "five_beat", "peakChapterIndex": 2 },
      "narrativeHints": { "hookTheme": "雨与慢走" },
      "source": "llm",
      "confidence": 0.82
    }
  },
  "curation": {
    "layoutSuggestions": [
      { "chapterId": "ch-02", "suggestion": "5 张竖图建议改 gallery", "accepted": false }
    ],
    "mosaicJudgeLog": [
      { "windowId": "w-03", "chosenCandidateId": "c-1", "tieEpsilon": 0.03 }
    ],
    "layoutFeedback": [
      { "chapterId": "ch-02", "reason": "too_many_photos", "notedAt": "2026-08-10T10:00:00Z" }
    ]
  },
  "pipeline": {
    "runs": [
      { "runId": "run-1", "agent": "intent_brief", "startedAt": "...", "finishedAt": "...", "model": "deepseek-chat" }
    ]
  }
}
```

`pipelineRun.agent` 枚举扩展为：`media_lab | curator | layout | storyteller | storyteller-lite | publisher | intent_brief | layout_critic | mosaic_judge | title_art_route_c | aesthetic_mllm`。

### 6.2 配置（示意）

```yaml
ai_capability:
  enabled: true                 # 独立于 aiSurfaceEnabled；此为工程能力开关
  max_calls_per_trip: 12
  intent_brief:
    enabled: true
    model_hint: small
  layout_critic:
    enabled: false               # W1 先内测
  mosaic_judge:
    enabled: false
    tie_epsilon: 0.03
  cache:
    dir: ".cache/ai"
  eval:
    blind_review_sample_rate: 0.1
```

### 6.3 API（Studio）

| 方法 | 路径 | 用途 |
|------|------|------|
| `GET` | `/__travelogue/ai/ops-summary` | 观测面数据（§5.2） |
| `POST` | `/__travelogue/trips/{id}/ai/intent-brief` | 手动触发/重跑 Intent Brief |
| `POST` | `/__travelogue/trips/{id}/ai/layout-critic` | G1 前手动触发 Layout Critic |
| `GET` | `/__travelogue/ai/unlock-gate` | 读 AIR 解冻门槛计算结果 |

### 6.4 隐私与安全

- 继承 ADR-019 + D-AIR-09：Key 仅本机 `secrets.json`；请求体白名单字段，禁止默认原图像素/base64。
- 新增 CI 静态审计（D-ACP-07）：扫描 `travelogue/ai/agents/*.py` 的请求体构造，断言不含 `file://` / 图片二进制字段，除非该字段显式标记为「已获用户许可的缩略图」。
- 遥测/日志：`ai/telemetry.py` 写入的记录不含 Prompt 原文与 API Key，只含耗时/成功标记/降级原因码。

### 6.5 测试与 Mock 策略（BLK-ACP-03 回写）

| 原则 | 说明 |
|------|------|
| **CI 禁止出网** | 单测中 `travelogue.llm.client.chat_completion` / `vision_chat_completion` 必须被 mock；`pytest` fixture 提供 `FakeLlmClient`，任何测试若真实发出 HTTP 请求即视为用例缺陷 |
| **四类必测 fixture** | `success`（正常 JSON）· `timeout`（触发 D-ACP-13 超时 fallback）· `malformed_json`（解析失败 fallback）· `budget_exceeded`（超 `max_calls_per_trip` fallback） |
| **门控矩阵测试** | 覆盖 §4.6 两道前置检查的全部组合（`ai_capability.enabled` × `aiSurfaceEnabled` × Key 有效性），断言不满足条件时零外呼 |
| **迁移零回归测试** | M2–M4 每步迁移后，既有 narrate / CAL / AA 单测与 golden/dom 回归必须全部保持通过，禁止「先迁移后补测试」 |
| **确定性回归（SHD-ACP-03）** | 新增一条 NR 测试：ACP 关闭时输出与迁移前 golden 逐位一致；ACP 开启但无建议被采纳时，`chapters[]`/`screens[]` 不变 |

---

## 7. 迁移计划（现有三处如何切入，保证零回归）

> **顺序与内容均按开发核查回写调整**：原 M2/M4/M6 的描述与实际代码耦合方式不符，已重写；且建议施工顺序改为 **M1 → M3 → M2 → M4**（先做风险最低、能验证 `ai/` 包骨架的 title_art，再做低成本的 narrate 接入，aesthetic_mllm 拆分单独排期）。

| 阶段 | 内容 | 回归保障 |
|------|------|----------|
| **M1** | 搭建 `travelogue/ai/`（gate/budget/cache/telemetry 基础设施 + 空的 agents 目录）；`ai/budget.py` 内部调用既有 `llm/shared_backoff.py`（D-ACP-18），不重复实现退避 | 无消费者接入，不影响现网 |
| **M3（提前）** | `title_art_adapter.py` 包一层 `route_c.py`+`ocr_verify.py`；`cover_engine` 侧调用切到 adapter——**唯一名副其实的「包一层」迁移**，优先做以验证 `ai/` 骨架 | 回归 `AC-CAL-*`、`docs/acceptance-records/cover-calligraphy-title-v1-*` |
| **M2（改为接入，非迁移）** | `services/llm_narrate.py` **物理位置不变**；新增对 `ai.budget`/`ai.cache`/`ai.telemetry` 的调用（D-ACP-17）；Prompt/Schema/API 响应字段不变 | 回归 `AC-AIR-*`、既有 narrate 单测 |
| **M4（拆分，工作量重估）** | 按 D-ACP-16：把 `build_mllm_shortlist`/`apply_aesthetic_mllm_scores`/`_write_mllm_fields`/oracle 函数**搬迁**至新 `curation/aesthetic_mllm_shortlist.py`；仅 `score_image_with_mllm` 核心下沉至 `ai/agents/aesthetic_mllm_adapter.py`；删除 `pyproject.toml` 对应三行 `ignore_imports`；**预留缓冲**：`cover_engine` 补入 `layers`（D-ACP-01a）后可能曝出未知的新反向依赖（现有 `unmatched_ignore_imports_alerting=none` 掩盖了未分层模块的债务），需一并处理 | 回归 AA 系列（`docs/aesthetic-alignment/` 全部 signoff 脚本） |
| **M5** | 新增 `intent_brief.py`（P0），挂载 `studio_jobs.py` 后台任务 stage；`intent_hints.py` 扩展消费；灰度开关 | 新增单测 + fixture，不改变默认关闭时行为 |
| **M6（Mosaic Judge 设计已改）** | 新增 `layout_critic.py`（挂载 `studio_jobs.py`）；新增 `mosaic_judge.py` **按 D-ACP-15 二阶段设计**（不进 beam 循环，事后异步复核）；**开工前须先完成一次产品/算法对齐会**，确认「决策者降级为复核者」的功能定义变化被认可 | 新增单测；`mosaic/compose.py` 候选集合断言不变；新增 SearchBudget 非侵入断言（AC-ACP-17） |
| **M7** | `eval/unlock_gate.py` + `eval/blind_review.py`（P2） | 独立脚本，不影响主链 |

---

## 8. 里程碑

| 里程碑 | 交付 | 门禁 |
|--------|------|------|
| **W0** | PRD 评审（✅ 七席+1 · 2026-08-10 Conditional Go）；开发负责人技术可行性核查（✅ 2026-08-10，本版已回写）；D-ACP-* 签字；`cover_engine` 补入 `layers`（D-ACP-01a）+ `travelogue.ai` 分层契约先合入（空包） | Review Go |
| **W1** | 按 §7 修订顺序：M1 → **M3**（title_art，优先验证 ai/ 骨架）→ **M2**（narrate 改为接入非迁移）→ **M4**（aesthetic_mllm 拆分，预留 cover_engine 分层曝出新债务的缓冲）+ §6.5 测试/Mock 策略落地，AC-ACP-01～04、13、14（零回归） | 既有 AI 相关验收全绿 + import-linter 债务行清零。**独立结项，允许长期停留（NG-ACP-08）**，不强制连续推进 W2 |
| **W2** | M5（Intent Brief 上线，灰度，挂载 `studio_jobs.py`） + §5.2 观测面 | AC-ACP-05、06、15、16；须 W1 全绿后才开工 |
| **W2.5（新增门禁）** | **Mosaic Judge 产品/算法对齐会**：确认 D-ACP-15 二阶段设计（决策者→事后复核）被接受；确认 SHD-ACP-01 阈值统计方法（含调用频次分布） | 未过此门禁不得开工 M6 中 mosaic_judge 部分；layout_critic 部分不受影响可先行 |
| **W3** | M6（Layout Critic 先行上线，灰度；Mosaic Judge 按二阶段设计上线，含 SHD-ACP-01 阈值统计、SHD-ACP-02 文案长度） | AC-ACP-07～09、17 |
| **W4** | M7（解冻门槛计算器 + 统一盲评框架；与 CTS `G-CTS-05` 核对字段契约 SHD-ACP-05） | AC-ACP-10～12；产出首份 AIR 解冻建议报告 |

---

## 9. 埋点

| 事件 | 属性 | 用途 |
|------|------|------|
| `ai_agent_call` | agent / source(llm\|cache\|fallback) / latencyMs / ok | §5.2 观测面主数据源 |
| `ai_agent_budget_exceeded` | agent / tripId | 预算降级监控 |
| `intent_brief_applied` | fieldsConsumed[] | 衡量四子系统实际读取了哪些 hints |
| `layout_critic_suggestion_shown` / `_accepted` | chapterId | Layout Critic 采纳率 |
| `mosaic_judge_invoked` | tieMargin | 校准 `tie_epsilon` |
| `ai_unlock_gate_result` | verdict(go\|no-go\|insufficient-data) | 支撑 AIR OQ-AIR-01 决策 |

不新增用户可见遥测面；本节全部为工程/产品内部观测，不涉及 NAS 用户面决策。

---

## 10. 验收标准（AC-ACP-*）

| ID | 断言 |
|----|------|
| **AC-ACP-01** | 迁移后 `AC-AIR-*` 全部保持通过（narrate 行为零回归） |
| **AC-ACP-02** | 迁移后 `AC-CAL-*` 全部保持通过（封面艺术字行为零回归） |
| **AC-ACP-03** | 迁移后 AA 系列 signoff 脚本全部保持通过（PA-MLLM 行为零回归） |
| **AC-ACP-04** | `pyproject.toml` 中 `vision.aesthetic_mllm → curation.*` 三行 `ignore_imports` 已删除且 import-linter 通过 |
| **AC-ACP-05** | Intent Brief 关闭时（默认）四子系统行为与迁移前逐位一致（NR 回归） |
| **AC-ACP-06** | Intent Brief 开启且解析失败/超预算时，`intent_hints.py` 正确回落正则规则，不抛异常 |
| **AC-ACP-07** | Layout Critic 输出的 `patternId` 建议全部落在既有白名单内 |
| **AC-ACP-08** | Mosaic Judge 的 `chosenCandidateId` 100% 命中已有候选集合（不会「发明」新窗口）；`mosaicJudgeLog` 正确记录 `overriddenFromFirstPass` |
| **AC-ACP-09** | 任意 Agent 调用异常（超时/HTTP 错误/解析失败）均不向上抛出阻断主链的异常（fail-open 断言） |
| **AC-ACP-10** | `/ai-ops-admin` 能正确展示至少 6 类 Agent 的调用统计（对一次含全部能力开启的 dogfood trip） |
| **AC-ACP-11** | `ai/eval/unlock_gate.py` 在给定 fixture 埋点数据下能输出确定性的 go/no-go/insufficient-data 结果（可单测） |
| **AC-ACP-12** | 请求体审计：`travelogue/ai/agents/*.py` 静态扫描无原图像素/base64默认发送 |
| **AC-ACP-13** | `cover_engine` 已补入 `pyproject.toml` `layers` 契约（D-ACP-01a），import-linter 全绿 |
| **AC-ACP-14** | CI 全流程无出网 LLM/VLM 调用（§6.5 Mock 断言） |
| **AC-ACP-15** | ACP 关闭或任意 Agent 超时/无 Key 时，「导入完成 → 可预览」耗时相对基线（ACP 关闭）不劣化（D-ACP-13） |
| **AC-ACP-16** | `ai_capability.enabled` × `aiSurfaceEnabled` × 有效 Key 三者任一为否时，零外部 LLM/VLM 请求（可用请求打点断言，D-ACP-14） |
| **AC-ACP-17**（开发核查回写） | Mosaic Judge 第一阶段（beam 确定性排版）的实际耗时/评估次数，在 Judge 完全关闭与完全开启两种情况下**逐位一致**——即第二阶段异步复核不改变、不拖慢第一阶段的 `SearchBudget` 消耗（D-ACP-15） |

---

## 11. 风险与开放问题

### 11.1 风险

| 风险 | 缓解 |
|------|------|
| 迁移三处现有能力时引入行为漂移 | title_art 严格「包一层」；narrate 严格「不搬只接入」（D-ACP-17）；aesthetic_mllm 严格按 D-ACP-16 边界拆分；每步独立回归既有验收 |
| 新抽象层增加复杂度，独立开发者维护成本上升 | Agent 签名极简（dict in / dict out + confidence + source）；不做框架化的多 Agent 编排引擎 |
| Layout Critic / Mosaic Judge 建议质量不稳定影响信任 | 严格 advisory-only；默认灰度关闭，先走 §5.7 盲评框架验证再默认开 |
| import-linter 新增 forbidden 契约后暴露更多隐藏反向依赖 | W0 先跑一次干跑（dry-run）盘点；`cover_engine` 补入 `layers` 后（M4 阶段）**预期会曝出新债务**（现有 `unmatched_ignore_imports_alerting=none` 掩盖了未分层模块），已在 §7 M4 预留缓冲，不当作意外 |
| **（新增·开发核查）** Mosaic Judge 塞入 beam 热路径会打穿 `SearchBudget`（2000ms/500 evaluations） | 已改为 D-ACP-15 二阶段设计（beam 先出结果，事后异步复核）；AC-ACP-17 断言两阶段解耦 |
| **（新增·开发核查）** narrate/aesthetic_mllm 的迁移工作量被 v0.1/v0.2 低估（"包一层"实际是"结构性搬迁"） | §7 已按 D-ACP-16/17 重写迁移内容与工作量描述；W1 排期已调整为 M1→M3→M2→M4 |

### 11.2 开放问题（OQ-ACP-*）

| ID | 问题 | 默认倾向 |
|----|------|----------|
| **OQ-ACP-01** | `travelogue/ai/` 与 `travelogue/llm/` 是否应最终合并为一个包？ | V1 **不合并**（迁移成本更低，边界更清晰）；观察 6 个月后再评估 |
| **OQ-ACP-02** | Layout Critic 的「G1 UI 展示位」是否需要新设计稿？ | 默认复用现有 G1 结构列表的次要提示区，不新开弹层 |
| **OQ-ACP-03** | 统一盲评框架是否需要单独的标注工具？ | V1 复用 `pa_acceptance.py` 的导出+人工打分模式，不建新工具 |
| **OQ-ACP-04** | `max_calls_per_trip` 默认值如何定？ | W1 先用当前三处调用点的历史统计估算，W4 用真实数据校准 |

---

## 12. 与既有 AI 主题的关系

| 既有主题 | 本主题动作 | 不变的部分 |
|----------|------------|------------|
| **DLLM / WEA**（`PRD-DESKTOP-LLM-SETUP-V1` / `PRD-WRITING-ENGINE-API-HARDENING-V1`） | 无动作；`travelogue/llm/` Gateway 层保持原样被复用 | provider 隔离、secrets 落盘、ping 合同 |
| **NAS**（`PRD-NO-AI-SURFACE-V1`） | 无动作；`aiSurfaceEnabled` 门控与本主题的 `ai_capability.enabled` 是两个独立开关（用户面 vs 工程能力面） | 默认关闭用户面 |
| **AIR**（`PRD-AI-RETURN-V1`） | 提供 §5.5 解冻门槛计算器 + §5.2 观测面数据，回应 `OQ-AIR-01` | 三语气、渠道包内容、迟晒逻辑等业务决策不变 |
| **CAL**（`PRD-COVER-CALLIGRAPHY-TITLE-V1`） | 路线 C 调用迁移进 `title_art_adapter.py`，接入统一预算/观测 | 白名单风格、OCR 校验规则、D-CAL-27 埋点定义不变 |
| **CTS**（`PRD-COVER-TYPESETTING-CONTINUITY-V1`） | `G-CTS-05` 所需的埋点解读直接复用 §5.2 观测面，不用另起一套 | 排版契约、字数档、身份线打磨不变 |
| **AA / PA-MLLM**（`docs/aesthetic-alignment/`） | 迁移进 `aesthetic_mllm_adapter.py`，顺带清偿 import-linter 债务 | Rubric、分层精选、校准公式不变 |
| **CAD / HIT**（`PRD-COVER-ART-DIRECTION-V1` / `PRD-HERO-INTEREST-TASTE-V1`） | 无强制动作；若未来引入 LLM 能力，建议直接作为本平台的新 Agent 接入 | 各自产品范围不变 |

---

## 13. 变更记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.3.0 | 2026-08-10 | 开发负责人技术可行性核查回写（对照现网代码，无代码改动）：新增 D-ACP-15（Mosaic Judge 二阶段设计，取代 beam 内实时 tie-break，因 `SearchBudget=2000ms` 与 8s LLM 超时不兼容）、D-ACP-16（aesthetic_mllm 拆分边界，明确哪些函数下沉 `ai/`、哪些搬去 `curation/aesthetic_mllm_shortlist.py`）、D-ACP-17（narrate 不物理迁移，物理位置不变仅接入 budget/cache/telemetry）、D-ACP-18（`ai/budget.py` 与 `llm/shared_backoff.py` 分工：次数上限 vs 限流退避）；D-ACP-13 适用范围收窄为 Intent Brief/Layout Critic；§4.2/§4.3/§4.4 模块清单与消费关系表按上述决策更正；§5.4 Mosaic Judge 功能规格重写为二阶段设计；§7 迁移计划 M2/M4/M6 内容重写，施工顺序改为 M1→M3→M2→M4；§8 新增 W2.5 Mosaic Judge 产品/算法对齐门禁；新增 AC-ACP-17（SearchBudget 非侵入断言）；§11 新增两条风险 |
| v0.2.0 | 2026-08-10 | 七席+1 评审（[review](./acceptance-records/acp-ai-capability-platform-v1-review-2026-08-10.md)）Must-Fix 回写：新增 D-ACP-01a（`cover_engine` 分层补齐）、D-ACP-13（延迟预算/异步不阻塞）、D-ACP-14（三方 AND 门控语义）、NG-ACP-08（W1 可独立结项长期停留）；新增 §4.6 调用前置检查、§6.5 测试与 Mock 策略；§4.5 事实更正（`cover_engine` 现状不在 `layers` 契约内）；新增 AC-ACP-13～16；§8 里程碑标注独立结项与开工前置 |
| v0.1.0 | 2026-08-10 | 初稿：承接架构评审的「LLM 能力独立系统」诉求，收编 narrate / title_art route C / PA-MLLM 三处调用点为 `travelogue/ai/` 平台；落地 P0（Intent Brief + 统一观测）、P1（Layout Critic + Mosaic Judge + 解冻门槛）、P2（反馈闭环 + 统一盲评）路线图 |
