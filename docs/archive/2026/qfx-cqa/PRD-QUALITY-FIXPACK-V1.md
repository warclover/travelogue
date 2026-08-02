# Travelogue · 日更质量修复包 V1 产品需求文档（PRD）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue Studio |
| **文档版本** | **v0.2.1** |
| **状态** | **Closed**（PR-A/B/C 已合；C2/D 结案就绪 · 2026-07-23） |
| **DOC-STATUS** | **Closed** |
| **主题代号** | 「日更质量修复包 V1（Quality Fixpack）」— **QFX** |
| **调研来源** | 2026-07-22 当日合入质量审查 + 七席根因评审 + **2026-07-23 开发负责人代码探查** |
| **审查基线** | `master` @ `ed4f032`（探查日复核：recipe/god-module 仍红；CSC lint 已在 PR） |
| **关联文档** | [CSC](../../../PRD-COMPLETION-SURFACE-CONVERGENCE-V1.md) · [NAS](../../../PRD-NO-AI-SURFACE-V1.md) · [Keep-All](../../../PRD-KEEP-ALL-PHOTOS-V1.md) · [UI Detail](../../../UI-DETAIL-CONTRACT-V0.md) · [SFI](../../../PRD-SHARE-FACE-INTEGRITY-V1.md) · [PMX](../../../PRD-POST-MERGE-UX-FIXPACK-V1.md) · [QUALITY-GATE](../../../QUALITY-GATE.md) |
| **评审纪要** | [acceptance-records/quality-fixpack-v1-review-2026-07-22.md](../../../acceptance-records/quality-fixpack-v1-review-2026-07-22.md) |
| **验收** | [ACCEPTANCE-QUALITY-FIXPACK-V1.md](./ACCEPTANCE-QUALITY-FIXPACK-V1.md) **Closed** |
| **实施清单** | [IMPLEMENTATION-QUALITY-FIXPACK-V1.md](./IMPLEMENTATION-QUALITY-FIXPACK-V1.md) |
| **更新日期** | 2026-07-23 |

> **v0.2.1 相对 v0.2.0（代码探查拍板 · 2026-07-23）**
>
> 产品确认采纳开发负责人三项建议，并写入硬合同：
>
> 1. **D-QFX-04b Config 投影**：NAS off 时 `GET /config` **仅** `aiSurfaceEnabled` + 非 LLM 字段；`llmAvailable` / `llmProvider` / `tripsDir` 仅 dark ON。  
> 2. **D-QFX-06 / R1.5 长图切片**：M1′ = 整卷 `(mtime,name)` **+** 最小 `current.json`；完整分段批次规则放 M2′；**禁止**用逐文件 mtime 假修分段。  
> 3. **D-QFX-02 God-module**：优先抽 **策展预处理模块**（回填/清标/硬丢）降耦；**禁止**把「搬 keep-all 几行」当降行银弹；`studio_pipeline` 超限另归因。  
>
> 另据探查修正：S-01 CI 叙事（CSC 已在 PR；缺口是审计/e2e）；D-07 `skipLowResExclusion` 硬优先级；D-13 数据已对齐、缺门禁；D-14b 扩现有 facade lint、不上新 import-linter；FE 升档须含 `import-run.js`。

> **v0.2 相对 v0.1（评审回写摘要）**
>
> - 从「14 条症状补丁」升格为 **4 条系统解法（S-QFX-01～04）+ 合同真测（S-05～08）**。  
> - **D-QFX-06**：长图权威改为 **导出 manifest**（mtime 仅旧盘 fallback）。  
> - **D-QFX-02/14**：LOC/substring 伪护栏降级；真实边界合同升挡。  
> - **D-QFX-03/04**：FE 去 setter = 契约硬化；**安全边界在 BE**；status **早拒**并回写 NAS。  
> - **D-QFX-07/08**：keep-all 单源意图 + 策展预处理幂等。  
> - 里程碑改为 **M1′ / M2′ / M3′**；Fix all = 结案范围，**禁止单 PR**。  
> - 增补 **AC-QFX-16～26**；结案必须回写邻接 PRD（QFX 非长期 SSOT）。

> **定位**
>
> 本 PRD 是质量修复包，不引入新功能面。目标不是让代理指标变绿，而是：
>
> 1. **合入系统先绿**：预合入 required；主干红禁叠主题。  
> 2. **状态单一真相源**：NAS / keep-all 不再 FE·BE 双推。  
> 3. **导出有事务点**：预览读成功 manifest，不扫目录猜。  
> 4. **审计 fail-closed**：测真组件、非空 schema；假绿路径为零。

> **一句话目标**：**预合入门禁挡住假绿；NAS off 读不到敏感 AI 状态；keep-all 只认显式意图且尺寸齐全；预览永远指向最近一次成功导出批次。**

