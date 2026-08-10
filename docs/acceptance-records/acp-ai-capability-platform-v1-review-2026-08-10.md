# PRD-AI-CAPABILITY-PLATFORM-V1 · 七席+1 评审纪要

| 属性 | 内容 |
|------|------|
| **文档** | [PRD-AI-CAPABILITY-PLATFORM-V1.md](../PRD-AI-CAPABILITY-PLATFORM-V1.md)（**ACP** · AI 能力平台 · 编辑智能收编） |
| **关联** | [AGENT-ARCHITECTURE.md §17](../AGENT-ARCHITECTURE.md) · [PRD-AI-RETURN-V1.md](../PRD-AI-RETURN-V1.md)（AIR）· [PRD-COVER-CALLIGRAPHY-TITLE-V1.md](../PRD-COVER-CALLIGRAPHY-TITLE-V1.md)（CAL）· [PRD-COVER-TYPESETTING-CONTINUITY-V1.md](../PRD-COVER-TYPESETTING-CONTINUITY-V1.md)（CTS）· `docs/aesthetic-alignment/`（AA/PA-MLLM）· `pyproject.toml` `[tool.importlinter]` |
| **评审版本** | PRD **v0.1.0** → Must-Fix 回写后升 **v0.2.0** ✅ |
| **日期** | 2026-08-10 |
| **结论** | **有条件通过（Conditional Go · 可冻结策划；W1「基础设施 + 零回归迁移」可 Kickoff；新增 Agent 能力仍受本纪要 BLK 门禁）** |
| **编码** | ☑ **策划冻结（v0.2.0 · BLK 已关）**　□ W1 M1–M4 迁移　□ W2 M5 Intent Brief　□ W3 M6 Layout Critic/Mosaic Judge　□ W4 M7 解冻门槛/盲评 |
| **参评角色（七席 + 1）** | 产品 · 算法 · 架构 · 开发 · 测试/QA · 视觉/排版 · 用户体验（狗粮手测） · **典型用户（真实旅行者视角，新增席）** |
| **评审方式** | 分席只读 PRD §0～§13 · D/G/AC/OQ 表 + **对照现网**（`travelogue/llm/`、`travelogue/services/llm_narrate.py`、`travelogue/cover_engine/title_art/route_c.py`、`travelogue/vision/aesthetic_mllm.py`、`pyproject.toml` import-linter 契约、`schemas/trip.schema.json`） |
| **记录人** | 七席+1 联合纪要（跨职能模拟联评 · 基于 2026-08-10 PRD v0.1.0 + 代码事实核查） |
| **本纪要状态** | **已结案 · Conditional Go** · **PRD v0.2.0 已回写 BLK-ACP-01～05** |
| **审查基线** | 执行引擎不变（LLM 只做意图/调参/消歧/解释）· Fail-open 铁律 · 架构方向单向 · 不做群聊多 Agent · 本地优先白名单上云 |

---

## 0. 会前宣读（主持人）

1. **切口**：ACP = 把已存在（narrate / route C / PA-MLLM）与规划中（Intent Brief / Layout Critic / Mosaic Judge / 解冻门槛 / 反馈闭环 / 盲评框架）的 LLM/VLM 能力**收编为一个独立系统**，不是重新设计任何一处的业务逻辑。
2. **勿重开**：narrate 语气/Prompt（归 AIR）、艺术字白名单/风格（归 CAL/CTS）、审美 Rubric（归 AA）——本场只审「基础设施是否该建、边界是否清楚、迁移是否会回归、新增 Agent 是否会失控」。
3. **本场必拍**：§4.5 的 import-linter 新契约是否真的能生效（`cover_engine` 现状是否已在分层契约内）；里程碑范围对**独立开发者**带宽是否现实；有没有测试/Mock 策略；新增的 LLM 调用会不会拖慢章程 O2「20 分钟内愿导出」；普通用户会不会在不知情下多担隐私/成本风险；新增能力是否会破坏章程 O4「同数据重渲染版式一致」。
4. **列车**：关 BLK → v0.2 冻结策划；W1（M1–M4 基础设施 + 零回归迁移）可独立 Kickoff 且**允许长期停留**，不强制同周期推进 P0 新增能力。

