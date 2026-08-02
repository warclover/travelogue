# Travelogue · 算法与布局管线优化 V3 产品需求文档（PRD）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue Studio |
| **文档版本** | **v0.3.1** |
| **状态** | **Conditional Go · Must-Fix 已回写**（[评审纪要](./acceptance-records/algorithm-v3-prd-review-2026-08-01.md) · BLK-01～10）· **§15 FE 同步矩阵已收录** · **开发负责人代码复核已回写（DEV-01～06 · §14）** · **A5/C4–C5/fine_craft/竖单产品口已锁** |
| **DOC-STATUS** | **active**（W0～W3 工程已合；产品锁见 [alg3-product-lock…](./acceptance-records/alg3-product-lock-a5-c4-fc-portrait-2026-08-02.md)） |
| **主题代号** | 「管线加深 · 就绪探测 · 开关诚实」— **ALG-V3** |
| **触发来源** | 2026-08-01 首席架构/算法审查 · 产品「LLM 默认可开、无 Key 跳过」· 五席联评 |
| **审查基线** | [FLOW](./FLOW-TRIPOLOGUE-PIPELINE.md) · [Algorithm V2](./PRD-ALGORITHM-OPTIMIZATION-V2.md)（封面不重开）· [AAD](./PRD-ARCH-ALGO-DEEPENING-V1.md) · [SSG](./PRD-SMART-SHOT-GROUPING-V1.md) · [NAS](./PRD-NO-AI-SURFACE-V1.md) · [DLLM](./PRD-DESKTOP-LLM-SETUP-V1.md) · [AI-Return](./PRD-AI-RETURN-V1.md) · [Pipeline Perf](./PRD-PIPELINE-PERF-V1.md) · Phase15/16 |
| **关联实现锚点** | `curation/{clustering,scene_clusters,shot_grouping}.py` · `layout_engine/mosaic/{candidates,scorer,compose,trip,selfheal}.py` · `layout_contract/search_budget.py` · `web/{studio_narrate,ai_surface}.py` · `config/{_common,vision,clustering,shot_grouping,mosaic,layout,misc,aesthetic,studio}.py` |
| **评审纪要** | [acceptance-records/algorithm-v3-prd-review-2026-08-01.md](./acceptance-records/algorithm-v3-prd-review-2026-08-01.md) |
| **验收** | [ACCEPTANCE-ALGORITHM-OPTIMIZATION-V3.md](./ACCEPTANCE-ALGORITHM-OPTIMIZATION-V3.md) · must-green [alg3-must-green-nodeids.txt](./acceptance-records/alg3-must-green-nodeids.txt) · **产品锁** [alg3-product-lock-a5-c4-fc-portrait-2026-08-02.md](./acceptance-records/alg3-product-lock-a5-c4-fc-portrait-2026-08-02.md) |
| **实施清单** | [IMPLEMENTATION-ALGORITHM-OPTIMIZATION-V3.md](./IMPLEMENTATION-ALGORITHM-OPTIMIZATION-V3.md) |
| **更新日期** | 2026-08-02 |

> **v0.3.0 相对 v0.2.1（开发负责人代码复核回写 · 证据见 §14）**
>
> 1. **DEV-01**：**TriState 改型 / 新增 bool 会硬打穿** `happy_path_recipe` 与 CSC 基线快照。新增 **D5 工作包 + AC-32**，`iter_bool_paths` → `iter_flag_paths` 提到 **W0 挡门**。
> 2. **DEV-02**：Ready 探测**不得**复用 `studio_llm_status()`（该函数会 `inject_secrets_into_environ`）。新增只读 `probe_llm_ready()`，D-ALG3-02 改写。
> 3. **DEV-03**：补 `capability=true` 且无凭证的真值（降级 false + `llm_no_key`），新增 **AC-06**。
> 4. **DEV-04**：**B3 已在代码中实现**（`compose` 打分前跳过 `hard_valid=False`）→ **删包**；**B2 拆 B2a/B2b**（默认路径缺的是静态几何预检，不是顺序摆错）；**B1 条件修正并降至 W3**。AC-20 口径由「拒前 build_screen ↓」改为 **`buildScreenCalls` 绝对计数**，「≥10% 墙钟」降级为观测项。
> 5. **DEV-05**：**W1a 拆 W1a-1（性能）/ W1a-2（合同）** 两个 PR；明确 **C1 对默认路径零行为变化**。
> 6. **DEV-06**：`mosaic_explain` 人话缺 SSG/atom/clone 是**存量缺陷**（非 W1b 引入）→ 由 §15 Should S01 **提升为 W0 Must FE-ALG3-05**。
>
> 另：补齐空缺的 **§14**（代码复核证据台账）；AC-21 字段白名单在 **W0** 钉死。

> **v0.2.1 相对 v0.2.0**  
> 增补 **§15 FE 同步矩阵**（上下游触点 · 分波 UI 是否改 · Must/Should/Nice/禁止 · 精修/导出回归）。对照代码调研：Studio 设置/NAS/mosaic_explain/stale 链路。

> **v0.2.0 相对 v0.1.0（五席 Must-Fix 回写）**
>
> 1. **BLK-01**：拆 **Ready / MayCall / Import** 三态；NAS 期禁止 decor/MLLM 暗改默认可达文案与版式胜出。  
> 2. **BLK-02**：释放 AI 面挂 [AI-Return](./PRD-AI-RETURN-V1.md)，非本列车 DoD。  
> 3. **BLK-03**：墙钟须**新配置键 + 贯通** `SearchBudget`（今日未接线）。  
> 4. **BLK-04**：默认 MCS 热路径 = 拒前 `build_screen`；`quality_pool` hoist 仅 LSE-on。  
> 5. **BLK-05**：拆 curate / LayoutUtility 所有权归 AAD；本 PRD 不平行实现。  
> 6. **BLK-06**：bool→TriState 禁 `bool("auto")`；example 先对齐 `false`。  
> 7. **BLK-07**：交付拆 **W1a（零成片意图）/ W1b（条件 clone）**。  
> 8. **BLK-08**：Atom **禁止**默认自动 widen（observe-only 合同）。  
> 9. **BLK-09/10**：AC 可执行化要点 + 视觉合同 VC-ALG3；盲评四问。  
> 10. OQ/T 写入**评审建议拍板**（产品可改口，须书面）。

> **一句话目标**  
> 在不推倒 MCS/SSG 分层的前提下：把「该不该同窗」算准且不过碎；砍掉窗级候选浪费；让搜索预算名实相符；把外部智能做成 **Ready 可探测、Call 受闸、Import 默认 stub**——NAS 期 L0 不变，未来经 AI-Return 释放面即可发挥作用。

> **与相邻文档边界**
>
> | 文档 | 管什么 | 本 PRD |
> |------|--------|--------|
> | Algorithm V2 | 封面/清晰度 | **不重开** |
> | AAD | 拆 `run_curate`、PrefixBeam、LayoutUtility | **拥有** D4/B5 公式；本 PRD 只提观测/接口诉求 |
> | NAS | 用户面隐藏 AI | **服从**；本 PRD 只做 Ready，不绕过「用不到」 |
> | DLLM | L0/L1 配置体验 | Import stub / Key 安全合同延续 |
> | **AI-Return** | 正式解冻 AI 面 | **M4 前置**；本 PRD 不交付 UI/COPY 解冻 |
> | Pipeline Perf | ingest/WebP | 不替代；vision 成本与之共背 P95 |
> | SSG / P15 / P16 | 分镜与拼图 | 演进开关/剪枝，不换骨架 |

---

## 0. 读者指南

| 角色 | 先读 |
|------|------|
| 产品 | §3 三态 · §3.6 视觉静默 · §5 · §11 已建议拍板 · **§15 FE 同步** |
| 算法 | §4（含热路径勘误）· §6 W1a/W1b · §10.4 盲评 · **§14.2 MCS 复核** |
| 架构 / 开发 | §3.3～3.5 · §6～9 · API 草图 §13.4 · **§14 全文（开工前必读）** · §15.1～15.2 |
| 测试 / QA | §10（含 **AC-32**）· 防假绿 · ACCEPTANCE 拆分要求 · **§14.1 兼容爆炸半径** · §15.4 回归 |
| 视觉 / UX | §3.6 VC · §10.4 四问 · **§15 全文** |

### 0.1 术语

