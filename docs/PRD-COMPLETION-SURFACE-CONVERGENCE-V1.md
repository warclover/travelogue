# Travelogue · 完工表面积收敛 V1 产品需求文档（PRD）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue |
| **文档版本** | **v0.2.2-CSC** |
| **状态** | **Conditional Go · 九席 + 根因 + AppConfig 布尔面决议已写入** · 根治主轴 = Happy Path Recipe；W0 交付 Recipe 初稿后方可称基线完成 |
| **特性代号** | **CSC**（Completion Surface Convergence · 完工表面积收敛） |
| **一句话代号** | 「别再做更强的排版引擎；收成更窄、更稳、更可解释的完工器」 |
| **性质** | **纲领 PRD**：战略诊断、问题账本、收敛波次与否决闸；**非**新功能面 PRD |
| **触发来源** | 2026-07-22 产品/架构复盘；九席评审见纪要 |
| **前置条件** | [CHARTER.md](./CHARTER.md) 有效；`run_trip` 已统一；不重开 ARCH-OPT P0 / AAD Utility / FTT 完成状态机 |
| **依据原则** | [CHARTER.md](./CHARTER.md) §7 |
| **关联文档** | [PRD-FINISH-THIS-TRIP-V1.md](./PRD-FINISH-THIS-TRIP-V1.md) · [PRD-ARCH-OPTIMIZATION.md](./PRD-ARCH-OPTIMIZATION.md) · [PRD-ARCH-ALGO-DEEPENING-V1.md](./PRD-ARCH-ALGO-DEEPENING-V1.md) · [TECH-ARCHITECTURE.md](./TECH-ARCHITECTURE.md) · [AGENT-ARCHITECTURE.md](./AGENT-ARCHITECTURE.md) |
| **评审记录** | [completion-surface-convergence-v1-review-2026-07-22.md](./acceptance-records/completion-surface-convergence-v1-review-2026-07-22.md) |
| **根因 / 根治** | [csc-root-cause-cure-2026-07-22.md](./acceptance-records/csc-root-cause-cure-2026-07-22.md)（**RES-CSC-ROOT-*** · 优先于逐项还债叙事） |
| **实施清单** | `IMPLEMENTATION-COMPLETION-SURFACE-CONVERGENCE-V1.md`（**待建** · 本文 §9 为任务卡） |
| **验收** | 建议 W0 后拆 `ACCEPTANCE-COMPLETION-SURFACE-CONVERGENCE-V1.md`；本文 §10 为合同源 |
| **更新日期** | 2026-07-22 |

> **v0.2.2 相对 v0.2.1（AppConfig 布尔面决议）**
>
> - 固化 **97 默认 True / 53 默认 False** 的产品含义：False 是防火墙，不是待开启清单  
> - 写入现状隐患、四档分型、优化序与明确否决（禁一键全开 / 禁无盘点批量关 True）  
> - 详见 §0.0.1；字段枚举仍以产线 `AppConfig()` 为准（评审时可脚本重扫）

> **v0.2.1 相对 v0.2.0（根因复核）**
>
> - 产线复核确认：`AppConfig` 布尔默认 True ≈ **97/150**；`StudioProfile` 只管编排薄面  
> - **根治主轴**：Happy Path Recipe Registry（唯一默认启用合同 + L1 预算 + UI 派生）  
> - W0/W1 成功标准升级为「Recipe 快照可测」，而非仅说明文 / 藏设置  
> - 详见 [csc-root-cause-cure-2026-07-22.md](./acceptance-records/csc-root-cause-cure-2026-07-22.md)

> **v0.2.0 相对 v0.1.0（九席决议入正文）**
>
> - **D-CSC-01 重写**：Happy Path = 冻结的 `StudioProfile.studio_default()`，不新建平行 Profile 类型  
> - **D-CSC-04/05 修订**：L0 运维根 vs L1≤10；legacy 用结构化债务表 ceiling，禁用全文 rg −30% KPI  
> - **§8 分层闸门**：存量祖父条款 + 新增才走完整盲测  
> - **波次修订**：W1 含设置/Advanced UI；W2b 让位 AAD；W2c 改棘轮  
> - **新增** G-CSC-WIP · 测评三题 · OQ 全关  
> - **BLK-CSC-01～08** 见评审纪要，已吸收