---

## 1. 总评（一句话）

> **八席一致 Conditional Go：把三处分散 LLM 调用收编为一个平台、且严格要求「先迁移零回归再新增能力」的顺序是对的；但 v0.1 有五处会在 Kickoff 后翻车——（1）§4.5 提出的新 import-linter 契约建立在一个不成立的前提上：`cover_engine` 当前根本不在分层契约的 `layers` 列表里，新增的 forbidden 契约看似约束了它、实际那条依赖方向从未被验证过，容易造成「看起来治理了、其实没治理」的假象；（2）里程碑把 M1–M7 + 两个新 admin 路由 + 一整套 eval 框架排在一起，对单人开发节奏不现实，需要明确「迁移可独立长期停留，不必连着做新增能力」；（3）全篇没有一句测试/Mock 策略，LLM 调用怎么进 CI 是空白；（4）新增 Agent 调用的延迟预算与章程 O2「20 分钟内出片」的关系没写进冻结决策，容易在 W2/W3 悄悄拖慢首屏；（5）「典型用户」一读就问：`ai_capability.enabled=true` 是不是意味着没配 Key 时这些新功能也在偷偷跑数据？—— 文档没有把这个 AND 语义钉死。关 BLK-ACP-01～05 后升 v0.2；W1 基础设施迁移可独立 Kickoff，新增 Agent（M5 起）仍需按里程碑逐项过闸。**

---

## 2. 分席表决