> **完成定义**
>
> | 门 | 含义 | 不等于 |
> |----|------|--------|
> | **M1′ Go** | recipe 绿 + status 早拒 + config 投影收口 + setter 只读 + 草稿/遥测不升 keep_all + 整卷 mtime + 最小 `current.json` | 完整分段批次校验；全量 e2e 上 PR |
> | **M2′ Go** | 策展预处理模块 + 幂等清标 + 分段批次合同 + hydration 三态 + 真双态审计 + strict=all + 邻接回写 | AI-Return |
> | **M3′ Go** | L1== 门禁 · 复制三态 · facade 扩扫 · 聚合 gate · QFX Closed | curate 全量大拆 |

---

## 0. 读者指南与边界

### 0.1 与相邻主题

| 主题 | 关系 | 本主题做什么 |
|------|------|--------------|
| [CSC](../../../PRD-COMPLETION-SURFACE-CONVERGENCE-V1.md) | 硬化执行 + 合入列车 | 同步 recipe；真实护栏；**不**重开 Recipe IA |
| [NAS](../../../PRD-NO-AI-SURFACE-V1.md) | **回写原合同** | status 读门控；**config 敏感投影收口（D-QFX-04b）**；FE 只读 snapshot；结案后条款归 NAS |
| [Keep-All](../../../PRD-KEEP-ALL-PHOTOS-V1.md) | **回写原合同** | §4.2 回填澄清；§4.4 推断单源；结案后条款归 Keep-All |
| [UI Detail](../../../UI-DETAIL-CONTRACT-V0.md) | 审计真值 | fail-closed；真组件；strict=all |
| [SFI](../../../PRD-SHARE-FACE-INTEGRITY-V1.md) / [PMX](../../../PRD-POST-MERGE-UX-FIXPACK-V1.md) | 导出权威 | manifest/`current`；不重开人话命名 |
| [QUALITY-GATE](../../../QUALITY-GATE.md) | 脚本入口 | 聚合 `quality_fixpack_gate`（或等价）进 PR required |

### 0.2 系统根因（评审锁定 · 非表象）

| ID | 根因 | 表象条目 |
|----|------|----------|
| **R1** | 状态多源推导（NAS / keep-all / L1） | Q3,Q4,Q7,Q9,Q13,Q14 |
| **R2** | 代理指标验收合同（LOC / 假 DOM / substring / 空测量） | Q2,Q5,Q10,Q11 |
| **R3** | 合入闭环断裂（**探查修正**：CSC lint 已在 PR；假绿类审计 / targeted e2e / `--strict` 仍偏 post-push） | Q5,Q10,Q11 + master recipe/god 红 |
| **R4** | 导出无成功事务点 | Q6 |
| **R5** | 兼容逻辑散落边缘 | Q7,Q8,Q9 |

### 0.3 审查问题 → 落点

| 审查 ID | 问题 | 严重度 | 落点 |
|---------|------|--------|------|
| **Q1** | CSC recipe 基线漂移 | **P1** | §4 R1.1 · D-QFX-01 · S-01 |
| **Q2** | god-module 超限 | **P1** | §4 R1.2 · D-QFX-02 · S-07 |
| **Q3** | 公开 setter 可翻转 AI 面 | **P1** | §4 R2.1 · D-QFX-03 · S-02 |
| **Q4** | `/llm/status` 未门控 | **P1** | §4 R2.2 · D-QFX-04 · S-02 |
| **Q5** | 能力卡伪造 DOM / 跳断言 | **P1** | §4 R2.3 · D-QFX-05 · S-06 |
| **Q6** | 长图预览可能陈旧 | **P1** | §4 R3.1 · D-QFX-06 · S-04 |
| **Q7** | 旧草稿升 keep_all | **P2** | §4 R3.2 · D-QFX-07 · S-03 |
| **Q8** | keep_all 跳过尺寸回填 | **P2** | §4 R3.3 · D-QFX-08 · S-05 |
| **Q9** | hydration / telemetry 错 | **P2** | §4 R2.4 · D-QFX-09 · S-09 |
| **Q10** | 空测量假绿 | **P2** | §4 R2.5 · D-QFX-10 · S-06 |
| **Q11** | `--strict` 局部 / token substring | **P2** | §4 R2.6 · D-QFX-11 · S-06 |
| **Q12** | 复制假成功 | **P3** | §4 R3.4 · D-QFX-12 · S-10 |
| **Q13** | L1 双源无 == 契约 | **P3** | §4 R3.5 · D-QFX-13 · S-11 |
| **Q14** | telemetry schema / facade 漏扫 | **P3** | §4 R2.7 / R1.3 · D-QFX-14 |

### 0.4 已拍板决策（v0.2.1 · 含 2026-07-23 探查拍板）