---

## 0. 一句话

在**不否定杂志感算法深度**的前提下，把 Travelogue 从「高度可配置的编辑算法平台」收敛为「默认路径更窄、更稳、更可解释的完工器」——**根上**建立唯一 **Happy Path Recipe**（默认启用集合 + L1 预算 + 设置派生），并以 facade / 债务清退 / curate 棘轮为执行器，而不是六场并列还债。

---

## 0.0 根因与根治（v0.2.1 · 优于症状清单）

| 根因 | 产线证据 | 根治动作 |
|------|----------|----------|
| 无单一默认合同 | Profile 薄；AppConfig 默认 True×97 | **Happy Path Recipe** 为 SSOT |
| 加性配置 / 默认开文化 | example 23 根；Phase 加开关 | L0/L1 预算；进默认须改 Recipe 快照 |
| 设置=白名单镜像 | expose/PATCH/HTML 并联 | UI **只渲染** Recipe.l1_keys |
| 出口 strangler + 空 facade | mobile→legacy；`__all__=[]` | Recipe.layout_exit + api facade |
| 编排过粗 / 文档无状态机 | curate 黑盒；PRD 自由状态字 | stage 合同对齐 AAD；文档三态 |

**RES-CSC-ROOT-01～04** 与最小切片 A/B/C 见根治文。未落地 Recipe 快照前，**不宣布 W1 Done**。

### 0.0.1 AppConfig 布尔面（97 True / 53 False）· 决议

**诊断时点口径**（可用脚本对 `AppConfig()` 重扫校准）：布尔字段约 **150**；默认 **True ≈ 97**；默认 **False ≈ 53**。

| 集合 | 产品含义 | CSC 态度 |
|------|----------|----------|
| **97 × 默认 True** | 今日静默生效的成册能力面；真相不在 Profile | **隐患主体**：不可见、难归因、Phase 易再加 |
| **53 × 默认 False** | 实验 / 昂贵 / 破坏默认路径的闸门 | **防火墙**：维持关是正确默认；**不是**待开启 backlog |

**保持现状是否算隐患？**  
算——但是**治理型隐患**（默认可漂移、表面积再 sprawl、误开成本极高），不是「不修就会立刻不可用」。53 个 False 继续关着**不构成**「能力没开完」的产品债。

**现状具体风险（写进账本）**

| ID | 风险 |
|----|------|
| **P-CSC-17** | 默认真相不可陈述：成册 = 97 个 True 的隐式拼盘 |
| **P-CSC-18** | 新增 `enabled: True` 进默认几乎零摩擦，L1 无预算 |
| **P-CSC-19** | 「关着=表面小」是错觉：False 仍占配置/文档认知面 |
| **P-CSC-20** | 误开 Danger 闸（如 G1 / allow_drop / LSE 总闸 / force_recluster）会陡变路径与成片 |

**四档分型（W0 Recipe 盘点必用）**

| 档 | 含义 | 典型归属 |
|----|------|----------|
| **Happy Path** | 默认成册必需；进 Recipe.capabilities ON | 现行主干（如 mosaic/LTE/bookends 等，以盘点为准） |
| **Advanced** | 默认关；仅设置高级区 | scoring、output_recipe 等 |
| **Research** | 仅 admin/env；不进用户档 example | LSE CAP、VL rerank、mllm 等 |
| **Danger** | 改默认须双人评审 + 不得进常用 UI | `g1_confirm_structure`、`mosaic.allow_drop`、`clustering.force_recluster`、LSE 总闸等 |

**优化序（决策级 · 禁止颠倒）**