| 席位 | 表决 | 一句话 |
|------|------|--------|
| **产品** | **Conditional Go** | 「先收编再扩能力」的顺序对，不是又开一条新故事线。但 §2.1 的 9 条目标一次性排给一个独立开发者，容易变成「说了但做不完」的第六个悬置主题（像 AIR/CTS 现在的状态）。要求：把 M1–M4（零回归迁移）钉成一个**可独立结项、且允许长期就停在这里**的里程碑，新增能力（Intent Brief 起）默认按需再拍板，不绑死同一节奏。 |
| **算法** | **Conditional Go** | Agent 统一签名（dict in / dict out + confidence + source）方向对，避免又出现「四套 JSON 解析各写一遍」。但 Mosaic Judge 的 `tie_epsilon` 默认值「参考 CAL/PA 同类阈值」是空话——CAL/PA 用的是不同量纲的分数（艺术字风险分 vs mosaic scorer 分），不能直接抄一个数字；需要单独用现有 mosaic 候选分布跑一次统计再定初始值，而不是写「参考」了事。 |
| **架构** | **Conditional Go** | 分层方向（`ai` 与 `media:vision:llm` 同层、单向依赖）判断正确，且抓住了真实债务（`vision.aesthetic_mllm → curation.*` 三行 `ignore_imports`）当抓手，这个思路值得肯定。**但**核查 `pyproject.toml` 现网发现 `cover_engine` **从未出现在** `layers` 列表里——§4.5 给的 forbidden 契约把它列为 `source_modules`/`forbidden_modules` 的对照对象，这个契约本身能跑（import-linter 允许约束未分层的模块），**但**它解决不了「cover_engine 到底该在分层图哪一层」这个更根本的问题，容易造成前后不一致的治理假象。必须先把这条现状写清楚，且给出「是否顺手把 cover_engine 补进 layers」的书面决定，而不是留白。 |
| **开发** | **Conditional Go** | M1–M7 + `ai/agents/*`（6 个）+ `ai/budget.py`/`cache.py`/`telemetry.py`/`eval/*`（4 个）+ 2 个新 Studio 路由 + 1 处 schema enum 扩展，一次性列在同一份 PRD 里，工作量比 CTS/CAL 单个主题明显更大。且没有任何一句话讲 CI 里 LLM 调用怎么跑（真调外部 API？会拖垮 CI 稳定性和额度）。要求：补一节「测试与 Mock 策略」，且把 M5 起的新增 Agent 拆成可独立排期的小切片，不要求一次评审全部拍板时间线。 |
| **测试 / QA** | **Conditional Go** | AC-ACP-01～04（零回归）方向对、可测。但 AC-ACP-05～09（新增 Agent 行为）缺少「输入 fixture 从哪来、LLM 响应怎么 mock」的具体约定，照现在的写法测试同学没法直接开工写用例。另外：ACP 开启后是否会破坏章程 O4「同数据重渲染版式一致」完全没有断言——advisory-only 说了但没有对应 AC，等于没锁。 |
| **视觉 / 排版** | **Conditional Go** | Layout Critic 的建议展示位「复用 G1 结构列表次要提示区」方向可以接受，但没有任何文案长度/频率约束——参考 CTS 已经踩过的坑（SHD-CTS-01：提示文案优先 ≤28 字硬顶 36），本主题的 Layout Critic 建议同样需要长度上限，否则 G1 页面会被一堆 LLM 建议文字挤满。 |
| **用户体验（狗粮手测）** | **Conditional Go** | 「新增能力默认灰度关闭」是对的，能避免用户被一堆新提示打断。但本主题会新增第三个 internal admin 面板（`/ai-ops-admin`，之前已有 `/templates-admin`、`/lse-flags-admin`），治理台越开越多本身是一种复杂度债务，建议至少在文档里留一句「未来考虑合并治理入口」的记录，别再假装这是零成本的。 |
| **典型用户（真实旅行者视角，新增席）** | **Conditional Go** | 完全看不懂"平台""Agent""预算"这些词，但我关心四件事：**①会不会变慢**——我选完照片是想 20 分钟内看到成品，不是等 AI 慢慢"理解我的意图"；**②会不会多花钱**——我自己配的 Key 是按调用次数/token 收费的，"预算"这个词听起来就是要多扣我的钱；**③我的备注和照片会不会被偷偷传上网**——我没点"生成杂志感"按钮，你们是不是也在后台悄悄调用 LLM 分析我写的东西；**④结果会不会每次都不一样**——同一批照片，我今天导出和明天导出应该长一样，不能因为多了个"AI 建议"就飘。这四条如果没有明确的书面承诺，我不会安心用。 |

**汇总**：**8/8 Conditional Go**。

**对齐评分**

| 维度 | 分（/10） | 说明 |
|------|-----------|------|
| 问题→方案因果完整度 | **8** | 三孤岛现状 + 已登记债务作抓手，叙事扎实 |
| 与既有 AI 主题边界 | **9** | §12 关系表清楚；不重开业务决策 |
| 工程可开工性（W1） | **6** | M1–M4 可开工；但范围/测试策略/带宽三处缺口拉分 |
| AC 可测性 / 防假绿 | **6** | 迁移零回归可测；新增 Agent 与「稳定性不回归」缺 AC |
| 对独立开发者的现实性 | **6** | 目标清单过长；需要明确「迁移先行、能力慢做」 |
| 用户可感知的信任与成本 | **6** | Fail-open/白名单方向对；AND 语义与延迟预算未钉死 |

---

## 3. 事实核查（对照现网）