| 决策 | 锁定结论 |
|------|----------|
| **D-QFX-01 Recipe 基线** | 同步 NAS `ai_surface_enabled` 后的权威计数（当前 151/54）；基线变更须**语义 diff** 与代码同 PR；**主干红禁止合入后续主题**（独立合入决策，见 S-01）。 |
| **D-QFX-02 God-module** | **拍板（2026-07-23）**：优先抽 **策展预处理模块**（回填 / 清本策略低清标 / 条件硬丢），使 `curate` 调用变薄并锁定 §4 R3.3 顺序——这是 Q8 正解，也是降耦主路径。探查事实：`curate` 内 keep-all 门控约数行；超限主因含 `studio_pipeline`（+27 量级）等，**禁止**把「搬 keep-all 几行到新文件」当降行银弹。LOC 棘轮 = **预警**；放行充分条件 = 预处理边界 + 不变量测。**禁止**「>1 人日则自动上调天花板」。仅当预处理抽离后仍超限，才允许 CODEOWNER + acceptance-records **留痕小幅上调**，并写明 pipeline 归因。 |
| **D-QFX-03 FE 门禁只读** | **不导出**任何写 setter。FE 只消费 BE 下发的只读 snapshot。定性：**产品面契约 + 纵深防御**；**安全边界在 BE 403**（非「删 setter = 安全完成」）。负向 E2E：动态 import 不得使默认 AI 面可见。死模块 `llm-readiness.js`（无调用方、无 NAS/鉴权）须删除或标 dark-only，防再引用。 |
| **D-QFX-04 status 早拒** | NAS off：`GET /llm/status` 在调用 `_status_body()` / 读 secrets·目录**之前** → **403** + `E_AI_SURFACE_DISABLED`。响应**零**敏感键。须回写 NAS D-NAS-17（已做）并 **同步 [IMPLEMENTATION-NO-AI-SURFACE-V1](../../../IMPLEMENTATION-NO-AI-SURFACE-V1.md) S7**（探查：该文仍写「status 可 200」——编码前必改，属文档挡门）。dark ON 不变。 |
| **D-QFX-04b Config 投影** | **拍板（2026-07-23）**：NAS off 时 `GET /__travelogue/config` **硬收口**——保留 `aiSurfaceEnabled:false` 与非 LLM 业务字段；**不得**暴露 `llmAvailable` / `llmProvider` / `tripsDir` / 其它 provider 细节。dark ON 可恢复完整投影。FE hydration **只依赖** config 的 `aiSurfaceEnabled`（不得因收口而整端 403 config）。回写 NAS §5 / Acceptance。 |
| **D-QFX-05 能力卡双态** | 生产默认永不展示（NAS）。测试：**(A) 禁用态**无真卡 DOM；**(B) 可达态**经**测试构建 / 依赖注入**挂载真实 `ensureRoot`+trap（**禁止**生产 URL 参数开关）。强制 role/aria-modal/label、首焦点、Tab、Shift+Tab、Esc、遮罩关闭、焦点恢复——**任何断言不得 skip**。禁止手写 fallback DOM。报告声明 `renderer=production`。 |
| **D-QFX-06 长图权威** | **第一权威** = 导出成功原子写入的 manifest / `current`（`batchId` + 有序 `files[]`）。预览/Bento **只读**该成功记录整组。挂点：写 = `export_handlers` Job/upload 成功返回前；读 = `_build_longshot_pages` 最前。mtime **仅**无清单旧盘 fallback。分段完整批次规则（聚合完整批 → 最新批 → 数字段号；禁逐文件混排；不完整批不可预览）= **M2′ 必达**。物理清旧图 = Park。 |
| **D-QFX-06b M1′ 长图切片** | **拍板（2026-07-23）**：M1′ **同时**交付 (1) 整卷 `_pick_longshot` 改为 `(st_mtime, name)` 降序（关 AC-11）；(2) Job/upload 成功路径写**最小** `current.json`（或等价），bento **优先读**（关 AC-25 大半）。**禁止**对分段用逐文件 mtime「假修好」。完整分段批次校验 / 不完整批拒绝 = M2′（AC-25 剩余 + 分段合同）。 |
| **D-QFX-07 意图单源** | 仅显式、校验通过的 `photoKeepMode` 具策略权威。旧布尔只经 BE adapter 一次归一；展示可推断，**永不落盘升为 keep_all**。FE 须对齐：`resolvePhotoKeepModeFromDraft` **与** `import-run.js` 遥测推断（探查：后者仍把 `cull=false∧dupes=true` 推成 `keep_all`）。FE/Python **共用合同向量**。**`skipLowResExclusion` 硬规则**：策略跳低清 **仅当** `photoKeepMode==keep_all`；独立布尔若残留于磁盘，**不得**优先于 mode；产品路径不落盘该键。 |
| **D-QFX-08 策展预处理** | 顺序固定：`尺寸回填（无条件）→ 清理本策略 low_resolution 旧标记 → 条件低清硬丢 → layout_assets`。keep_all 只跳硬丢。**禁止**再对 `apply_low_resolution_exclusion` 整函数短路。断言用**真实图**；现有「mock 未调用即绿」测须在 M2′ 删除或改为负例。 |
| **D-QFX-09 Hydration 三态** | 状态机：`unknown \| disabled \| enabled`。使用 `studioAuthHeaders()`；非 2xx/坏 JSON/网络错误 → `unknown`（**不**报 `enabled:false`）、清空 inflight 可重试。仅成功解析后 telemetry；`trackStudioEvent` 须可观测成功；`sessionStorage` 去重；服务端 meta **恰好** `{enabled: bool}`。 |
| **D-QFX-10 空测量 P0** | 缺字段 / 零样本 / 空 colors / NaN / 类型错误 → `D-UID-HARNESS` P0；进 PR CI。 |
| **D-QFX-11 Strict 全量** | `python … --strict`（bare）⇒ `wave=all`，且为 **required PR check**。Settings/Sheet token：解析目标根选择器与 `var()` 引用链；禁止全文 substring（轻量块解析即可，不上完整 CSS 引擎）。 |
| **D-QFX-12 复制三态** | 原生成功 / fallback 成功 / 最终失败。仅确认成功可显示成功文案；失败聚焦只读可选手动地址。**= 发版挡门**，可独立小 PR，不挡架构 M1′。 |
| **D-QFX-13 L1 等值** | 探查：HTML `data-csc-tier=l1` 三键与 `happyPath.l1Keys` **内容已对齐**；缺口是 **== 门禁测试**（非改数据）。锁定集合 **==**；检查唯一性、可见性、L1≤10。本包不强制服务端驱动渲染。 |
| **D-QFX-14a Telemetry schema** | 见 D-QFX-09；事件级严格 schema。 |
| **D-QFX-14b Facade 边界** | **扩现有** `lint_layout_engine_facade.py` 扫描根至 `travelogue/**`（排除 `layout_engine/**`）；grandfather 须 **owner + expiry**；新增 = 0。**不上**第二套 import-linter（仓内已有分层 `lint-imports`，与 facade 正交）。 |