1. **先可见**：导出并单测锁定「默认启用快照」（Recipe 切片 A）；行为可暂不变  
2. **再分档**：W0 把 150 布尔标成上表四档（含 53 个 False 的 Research/Danger 标注）  
3. **卡住入口**：新增默认 True / 新增常用设置控件 → 必须改 Recipe；否则 CI 失败  
4. **有证据再关 True**：禁止运动式把 97 个 True 批量改 False；关项须狗粮/盲测不伤完工与敢发  

**明确否决**

| 否决 | 原因 |
|------|------|
| 将 53 个 False **一键改 True** | 路径变长、成本暴涨、版式无证明漂移；撕掉防火墙 |
| 无盘点把 97 个 True **批量改 False** | 无祖父条款会伤成册质量 |
| 以「False 比例升高」为成功 KPI | 激励假收敛；成功应以 Recipe 可陈述 + L1 预算为准 |

**与根治主轴的关系**：布尔面治理是 Recipe 的**第一盘点对象**；不另开平行专项。字段枚举以产线为准，评审讨论记录可附脚本输出，不必把 150 行路径全部粘进本 PRD。

---

## 0.1 读者指南

| 角色 | 读什么 |
|------|--------|
| 产品 | §1–3 · §5 · OUT · 与 FTT 边界 · 测评三题 |
| 架构 / 开发 | §4 · §6–8 · §9 · G-CSC-WIP |
| 前端 / UI | §5.3 设置库存 · F-CSC 轻合同 |
| 测试 | §10 · W0 基线产物 |
| 文档治理 | §7.3 |

### 0.2 本 PRD 的角色

| 角色 | 含义 |
|------|------|
| **诊断账本** | 固化复盘与九席共识 |
| **纲领 PRD** | 收敛原则、波次、否决闸、WIP |
| **非重复规格** | 不重写 FTT / ARCH-OPT P0 / AAD 公式 |
| **否决闸** | 扩大默认集合无闸门证据、新增 L1 根不替换、admin 进主 CTA、运动式大重构 → 默认否决 |

### 0.3 与相邻 PRD 的边界

| 文档 | 本 PRD 做什么 | 本 PRD 不做什么 |
|------|---------------|-----------------|
| **FTT** | 提供更窄默认工程底座与设置面 | 不重写完成状态机 / 成功面 / 14 日回流 |
| **ARCH-OPT** | 承接表面积相关后续 | 不重开写锁等 P0 |
| **AAD** | facade 锁进口；W2b 验收对齐 | 不并行大拆 `curate.py`；不规定 Utility/beam |
| **LSE / MCS / LTN** | 默认外置 / Advanced | 不改专项字段合同 |

### 0.4 范围承诺与 WIP

| 承诺 | 说明 |
|------|------|
| **减法优先** | 成功 = 默认更短、可见旋钮更少、文档更好找 |
| **分波交付** | W0→W1→W2a→（W2b 对齐）→W2c 棘轮→W3；禁止大爆炸 |
| **默认零 intentional 版式变更** | 结构收敛须 golden/replay 或 DIFF 表 |
| **G-CSC-WIP** | 与 FTT/体验冲突 → 体验优先；与 AAD 同改 curate → AAD 优先；单迭代勿多波齐开 |
| **两本账** | 对外完工/敢发/可解释；对内 L1 根数、债务表、facade、文档状态 |

---

## 1. 背景与战略诊断

### 1.1 复盘结论（维持）

复杂度配得上杂志感成册；短板是**表面积失控**——默认简单性靠「开关默认关 + 文档纪律」，而非更小运行时/认知表面。  
九席确认：该判断成立，且用户痛点优先在**设置/话术/入口**，其次才是包结构。

### 1.2 体量与产线快照（评审日冻结意向）