| 术语 | 定义 |
|------|------|
| **Ready** | 依赖可解析（如 `llmAvailable`）；写入摘要；**不等于**会调用 |
| **MayCall** | 是否允许对默认可达成片/文案路径发起外部调用（Surface∨dark∨显式旗） |
| **Import 调用** | 导入/G1 主链是否走 LLM（`prefer_llm_when_ready`） |
| **Capability Auto** | Ready 层倾向 `auto`：有凭证则 ready=true，无则 false；**不**自动等于 MayCall |
| **用户面（Surface）** | NAS / `ai_surface_enabled` / `TRAVELOGUE_AI_SURFACE` |
| **有效配置摘要** | trip meta：本趟生效开关 + 降级原因（可含 ready，不对终端用户营销） |
| **MCS / SSG** | 拼图竞选 / 智能分镜投影层 |

### 0.2 产品共识（铁律）

1. **L0 永不因缺外部依赖失败**。  
2. **Ready ≠ MayCall ≠ Import** — NAS 期默认可达面「看不见、配不了入口、**用不到**」仍成立。  
3. **失败归因局部化** — 不标成「生成失败」。  
4. **不重写 MCS/SSG 分层**。  
5. **开关诚实** — 禁静默 no-op；禁 `bool("auto")` 陷阱。  
6. **证据驱动** — 性能包 snapshot 等价；质量包盲评/基线 JSON。  
7. **VC-ALG3-05** — 本波不因算法增强改 Wait Tips / FirstSuccess / Help 的 AI 话术。

---

## 1. 背景与问题

### 1.1 管线事实（As-Is）

```text
ingest → clustering → shot_grouping
      → curate（含窗级 MCS）→ compose_trip / maybe_replan（scoring 常关）
      → lock_structure →（可选 G1）→ narrate（Studio 导入恒 stub）
      → lock_copy → render
```

四层概念：`eventId/章` ≠ `sceneClusterId` ≠ `shotGroupId` ≠ `burstGroupId`。

### 1.2 结构性短板

| ID | 短板 | 证据 | 维度 | 勘误（v0.3 已按代码复核，见 §14） |
|----|------|------|------|-----------|
| **P-ALG3-01** | HDBSCAN 不消费 `cluster_eps`；小册易过碎 | `scene_clusters._cluster_labels` | 准确度 | — |
| **P-ALG3-02** | soft-split 固定 6h × Atom 硬拒 → 候选枯竭 | `_soft_split_runs` · `atom_boundary` | 效果 | 枯竭为叠乘，非单因 6h |
| **P-ALG3-03** | 无 SSG 时 clone 硬门关 → 假切条 | `NearSceneCloneGateConfig.enabled=False` | 准确度 | SSG on 时硬拒不依赖该门 |
| **P-ALG3-04** | 候选浪费 + 乘性堆叠 | `candidates`/`scorer`/`combine_utility` | 性能+准确度 | **v0.3 重定位**：廉价硬拒**已在** `build_screen` 之前；默认热点是**缺静态几何预检**（几何/main_ar/sidebar 拒必须先建 screen）→ B2a。「打分前跳过硬拒」**已实现**→ 删 B3 |
| **P-ALG3-05** | scoring 开时墙钟虚设 | `SearchBudget`；**无配置键、调用方未传入** | 稳定性 | 结论成立（`layout_search.py` 构造时未传参）；但 scoring 默认关 → **默认路径收益为 0**，属正确性修复 |
| **P-ALG3-06** | scene + look **二次编码链** | clustering · look_appearance | 性能 | session 多已共享；成本在二次 encode/逐张 look |
| **P-ALG3-07** | LTE↔legacy + 实验旗 | `lte_adapter` · `_legacy_generated` | 稳定性 | — |
| **P-ALG3-08** | LLM Ready 与 Call/Surface 纠缠 | narrate 恒 stub · NAS · decor example≠code | 产品就绪 | 用三态合同解决 |
| **P-ALG3-09** | 开关清单只认 `bool`，TriState/新键即打穿基线 | `iter_bool_paths` · `RESEARCH_DEFAULT_FALSE` · CSC 基线 JSON | 工程稳定性 | **v0.3 新增**（DEV-01）→ D5 + AC-32，W0 挡门 |
| **P-ALG3-10** | Ready 探测有写 `os.environ` 副作用 | `studio_llm_status` → `inject_secrets_into_environ` | 稳定性+隐私 | **v0.3 新增**（DEV-02）→ 只读 `probe_llm_ready()` |

### 1.3 产品诉求（回应）

> 无 Key 用户不被挡；有 Key 时引擎就绪；未来释放面即用。  
> **v0.2 答法**：Ready=`auto` 现在就做；MayCall/Import 默认关；释放面走 AI-Return。

### 1.4 Non-Goals

| 排除 | 原因 |
|------|------|
| 官方代付 Key | DLLM |
| 端到端 LLM 出整本版式 | 可复现/成本 |
| 默认开 PrefixBeam / 全 LSE / TPC | 实验 |
| 封面 V2 / 拆 NAS 战略 | 既有合同 |
| 替代 Pipeline Perf | 另文档 |
| Atom 默认自动放宽 | 与 observe-only 冲突（BLK-08） |
| 平行实现 AAD Utility / 拆 curate | BLK-05 |

---

## 2. 目标与成功标准

| ID | 目标 | 衡量 |
|----|------|------|
| **G-ALG3-01** | Ready Auto：有凭证则 `llm.ready=true`，无则 false；无 Key 零外部调用 | AC-01/02 |
| **G-ALG3-02** | NAS 期 MayCall=off：不改默认可达文案/版式胜出；Surface 仍隐藏 | AC-04 · VC-02 |
| **G-ALG3-03** | 无 vision/SSG：条件 clone 门降低切条类假切条 | AC-10（W1b） |
| **G-ALG3-04** | 噪声可观测；soft-split 自适应（Atom 不默认 widen） | AC-11；AC-12 仅实验旗 |
| **G-ALG3-05** | W1a-1：默认路径 `buildScreenCalls` 绝对计数↓ + snapshot 等价 | AC-20/21 |
| **G-ALG3-06** | 墙钟可配置并贯通；scoring 开时可硬截断（**默认路径行为不变**） | AC-22 |
| **G-ALG3-07** | 每趟有效配置摘要 | AC-30 |
| **G-ALG3-08** | 实验旗默认关审计 | AC-31 |
| **G-ALG3-09** | 开关清单单源可承载 TriState；新增/改型开关不静默漂移基线 | AC-32 |

---

## 3. 外部智能 · 三态合同（BLK-01）

### 3.1 已拍板决策（评审建议 · 产品默认可沿用）

| ID | 决策 | 说明 |
|----|------|------|
| **D-ALG3-01** | 复用现有 **`TriState`**（`true\|false\|auto`） | 勿平行枚举；统一 `normalize_tri_state` |
| **D-ALG3-02** | Ready = **只读** `probe_llm_ready()`（与 `studio_llm_status` 同底层解析、**不共用副作用**） | **可解析 ≠ ping ok**；import **禁**真 ping；**禁**在观测路径写 `os.environ`（DEV-02） |
| **D-ALG3-03** | Surface ≠ **Ready**；NAS 期 Surface ≠ **MayCall** | 隐藏面时默认可达路径不得外呼 |
| **D-ALG3-04** | `prefer_llm_when_ready` **默认 false** | 导入/G1 恒 stub（对齐 DLLM/AIR） |
| **D-ALG3-05** | 调用失败 → stub/规则 + `degradeReason`；不失败整趟 | L0 |
| **D-ALG3-06** | **MayCall** = `Surface∨dark∨显式 cohort 旗` | NAS 默认 false |
| **D-ALG3-07** | 释放面里程碑 = **[AI-Return](./PRD-AI-RETURN-V1.md)** | 本 PRD 不交付 UI/COPY |

### 3.2 三态真值表（NAS 默认）

| 层 | 默认 | 有 Key 时 | 用户可见影响 |
|----|------|-----------|--------------|
| **Ready** | capability=`auto` → ready 随密钥 | ready=true | 仅摘要/dogfood |
| **MayCall** | **false** | 仍 false（除非 dark/cohort） | **无**文案/成片变化 |
| **Import** | prefer=**false** | stub | 无 |
| **Surface** | ai_surface=**false** | 隐藏 | 无 AI 入口 |

dark（`TRAVELOGUE_AI_SURFACE=1`）或未来 AIR 解冻后：MayCall 可开；prefer 由产品另定。

### 3.2.1 `capability_allows` 真值表（DEV-03 · 新增）

`llm.capability` 是 **TriState**，与探测到的 `ready` 组合出唯一结果。**显式 `true` 但无凭证不得静默无效**——这是最容易变成支持工单的分支。