**挂钩**：修复旁路在本包落地，但 **结案前必须回写 NAS / Keep-All / CSC**；宣布 QFX Closed 后不得保留平行 SSOT。编码前须同步 NAS **IMPLEMENTATION** S7（非代码，文档挡门）。

---

## 1. 背景与证据

### 1.1 审查环境

| 项 | 内容 |
|----|------|
| HEAD | `master` @ `ed4f032` |
| 当日 | 31 commits · ~227 files |
| 复现 | `lint_csc_recipe_baseline.py` fail；`lint_csc_god_module_ratchet.py` fail |
| 评审 | [quality-fixpack-v1-review-2026-07-22.md](../../../acceptance-records/quality-fixpack-v1-review-2026-07-22.md) · Conditional Go |

### 1.2 已确认有效（不重开）

- NAS 写路径硬拒；`aiSurfaceEnabled` 不进 PATCH；能力卡首启硬推永久关；dark ON 可恢复 DLLM 核心入口（不含能力卡）。

### 1.3 根因（评审定稿）

见 §0.2。v0.1「疑似根因」表降级为历史；实施以系统根因 R1–R5 与 §3 根本解法为准。

---

## 2. 问题陈述（P-QFX-*）

（与 v0.1 同表；严重度不变。完整列表见评审纪要 §0.2 / 原审查。要点：P-QFX-01～06 = P1；07～11 = P2；12～14 = P3。）

---

## 3. 根本解法与目标

### 3.1 根本解法（S-QFX-* · 实施优先级）

#### P0 · 先修系统

| ID | 解法 | 退出 |
|----|------|------|
| **S-QFX-01** | 预合入闭环（探查修正）：CSC 四件套**已在** PR lint；本包须把 `static_audit --strict`、status/config 403 单测、keep-all 合同向量、**窄标记** targeted Playwright 进 PR required；**不要**整包 `test-e2e` 上 PR；主干红禁合入 | 失败 PR 不可 merge；AC-24 |
| **S-QFX-02** | NAS：status 早拒 + **config 投影收口（04b）** + FE 只读；同步 IMPLEMENTATION-NAS S7 | AC-04/05/23/27；NAS 回写 |
| **S-QFX-03** | `photoKeepMode` 唯一权威；BE adapter；跨语言合同向量；FE 含 wizard + import-run | AC-12；Keep-All 回写 |
| **S-QFX-04** | 导出最小 `current`（M1′）→ 完整批次合同（M2′）；预览只读权威记录 | AC-11/25 |

#### P1 · 合同真测

| ID | 解法 | 退出 |
|----|------|------|
| **S-QFX-05** | 策展预处理合同（回填→清标→条件硬丢） | AC-13/26 |
| **S-QFX-06** | 审计 fail-closed（真组件 / schema / strict=all） | AC-06～08/16～20 |
| **S-QFX-07** | 真实架构护栏（facade 边界；LOC 预警） | AC-02/03 |
| **S-QFX-08** | 结案回写邻接合同；QFX 非长期 SSOT | DOC 闭环 |

#### P2 · 体验与防复发（挡发版）

| ID | 解法 |
|----|------|
| **S-QFX-09** | hydration 三态 + telemetry 成功确认 |
| **S-QFX-10** | 复制三态 |
| **S-QFX-11** | L1 集合 == |
| **S-QFX-12** | `scripts/quality_fixpack_gate.py`（或等价）= required |