| # | 断言 | 会中核查 |
|---|------|---------|
| **F-01** | `vision.aesthetic_mllm → curation.*` 是已登记债务（三行 `ignore_imports`，标注 pending P2） | ✅ `pyproject.toml` L121-126 属实 |
| **F-02** | `pipelineRun.agent` 枚举当前不含任何 LLM/VLM 相关值 | ✅ `schemas/trip.schema.json` 现枚举为 `media_lab/curator/layout/storyteller/storyteller-lite/publisher`，属实 |
| **F-03** | `cover_engine` 已被 `pyproject.toml` `layers` 契约管辖 | ❌ **不属实**：现网 `layers` 列表仅含 `cli/web/desktop`、`orchestrator`、`render:export`、`services:templating`、`curation:layout_engine:layout_templates`、`media:vision:llm`、`config`、`util:...`；**`cover_engine` 未出现** |
| **F-04** | `narrate.py`（stub）与 `llm_narrate.py`（LLM 填槽）现状分离，前者是主链默认 | ✅ 属实，`services/narrate.py` 为默认 stub 路径 |
| **F-05** | `aiSurfaceEnabled` 默认 False（NAS 门控），与本主题 `ai_capability.enabled` 是两个不同配置键 | ✅ 属实（`travelogue/web/ai_surface.py`）；**但** PRD v0.1 未钉死二者与「是否已配 Key」的三方 AND 关系 |
| **F-06** | `ai/agents/*` 新增模块数量（6 个 Agent + budget/cache/telemetry + eval 下 2 个） | ✅ 按 §4.3 统计属实，共 10 个新文件 + 2 处已有文件适配 |
| **F-07** | PRD 中含 CI/测试 Mock 策略章节 | ❌ **不属实**：v0.1 全篇无一处提及 LLM 调用的测试隔离方式 |
| **F-08** | PRD 中含新增 Agent 调用与章程 O2「20 分钟出片」延迟预算的关系 | ❌ **不属实**：§5 各 Agent 只写「1 次/trip」，未写超时/异步不阻塞的冻结决策 |
| **F-09** | PRD 中含 ACP 开/关对渲染结果确定性（章程 O4）影响的验收 | ⚠️ **部分属实**：D-ACP-08/09 写了 advisory-only 原则，但 §10 无对应 AC |

---

## 4. 全场共识

1. **收编方向正确**：三处分散 LLM/VLM 调用统一到一个平台是对的工程决定，且抓到了仓库里已登记的真实债务（F-01）。
2. **顺序正确**：先迁移零回归（M1–M4），再谈新增能力（M5 起）——必须在里程碑里写死这个先后依赖，不能并行拍时间线。
3. **架构方向单向依赖判断正确**，但 `cover_engine` 现状缺口（F-03）必须写清楚，不能让新契约建在一个隐藏的空白上。
4. **必须补测试/Mock 策略**，否则 W1 无法真正开工写 CI。
5. **必须把「不拖慢首屏」「不破坏渲染确定性」写成冻结决策 + AC**，这两条直接对应章程 O2/O4，不是锦上添花。
6. **必须钉死 `ai_capability.enabled` × `aiSurfaceEnabled` × 「是否有效 Key」三者的 AND 语义**，并复用现有隐私文案，不新造第二套说法。
7. **范围过大是本轮最大风险**：建议 v0.2 明确「W1 迁移可独立结项、长期停留亦可接受」，避免 ACP 变成第 6 个悬置主题。

---

## 5. Must-Fix（阻塞 · 升 v0.2 前关闭）