| `capability` | `probe_llm_ready()` | 结果 `llm.ready` | `degradeReasons` | 说明 |
|--------------|---------------------|------------------|------------------|------|
| `auto`（默认） | false | **false** | **不写** | NAS 常态；用 `ready=false` 表达即可（§7.1） |
| `auto` | true | **true** | 不写 | 引擎就绪；是否实调仍看 MayCall |
| `true`（用户显式） | false | **false** | **`llm_no_key`** | **降级而非报错**；唯一允许在「未尝试调用」时记账的例外 |
| `true` | true | true | 不写 | — |
| `false` | 任意 | **false** | 不写 | 用户显式关闭，不记降级 |

`ready=true` **不**蕴含任何调用；调用与否仍由 MayCall（§3.5）单独判定。

### 3.3 能力矩阵（v0.2）

| 能力 | 代码/example 现状 | Ready | MayCall（NAS） | 无依赖 |
|------|-------------------|-------|----------------|--------|
| 杂志感 narrate | 导入恒 stub | capability=`auto` | 受 prefer+MayCall | stub |
| decorLine LLM | code `false` / example `true` | TriState 可 `auto` | **默认不实调**（false） | 规则/空句 |
| Aesthetic MLLM | `false` | TriState 可 `auto`；须 **VL 能力** | **默认不实调** | skip shortlist |
| Bookends VL / geocode | false | — | 保持关 | — |

**example 对齐（BLK-06）**：`config.yaml.example` 的 `decor_line_llm_enabled` **先改为 `false`**（与代码一致）；待 MayCall 合同与 loader TriState 落地后，再允许写 `auto` 且审计「auto≠实调」。

### 3.4 配置草案

```yaml
llm:
  provider: stub
  capability: auto              # Ready 层 TriState

narrative:
  decor_line_llm_enabled: false # W0 对齐；日后 TriState；实调另受 MayCall

studio:
  ai_surface_enabled: false     # Surface · NAS；不进用户 PATCH 白名单
  prefer_llm_when_ready: false  # Import 层

aesthetic:
  mllm:
    enabled: false              # W0 保持；日后 TriState + supports_vision + MayCall
```

**兼容**：旧 bool 可读；**禁止**对 TriState 候选键使用裸 `bool(yaml_value)`（`"auto"`→True）。

### 3.5 运行时合同

```text
ready := probe_llm_ready()                  # 只读；可解析，非 ping；不写 os.environ
may_call := surface_or_dark_or_cohort()

# Ready 记账（始终可写摘要）
llm.ready := capability_allows(llm.capability, ready)

# Import narrate（复用/收敛 resolve_studio_narrate_provider）
if force_stub or not prefer_llm_when_ready or not llm.ready or not may_call_for_import:
    provider := stub
else:
    provider := resolved  # ≡ 今日 if_ready

# decor / mllm
if not may_call or not capability_allows(flag, ready) or (mllm and not supports_vision):
    skip  # 不改默认可达结果
else:
    try call; on error → 规则路径 + degradeReason
```

`prefer_llm_when_ready` / `llm.capability`：**默认不进**对终端开放的 `patch_config_file` 白名单。

**探测副作用合同（DEV-02）**：`probe_llm_ready()` 必须**纯只读**——读取 secrets、尝试解析 runtime、返回布尔，**不得** `inject_secrets_into_environ`、不得改全局 config、不得发起网络请求。现有 `studio_llm_status()` 保留现状供 Studio 交互路径使用（它注入 environ 是 Studio 后续真调用所需），两者共用底层解析函数但**不得互相调用**。摘要（§7.1）只写 `capability/ready/mayCall/usedOnImport/decorLine/mllm`，**不写** provider 之外的任何凭证派生信息。

### 3.6 视觉 / NAS 静默合同（VC）

| ID | 条文 |
|----|------|
| **VC-ALG3-01** | 切条/假一条类才跨组硬拒；合法杂志混拼可跨组（软约束）。回引 D-SSG-05/17/21 |
| **VC-ALG3-02** | Surface=off 且无 dark/cohort 时，Capability **不改变**默认可达**文案与版式胜出**；允许 Ready 摘要 |
| **VC-ALG3-03** | Atom/soft-split **实验性**放宽须同时过假切条+跳戏盲评（双门）；**默认不自动 widen** |
| **VC-ALG3-04** | 连续同 **`patternId`** 超阈为质量回归项（主尺锁定；阈默认 2）。`layout_kind` 不作本波主尺。见 [产品锁 PL-VC04](./acceptance-records/alg3-product-lock-a5-c4-fc-portrait-2026-08-02.md) |
| **VC-ALG3-05** | 本波禁止改 Wait Tips / FirstSuccess / Help 的 AI/「升级」话术 |

本波**不需要**新线框/COPY 冻结表；释放面时由 AIR 解冻。

### 3.7 阶段策略

| 阶段 | Surface | Ready | MayCall | Import | 感知 |
|------|---------|-------|---------|--------|------|
| NAS（现在） | off | auto | off | stub | 无 AI；有 Key 不耗默认可达额度 |
| dark dogfood | on(env) | auto | on | 可开 prefer | 完整 L1 |
| AIR 释放 | on | auto | on | 产品定 prefer | 配置可见 |

---

## 4. 算法病灶与工作包

### 4.1 上游

| 包 | 方向 | 波次 | 备注 |
|----|------|------|------|
| **A1** | `cluster_selection_epsilon` **新键或删死旋钮**（禁 silent remap `cluster_eps`）；规模曲线；cache fingerprint | W2 / A1 低风险可 W0 | — |
| **A2** | `cluster_noise_ratio` 进 meta/漏斗 | W0 观测 | — |
| **A3** | soft-split 按簇内中位间隔自适应（夹紧） | W2 | — |
| **A4** | Atom：**仅**显式实验旗；优先降窗/告警；**禁止** observe floor 自动 widen | W2 实验 | BLK-08 |
| **A5** | Look 参考：默认 **first**；EMA/medoid **opt-in** + skip 可观测 | W3 | [产品锁 PL-A5](./acceptance-records/alg3-product-lock-a5-c4-fc-portrait-2026-08-02.md) |
| **A6** | look **批量化 encode** + 共享 session；超时可观测 | W2 | 非「二次热身」 |

### 4.2 中游 MCS

> **v0.3 复核后重排（DEV-04）**：`candidates.py` 的实际顺序已是 `pattern_disabled → try_order → atom → shot_group_cross → anti_slice → near_scene_clone → build_screen → geometry/main_ar/sidebar/usage_rule`。廉价硬拒**已经**在 `build_screen` 之前，`build_screen` 之后的拒**本质上需要 screen 才能判**。证据见 §14.2。

| 包 | 方向 | 波次 | 备注 |
|----|------|------|------|
| **B1** | 窗级 `quality_pool` hoist 条件收敛为**只看** `lse_quality_unified`，并经参数传入 `score_candidate` | **W3 / 随 LSE 开包** | v0.3 降波：真实漏洞是 `lse_quality_unified=True ∧ lse_hungarian_assignment=False` 时窗级池**根本没建**；两 flag 默认均 `False` → **不在默认路径** |
| **B2a** | **静态几何预检**：由 pattern grid specs × `aspects` 纯函数判定（`slot_cell_aspect_ratio`/`asset_fits_cell` 已是纯函数），命中即跳过 `build_screen` | **W1a-1** | **默认路径唯一有量级的增益点**。风险：MSA 的 `displayAspect` 覆写会使预检与 `screen_slots_geometry_ok` 不等价 → **MSA 开启时退化为不预检** |
| **B2b** | 匈牙利路径避免 `build_screen` 双算（重排后原地改 slots，不重建） | W3 / 随 LSE 开包 | 仅 `lse_hungarian_assignment=True` 时发生（默认 `False`） |
| ~~**B3**~~ | ~~硬拒项打分跳过~~ | **删除** | **已实现**：`compose.pick_best_window` 打分前即 `continue` 掉 `hard_valid=False`；`candidates` 内硬拒分支本就不入 `out`。人日退还 B2a |
| **B4** | signature 白名单：先看 miss 率 telemetry | W3 按需 | 已有多档覆盖 |
| **B5** | 惩罚饱和 + floor + `scorer_version` | W3 | **公式所有权 AAD**；本波可观测 |
| **B6** | self-heal 限次 / 限 SKU | W1a-1 | — |
| **B7** | `ssgMode∈{off,empty}` ∨ vision 降级 → clone 硬门；SSG 正常维持今日 | **W1b** | 仅切条类；VC-01 |

**开工前置**：B2a 合码前须先出一次 `buildScreenCalls` 基线 profile（固定语料，见 AC-20）。**未 profile 前不得把「≥10% 墙钟」写进任何承诺**——它是观测项，不是退出条件。