| 项 | 约略 / 事实 |
|----|-------------|
| 产品源码 | ~17–20 万行 |
| `config.yaml.example` 顶层键 | **23** |
| `StudioProfile.studio_default` | 已存在（clustering / editorial / export auto…） |
| `curate.py` / `studio_pipeline.py` | ~1938 / ~1127 行 |
| `layout_engine.__all__` | `[]` |
| curation→layout_engine | ~20 import（多数经 adapter） |
| 原始 `\blegacy\` 命中 | ~236（**不可直接作 KPI**） |

### 1.3 核心张力

```text
产品承诺：选相册 → 出游记 → 分享
工程现实：深算法平台 + 宽配置 + 多 Phase 文档
CSC：深度留在内部/Advanced；默认只暴露最小充分可见面
```

---

## 2. 原则与冻结决策

### 2.1 原则（维持 CSC-PR-01～08）

完工器优先 · 默认路径一等公民 · facade levelling · 债务清退预算 · 配置是产品 · 文档 SSOT · 最小充分集 · Studio 不做研究控制台。

### 2.2 冻结决策（九席定案）

| ID | 决策 | 状态 |
|----|------|------|
| **D-CSC-01** | Happy Path **运行时身份** = `HappyPathRecipe(recipe_id=studio_default)`；其中 orchestration 字段承接现有 `StudioProfile.studio_default()`；**不新建**平行 Profile 类型；能力 ON/OFF 与 L1 键进 Recipe | **Accepted · v0.2.1 强化** |
| **D-CSC-02** | `layout_engine` 公开符号经 `api.py`/`__all__` 冻结；含对 `compose_trip` 的 **facade 再导出** | **Accepted** |
| **D-CSC-03** | `run_curate` coordinator 化：**以 AAD 为准**；CSC 做验收对齐或薄切片，不独开大拆 | **Accepted** |
| **D-CSC-04** | 配置分 **L0 运维根** / **L1 结果旋钮（≤10）** / L2 配方 / L3 research；≤10 **只约束 L1** | **Accepted** |
| **D-CSC-05** | legacy/shim **结构化债务表** + 绝对 ceiling（只降不升）；禁止全文 rg −30% KPI | **Accepted** |
| **D-CSC-06** | 文档入口：CHARTER → TECH 现行 → 活跃 ADR → ACCEPTANCE 索引 → FTT / CSC | **Accepted** |
| **D-CSC-07** | **新增/扩大**默认能力须过 §8 完整闸；**存量**走 W0 祖父盘点，不强制重盲测 | **Accepted** |
| **D-CSC-08** | W1 必须含 Settings/Help/Advanced **可见面库存与隔离**（前端一等交付） | **Accepted** |
| **D-CSC-09** | 53 个默认 False = **防火墙**，不是待开启清单；默认保持关，晋升须走 §8 + 四档评审 | **Accepted · v0.2.2** |
| **D-CSC-10** | 布尔优化序固定为：快照可见 → 四档分型 → CI 卡住新增默认 True → 有证据再关 True | **Accepted · v0.2.2** |
| **D-CSC-11** | 禁止以 False 比例或「全开能力」为 CSC 成功故事 | **Accepted · v0.2.2** |

---

## 3. 目标 / 非目标

### 3.1 目标

| ID | 目标 |
|----|------|
| **G-CSC-01** | ≤3 份现行文档能讲清默认完工路径 |
| **G-CSC-02** | Happy Path 启用集合可快照测试；Advanced 可视隔离 |
| **G-CSC-03** | facade 外无新增深 import；curate 边界可测（对齐 AAD） |
| **G-CSC-04** | L1 根数与债务表可 CI 下降 |
| **G-CSC-05** | 首趟路径不依赖 admin；测评三题通过 |

### 3.2 非目标

OUT-01～06 维持（无模板商城/微服务/无证据砍质量/不改 CHARTER/不全库物理删文档等）。  
**新增 OUT-07**：不把全文 `legacy` 字符串竞赛当作成功故事。  
**新增 OUT-08**：CSC 不独吞 `curate.py` 大重构所有权。

### 3.3 成功指标

| 指标 | W0 钉基线 | 目标 |
|------|-----------|------|
| L1 结果旋钮根数 | 键表盘点 | ≤10 |
| 结构化债务表条目 | 冻结 | ceiling 只降不升；按批删除 |
| facade 外深 import 新增 | 0 容忍 | CI 红灯 |
| 设置 L1 控件（UI） | 库存盘点 | W1 后可陈述「常用/高级」分层 |
| 测评：解释默认路径 | — | ≤3 分钟且无 LSE/MCS 黑话 |
| 测评：首趟设置 L1 点击 | W0 建议 ≤2 | 写入 ACCEPTANCE |
| 测评：首趟路由无 admin | — | 0 次 |
| FTT 漏斗 | — | CSC 不另设；不阻挡 |

---

## 4. 问题账本（P-CSC-*）

P-CSC-01～14 与 S-01～05 **维持 v0.1**（见评审纪要未推翻）。  
九席补充强调：

| ID | 增补 |
|----|------|
| **P-CSC-15** | 设置/帮助/Advanced 可见面未计量，后端收敛无法单独改善用户体感 |
| **P-CSC-16** | 原始 legacy 命中含叙事噪声，错误 KPI 会激励删注释而非删路径 |

---

## 5. W1 · Happy Path（冻结 studio_default + 可见面）

### 5.1 需求

| ID | 需求 |
|----|------|
| **R-CSC-HP-01** | 将现行 `StudioProfile.studio_default()` 标为唯一 Studio 导入主路径 Happy Path；变更须评审 + 快照测更新 |
| **R-CSC-HP-02** | CLI 默认与 Studio 差异写清（`cli_default` vs `studio_default`）；禁止静默漂移 |
| **R-CSC-HP-03** | 用户短文：「默认启用 / 明确不启用」；禁止 LSE/MCS/Profile 黑话 |
| **R-CSC-HP-04** | Advanced（LSE flags、模板治理、research）与主 CTA 隔离 |
| **R-CSC-HP-05** | **设置面库存**：控件 → L0/L1/L3 映射；常用/高级分层落地 |

### 5.2 UI 轻合同（F-CSC）

| ID | 内容 | 挡门 |
|----|------|------|
| **F-CSC-1** | 设置：常用 vs 高级（高级默认折叠/二次展开） | W1 |
| **F-CSC-2** | 主路径无 admin 入口；admin 保持 internal URL | W1 |
| **F-CSC-3** | Happy Path 短文挂帮助/空态可发现位置（不抢主 CTA） | W1 |

可用简单对照表或叠加现网 Bento，不强制整站重设计。

### 5.3 验收要点

- 导入→成稿→导出不依赖理解 23 配置根或 admin 页。  
- Profile 启用集合快照测试绿。  
- 测评三题（§10.2）通过。

---

## 6. W2 · 结构收敛

### 6.1 `layout_engine` 公共 API

| ID | 需求 |
|----|------|
| **R-CSC-API-01** | 公开：`plan_chapter_screens` · `attach_screens_to_chapters` · **`compose_trip`（再导出）** · 可选 `explain_decision` |
| **R-CSC-API-02** | CI 禁止 web/services/curation **新增**对 planner/mosaic 内部模块的 import |
| **R-CSC-API-03** | `layout_engine/api.py` 或等价为唯一推荐入口 |

### 6.2 拆 `run_curate`（对齐 AAD）

| ID | 需求 |
|----|------|
| **R-CSC-CUR-01** | 子链可识别；以 AAD 交付为准 |
| **R-CSC-CUR-02** | CSC 独有：禁止继续往 `curate.py` 堆新业务（棘轮） |
| **R-CSC-CUR-03** | 若 AAD 未动：仅允许薄 coordinator 切片，不做 Utility/beam |

### 6.3 Studio pipeline（棘轮，非大拆）

| ID | 需求 |
|----|------|
| **R-CSC-WEB-01** | 禁止净增业务逻辑进 `studio_pipeline.py`（实施清单钉度量） |
| **R-CSC-WEB-02** | 机会主义下沉 services/handlers；不设「一次拆到只剩编排」DoD |
| **R-CSC-WEB-03** | admin 不进默认首页主路径（与 F-CSC-2 一致） |

---

## 7. W3 · 清退与文档 SSOT

### 7.1 债务表清退

| ID | 需求 |
|----|------|
| **R-CSC-LEG-01** | W0 产出结构化债务表（路径/再导出/双路径模块）并设 ceiling |
| **R-CSC-LEG-02** | 按批删除无调用 shim；旧引擎仅留 golden 对照最小面 |
| **R-CSC-LEG-03** | 新功能写入债务路径 → CI 失败 |

### 7.2 配置分层

| 层 | 内容 | 可见性 |
|----|------|--------|
| **L0 运维根** | 如 `trips_dir` / `llm` / `ffmpeg` / `geocode`… | 安装/本地配置；**默认不进设置 UI** |
| **L1 结果旋钮** | ≤10 根真正影响成册结果的键 | 用户档 example + 设置「常用/高级」 |
| **L2 配方** | travel / family / citywalk 等 | 可选 |
| **L3 research** | 深参与实验旗标 | 第二文件或 env；不进主 example |

### 7.3 文档状态机

`active | superseded | archive`。  
W3c：**先** README 入口与状态标注机制 + **≥5 篇**示范，不要求一次清库。

---

## 8. 最小充分集纪律（分层）

### 8.1 存量（祖父条款）

W0 盘点「当前默认已启用能力」清单 → 标 `grandfatherClauses`；**不强制**本波重做分享意愿盲测。  
若要从默认**移除**，走产品评审 + 回归，不 silently。

### 8.2 新增 / 扩大默认集合（G-CSC-MIN 完整版）

须同时满足：holdback 或 dogfood 协议；主指标=分享意愿或首趟完工；失败可解释；可关且不影响 Happy Path 合同；L1 预算替换而非叠加。

不满足 → 仅 research / Advanced。

---

## 9. 波次任务卡

| 波次 | 主题 | 主要产出 | 挡门 |
|------|------|----------|------|
| **W0** | **Recipe 初稿 + 基线** | HappyPathRecipe 草案（可先只读快照）· 债务表 · L0/L1 键表 · 设置库存 · DIFF 空表 · 测评数字 | Conditional Go（已） |
| **W1** | **Recipe 挂载 + UI 派生** | 主路径读 Recipe · expose/常用设置 ← l1_keys · 用户短文 · F-CSC-1/2/3 | Recipe 快照单测绿 |
| **W2a** | LSE facade | api/`__all__` + lint | 零 intentional 版式差或 DIFF |
| **W2b** | curate 对齐 | AAD 证明或薄切片 + 禁堆料棘轮 | G-CSC-WIP |
| **W2c** | pipeline 棘轮 | 度量 + 机会主义抽取 | 主路径 e2e 绿 |
| **W3a** | 债务删除批 | ceiling CI | 只降不升 |
| **W3b** | 配置分层落地 | 用户档 L1≤10 · research 外置 | 迁移说明 |
| **W3c** | 文档 SSOT | 入口 + ≥5 篇状态示范 | D-CSC-06 |

---

## 10. 验收合同

### 10.1 工程 AC

| ID | 验收项 |
|----|--------|
| **AC-CSC-01** | `studio_default` 启用集合快照单测 |
| **AC-CSC-02** | facade 外新增深 import → CI 失败 |
| **AC-CSC-03** | W0 基线产物入库；债务 ceiling 脚本可跑 |
| **AC-CSC-04** | **L1** 键表 ≤10（明确排除 L0） |
| **AC-CSC-05** | curate：AAD 对齐证明 **或** ≥3 子步骤可测薄边界 + 禁堆料棘轮 |
| **AC-CSC-06** | 主路径 e2e 不依赖 admin |
| **AC-CSC-07** | docs README 现行区含 CSC 与边界说明 |
| **AC-CSC-08** | W2 结构改动附 golden/replay 或 DIFF |
| **AC-CSC-12** | `studio_pipeline` 禁堆料棘轮有度量与 PR 检查说明 |

### 10.2 产品 / 测评 AC

| ID | 验收项 |
|----|--------|
| **AC-CSC-09** | Happy Path 短文可支撑 ≤3 分钟复述（无黑话） |
| **AC-CSC-10** | Advanced 不影响首趟主 CTA（F-CSC） |
| **AC-CSC-11** | ≥5 篇文档完成状态标注（机制示范） |
| **AC-CSC-13** | 首趟狗粮：L1 设置点击 ≤ W0 钉定阈值（建议 2） |
| **AC-CSC-14** | 首趟路由/HAR：0 次 admin |

### 10.3 明确不验

算法分上升；文档总行数绝对值；全文 legacy 字符串降幅。

---

## 11. 风险、OQ、否决

### 11.1 风险

| ID | 风险 | 缓解 |
|----|------|------|
| **RK-01** | 做成大重构运动 | 分波、棘轮、WIP |
| **RK-02** | 与 AAD 抢 curate | W2b 让位 |
| **RK-03** | 高级用户找不到项 | L3/高级可发现说明 |
| **RK-04** | 归档误伤 | 只标状态，先示范 |
| **RK-05** | 闸门主观化 | 分层 + 证据模板 |
| **RK-06** | 只改后端用户无感 | D-CSC-08 强制 W1 UI |

### 11.2 OQ（已关闭）

| ID | 定案 |
|----|------|
| **OQ-CSC-01** | 运行时 = `studio_default`；叙事名「这一趟默认路径」 |
| **OQ-CSC-02** | 结构化债务表 + 绝对 ceiling |
| **OQ-CSC-03** | `compose_trip` facade 再导出 |
| **OQ-CSC-04** | ≤10 = L1 only |
| **OQ-CSC-05** | AAD 优先 curate；W2a 可并行 |

### 11.3 否决模板

1. 扩大 Happy Path 无 §8.2 证据  
2. 新增 L1 根不替换旧根  
3. 往 `curate.py` / `studio_pipeline.py` 净增业务（超棘轮）  
4. 新 PRD 实为「默认新能力」而非收敛  
5. admin 链入首趟主 CTA  
6. 以全文 legacy rg 降幅宣称胜利  

---

## 12. 里程碑与宣布用语

| 里程碑 | 含义 |
|--------|------|
| **Conditional Go** | 九席通过；v0.2 已回写 |
| **W0 Done** | 基线产物入库 |
| **W1 Done** | Happy Path 冻结 + 设置分层 + 测评三题 |
| **W2 Done** | facade + curate 对齐/棘轮 + pipeline 棘轮 |
| **W3 Done** | 债务 ceiling + L1≤10 + 文档状态示范 |
| **CSC V1 Closed** | acceptance-records 结案 |

**可说**：默认完工路径已收敛；可见旋钮与文档入口进入可计量清退。  
**不可说**：排版算法全面升级；防搁置已验证（FTT）；legacy 字符串下降 XX%。

---

## 13. 附录 A · 复盘建议映射

| 建议 | 落点 |
|------|------|
| Happy Path 一等公民 | §5 · D-CSC-01（studio_default） |
| 拆 run_curate | §6.2 · 让位 AAD |
| layout_engine API | §6.1 |
| 双路径清退 | §7.1 债务表 |
| 收缩配置 | §7.2 L0/L1 |
| Studio 压表面 | §5.3 · §6.3 |
| 文档 SSOT | §7.3 |
| 最小充分集 | §8 分层 |

## 14. 附录 B · 最务实优先级（评审合成）

| 优先级 | 动作 |
|--------|------|
| P0 | W0 可 CI 基线 |
| P0 | W1 冻结 studio_default + 砍/藏设置可见面 |
| P1 | W2a facade 锁进口 |
| P1 | 文档入口状态标注 |
| P2 | 债务表删 shim；pipeline 棘轮 |
| P2 | curate 大拆归 AAD |

---

## 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1.0-CSC | 2026-07-22 | 初稿 |
| v0.2.0-CSC | 2026-07-22 | 九席 Conditional Go 入正文；OQ 全关；BLK 吸收；波次与测评口径修订 |
| v0.2.1-CSC | 2026-07-22 | 根因复核：Recipe Registry 为根治主轴；W0/W1 成功标准升级 |
| v0.2.2-CSC | 2026-07-22 | AppConfig 97/53 布尔面：防火墙含义、四档、优化序与否决写入 §0.0.1 |