| ID | 议题 | 要求（冻结一字面） | 挡 | 状态 |
|----|------|-------------------|----|------|
| **BLK-ACP-01** | `cover_engine` 分层现状缺口 | §4.5 补充事实：`cover_engine` 当前**不在** `pyproject.toml` `layers` 列表内；新增 forbidden 契约独立生效、不依赖其在 layers 中的位置；同时新增 **D-ACP-01a**：本主题实施时**一并**将 `cover_engine` 补入 `layers`（置于 `render:export` 与 `media:vision:llm:ai` 之间），消除「治理假象」。新增 **AC-ACP-13**：`cover_engine` 补入 layers 后 import-linter 全绿。 | W1→v0.2 | ✅ **已回写 v0.2.0** |
| **BLK-ACP-02** | 里程碑/带宽错配 | 新增 **NG-ACP-08**：不强制同一迭代周期内完成 P0–P2 全部内容；**M1–M4（基础设施 + 零回归迁移）可独立结项并长期停留**，新增能力（M5 起）按需再评审时间线，不在本 PRD 一次性拍死。§8 里程碑表新增该备注行。 | W1→v0.2 | ✅ **已回写 v0.2.0** |
| **BLK-ACP-03** | 测试/Mock 策略缺失 | 新增 **§6.5 测试与 Mock 策略**：CI 单测必须 mock `travelogue.llm.client.chat_completion`/`vision_chat_completion`，禁止真实网络调用；fixture 至少覆盖 `success`/`timeout`/`malformed_json`/`budget_exceeded` 四类。新增 **AC-ACP-14**：CI 全程无出网 LLM 调用。 | W1→v0.2 | ✅ **已回写 v0.2.0** |
| **BLK-ACP-04** | 延迟预算 vs 章程 O2 | 新增 **D-ACP-13**：所有 §5 新增 Agent 调用必须**异步执行、不阻塞首屏预览**（继承 `AGENT-ARCHITECTURE.md` §17.6），单次调用超时保护（默认 8s），超时直接 `fallback`。新增 **AC-ACP-15**：ACP 关闭或任意 Agent 超时/无 Key 时，「导入完成 → 可预览」耗时相对基线（ACP 关闭）不劣化。 | W1→v0.2 | ✅ **已回写 v0.2.0** |
| **BLK-ACP-05** | 门控 AND 语义未钉死（典型用户提出） | 新增 **D-ACP-14**：`ai_capability.enabled` × `aiSurfaceEnabled` × 「provider 非 stub 且有效 Key」三者为 **AND** 语义；任一为否，所有 `ai/agents/*` 直接走 `fallback`，不发出请求。隐私确认文案复用既有 D-AIR-09/`COPY-AIR-PRIVACY`，不新造第二套说法。新增 **AC-ACP-16**：三者任一为否时零外呼（可用请求打点断言）。 | W1→v0.2 | ✅ **已回写 v0.2.0** |

**Should-Fix（不阻塞 v0.2 冻结，挡未来里程碑）**

| ID | 建议 | 状态 |
|----|------|------|
| **SHD-ACP-01** | Mosaic Judge `tie_epsilon` 默认值不得写「参考同类阈值」，需在 M6 前用现网 mosaic 候选分数分布单独统计一次初始值 | ✅ W2.5 纪要 + `tie_epsilon_stats` / 默认 0.03 |
| **SHD-ACP-02** | Layout Critic 建议文案长度上限：复用 CTS `SHD-CTS-01` 结论（优先 ≤28 字，硬顶 36） | ✅ W3 Critic 文案截断 |
| **SHD-ACP-03** | 渲染确定性回归：新增 AC 断言「ACP 开启但用户未采纳任何建议时，`chapters[]`/`screens[]` 输出与关闭时逐位一致」（对应章程 O4） | ✅ `test_shd_acp_03_*` |
| **SHD-ACP-04** | 第三个 internal admin 面板（`/ai-ops-admin`）治理债务：留 OQ，未来与 `/templates-admin`、`/lse-flags-admin` 合并评估 | 待未来 |
| **SHD-ACP-05** | `unlock_gate.py` 与 CTS `G-CTS-05` 的字段命名需要双方书面确认接口契约，避免各自另造一套观测字段 | 待 W4 |

---

## 6. 典型用户提问 Q&A（新增席位专属记录）

> 用「一个刚拍完旅行照片、只想快点出图发朋友圈的普通用户」的语言逐条追问，供产品/文案侧后续转译参考；本节不是正式验收项，但 BLK-ACP-04/05 直接回应了①②③④。