### 4.3 下游搜索 / 节奏

| 包 | 方向 | 波次 | 备注 |
|----|------|------|------|
| **C1** | `layout.scoring.wall_clock_limits_output`（名待定）→ loader → `SearchBudget`；scoring 开时默认 true | **W1a-2** | 贯通，非改魔法默认。**scoring 默认关 → 默认路径零行为变化**；新增 bool 键须同步 AC-32 |
| **C2** | `max_evaluations_per_segment` 有限默认（开 scoring 时） | W3 / 先修再开包 | — |
| **C3** | 「no_mosaic 条件枚举」**已部分落地**；W3 剪 always-on 变体（`no_hero` 等） | W3 | 勿重复造 |
| **C4/C5** | C4：节奏口径统一到 `patternId` streak；C5：diversity holdback **默认 off** | W3 | VC-04 · [产品锁](./acceptance-records/alg3-product-lock-a5-c4-fc-portrait-2026-08-02.md) |
| **C6** | PrefixBeam 默认关 | — | — |

### 4.4 工程

| 包 | 方向 | 所有权 |
|----|------|--------|
| **D1** | 有效配置摘要 | ALG-V3 W0 |
| **D2** | LTE 唯一源 + parity | W4 / 可并 P16 |
| **D3** | 删死 shim | W4 |
| **D4** | curate stage 化 / 窗决策复用 | **AAD**（本 PRD 不平行实现） |
| **D5** | **开关清单单源支持 TriState**：`iter_bool_paths` → `iter_flag_paths`（bool + TriState 统一收录，TriState 落 `tristate_flags` 独立段并进快照）；`tier_for_bool_path` 同步；`RESEARCH_DEFAULT_FALSE` / `DANGER_DEFAULT_FALSE` 对 TriState 键的语义定义为「默认值须为 `false` 或 `auto`+ready-only」 | **ALG-V3 W0 · 挡门**（DEV-01） |

---

## 5. 开关审计（v0.2 定案意向）

### 5.1 变更意向

| 开关 | 定案意向 | 说明 |
|------|----------|------|
| `llm.capability` | **auto**（Ready） | 新键 |
| `prefer_llm_when_ready` | **false** | Import |
| `decor_line_llm_enabled` | W0=**false**（对齐 example）；日后 TriState，实调受 MayCall | T5 修正案 |
| `aesthetic.mllm.enabled` | W0=**false**；日后同左 + VL 探测 | OQ-05 |
| `vision.enabled` | **先维持 false 或仅 cohort**（OQ-02=C；**不**绑 fine_craft 自动开） | [产品锁 PL-FC](./acceptance-records/alg3-product-lock-a5-c4-fc-portrait-2026-08-02.md) |
| `near_scene_clone_gate` | **条件开**（W1b） | OQ-03=A |
| `layout.scoring.wall_clock_*` | **新键贯通**；scoring 开时默认硬截断 | C1 |
| `layout.scoring.enabled` | **保持 false** | OQ-04=A |

### 5.2 保持

`clustering`/`shotGrouping`=`auto`；`mosaic.enabled=true`；`read_templates_from_lte=true`；pipeline 并行/延迟衍生=true（与 Perf 一致）。

### 5.3 保持关（默认）

scoring / prefix_beam / LSE caps / TPC 切引擎 / usage_rules / editorial 试点 / geocode / ai_surface / bookends VL；MTSO/MSA 维持实验纪律。  
（`template_experiments` 以**代码实际 cohort 默认**为准做审计，禁止错误写成「空=无人」若代码已是 `*`。）

### 5.4 产品勾选（评审建议已填 · 可改口）

| 项 | 建议 | 状态 |
|----|------|------|
| **T1** Capability Ready + import stub | **Go** | 建议采纳 |
| **T2** vision 默认 auto | **Conditional → 先 C** | 待产品最终口 |
| **T3** 无 SSG 条件 clone | **Go（W1b）** | 建议采纳 |
| **T4** scoring 本波不默认开 | **Go** | 建议采纳 |
| **T5** decor/mllm | **Ready 可 auto；MayCall 默认 false；example 先 false** | 修正案 |
| **T6** 释放面 | **挂 AIR，后置** | 建议采纳 |

---

## 6. 分波交付

### W0 · 合同与观测（约 6–8 人日 · v0.3 上调）

- D-ALG3 / TriState 兼容层；example decor=**false**  
- **D5 · `iter_flag_paths` 改造 + CSC 基线重签（挡门）** — 不做完，W1a-2 的 C1 一合入即红（§14.1）  
- **AC-21 字段白名单钉死进 ACCEPTANCE**（至少明确 `slotAssignmentFallback` / `candidateSource` / `displayAspect` 是否计入差异）  
- **FE-ALG3-05 · `mosaic_explain` 人话补全**（存量缺陷，成本≈一个 dict，见 §14.3）  
- `algoV3` 摘要 schema（§7.1）· `probe_llm_ready()` 只读探测  
- reject_funnel / noise 聚合 · `buildScreenCalls` 计数埋点（供 B2a 出基线）  
- 防假绿禁令进 ACCEPTANCE  
- **不成片**

**W0 退出**：AC-30/31/32 绿；`mosaic_explain` 对已知 reason 无原文英文外泄；`buildScreenCalls` 基线 JSON 已冻结。

### W1a · **拆两个 PR**（约 1.5–2 周）— **先合**

> **v0.3 拆分理由（DEV-05）**：原 W1a 把性能改造、CSC 兼容改造、Web 层 Ready 接线、隐私口径塞进同一个 PR。任何一处让 AC-21 等价性回归变红都极难定位。两者无依赖，可并行开发、串行合入。

#### W1a-1 · 性能（零合同变更 · 零成片意图）

| 项 | 包 | AC |
|----|-----|-----|
| 静态几何预检（MSA 开时退化） | **B2a** | AC-20 |
| self-heal 限次 / 限 SKU | B6 | — |
| snapshot A/B 等价 | — | AC-21 |

**退出**：固定语料 `buildScreenCalls` 总数较 W0 基线下降且有数；`patternId`+`slots`（剔除 W0 钉死的白名单字段）与基线**逐窗等价**；不引入任何新配置键。

#### W1a-2 · 合同（默认路径零行为变化）

| 项 | 包 | AC |
|----|-----|-----|
| 墙钟配置贯通 → `SearchBudget` | C1 | AC-22 |
| `probe_llm_ready()` + prefer 接线（默认 false） | §3 | AC-01/02/06 |
| `algoV3` 摘要落盘 | D1 | AC-30 |
| 新增 bool 键 → 基线重签 | D5 | **AC-32** |

**退出**：无 Key 零 outbound；有 Key 时 `ready=true` ∧ `usedOnImport=false` ∧ `mayCall=false`；`capability=true` 无 Key 时降级并写 `llm_no_key`；**默认配置下 chapters/slots 与合入前完全一致**（C1 只在 scoring cohort 生效）。

### W1b · 条件 clone 硬门（另 PR）

- B7 + VC-01  
- 基线 JSON + reject_funnel 硬可见 + 盲评问1/3  
- **明确成片变更**（无 vision/SSG 路径）

### W2 · 上游准确度（约 2–3 周）

- A1/A2/A3/A6  
- A4 **仅实验旗**  
- vision：按 OQ-02 最终口（cohort 或 auto）  
- 与 Perf 共背大册 P95

### W3 · 效用与节奏（flag + holdback）

- B5（协同 AAD）· A5 · C2/C3/C4/C5  
- scoring 仅内部 cohort

### W4 · 架构收口

- D2/D3；D4 **并 AAD**

### M4 · AI-Return（非本 DoD）

- Surface 解冻 · COPY · prefer 决策 · 有/无 Key 狗粮

---

## 7. 数据与可观测

### 7.1 `curation.algoV3`（或等价）

```json
{
  "visionEffective": "off|auto_ran|auto_skipped|true",
  "ssgMode": "off|empty|scene|look",
  "clusterNoiseRatio": 0.0,
  "cloneGateEffective": false,
  "layoutScoringEffective": false,
  "wallClockHardLimit": false,
  "llm": {
    "capability": "auto",
    "ready": false,
    "mayCall": false,
    "usedOnImport": false,
    "decorLine": "off|skipped_may_call|skipped_no_key|applied",
    "mllm": "off|skipped_may_call|skipped_no_vl|applied"
  },
  "degradeReasons": [],
  "rejectFunnelTop": {"atom_boundary": 0, "shot_group": 0, "near_scene_clone": 0},
  "buildScreenCalls": 0
}
```