### 3.2 非目标

- 不重开 AI-Return / 能力卡产品化硬推。  
- 不重写 curate 算法内核 / narrate / 排版族。  
- 不强制历史长图物理清理；不强制 facade grandfather 清零。  
- 不做设置页服务端动态渲染；不做 HEAD 全路径（Park）。  
- **禁止**单 PR 塞满 Fix all。

### 3.3 成功指标

| 指标 | 现状 | 目标 |
|------|------|------|
| CSC recipe / god-module lint | fail | **pass**（合入前） |
| NAS off `/llm/status` | 200+敏感 | **403 且零敏感键** |
| NAS off config 含 `llmProvider`/`tripsDir` | 是 | **否**（仅 `aiSurfaceEnabled`+非 LLM） |
| 公开写 API 翻转默认面 | 是 | **否** |
| 能力卡假 DOM 路径 | 有 | **0** |
| 空测量通过 | 是 | **0** |
| 旧草稿→keep_all | 是（FE） | **0** |
| keep_all 尺寸齐全 | 否 | **是** |
| 有 `current`/manifest 时预览指成功批次 | 否 | **100%** |
| bare `--strict` 审 all | 否 | **是** |
| L1 DOM == l1Keys | 数据已齐、门禁未建 | **差集为空（有测）** |

---

## 4. 需求详述

### WS1′ · 止血 + 直接伤害 — M1′

#### R1.1 Recipe + 合入列车（P-QFX-01 · D-QFX-01 · S-01）

- 同步 baseline / 单测至权威计数。  
- CI：**窄集**进 PR required（见 S-01）；CSC 已在 PR，勿重复叙事。  
- 文档约定「主干红禁叠主题」。  
- 验收：AC-01、AC-24。

#### R1.2 God-module / 预处理边界（P-QFX-02 · D-QFX-02 · S-07 · ALG-05）

- **主路径**：抽出策展预处理模块（回填→清标→条件硬丢），`curate` 只编排；锁定顺序不变量测。  
- **禁止**空搬 keep-all 门控充数。  
- LOC：预处理落地后力争回天花板；仍超则留痕上调并归因 pipeline。  
- 验收：AC-02（M1′ 可先绿棘轮或留痕；预处理完整验收可跨 M1′/M2′，以 AC-13/26 为准）。

#### R1.3 NAS status 早拒 + config 投影 + FE 只读（P-QFX-03/04 · D-QFX-03/04/04b · S-02）

- `handle_llm_status`：gate 失败立即 403，**不**调用 `_status_body`。  
- config：off 时执行 D-QFX-04b 投影。  
- 移除公开 setter；统一带 `studioAuthHeaders` 的 status helper；处理/删除 `llm-readiness.js`。  
- 文档：同步 IMPLEMENTATION-NAS S7；NAS Acceptance 增 config 投影条（若尚未有）。  
- 验收：AC-04/05/23/27。

#### R1.4 草稿与遥测不升 keep_all（P-QFX-07 · D-QFX-07 · S-03）

- `resolvePhotoKeepModeFromDraft` 对齐 `infer_mode_from_bools`（删 session「cull 关→keep_all」特例）。  
- 同步改 `import-run.js` 完成态/遥测推断。  
- 落地合同向量 JSON（Python+JS 同读）。  
- `skipLowResExclusion` 读路径改为 mode 唯一权威（D-QFX-07）。  
- 验收：AC-12。

#### R1.5 预览绑成功导出（P-QFX-06/06b · S-04）— **拍板切片**

- **M1′ 必达**：  
  1. 整卷 `_pick_longshot` → `(st_mtime, name)`（AC-11）；  
  2. Job + upload 成功写最小 `current.json`（`batchId` + 有序 `files[]`），`_build_longshot_pages` 优先读（AC-25 主路径）。  
- **M1′ 禁止**：分段逐文件 mtime 混排「假修」。  
- **M2′ 必达**：完整分段批次聚合 / 不完整批拒绝；无清单旧盘 fallback 行为固化。  
- 验收：M1′ AC-11 + AC-25（最小 current）；M2′ 分段合同补强。

---

### WS2′ · 合同真实 — M2′

#### R2.1 策展预处理（P-QFX-08 · D-QFX-08 · S-05 · 衔接 D-QFX-02）

- 落地预处理模块（可与 M1′ R1.2 同 PR 若容量允许，否则 M2′ 收口）。  
- 幂等清 `low_resolution` 本策略标记；真实图单测替换整函数 mock。  
- 分段长图批次合同收口（衔接 R1.5）。  
- Keep-All §4.2 已澄清回填；本波确认实现一致。  
- 验收：AC-13/26 + AC-25 分段补强。

#### R2.2 Hydration / telemetry（P-QFX-09/14a · D-QFX-09 · S-09）

- 三态；可重试；成功确认后 track；严格 schema。  
- 验收：AC-09/10/21/22。

#### R2.3 审计 fail-closed（P-QFX-05/10/11 · D-QFX-05/10/11 · S-06）