| 提问 | 会中回应（对应决策） |
|------|----------------------|
| ① 会不会变慢？我就想 20 分钟内出图 | 回应：新增 Agent 必须异步、不阻塞首屏，超时直接跳过（D-ACP-13 / AC-ACP-15） |
| ② 会不会多花我配的 Key 的钱？ | 回应：trip 级预算上限 `max_calls_per_trip`（已有 D-ACP-04）；新增说明：默认全部新增 Agent 出厂灰度关闭，用户不主动开启不产生任何调用 |
| ③ 我没点"生成杂志感"，你们是不是也在偷偷调 LLM？ | 回应：D-ACP-14 钉死三方 AND 语义——没配 Key / 没开写作引擎 / provider 是 stub，任何一条不满足，新增 Agent 直接 fallback，零外呼（AC-ACP-16 可断言） |
| ④ 同样的照片，今天和明天导出会不会长得不一样？ | 回应：所有 Agent 输出均为 advisory 字段，不自动改 `chapters[]`/`screens[]`；SHD-ACP-03 补一条确定性回归 AC，跟踪落实 |

---

## 7. 对 OQ 的会中倾向（不替代产品终裁）

| OQ | 会中倾向 | 是否升 BLK |
|----|----------|------------|
| **OQ-ACP-01**（`ai` 与 `llm` 是否合并） | 维持不合并；6 个月后用实际维护成本复议 | 否 |
| **OQ-ACP-02**（Layout Critic UI 展示位） | 复用 G1 次要提示区，但需配 SHD-ACP-02 长度约束 | 否（已转 Should-Fix） |
| **OQ-ACP-03**（盲评工具） | V1 复用 `pa_acceptance.py` 模式，不建新工具 | 否 |
| **OQ-ACP-04**（`max_calls_per_trip` 默认值） | W1 先用现有三处调用点历史统计估算，不新增讨论 | 否 |
| **（新增）第三方 admin 面板治理** | 记录为 SHD-ACP-04，不在本轮升级为 BLK | 否 |

---

## 8. 里程碑裁定

| 里程碑 | 本场裁定 |
|--------|----------|
| **策划冻结（v0.2）** | **批准**：关 BLK-ACP-01～05 后 |
| **W1 M1–M4（基础设施 + 零回归迁移）** | **批准 Kickoff，且允许独立长期停留**，不强制连续推进新增能力 |
| **W2 M5（Intent Brief）** | **不批开工**直至 W1 全绿（AC-ACP-01～04、13、14） |
| **W3 M6（Layout Critic / Mosaic Judge）** | **不批开工**直至 W2 完成且 SHD-ACP-01/02 已处理 |
| **W4 M7（解冻门槛 / 盲评框架）** | 维持原计划，可与 CTS `G-CTS-05` 并行核对字段契约（SHD-ACP-05） |

---

## 9. 签核

| 席位 | 签字（模拟） | 日期 |
|------|--------------|------|
| 产品 | Conditional Go · 迁移先行、能力慢做 · 不绑死同周期 | 2026-08-10 |
| 算法 | Conditional Go · tie_epsilon 需单独统计，不可抄阈值 | 2026-08-10 |
| 架构 | Conditional Go · cover_engine 分层缺口须写清并补齐 | 2026-08-10 |
| 开发 | Conditional Go · 补测试/Mock 策略 · 新增能力拆小切片 | 2026-08-10 |
| 测试 / QA | Conditional Go · fixture 四类 + 确定性回归 AC | 2026-08-10 |
| 视觉 / 排版 | Conditional Go · Layout Critic 文案长度上限 | 2026-08-10 |
| 用户体验 | Conditional Go · 第三个治理台留债务记录 | 2026-08-10 |
| **典型用户** | Conditional Go · 四条书面承诺（速度/成本/隐私/稳定）落实才安心 | 2026-08-10 |

---

## 10. 下一步（主持人交办）

1. ✅ **BLK-ACP-01～05 已回写** PRD **v0.2.0**（D-ACP-01a/13/14、NG-ACP-08、AC-ACP-13～16、§4.5 事实更正、§6.5 测试策略新增）。
2. **并行**：M1（`travelogue/ai/` 空包 + budget/cache/telemetry 基础设施）可立即开工。
3. **下一步**：拆 `ACCEPTANCE-AI-CAPABILITY-PLATFORM-V1.md` / 实施清单；W1 范围严格限定 M1–M4，不夹带 M5 起的新增能力。