**`buildScreenCalls`（v0.3 新增 · DEV-04）**：本趟 `build_screen` 的**绝对调用次数**。AC-20 以它做门，而不是「拒前 build_screen 数」——后者改完天然趋零，属自证（X08）。W0 先埋点出基线，W1a-1 再比。

**degradeReasons 枚举（须冻结）**：`llm_auth` · `llm_timeout` · `llm_quota` · **`llm_no_key`** · `mllm_no_vl` · `vision_timeout` · …  
NAS 默认不尝试调用时：**不要**每次堆 `llm_not_ready`；用 `ready=false` 表达即可。**唯一例外**是 `llm_no_key`——仅当用户把 `capability` 显式置 `true` 而探测不到凭证时写入（§3.2.1），用于区分「没配」与「配了但显式关」。

### 7.2 仪表

- 耗时：clusteringMs · shotGroupingMs · embedStats · MCS · beam evaluations  
- 质量：假切条窗率 · mosaic share · pattern streak · look skip · atom/clone/shot_group funnel  
- LLM：ready 率 · mayCall · usedOnImport · 实调率（dark）

---

## 8. 风险与回滚

| 风险 | 缓解 | 回滚 |
|------|------|------|
| MayCall 误开耗额度 | 默认 false；摘要审计；禁用户 PATCH | mayCall 关 |
| `bool("auto")` 静默开 | loader 统一 normalize | — |
| clone 误杀混拼 | VC-01 作用域 | gate 条件关 |
| Atom 实验放宽跳戏 | VC-03 双门 | 关旗 |
| 墙钟截断版式漂 | 仅 scoring on；deterministic 合同 | 硬截断关 |
| vision cohort 成本 | Perf P95 共门 | vision=false |
| B5 与 AAD 双改 | 所有权表 | 旧 scorer_version |
| **B2a 预检与真实几何不等价**（MSA `displayAspect` 覆写） | MSA 开启时**退化为不预检**；AC-21 逐窗等价 | 关预检开关，回落原路径 |
| **新开关静默漂移 CSC 基线** | D5 + AC-32 挡门（W0 先行） | 回滚键，重签基线 |
| **Ready 探测污染 `os.environ`** | `probe_llm_ready()` 纯只读合同（§3.5） | 摘要不写 llm 段 |

---

## 9. 非功能

| 项 | 要求 |
|----|------|
| 确定性 | W1a-1 snapshot 双跑/A-B；W1a-2 默认路径字节级对照 |
| 隐私 | Key 不进 trip/日志明文；**观测路径不得注入 `os.environ`**（§3.5） |
| 本地优先 | 无网/无 Key 完整 L0 |
| 兼容 | bool→TriState **须先落 D5**；任何新增/改型开关必须同 PR 更新 `csc-w0-baseline-happy-path-recipe.json` 与 `bool_fields`/`default_true`/`default_false` 三计数，并同步 `algorithm_profile` 指纹（AC-32） |
| 安全 | 不盲重试打爆 endpoint |
| CI | 无真实 Key；性能用计数门，绝对值作记录 |

---

## 10. 验收

> 详细 nodeid / 基线路径在 ACCEPTANCE 钉死。以下为合同级断言（v0.2 已去空指针）。

### 10.1 Capability / Surface

| ID | 断言 | 夹具要点 |
|----|------|----------|
| **AC-01** | 无 Key：零 outbound LLM；import 成功；无用户错误页；`ready=false`·`usedOnImport=false` | spy/mock HTTP；清 secrets |
| **AC-02** | 有 Key + prefer=false：import stub；`ready=true`·`usedOnImport=false`·`mayCall=false` | inject secrets + mock resolve；非 ping |
| **AC-03** | prefer=true 且 MayCall 允许：可走 LLM；401/超时→stub 成稿 | **dark/mock job**；非默认面 CI |
| **AC-04** | Surface=off：无 AI 入口；有 Key 亦然 | 指针 NAS AC + 本回归 |
| **AC-05a** | decor：MayCall=false → 不实调（即使 ready） | 契约 |
| **AC-05b** | mllm：无 VL 或 MayCall=false → skip | `supports_vision` |
| **AC-06** | `capability=true` **且无凭证**：`ready=false` ∧ `degradeReasons` 含 `llm_no_key` ∧ **导入正常成稿**（不报错、不弹用户错误页）；`capability=auto` 无凭证时**不得**写 `llm_no_key` | 清 secrets；对照 auto/true 两跑（§3.2.1） |
| **AC-07** | `probe_llm_ready()` 调用前后 `os.environ` **无差异**；且未发起任何网络请求 | 快照 `os.environ` + outbound spy（DEV-02） |

### 10.2 质量

| ID | 断言 | 夹具要点 |
|----|------|----------|
| **AC-10** | W1b：无 vision/SSG 语料上，条件 gate vs off：**切条类**假切条窗率相对 ↓≥**40%**（对齐 SSG 量级）或漏斗硬可见+盲评问1≥平 | 冻结 corpus JSON；**不得**用「SSG 已绿」代替 |
| **AC-11** | fixture 噪声比 ≤ 基线+**0.03**；改 HDBSCAN 消费参数须 cache fingerprint 变 | 写入 meta |
| **AC-12** | Atom/soft-split **实验旗 on**：`atom_boundary` 占比↓≥**25%** 且 multi-slot share≥observe floor **且**盲评问1+2 不差 | 旗默认关；off 时行为不变 |

### 10.3 性能 / 稳定性

| ID | 断言 | 夹具要点 |
|----|------|----------|
| **AC-20** | W1a-1：固定语料下 `algoV3.buildScreenCalls` **总数**较 W0 冻结基线下降，且下降量有数可比；**CI 用该计数做门，禁用绝对毫秒**。墙钟改善（默认路径目标 ≥10%、LSE-on ≥15%）为**本机观测记录项，非退出条件** | W0 先冻结基线 JSON；**禁**用「拒前 build_screen 数↓」自证（X08） |
| **AC-21** | W1a-1：`patternId`+`slots` 与基线**逐窗等价**，差异字段白名单**须在 W0 已写入 ACCEPTANCE**（含 `slotAssignmentFallback` / `candidateSource` / `displayAspect` 的取舍） | 非仅自反双跑；白名单缺失即视为 AC 未定义、不得判绿 |
| **AC-22** | scoring **cohort 开启** + 硬截断：`timedOut∧wallClockExceeded`；evaluations 不再增长；chapters 合法非空。**同时**断言：默认配置（scoring=false）下 C1 合入前后 chapters 字节级一致 | 贯通测，非只测 `SearchBudget` 对象；默认路径对照跑不可省 |
| **AC-30** | §7.1 必填键（含 `buildScreenCalls`）；无 Key / SSG empty 两场景值分化 | schema |
| **AC-31** | §5.3 实验旗默认关；与 happy_path/CSC 单源 | 快照 |
| **AC-32** | **本 PR 引入的任何新增/改型开关**（新 bool、bool→TriState）：`studio_default_recipe()` 快照与 `bool_fields`/`default_true`/`default_false` 三计数在同 PR 内更新且解释增量；TriState 键出现在 `tristate_flags` 段而非从清单消失；`RESEARCH_DEFAULT_FALSE` / `DANGER_DEFAULT_FALSE` 中的键**一个都不缺项** | `test_happy_path_recipe.py` · `csc-w0-baseline-happy-path-recipe.json`；**W0 挡门**（§14.1） |

### 10.4 防假绿禁令

| ID | 禁令 |
|----|------|
| **X01** | 禁止「import 成功」单独过 AC-01/03 |
| **X02** | 禁止无 outbound spy 声称未调 LLM |
| **X03** | 禁止自反双跑冒充 AC-21 |
| **X04** | 禁止仅 funnel↓ 过 AC-12 |
| **X05** | 禁止远程 CI 绝对毫秒过 AC-20 |
| **X06** | 禁止 default job 跑 prefer=true 真网 |
| **X07** | 禁止摘要「键存在即过」 |
| **X08** | 禁止用「拒前 `build_screen` 计数↓」过 AC-20（改完天然趋零，自证）；必须用 `buildScreenCalls` 绝对总数 |
| **X09** | 禁止用「改了 baseline JSON 后测试变绿」过 AC-32；须在 PR 描述中逐键解释增量来源 |
| **X10** | 禁止在无 `os.environ` 前后快照的情况下声称 `probe_llm_ready()` 只读（AC-07） |

### 10.5 盲评四问（签核）

1. 假切条　2. 跳戏　3. 混拼/过碎　4. 节奏（同模板连用）  