- 删假 DOM；完整 a11y；metrics schema；bare `--strict`=all；token 引用链。  
- 验收：AC-06～08/16～20。

#### R2.4 邻接合同回写落盘（S-08 · P-02/08）

- NAS / Keep-All /（必要时 CSC）Acceptance 与本包决策一致。  
- 验收：文档 diff 可审；Kickoff 清单勾选。

#### R2.5 Facade 扩扫（P-QFX-14b · D-QFX-14b）

- 扩扫 + grandfather owner/expiry。  
- 验收：AC-03。

---

### WS3′ · 防复发 + 体验 — M3′

#### R3.1 复制三态（P-QFX-12 · D-QFX-12 · S-10）

- 见 §5 COPY。验收：AC-14。

#### R3.2 L1 ==（P-QFX-13 · D-QFX-13 · S-11）

- 验收：AC-15。

#### R3.3 聚合 gate（S-12）

- `python scripts/quality_fixpack_gate.py`（或文档钉死的命令列表）= required。  
- 验收：AC-24。

#### R3.4 NAS 静态审计可达性

- 缩小 dark-only 整文件跳过为导出/入口白名单。

#### R3.5 Park

- HEAD 全路径；历史长图物理清理；facade 清零；轮播热区——见 §10。

---

## 5. 文案 / 体验

| ID | 场景 | 文案 / 交互 |
|----|------|-------------|
| **COPY-QFX-01** | 复制中 | `正在复制…` |
| **COPY-QFX-02** | 原生/fallback 成功 | `地址已复制，请在电脑浏览器打开` |
| **COPY-QFX-03** | 最终失败 | `无法自动复制。请长按选择下方地址并复制。`；按钮改 `重新复制`；聚焦只读地址控件并全选 |
| **COPY-QFX-04** | NAS 403 | 沿用 `E_AI_SURFACE_DISABLED` 中性 message；默认面不新增 AI 入口 |

---

## 6. 非功能

| 项 | 要求 |
|----|------|
| 安全 | status 早拒；**config 投影收口**；telemetry 白名单；FE 非安全边界 |
| 兼容 | 旧布尔不升 keep_all；dark ON 回归；旧盘无 `current` 时整卷 mtime fallback |
| 可测 | fail-closed；mutation fixture；跨语言合同向量 |
| CI | 窄集 PR required（非全量 e2e）；本地与 CI 同绿；聚合 gate |
| 文档 | 编码前同步 IMPLEMENTATION-NAS S7；结案回写邻接 PRD；QFX Closed |

---

## 7. 里程碑（可回滚 PR）

| 里程碑 | 范围 | 退出 | 建议 PR |
|--------|------|------|---------|
| **M1′** | R1.1–R1.5 | AC-01/04/05/12/23/27 + AC-11 + AC-25（最小 current）+ AC-02 或留痕；PR 窄门禁接线 | **PR-A / PR-B**（见 §8） |
| **M2′** | R2.1–R2.5 | AC-03/06～10/13/16～22/26 + 分段批次补强 + 邻接回写 | **PR-C** |
| **M3′** | R3.1–R3.4 | AC-14/15/24 + Closed 指针 | **PR-D** |

**禁止** M1′+M2′+M3′ 同一 PR。M1′ 未绿不得开 M2′ 合入主干。

**建议切片（与探查一致）**

| PR | 内容 |
|----|------|
| **PR-A** | recipe + status 早拒 + config 04b + setter 只读 + FE 草稿/遥测对齐 + 合同向量起步 + IMPLEMENTATION-NAS S7 文档同步 |
| **PR-B** | 整卷 mtime + 最小 `current.json` 写/读；预处理抽离起步或 god-module 留痕 |
| **PR-C** | 预处理完整 + 幂等 + 分段批次 + hydration + 审计 fail-closed + `--strict`=all |
| **PR-D** | L1== 门禁 · 复制三态 · facade 扩扫 · 聚合 gate · Closed |

---

## 8. 实施任务卡（IMPLEMENTATION 展开）

| 卡 | 锚点 | 里程碑 / PR |
|----|------|----------------|
| **T-QFX-00** | 同步 IMPLEMENTATION-NAS S7（status 403）；NAS config 投影 Acceptance | 文档 · PR-A 前或同 PR |
| **T-QFX-01** | recipe baseline + PR 窄门禁接线 | M1′ · PR-A |
| **T-QFX-02** | 策展预处理模块起步（非空搬 keep-all）/ 棘轮留痕 | M1′–M2′ · PR-B/C |
| **T-QFX-03** | status 早拒 + config 04b 投影 | M1′ · PR-A |
| **T-QFX-04** | ai-surface 只读 + `llm-readiness` 处理 + 负向测 | M1′ · PR-A |
| **T-QFX-05** | wizard-logic + import-run 对齐 + 合同向量 + skip 读路径 | M1′ · PR-A |
| **T-QFX-06** | 整卷 mtime + 最小 `current.json` + bento 优先读 | M1′ · PR-B |
| **T-QFX-07** | 预处理完整 + 幂等 + 分段批次 + 真实图测 | M2′ · PR-C |
| **T-QFX-08** | hydration 三态 + telemetry schema | M2′ · PR-C |
| **T-QFX-09** | UI Detail fail-closed（helpers/wave11/strict/token） | M2′ · PR-C |
| **T-QFX-10** | facade 扩扫（现有脚本）+ grandfather owner/expiry | M2′/M3′ · PR-C/D |
| **T-QFX-11** | 复制三态 · L1== 门禁 · quality_fixpack_gate · Closed | M3′ · PR-D |