| 门 | 标准 |
|----|------|
| W1b | 问1 On≥Off；问3 混拼不差 |
| W2 | 问1+2 ≥基线；问3 不差 |
| W3 | 问4 ≥基线；streak 超阈↓ |

语料：混导密连拍、换装同地、横竖混拼、小册、无 vision 对照；含窄屏长图。

---

## 11. 开放问题（评审建议拍板）

| ID | 问题 | **v0.2 建议拍板** |
|----|------|-------------------|
| **OQ-01** | NAS 期 import 自动 LLM？ | **A 否** |
| **OQ-02** | vision 默认 auto？ | **先 C（cohort SSOT）**；**不**绑 fine_craft 自动开；狗粮后再议 A · [PL-FC](./acceptance-records/alg3-product-lock-a5-c4-fc-portrait-2026-08-02.md) |
| **OQ-03** | clone 门？ | **A 条件开** |
| **OQ-04** | 本波开 scoring？ | **A 否** |
| **OQ-05** | MLLM 凭证？ | **须 VL 能力；否则 skip** |
| **OQ-06** | 释放面同列车？ | **后置 AIR** |

产品若改口须书面修订本表与 ACCEPTANCE。

---

## 12. 里程碑

| 里程碑 | 内容 | Go |
|--------|------|-----|
| **M0** | ACCEPTANCE + IMPLEMENTATION + 基线资产清单 | ☑ 2026-08-01：ACCEPTANCE（含 **AC-21 白名单**）· IMPL · must-green · baseline 占位；OQ 表仍待产品最终口 |
| **M0.5** | **W0（挡门）** | **AC-30/31/32** · **FE-ALG3-05** · `buildScreenCalls` 基线冻结 |
| **M1a** | **W1a-1 性能** | AC-20/21 |
| **M1c** | **W1a-2 合同** | AC-01/02/04/05a/**06/07**/22/30/32 · FE-ALG3-01/02/04 |
| **M1b** | W1b | AC-10 + funnel + 盲评问1/3 · **FE-ALG3-S03** |
| **M2** | W2 | AC-11；A4 旗 off 默认；vision 按 OQ-02 |
| **M3** | W3 holdback | 四问 + scorer_version（协同 AAD） |
| **M4** | AI-Return | 非 ALG-V3 DoD |

---

## 13. 附录

### 13.1 Keep

MCS 三件套 · SSG 投影层 · 乘性代数（可饱和）· fail-open · burst>look>scene · `compose_trip` 入口 · Atom 默认硬边界（非实验旗时）

### 13.2 Top10 → 包

| 审查项 | 包 |
|--------|-----|
| 候选浪费 / 早拒 | **B2a/B6 · W1a-1**（B3 已实现已删；B2b 随 LSE） |
| 墙钟虚设 | **C1 · W1a-2** |
| 开关清单打穿基线 | **D5 · W0 挡门** |
| 无 vision 假切条 | B7 · W1b |
| HDBSCAN / soft-split | A1/A3 · W2 |
| Atom 枯竭 | A4 实验 · VC-03 |
| 二次编码 | A6 · W2 |
| 乘性堆叠 | B5 · W3/AAD |
| Ready vs 释放 | §3 · AIR |
| 双注册表 | D2 · W4 |

### 13.3 一页纸

1. **Ready auto，MayCall/Import 默认关** — NAS 静默；探测**只读**。  
2. **W0 是挡门**（D5 开关清单 + explain 人话 + 白名单 + 基线），不做完后面必红。  
3. **W1a 拆两个 PR**：W1a-1 只动性能（B2a 静态几何预检），W1a-2 只动合同（C1+Ready）；W1b 另开（clone）。  
4. **默认热点是「缺静态几何预检」**，不是顺序摆错；B3 已实现、B1/B2b 不在默认路径。  
5. **墙钟是正确性修复**，默认路径收益为 0，别当性能包验收。  
6. **Atom 不自动 widen**；scoring/PrefixBeam/LSE 默认关。  
7. **释放面 = AIR**，不是再改一轮算法默认。

### 13.4 API 草图（开发）

```python
# 复用 TriState + normalize_tri_state（禁 bool("auto")）
def probe_llm_ready(*, cfg=None) -> bool:
    """只读探测：读 secrets → 尝试解析 runtime → 返回布尔。
    合同（DEV-02 / AC-07）：不 inject_secrets_into_environ、不改全局 config、不发网络请求。
    与 studio_llm_status 共用底层解析，但两者不得互相调用。
    """

def capability_allows(flag: TriState, *, ready: bool) -> tuple[bool, str | None]:
    # 见 §3.2.1 真值表；true ∧ not ready → (False, "llm_no_key")

def resolve_studio_narrate_provider(*, cfg, force_stub=False) -> str:
    # stub unless prefer ∧ ready ∧ capability ∧ (import may_call policy)
    # 收敛今日恒 stub 与 if_ready 双真相

def resolve_llm_feature(flag: TriState, *, may_call: bool, need_vision=False) -> tuple[bool, str]:
    # decor / mllm；返回 (should_call, degrade_reason)


# D5（W0 挡门）· travelogue/orchestrator/happy_path_recipe.py
def iter_flag_paths(obj) -> tuple[list[tuple[str, bool]], list[tuple[str, str]]]:
    """替代 iter_bool_paths：同时收集 bool 叶子与 TriState 字符串叶子。
    TriState 落 recipe["tristate_flags"]，bool 仍落 recipe["appconfig_bools"]；
    两段都进 CSC 快照，确保 TriState 改型不会让键「凭空消失」。
    """


# B2a（W1a-1）· travelogue/layout_engine/mosaic/slot_geometry.py
def pattern_geometry_precheck(pattern_id, ordered_ids, aspects) -> bool | None:
    """基于静态 grid specs × aspects 的纯函数预检；返回 None 表示「无法判定，需建 screen」。
    MSA（effective_slot_adaptation_enabled）开启时一律返回 None —— displayAspect 覆写
    会使预检与 screen_slots_geometry_ok 不等价（§8 风险表）。
    """
```

### 13.5 BLK 追溯

| BLK | 回写位置 |
|-----|----------|
| 01 三态 | §3 |
| 02 AIR | §0 边界 · D-07 · M4 |
| 03 墙钟 | P-05 · C1 · AC-22 |
| 04 热路径 | P-04 · B1/B2 · AC-20 |
| 05 AAD | §0 · D4/B5 · W3/W4 |
| 06 TriState/example | §3.3～3.4 · W0 |
| 07 W1a/b | §6 · §12 |
| 08 Atom | A4 · VC-03 · AC-12 |
| 09 AC | §10 |
| 10 VC | §3.6 · §10.5 |

### 13.6 DEV 追溯（v0.3 · 开发负责人代码复核）

| DEV | 主题 | 回写位置 |
|-----|------|----------|
| **01** | 开关清单 / CSC 基线爆炸半径 | P-09 · D5 · §6 W0 · §9 · **AC-32** · X09 · §14.1 |
| **02** | Ready 探测只读化 | P-10 · D-ALG3-02 · §3.5 · **AC-07** · X10 · §13.4 |
| **03** | `capability=true` 无 Key 真值 | **§3.2.1** · §7.1 `llm_no_key` · **AC-06** |
| **04** | MCS 病灶重定位 | P-04 · §4.2（B1 降波 / B2a·B2b / **删 B3**）· **AC-20** · X08 · §14.2 |
| **05** | W1a 拆 PR | §6 W1a-1 / W1a-2 · §12 M1a/M1c |
| **06** | explain 人话存量缺陷 | §6 W0 · **FE-ALG3-05** · §15.2/15.3 · §14.3 |

---

## 14. 附录 · 开发负责人代码复核台账（v0.3 依据）

> **定位**：v0.3 的每一处改写都由代码事实驱动。本节钉死证据，避免实施期反复重查。  
> **复核日期**：2026-08-01 · 复核范围：`happy_path_recipe` · `candidates`/`compose`/`scorer` · `search_budget`/`layout_search` · `studio_narrate` · `mosaic_explain` · `config/mosaic`。

### 14.1 兼容爆炸半径（DEV-01 · 最高优先级）

`travelogue/orchestrator/happy_path_recipe.py` 的开关清单**只认 `bool`**：

```python
if isinstance(value, bool):
    out.append((path, value))
```

由此产生两条必然失败路径：

| 触发动作 | 后果 | 落点 |
|----------|------|------|
| C1 新增 `layout.scoring.wall_clock_limits_output`（bool） | `bool_fields` 151→152、`default_false` 54→55 → `test_bool_counts_match_prd_diagnostic_band` 断言失败 + `csc-w0-baseline-happy-path-recipe.json` 快照失配 | `tests/unit/orchestrator/test_happy_path_recipe.py` |
| `narrative.decor_line_llm_enabled` / `aesthetic.mllm.enabled` 改 TriState（str） | 两键**从 `appconfig_bools` 中消失**；`RESEARCH_DEFAULT_FALSE` 归类丢项、`tier_for_bool_path` 覆盖出洞、快照失配 | 同上 + `RESEARCH_DEFAULT_FALSE` |

现有测试写死了具体数字（`bool_fields == 151` / `default_true == 97` / `default_false == 54`），所以这不是「顺手改一下 baseline」，而是**清单模型本身不支持 TriState**。→ 必须先做 **D5**，再做 C1 与任何 TriState 改型。

### 14.2 MCS 热路径复核（DEV-04）

`generate_window_candidates_with_rejections` 的**实际**判定顺序：

```text
pattern_disabled → try_order_for_pattern → atom_boundary
  → shot_group_cross → shot_group_anti_slice → near_scene_clone
  → build_screen ←──────────── 分界线
  → [hungarian 时二次 build_screen]
  → geometry_invalid → contract eligibility
  → main_ar_mismatch → sidebar_min_short_side → usage_rule
```

三条结论：

1. **所有廉价硬拒已在 `build_screen` 之前**。原 B2「ordering 后、build_screen 前廉价 gate」在代码上已成立，不是待办。分界线之后的拒（几何 / main_ar / sidebar / usage_rule）**本质上需要已构建的 screen**，属「缺静态预检」而非「顺序摆错」→ 改写为 **B2a**。
2. **B3 已实现**：`compose.pick_best_window` 在打分前 `continue` 掉 `hard_valid=False` 与 disabled pattern，`candidates` 内硬拒分支本就不入 `out` → **删包**。
3. **B1 的漏洞形态与 PRD 原描述不同**：窗级 hoist 门是 `lse_hungarian_assignment ∧ lse_quality_unified`，而 `score_candidate` 内重建只看 `lse_quality_unified`。真实漏洞是 `lse_quality_unified=True ∧ lse_hungarian_assignment=False` 时窗级池根本没建。两 flag 在 `config/mosaic.py` 中默认均为 `False` → **不在默认路径**，降至 W3。

同时确认 **P-ALG3-05 成立**：`layout_engine/planner/layout_search.py` 构造 `SearchBudget(...)` 时传了 `search_timeout_ms` / `max_evaluations_per_segment`，唯独**未传** `wall_clock_limits_output`，字段恒为 dataclass 默认 `False`，超时只置 `wall_clock_exceeded` 不置 `timed_out` → 不截断。

### 14.3 存量缺陷：explain 原文外泄（DEV-06）

`travelogue/curation/mosaic_explain.py` 的 `_REJECT_LABELS` 仅六条，`_human_reject` 的兜底是 `label = reason`（原始英文）。当前缺失且**已在默认路径产出**的 reason：

`atom_boundary` · `shot_group_cross` · `shot_group_anti_slice` · `near_scene_clone` · `main_ar_mismatch` · `sidebar_min_short_side` · `contract:mix_miss` · `mixed_portrait_is_hero`

用户在「为何没拼」抽屉会看到形如 `5-main：near_scene_clone（penalty=0.82）` 的原文。SSG 已在默认路径产出前三个 → **这是今天就存在的缺陷，不是 W1b 引入**。修复成本≈补一个 dict → 由 §15 Should S01 **提升为 W0 Must（FE-ALG3-05）**。

### 14.4 Ready 探测副作用（DEV-02）

`travelogue/web/studio_narrate.py` 的 `studio_llm_status()` 在判定可解析之前会 `inject_secrets_into_environ(secrets)`——对 Studio 交互路径是必要的（后续真调用依赖环境变量），但 W0 要求「每趟写有效配置摘要」会把这个写 `os.environ` 的副作用搬进**导入主链的观测动作**。→ 拆出只读 `probe_llm_ready()`，见 §3.5 与 AC-07。

同时确认 `resolve_studio_narrate_provider` 今日**恒返回 `stub`**（`_ = cfg` 占位），`resolve_studio_narrate_provider_if_ready` 是另一条真相 → §13.4 的收敛方向成立。

---

## 15. 附录 · FE 同步矩阵（Studio 上下游与交互）

> **定位**：回答「ALG-V3 改管线后，前端/交互要不要同步改」。  
> **结论先行（v0.3 修订）**：W1a-1/W1a-2 **不需要新产品 UI**；**W0 有一项 Must** —— `mosaic_explain` 人话补全（FE-ALG3-05，修存量原文外泄，§14.3）；W1b（条件 clone）**应轻量同步** stale/导出回归；AI/LLM 面本波 **禁止解冻**（归 [AI-Return](./PRD-AI-RETURN-V1.md) / [NAS](./PRD-NO-AI-SURFACE-V1.md)）。  
> **调研锚点**：`templates/studio/**` · `travelogue/web/{ai_surface,studio_narrate,studio_trips}.py` · `curation/mosaic_explain.py` · `algorithm_profile.py` · 设置区 `studio-home-v2.html`。

### 15.1 管线上下游 × UI 触点

```text
[上游] ingest · GPS · burst ·（可选）CLIP
   ↓ clustering → sceneClusterId / eventId
   ↓ shot_grouping → shotGroupId
   ↓ curate 内 MCS → screens / mosaicDecisionLog / reject_funnel
   ↓ compose_trip（layout.scoring 默认关 → 常 idle）
   ↓ lock → narrate(stub) → render → 预览
   ↓ [下游] 精修/replan/rerender · longshotStale · algorithmStale · 导出
```

| 能力 | 上游写入（BE） | 下游消费（BE） | Studio 现有 UI 触点 | 用户可 PATCH？ |
|------|----------------|----------------|---------------------|----------------|
| vision / 聚类 | `ClusteringLayer` | SSG · Atom · 子段 | 设置「行程识别 / 场景分析」；FS `clusterNotice`；导入阶段文案 | ✅ `clustering.enabled` · `vision.enabled` |
| SSG | `run_shot_grouping_layer` | MCS 硬拒 · clone 软罚 | **无独立开关**（跟随 clustering） | ❌ |
| MCS / clone | `candidates` / `compose` | `chapters` · explain | 「为何没拼」· 精修拼图 · 更新版面 | ❌（clone 门仅 yaml/dogfood） |
| scoring / Budget | `compose_trip`（常关） | chapters 重排 | 设置「智能排版（实验）」 | ✅ 仅 `layout.scoring.enabled` |
| LLM 三态 | narrate / decor / mllm | 文案 / decor | **NAS 隐藏**；dark 见写作增强 | ❌ Surface/prefer/capability/decor/mllm |
| `algoV3` 摘要 | （W0 拟写） | dogfood / AC | **无终端 UI**（刻意） | ❌ |

**默认可达仍可见的关键面**

| 面 | 路径 |
|----|------|
| 设置·导入与分析 | `templates/studio/studio-home-v2.html` · `js/advanced.js` · `homepage-v2/settings-panel.js` |
| 导入进度 / Wait Tips | `homepage-v2/import-run*.js` · `wait-tips*.js` |
| FirstSuccess | `homepage-v2/first-success.js` |
| 「为何没拼」 | `preview-toolbar/drawers.js` · `curation/mosaic_explain.py` |
| 精修 → 更新版面 → 导出 | `preview-toolbar/{features,core,longshot}.js` |
| 书架 / Bento stale | `homepage-v2/{shelf,bento-stale,shelf-actions-logic}.js` · `curation/algorithm_profile.py` |

**NAS 已藏、本波勿解冻**

| 面 | 路径 |
|----|------|
| AI 设置区 / LLM Modal | `#v2-settings-zone-ai` · `js/llm-settings.js` · `js/ai-surface.js` |
| Sheet 杂志感 / Dock 再生成文案 | `preview-toolbar-v3-sheet.js` · `init-v3.js` · task-dock |
| 能力卡 / stub banner | `capability-card.js` · `home-stub-banner.js`（默认 no-op / 隐藏） |

### 15.2 分波：用户可见变化 × 是否改 UI