---

## 9. 验收（AC-QFX-*）

| ID | 断言 | 门 |
|----|------|-----|
| **AC-QFX-01** | `lint_csc_recipe_baseline.py` pass | M1′ |
| **AC-QFX-02** | `lint_csc_god_module_ratchet.py` pass | M1′ |
| **AC-QFX-03** | `lint_layout_engine_facade.py` pass（扩扫后） | M2′ |
| **AC-QFX-04** | 动态 import 无法使默认 AI 设置入口可见 | M1′ |
| **AC-QFX-05** | NAS off：`GET /llm/status` → 403，无敏感键 | M1′ |
| **AC-QFX-06** | 能力卡无假 DOM；可达态强制完整 trap | M2′ |
| **AC-QFX-07** | 空/缺字段测量 → P0 | M2′ |
| **AC-QFX-08** | bare `--strict` ⇒ all | M2′ |
| **AC-QFX-09** | LAN/token dark ON hydration = enabled | M2′ |
| **AC-QFX-10** | gate meta 恰好 `{enabled:bool}`；失败不报 false | M2′ |
| **AC-QFX-11** | 无 `current` 时整卷新旧文件预览选 `(mtime,name)` 更新者 | M1′ |
| **AC-QFX-12** | 旧草稿与 import-run 推断永不→keep_all；与合同向量一致 | M1′ |
| **AC-QFX-13** | keep_all 回填尺寸、不硬丢低清 | M2′ |
| **AC-QFX-14** | 复制失败无成功态；失败聚焦地址 | M3′ |
| **AC-QFX-15** | `data-csc-key` **==** `l1Keys`（门禁测；数据探查已齐） | M3′ |
| **AC-QFX-16** | 报告 `renderer=production`；假 DOM mutation 必败 | M2′ |
| **AC-QFX-17** | a11y 全矩阵执行且无 skipped | M2′ |
| **AC-QFX-18** | metrics 缺字段/零样本/NaN → P0（参数化） | M2′ |
| **AC-QFX-19** | `main(["--strict"])` 调用 `wave=all` | M2′ |
| **AC-QFX-20** | token 仅在无关选择器 → 审计失败 | M2′ |
| **AC-QFX-21** | hydration 失败后可重试成功；失败期 0× false gate | M2′ |
| **AC-QFX-22** | 同 tab reload ≤1 条 gate；新 session 可再发 | M2′ |
| **AC-QFX-23** | status off 在 secrets/目录读取前 403（不调 `_status_body`） | M1′ |
| **AC-QFX-24** | QFX PR gate 为 required（流程可证明） | M1′/M3′ |
| **AC-QFX-25** | 有 `current`/manifest 时预览忽略更旧文件/名序；M2′ 另验分段完整批次 | M1′（最小 current）/ M2′（分段） |
| **AC-QFX-26** | keep_all 切换幂等：旧 low_res 标记清除且尺寸齐全 | M2′ |
| **AC-QFX-27** | NAS off：`GET /config` 响应无 `llmAvailable`/`llmProvider`/`tripsDir`；含 `aiSurfaceEnabled:false` | M1′ |

---

## 10. 风险 · Park · Kickoff

### 10.1 风险

| ID | 风险 | 缓解 |
|----|------|------|
| **R-QFX-01** | 抽离破坏 curate 顺序 | ALG-05 不变量清单 + 回归 |
| **R-QFX-02** | IMPLEMENTATION-NAS 仍写 status 可 200 | **编码前**改 S7；全库短路；AC-05/23 |
| **R-QFX-03** | 测试开关漏进生产 | 禁 URL 开关；仅测试构建/DI |
| **R-QFX-04** | `current` 写入非原子 | 写临时+rename；失败不更新 `current` |
| **R-QFX-05** | 只 403 status、不收口 config | 已拍板 04b；AC-27 挡门 |
| **R-QFX-06** | 分段假 mtime 混排 | M1′ 明确禁止；分段规则 M2′ |

### 10.2 Park

| 项 | 说明 |
|----|------|
| 历史长图物理清理 | manifest 后再做 |
| HEAD 全路径 | 不挡发版 |
| facade grandfather 清零 | 本包禁新增 + owner/expiry |
| curate/pipeline 全量大拆 | 另题 |
| 轮播热区 | 非本包根因 |

### 10.3 Kickoff 清单（编码前勾选）

- [x] PRD **v0.2** 回写评审 S/D/AC  
- [x] NAS D-NAS-17 / AC-NAS-17c 与 Keep-All §4.2 澄清  
- [x] PRD **v0.2.1** 三项拍板 + 探查修正入文（2026-07-23）  
- [x] NAS PRD 同步 D-NAS-17b config 投影（本波）  
- [x] **同步 IMPLEMENTATION-NAS S7/S7b**（v0.2.2 · status 403 · config 投影）  
- [x] IMPLEMENTATION-QUALITY-FIXPACK-V1 **v0.1.0** 展开 T-QFX-*  
- [x] 最小 `current.json` 字段草签（IMPLEMENTATION T-06 / §11.4）  
- [x] keep-all 合同向量路径（`tests/fixtures/qfx/photo_keep_mode_vectors.json`）  
- [x] 开分支 `fix/qfx-pr-a-m1-hemostasis` 并开始编码（PR-A T-00～05 + AC-02 留痕 + AC-24 起步） 

---

## 11. 附录

### 11.1 门禁命令（PR 窄集 · M1′）

```powershell
python scripts/lint_csc_recipe_baseline.py
python scripts/lint_csc_god_module_ratchet.py
python scripts/lint_layout_engine_facade.py
python scripts/studio_ui_detail_static_audit.py --strict
python -m pytest tests/unit/web/test_ai_surface_gate.py tests/unit/web/test_studio_ui_detail_static_audit.py -q
```

M2′/M3′ 另加：合同向量 · wave11（真组件）· NAS e2e 窄标 · 聚合 gate（见 IMPLEMENTATION）。**禁止**把全量 `test-e2e` 无差别上 PR。

### 11.2 关键文件

| 区域 | 路径 |
|------|------|
| NAS | `ai-surface.js` · `ai_surface.py` · `llm_settings_handlers.py` · `config_handlers.py` · `telemetry_handlers.py` · `llm-readiness.js` |
| CSC | `studio.py` · `happy_path_recipe.py` · `scripts/lint_csc_*.py` · `ci.yml` |
| UI Detail | `studio_ui_detail_static_audit.py` · `ui_detail_runtime_helpers.py` · wave11 |
| Keep-all | `import-wizard-logic.js` · `import-run.js` · `photo_keep_mode.py` · `curate.py` · `media/quality.py` |
| 导出 | `studio_bento_preview.py` · `export_handlers.py` · `export/longshot.py` |
| 窄屏 | `narrow-gate.js` |

### 11.3 邻接回写指针

| 文档 | 变更 |
|------|------|
| [PRD-NO-AI-SURFACE-V1](../../../PRD-NO-AI-SURFACE-V1.md) | D-NAS-17 status 403；**D-NAS-17b** config 投影（v0.2.3） |
| [ACCEPTANCE-NO-AI-SURFACE-V1](../../../ACCEPTANCE-NO-AI-SURFACE-V1.md) | AC-NAS-17c → 403；AC-NAS-17d config 投影 ✅（QFX PR-A） |
| [IMPLEMENTATION-NO-AI-SURFACE-V1](../../../IMPLEMENTATION-NO-AI-SURFACE-V1.md) | ✅ **v0.2.2**：S7 status 403 · S7b/BE-NAS-04 config 投影 |
| [IMPLEMENTATION-QUALITY-FIXPACK-V1](./IMPLEMENTATION-QUALITY-FIXPACK-V1.md) | ✅ **v0.1.0**：T-00～11 · PR-A/B/C/D |
| [PRD-KEEP-ALL-PHOTOS-V1](../../../PRD-KEEP-ALL-PHOTOS-V1.md) | §4.2 回填仍执行；策略跳低清仅 `photoKeepMode==keep_all` |

### 11.4 最小 `longshot-current.json`（M1′ · 已锁定）

路径：`{trip_dir}/longshot-current.json`（与 PNG 同层；PR-B 选定）。

```json
{
  "schemaVersion": 1,
  "batchId": "opaque-or-job-id",
  "createdAt": "ISO-8601",
  "kind": "whole | segmented",
  "files": ["相对 trip 根的有序文件名"]
}
```

写：临时文件 + `os.replace`；失败不更新。读：存在且 `files` 非空且文件均在盘 → 权威；否则整卷 mtime fallback。

---

## 12. 下一步

1. ~~PRD v0.1~~ Done  
2. ~~七席评审~~ Done  
3. ~~PRD v0.2 / v0.2.1 回写~~ **Done**  
4. ~~同步 IMPLEMENTATION-NAS / 写 QFX IMPLEMENTATION~~ **Done**  
5. ~~开 **PR-A** 编码~~ **Done（已合 master）** → **PR-B 编码中** → PR-C → PR-D  
6. ACCEPTANCE 勾选 → 宣布 QFX Closed 并归还邻接 SSOT  

**结案范围：Fix all（AC-01～27）。**  
**Park 仅**：HEAD、旧图物理清理、facade 清零、轮播热区、全量大拆、全量 e2e 上 PR。