| 波次 | 默认可达用户感知（无新 UI 工时） | FE / 交互同步 |
|------|----------------------------------|---------------|
| **W0** 摘要 / TriState / example / D5 | 无感；**但「为何没拼」文案变可读** | **Must FE-ALG3-05**（explain 人话，修存量原文外泄）；摘要仍仅 meta/dogfood |
| **W1a-1** 静态几何预检 | 可能更快；版式**逐窗等价** | **不需要** |
| **W1a-2** Ready + 墙钟 | 无（默认路径零行为变化）；有 Key 仍不耗额度 | **不需要**；禁加「已就绪」营销 |
| **W1b** 条件 clone | **拼图成片会变**（少假切条） | **Should**：stale/导出回归（explain 人话已在 W0 完成） |
| **W2** 聚类 / soft-split / vision cohort | 分章/拼图可能变；首跑可能变慢 | **Should**：设置 hint / Help H0 诚实；禁 AI 腔 Wait Tips |
| **W3** scoring cohort | 仅开了「智能排版」的人 | **Should**：scoring hint 补中性「可能提前结束搜索」 |
| **M4 AIR** | 解冻 AI 面 | **整包 UI/COPY** — **非本列车 DoD** |

### 15.3 Must / Should / Nice / 禁止

#### Must（同列车或挡门 · FE-ALG3-*）

| ID | 要求 |
|----|------|
| **FE-ALG3-01** | **禁止**为 Ready/MayCall 解冻 AI 区、能力卡、FS/Wait Tips「升级写作」——服从 VC-ALG3-02/05 与 NAS |
| **FE-ALG3-02** | **禁止**在设置里向普通用户暴露 `prefer_llm_when_ready` / `llm.capability` / clone 门 / `algoV3` 营销 |
| **FE-ALG3-03** | W1b 合码前：盲评+基线；成片可变，COPY 仍中性（不教育「AI 更强了」） |
| **FE-ALG3-04** | `prefer` / `capability` **不进**用户开放 PATCH 白名单；前端勿加对应控件 |
| **FE-ALG3-05** | **W0 必做**：`mosaic_explain._REJECT_LABELS` 补全 `atom_boundary` / `shot_group_cross` / `shot_group_anti_slice` / `near_scene_clone` / `main_ar_mismatch` / `sidebar_min_short_side` / `contract:mix_miss` / `mixed_portrait_is_hero` 的中文人话；「为何没拼」抽屉**不得外泄原始英文 reason**。存量缺陷（§14.3），非 W1b 引入 |

#### Should（跟 W1b / W2 / W3 · FE-ALG3-S*）

| ID | 项 | 挂载波次 | 锚点 |
|----|-----|----------|------|
| ~~**FE-ALG3-S01**~~ | ~~`mosaic_explain` 人话覆盖~~ | **已提升为 Must FE-ALG3-05 · W0** | 见上表（§14.3） |
| **FE-ALG3-S02** | 「智能排版」hint 补中性「搜索可能按时长提前结束」 | **W1a-2 墙钟合入后** 或 W3 | `#studio-cfg-layout-scoring-hint` |
| **FE-ALG3-S03** | 回归 `algorithmStale` / `longshotStale` /「更新并导出」不误亮、不漏拦 | **W1b / W2** | `algorithm_profile.py` · `longshot.js` · shelf/bento |
| **FE-ALG3-S04** | 「场景分析」hint / H0 与 OQ-02 最终口对齐（关 vs cohort/auto） | **W2** | `studio-home-v2.html` · `help-onboarding.js` |

#### Nice

| ID | 项 |
|----|-----|
| **FE-ALG3-N01** | dark/dogfood 展示 `algoV3` 一行（非终端产品面） |
| **FE-ALG3-N02** | 内部仪表消费 rejectFunnelTop（非首页） |

#### 禁止本波动

| ID | 项 |
|----|-----|
| **FE-ALG3-X01** | 改 Wait Tips / FirstSuccess / Help 的 AI 或「升级」话术（VC-ALG3-05） |
| **FE-ALG3-X02** | 解冻 `#v2-settings-zone-ai` 或恢复能力卡首启 |
| **FE-ALG3-X03** | 为本波新建 LLM/能力线框（释放面时由 AIR 解冻） |
| **FE-ALG3-X04** | 为窄屏/手机单独做 ALG-V3 UI（工作台门槛已拦；长图成片变即可） |

### 15.4 精修 · 导出耦合（W1b 回归清单）

```text
新 import（W1b 成片 mosaic 变）
  → 预览直接看到新拼图（无需新按钮）
  → 「为何没拼」须可读（FE-ALG3-05 · W0 已交付）
  → 不必然点亮旧 trip 的 algorithmStale

旧 trip 精修拼图 / 密度 / 精选重排
  → 仍走「更新版面」(/rerender) → longshotStale → 导出拦截
  → ALG-V3 不改该合同；合码后抽检勿误伤
```

| 检查项 | 期望 | 文件 |
|--------|------|------|
| 更新版面后可导出 | 拦截文案仍局部化、非「生成失败」 | `preview-toolbar/longshot.js` |
| 纯改文案 | 不升 longshotStale（Trust 合同） | `init-v3.js` 注释 / longshot 逻辑 |
| 书架重新排版 | 仅真配置/选片过期时亮；勿因摘要字段 alone 假 stale | `algorithm_profile.py` · `bento-stale.js` |
| 单屏 replan | 仍 bump revision；与 W1b 无冲突 | `trip_replan_handlers.py` |

### 15.5 与里程碑挂载

| 里程碑 | FE 义务 |
|--------|---------|
| **M0** | ☑ ACCEPTANCE/IMPL/must-green 已齐；§15 FE 范围已指针；W0/W1a 无新产品 UI 工时（FE-ALG3-05≈0.5 人日纯文案表） |
| **M0.5（W0）** | **FE-ALG3-05 必做**（explain 人话，挡门） |
| **M1a / M1c（W1a-1/2）** | FE-ALG3-01/02/04 回归（确认无解冻、无新开关）；S02 可选 |
| **M1b（W1b）** | S03 回归；盲评问1/3（S01 已在 W0 关闭） |
| **M2** | S04；S03 再跑 |
| **M3** | S02 若未做则补；开 scoring cohort 时强制 |
| **M4** | AIR 整包 UI — 非 ALG-V3 |

### 15.6 Copy 风险速查（默认面）

| 想写的 | 判定 |
|--------|------|
| AI / LLM / 写作引擎 / 升级配置 Key | **禁** |
| 识图 / 场景分析 / 拼图 / 分章（中性） | 可用 |
| 「有 Key 更精彩」「引擎已就绪」面向终端 | **禁**（Ready 仅 meta） |
| 「为何没拼：同场景过近，未做成切条」类 | **鼓励**（FE-ALG3-05） |
| 「为何没拼：near_scene_clone（penalty=0.82）」类原始英文 | **禁**（存量缺陷，W0 修） |

---

## 16. 修订历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1.0 | 2026-08-01 | Draft 供审核 |
| v0.2.0 | 2026-08-01 | 五席 Conditional Go · Must-Fix 回写 · 三态合同 · W1a/b 拆分 |
| v0.2.1 | 2026-08-01 | 增补 §15 FE 同步矩阵（上下游触点 · 分波 UI · Must/Should/禁止） |
| **v0.3.0** | 2026-08-01 | **开发负责人代码复核回写（DEV-01～06）**：新增 §14 证据台账；D5 开关清单单源 + AC-32 挡门；`probe_llm_ready()` 只读探测 + AC-07；§3.2.1 capability 真值表 + AC-06；MCS 重定位（删 B3 / 拆 B2a·B2b / B1 降 W3）+ AC-20 改口径；W1a 拆 W1a-1/W1a-2；explain 人话由 S01 升 Must FE-ALG3-05 |
| v0.3.0+M0 | 2026-08-01 | **开发前准备（不改代码）**：拆 ACCEPTANCE（钉 AC-21 白名单）· IMPLEMENTATION（W0/W1a 任务表）· must-green nodeids · 两份 baseline 占位 JSON |
| **v0.3.1** | 2026-08-02 | **产品口锁定**：A5 默认 first / EMA·medoid opt-in；VC-04 主尺 `patternId`（阈 2）；C5 holdback 默认 off；fine_craft 不绑 vision（cohort SSOT）；竖单本波不改默认 · [产品锁](./acceptance-records/alg3-product-lock-a5-c4-fc-portrait-2026-08-02.md) |

---

**下一步**

1. ~~产品确认 A5 / C4–C5 / fine_craft / 竖单~~ → **已锁**（2026-08-02）。  
2. 人评：W1b / A4 盲评 PENDING（挡宣称，不挡 A5/C4/C5 默认-off 编码）。  
3. 可编码：A5 opt-in · C4 口径/遥测 · C5 flag 骨架（均默认不成片）。  
4. 本波不做：fine_craft→vision；竖单默认策略；竖单×`layoutDensity` 分档。
