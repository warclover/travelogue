# Travelogue · Phase 17 产品需求文档（PRD · 智能排版引擎）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue |
| **文档版本** | v0.17.6-PHASE17 |
| **状态** | **有条件通过** · 2026-06-07 跨职能 + CTO/算法 + 前端/页面评审已纳入 |
| **评审纪要** | 本文 §16（产品/算法/架构/需求/UX/交互）；§17（CTO/算法专家 v0.17.4 + 前端/页面 v0.17.5） |
| **Phase 17 代号** | 「智能排版引擎」（Layout Strategy Engine，**LSE**） |
| **前置条件** | Phase 16 LTE 默认路径稳定（`read_templates_from_lte=true`）；Phase 15 MCS S1–S3 已落地；`layout_engine=screens` 与 `ScreenLayoutPlannerState` 节奏配额可用 |
| **关联文档** | [PRD-PHASE16-layout-template-engine.md](./PRD-PHASE16-layout-template-engine.md)、[DESIGN-PHASE15-mosaic-system.md](./DESIGN-PHASE15-mosaic-system.md)、[PRD-FINE-CRAFT-LAYOUT-DENSITY.md](./PRD-FINE-CRAFT-LAYOUT-DENSITY.md)、[PRD-ALGORITHM-OPTIMIZATION-V2.md](./PRD-ALGORITHM-OPTIMIZATION-V2.md)、[智能排版.md](./智能排版.md)、[AGENT-ARCHITECTURE.md](./AGENT-ARCHITECTURE.md)、`travelogue/curation/screen_planner_stages.py`、`travelogue/curation/mosaic/`、`travelogue/templating/` |
| **更新日期** | 2026-06-07 |

> **定位**
>
> Phase 16 将拼图/组屏 **模板几何** 升格为 LTE 一等公民。Phase 15 将 **多候选择优** 收敛为 MCS。但 **排版决策本身**——stage 流水线、节奏配额、beam 搜索、打分权重、用户密度意图、决策可解释与运营调参——仍散落在 `config.yaml`、Python 常量、`screen_planner.py` / `mosaic/scorer.py` 多处，**无统一策略注册、无治理后台、无标定闭环**。
>
> Phase 17 将 **智能排版决策层** 升格为 **排版策略引擎（LSE）**：统一管理 Strategy Pack（策略包）、运行时调参、决策日志与回归门禁；**复用** `travelogue/templating/` 治理平台与 Studio `template_admin_handlers`，**不另造** LayoutStrategyAdmin。
>
> **与 LTE 分工**：LTE 回答「这个 pattern 几何是否合法」；LSE 回答「此刻该不该出 mosaic-5、权重多少、九宫配额够不够」。**二者并列，不可合并。**
>
> **产品原则（冻结 · P17 章程）**：**最小用户干扰 · 后台自动运行 · 直接给结果**。用户上传相册后即获得成稿；排版增强均在 `run_curate` 管线内静默完成。C 端不新增排版工作台、不要求逐步确认；Studio 策略后台仅服务运营/研发治理，不对普通用户暴露。
>
> **交付三分法（评审冻结）**：
>
> - **P17-Core** — Phase 17 **完成**判定线（W1–W4 必做）
> - **P17-Plus** — 同 Phase 内 **资源允许**再做（不阻断发布）
> - **P17-B / P18** — 明确 **不在 Core 完成条件内**

---

## 1. 背景与问题

### 1.1 Phase 16 之后仍存在的结构性问题

| ID | 问题 | 工程表现 | 用户/运营体感 |
|----|------|----------|---------------|
| **P17-P-01** | 策略定义分散 | `layout.scoring`、`mosaic.*`、`screen_layout_state` 阈值、`mixed_proximity_seconds` 等跨 5+ 模块 | 调参靠改 config + 发版，难 A/B |
| **P17-P-02** | 打分口径割裂 | layout 加性、`mosaic` 乘性惩罚、封面 v2 加性 logit 三套模型 | 同一因子名权重不可比、解释误导 |
| **P17-P-03** | 决策不可观测 | mosaic 有部分 decision log；stage 级 reject 原因分散在代码分支 | 「为何全是 portrait-3」无法运营解释 |
| **P17-P-04** | 无策略版本化 | `scorer_version` 存在，但无统一 `strategyId` + `weights_hash` 快照 | 同 trip 重跑难对齐、审计缺失 |
| **P17-P-05** | 用户意图映射隐式 | `layoutDensity`（hero_first/collage_first）硬编码在 `layout_density.py` | 产品旋钮与算法参数断层 |
| **P17-P-06** | 调参无治理 | 权重在 `config.yaml` 直改，无双人审批、无回滚 revision | 误调权重直接影响全量成稿 |
| **P17-P-07** | 与 MCS 边界名实不符 | `screen_planner` God 文件仍兼 stage + state + 部分打分入口 | 新功能不知落点，测试域模糊 |
| **P17-P-08** | 标定闭环缺失 | 算法 V2 Phase D（pairwise 标定）未接入排版权重 | 「调教算法」停留在手工试错 |
| **P17-P-09** | 混排分配次优 | 窗内 asset↔slot 贪心 `try_order_for_pattern` | 竖进宽格、人脸裁切、混排高发缺陷 |
| **P17-P-10** | 裁切未用显著性 | `focalPoint` 有值但打分未统一 `salient_retention` | 宽槽横图、hero 窄槽肉眼裁切差 |
| **P17-P-11** | 杂志节拍缺失 | 仅有单窗/单章最优，无全 trip **叙事节拍曲线** | 成稿「均匀机器感」，不像相册书/回忆短片 |
| **P17-P-12** | 跨屏色调未启用 | `tone_continuity` / `luminance_continuity` 权重常为 0 | 卷轴阅读色块跳跃 |
| **P17-P-13** | 段内序未优化 | [智能排版.md](./智能排版.md) Layer 1.5 规划未落地 | 同日内人物/风景主题乱跳 |
| **P17-P-14** | 用户纠偏未回流 | `replan_screen` / inline-edit 有行为无聚合 | 无法从真实使用中自动改进策略 |

### 1.2 与 Phase 16 / Phase 15 非目标的关系

| 上游 Phase | 已解决 | 留给 P17 |
|------------|--------|----------|
| **P15 MCS** | 候选生成、乘性打分、段内 beam、self-heal 契约 | 策略收敛与统一日志，**不重写** beam 架构 |
| **P16 LTE** | pattern YAML、几何校验、模板 lifecycle、`overrides.disable` | LSE **消费** LTE，**不定义**槽位拓扑 |
| **P14 版面密度** | `trip.intent.layoutDensity` 三档 UI | LSE 将意图映射为 **density profile**，可配置可审计 |

### 1.3 设计讨论中已拍板的前置认知（本文档约束）

| ID | 认知 | 对 LSE 的要求 |
|----|------|---------------|
| **D-P17-01** | LSE ≠ LTE；LSE 管 **决策**，LTE 管 **几何** | MCS 经 `lte_adapter` 读模板；LSE 经 `lse_adapter` 读策略，禁止 curate 直读散落 YAML |
| **D-P17-02** | Editorial Layer 不归 LSE | folio/breath/封面/章 hero 在 MCS 之后只读 `screens[]`（D-MCS-07） |
| **D-P17-03** | 结构用 Git，参数用 Runtime | stage 顺序、硬阈值分档表 → Strategy Pack GitOps；weights/penalties → runtime 双人审批 |
| **D-P17-04** | 算法代码不可后台编辑 | beam 实现、stage 逻辑、特征定义绑定 `algorithm_version`，仅研发发版 |
| **D-P17-05** | 确定性 + fail-open 不变 | 同 trip + 同 strategy revision → 同 screens；超时 → `legacy_segment` |
| **D-P17-06** | 用户意图 ≠ 算法裸参数 | C 端/精细制作只暴露 `layoutDensity` 等语义旋钮，不暴露 20 个 weight 滑块 |
| **D-P17-07** | **零步排版** | 所有 LSE 能力默认在 curate 内自动执行；用户无需逐步确认 pattern/槽位 |
| **D-P17-08** | **隐式反馈_only** | 从 replan、删屏、调序等**已有**编辑行为沉淀信号；不新增「请为排版打分」类交互 |
| **D-P17-09** | **对标相册书而非社交模板** | 借鉴 Shutterfly/Mixbook/Apple Memories 的**自动节奏**；不引入 Reels 竖屏拖拽拼版心智 |
| **D-P17-10** | **增强走特征层** | 新能力以 `LayoutFeatures` 因子 + Strategy Pack 权重注入；避免散落魔法常数 |

### 1.4 业内对标与引入策略（摘要）

| 业内能力来源 | 可借鉴点 | P17 引入形态 | 用户可见 |
|-------------|----------|--------------|----------|
| **相册书（Mixbook/Shutterfly）** | 页型节奏、张数分档配额、hero↔网格交替 | `rhythm.beat_profile` + 既有九宫配额 | 否（自动） |
| **Apple Photos Memories** | 全片快慢节奏、高潮段加速 | `pace_profile` 曲线（LSE-CAP-13） | 否 |
| **Google Photos** | 事件内精选、高光时刻窗 | `highlight_windows` 软加权（LSE-CAP-15）+ `QualityFeatures` | 否 |
| **Unfold/Mojo 叙事节拍** | 封面→展开→高潮→收尾序列 | `beat_profile: classic_magazine` | 否 |
| **Flipboard/杂志 App** | 跨页色调、folio 呼吸 | `tone_continuity` + **`editorial_hints`**（LSE-CAP-14） | 否 |
| **版面分配学术/相册工具** | 匈牙利最小代价匹配 | MCS `slot_assignment: hungarian`（W4） | 否 |
| **智能裁切（显著性）** | 主体保留率驱动选槽/打分 | `salient_retention` 惩罚（W3） | 否 |
| **推荐系统隐式反馈** | 换版式/删屏 → 偏好信号 | `layoutFeedback` 事件 → 离线标定提案（W4） | 否 |

> 完整能力规格见 **§4.5**（LSE-CAP-01～15）；明确**不引入**项见 **§2.2**。

### 1.5 四方评审待决议（W0 冻结）

| ID | 议题 | 建议决议 |
|----|------|----------|
| **R-P17-01** | 新包路径 | **`travelogue/layout_engine/`**（LSE）；`screen_planner` 保留薄包装，stages 渐进迁入 |
| **R-P17-02** | 策略权威格式 | **`lse_policy.yaml` + `strategies/*.yaml`** 为 Git 权威源；`lse_runtime.json` 存审批后覆盖 |
| **R-P17-03** | 治理复用 | **复用 `travelogue/templating/`**（R-P17-12 对齐 R-P16-12），扩展 `config_governance` 支持 `layout_strategy_*` patch |
| **R-P17-04** | MCS 归属 | MCS 作为 LSE **子模块**保留在 `curation/mosaic/`，经 `layout_engine/adapter.py` 统一入口，不拆第三引擎 |
| **R-P17-05** | 默认路径 | **切引擎与上 CAP 解耦**：先 `enabled=true`（纯收敛、行为 parity、**不带任何 CAP**）单独灰度稳定，再逐个开 CAP-02/03/04；`false` 时行为与 P16 末态一致。理由：把「换引擎」与「上新算法」分离，任一回归可独立定位 |
| **R-P17-06** | 旧 trip 兼容 | 策略变更 **不自动** 重排版已有 trip；可选「layout-only replan」放 P17-W4 |
| **R-P17-07** | 匈牙利匹配优先级 | 从「可选轨」提升为 **W4 必交付**（混排核心短板）；生成式 composite / 4P+3L 仍放 P17-B |
| **R-P17-08** | 段内序优化器 | 纳入 **W4**；硬约束保持 burst 块与时间单调（[智能排版.md](./智能排版.md) §5.3） |
| **R-P17-09** | `layout-only replan` | 仅在**用户已触发**的 re-curate / 改 `layoutDensity` 时自动重跑 LSE；**不**作为 C 端主路径新按钮 |
| **R-P17-10** | 跨屏色调 | W3 起 `tone_continuity` + `luminance_continuity` 在默认 profile 权重 **>0**（可配置回退 0） |
| **R-P17-11** | Trip 节奏曲线 | W3 交付 `pace_profile`（LSE-CAP-13）；默认 `memories_pace`，与 `beat_profile` 正交叠加 |
| **R-P17-12** | Editorial 联动 | W4 交付 `trip.curation.editorialHints`（LSE-CAP-14）；**只写 hint**，breath/folio 仍由 Editorial 决策 |
| **R-P17-13** | 高光窗 | W4 交付章内 `highlight_windows` 检测 + 打分加权（LSE-CAP-15）；不新增用户标记 UI |
| **R-P17-14** | 交付轨道 | 正式拆分 **P17-Core / P17-Plus / P17-B**（§2.4）；AC 标注 Core/Plus（§8） |
| **R-P17-15** | `beat` × `pace` | W3 **仅默认开启 `beat_profile`**；`pace_profile` 推迟 **W5** 或 Plus-W4；合成公式见 §4.7 |
| **R-P17-16** | 策略包 lifecycle | W1–W3 **仅单包** `lse-default-2026-06`；多包 5 态晋升 → **W5** |
| **R-P17-17** | W2 范围收窄 | W2 交付 **Inspector + L3 overrides**；双人审批 + Trip 沙箱 → **W3** |
| **R-P17-18** | `editorial_hints` | W4 **MVP 只写 hint**；Editorial 强制消费 → **W5**（§4.5.12） |
| **R-P17-19** | 标定上线 | W4 仅 **采集+导出**；pairwise 自动提案上线 → **P18** |
| **R-P17-20** | `enabled=true` 门禁 | parity CI + **零步 E2E** + **quick_share 零 diff** 三连过；建议 dogfood **2 周** |

### 1.6 用户可感知价值（产品叙事 · 评审补充）

| 用户体感（人话） | 工程能力 | 轨道 |
|------------------|----------|------|
| 混排更少裁脸、主体更完整 | CAP-02 显著性 + CAP-01 匈牙利 | Core |
| 版式不那么单调、更像杂志页 | CAP-03 节拍 + CAP-04 色调 | Core |
| 大图/拼图偏好真的生效 | `layoutDensity` → density profile | Core |
| 同一天照片不再乱跳 | CAP-06 段内序 | Plus |
| 卷轴阅读更有呼吸感 | CAP-14 editorial hints（W5 联动） | Plus |

C 端 **不暴露** CAP 术语；精细制作成功页可展示 **一行人话摘要**（S-P17-06，非 balanced 时）。

---

## 2. 目标与非目标

### 2.1 目标

| ID | 目标 | 说明 |
|----|------|------|
| **G-P17-01** | **策略一等公民** | 每套排版策略一份 Strategy Pack：stage、节奏、打分 profile、搜索预算、rollout |
| **G-P17-02** | **决策可观测** | 统一 Decision Log：候选、得分、reject、layout_state 快照、weights_hash |
| **G-P17-03** | **治理可复用** | 生命周期 5 态、RBAC、审计、双人审批、紧急 disable，接入既有 templating 平台 |
| **G-P17-04** | **调参可分级** | L0–L3 自由度金字塔（§5）；运营可安全调 L2/L3，结构变更走 Git |
| **G-P17-05** | **LTE 解耦** | LSE 只引用 `patternId` / LTE quota；不改 YAML 几何 |
| **G-P17-06** | **意图可映射** | `layoutDensity` → density profile；telemetry 可解释三档差异 |
| **G-P17-07** | **回归可门禁** | golden trip + `weights_hash` 快照；L2 变更须过沙箱 diff 阈值 |
| **G-P17-08** | **标定可铺路** | 导出 feature 矩阵 + pairwise label，对接算法 V2 Phase D 提案流 |
| **G-P17-09** | **North Star 可度量** | `layout.chapter.pattern_diversity_p50`、mosaic5 exposure、hero_first/collage_first 达成率可报表 |
| **G-P17-10** | **混排全局最优分配** | 窗内 asset↔slot 匈牙利匹配（或等价最小代价），替代贪心；确定性可复现 |
| **G-P17-11** | **显著性保护裁切** | 打分含 `salient_retention`；与 `face_crop` 合并口径，降低裁头/裁脸 |
| **G-P17-12** | **杂志叙事节拍** | 默认 `beat_profile` 驱动章内 hero/mosaic/single 节奏，无需用户逐步选版 |
| **G-P17-13** | **跨屏视觉连贯** | 相邻屏 ΔE / 亮度差软惩罚默认开启，卷轴阅读更「成册」 |
| **G-P17-14** | **段内主题聚合** | 时间窗口内 person/pet/scenery run 优化，不打破全局 chronology |
| **G-P17-15** | **隐式学习闭环** | 编辑行为 → `layoutFeedback` → 离线标定提案 → 双人审批；用户无感 |
| **G-P17-16** | **质量特征统一** | hero/主位/窗内选图共用 `QualityFeatures`（sharp + aesthetic trip 内百分位） |
| **G-P17-17** | **全片节奏曲线** | `pace_profile` 驱动章/段密度快慢（对标 Apple Memories），后台自动、无用户调速 UI |
| **G-P17-18** | **Editorial 信号输出** | LSE 输出 `breath_hint` / `folio_hint` 供 Editorial 只读消费，增强杂志呼吸与对开 |
| **G-P17-19** | **高光时刻窗** | 自动检测章内 peak 窗并提高精选图/hero 权重（对标 Google Photos 高光段） |

### 2.2 非目标

| ID | 非目标 |
|----|--------|
| **NG-P17-01** | 不做可视化拖拽拼版 / 流程图规则编辑器 |
| **NG-P17-02** | 不替代 LTE 模板注册与几何校验 |
| **NG-P17-03** | 不替代 Editorial Layer（封面、arc、breath、folio）；LSE 仅可写 **`editorialHints` 建议**，不得直接插入 breath/folio 屏 |
| **NG-P17-04** | 不让后台编辑 Python stage 逻辑或 beam 实现（L0 仅代码发版） |
| **NG-P17-05** | 不要求 C 端用户手动指定单屏 pattern（inline-edit 不触发换模板） |
| **NG-P17-06** | 不在 P17 默认开启端到端 ML 自动调权上线；W4 仅采集导出，**上线放 P18**（R-P17-19） |
| **NG-P17-07** | 不统一 mosaic 乘性惩罚为加性模型（长期特征层统一放 P17-W3+，不阻塞 W1） |
| **NG-P17-08** | 不在 P17 对旧 trip 自动迁移策略（视觉会变）；重排版需显式用户动作 |
| **NG-P17-09** | 不新建独立 Admin 端口或第二进程（遵守 ADR-004） |
| **NG-P17-10** | 不新增 C 端「逐步确认排版」向导或 pattern 挑选 UI |
| **NG-P17-11** | 不要求用户为排版结果打分或填写问卷（仅采集已有编辑隐式信号） |
| **NG-P17-12** | 不引入端到端黑盒 Layout GNN/Transformer 替代可解释 beam |
| **NG-P17-13** | 不对标社交媒体竖屏模板/Reels 式手动拼贴心智 |
| **NG-P17-14** | 不在 P17 做 LLM 每窗选版式（违反 L2 可复现契约，见 [PRD-FINE-CRAFT-LAYOUT-DENSITY.md](./PRD-FINE-CRAFT-LAYOUT-DENSITY.md) D-LD 非目标） |
| **NG-P17-15** | 不做跨 trip 全局人脸 ID 驱动排版重排（延续 [智能排版.md](./智能排版.md) 非目标） |
| **NG-P17-16** | 不做 trip 级全册调色板/品牌色板统一（Canva 式）；P17 仅相邻屏 tone 软惩罚（§评审补充） |

### 2.3 能力增强分期（用户零步 · 后台自动）

| 轨道 | 能力 ID | 名称 | 交付波次 | 用户操作 |
|------|---------|------|----------|----------|
| **Core** | **LSE-CAP-02** | 显著性裁切 `salient_retention` | W3 | 无 |
| **Core** | **LSE-CAP-03** | 叙事节拍 `beat_profile` | W3 | 无 |
| **Core** | **LSE-CAP-04** | 跨屏 tone/luminance 连贯 | W3 | 无 |
| **Core** | **LSE-CAP-01** | 匈牙利 slot 匹配 | W4 | 无 |
| **Core** | **LSE-CAP-08** | `QualityFeatures` 统一选片 | W4 | 无 |
| **Plus** | **LSE-CAP-06** | 段内序列优化器 | W4 末 / W5 | 无 |
| **Plus** | **LSE-CAP-05** | 隐式反馈采集+导出（不上线标定） | W4 | 无 |
| **Plus** | **LSE-CAP-10** | layout-only 自动 replan | W4 | 改密度后 re-curate |
| **Plus** | **LSE-CAP-13** | `pace_profile` 全片节奏 | W5 | 无 |
| **Plus** | **LSE-CAP-14** | `editorial_hints` 写入（MVP） | W4 | 无 |
| **Plus** | **LSE-CAP-15** | 章内高光窗 | W4 | 无 |
| **Plus** | **LSE-CAP-07** | 章级 DPP/版式熵 | **W5**（从 W4 推迟） | 无 |
| **P17-B** | **LSE-CAP-11** | 生成式 composite（LTE） | P17-B | 无 |
| **P17-B** | **LSE-CAP-12** | 7 张 4P+3L 模板 | P17-B | 无 |
| **P18** | **LSE-CAP-09** | 构图角色 `compositionRole` | P18 | 无 |

### 2.4 P17-Core / Plus / B 定义（评审冻结）

#### P17-Core（Phase 17 完成判定）

| 类别 | 交付物 |
|------|--------|
| **引擎** | `layout_engine/` Registry、`adapter.py`、默认 Strategy Pack、parity CI |
| **可观测** | decision log、`strategyId` + `weightsHash`（FR-P17-TRACE） |
| **治理** | Studio Inspector（只读）+ L3 `overrides`；**W3 起**双人审批 + 沙箱 |
| **算法** | CAP-02/03/04（W3）；CAP-01/08（W4） |
| **门禁** | golden probe CI、AC-P17-23 零步 E2E、**quick_share 零 diff** |
| **策略** | W1–W3 **仅** `lse-default-2026-06` 单包，无多包 lifecycle |

**Core 出口 AC**：§8 表中标注 **Core** 的行全部通过。

#### P17-Plus（不阻断 Phase 完成）

CAP-05/06/10/14/15、CAP-07（W5）、`pace_profile`（W5）、KPI 自动回滚提案、多包 lifecycle（W5）。

#### P17-B / P18

CAP-11/12、CAP-09、pairwise **标定自动上线**、trip 级全册调色板统一。

### 2.5 评审补充规格索引（S-P17）

| ID | 内容 | PRD 节 |
|----|------|--------|
| **S-P17-01** | P17-Core / Plus / B 三分 | §2.4 |
| **S-P17-02** | `beat × pace` 合成公式 | §4.7 |
| **S-P17-03** | `run_curate` 性能预算 ≤+15% | §4.9、AC-P17-28 |
| **S-P17-04** | 封面/hero/高光选片优先级 | §4.8 |
| **S-P17-05** | W0 阻断交付物 | §13.4 |
| **S-P17-06** | 成功页人话一行（非 balanced） | AC-P17-29、§1.6 |
| **S-P17-07** | Inspector：pattern 条 + 裁切告警 | §5.1 |
| **S-P17-08** | `editorialDecisionLog` schema | §4.5.12 |
| **S-P17-09** | `enabled=true` 三连门禁 + dogfood 2 周 | R-P17-20、§14 |

**可追溯（FR-P17-TRACE）**：任意成稿可回溯 `strategyId` + `weightsHash` + `capability_flags`（AC-P17-04）。

---

## 3. 系统定位与边界

### 3.1 全链路位置

```
[筛选 P9] → [聚类 P3/P8] → [★ LSE 智能排版引擎] → [LTE 模板几何] → [Editorial] → [Render]
                ↑                    ↑                      ↑
           layoutEligible      Strategy Pack            pattern 校验
           burst/aspect        stage+beam+scoring       slot AR
                                    ↓
                            screens[] + decision_log
```

### 3.2 职责边界

| 模块 | 负责 | 不负责 |
|------|------|--------|
| **LSE** | Strategy Pack 注册、stage 流水线、节奏/pace 曲线、高光窗、beam 预算、打分 profile、**`editorialHints` 输出**、决策日志、runtime 调参 | pattern 拓扑、CSS、槽位 AR；**不**直接插入 breath/folio 屏 |
| **MCS**（LSE 子模块） | 滑窗候选、乘性打分、段内 beam、self-heal、diversity MMR/DPP | 模板几何、叙事结构 |
| **LTE**（P16） | TemplateDef、validator、CSS-gen、`overrides.disable` | 选图顺序、章序、beam |
| **Editorial** | arc、breath、folio、封面、章 hero；**可读** `trip.curation.editorialHints` | 改写 `screens[]` 几何；hints 为软输入非硬命令 |
| **Render** | 执行已固化 `screens[]` | 组屏决策 |
| **Studio** | 策略 Inspector、沙箱重放、审批 UI（**internal only**） | C 端排版工作台、裸 weight、逐步确认 |

### 3.3 `run_curate` 写权限（权威）

| 阶段 | 归属 | 可改 `screens[]` |
|------|------|-----------------|
| `attach_screens` / stage 流水线 | **LSE** | ✅ |
| `maybe_replan_chapters`（段内 beam） | **LSE / MCS** | ✅ |
| SelfHeal（`allow_drop` 默认关） | **LSE / MCS** | ✅ |
| `build_folio_plan` / breath / explain | **Editorial**（可读 LSE `editorialHints`） | ⛔ 只读 `screens[]` |
| LSE 写入 `editorialHints` | **LSE** | ⛔ 不改 `screens[]` |
| 封面 / epilogue | **Editorial** | ⛔ 只读 |

### 3.4 LSE 与 LTE / MCS 接口（契约）

```python
# 概念接口 · 落于 travelogue/layout_engine/（R-P17-01）

class LayoutStrategyEngine:
    def load(*, strategy_id: str | None = None) -> StrategyPack: ...
    def active_profile(*, trip_intent: dict) -> ScoringProfile: ...
    def planning_context(*, trip: dict, cfg: AppConfig) -> PlanningContext: ...
    def weights_hash(profile: ScoringProfile) -> str: ...
    def emit_decision_log(event: DecisionEvent) -> None: ...

# curate 唯一入口（防腐层）
def plan_chapter_screens(ctx: ChapterPlanContext, *, engine: LayoutStrategyEngine) -> list[dict]: ...

# MCS 仍经 lte_adapter 读模板；打分权重从 LSE profile 注入
def score_candidate(..., profile: ScoringProfile, layout_state: ScreenLayoutPlannerState) -> MosaicScoreResult: ...
```

**管理侧 —— 复用 `travelogue/templating/`（R-P17-03）**：

| 能力 | 委托 |
|------|------|
| 生命周期 5 态 | `templating.lifecycle` |
| 双人审批 | `config_governance.propose/approve`（扩展 `layout_strategy_weights` 等 patch 键） |
| 审计/回滚 | `admin_store.list_audit` / `apply_rollback` |
| RBAC | `templating.roles` |
| Web | `template_admin_handlers` 扩展 **「排版策略」** Tab |

LSE 唯一新增管理 hook：

```python
class LayoutStrategyHook:
    def validate_strategy_pack(pack: StrategyPack) -> ValidationReport: ...
    def diff_runtime(base: StrategyPack, runtime: dict) -> StrategyDiff: ...
    def sandbox_replay(trip_id: str, *, profile_id: str) -> SandboxResult: ...
```

---

## 4. 核心概念与分层

### 4.1 Strategy Pack（策略包）

每套策略由 **一份 YAML**（Git 权威）描述，启动时加载并合并 runtime 覆盖。

**权威 Schema**：`travelogue/layout_engine/lse_strategy.schema.json`（P17-W0 冻结）。

| 分组 | 字段（示例） | 说明 |
|------|--------------|------|
| 身份 | `id`, `version`, `status`, `algorithm_version` | `algorithm_version` 绑定代码，不可后台改 |
| 规划 | `planning.screen_plan_scope`, `planning.stages[]`, `planning.mixed_proximity_seconds` | L1 GitOps |
| 节奏 | `rhythm.nine_grid_limits[]`, `rhythm.consecutive_bans[]`, `rhythm.beat_profile`, `rhythm.pace_profile` | 章级节拍见 §4.5.3；全片快慢见 §4.5.11 |
| 高光 | `highlight_windows.enabled`, `highlight_windows.min_quality_pct` | 章内 peak 窗检测见 §4.5.13 |
| Editorial | `editorial_hints.enabled`, `editorial_hints.breath_gap_threshold` | 只写 hint，见 §4.5.12 |
| 密度 | `density_profiles.balanced/hero_first/collage_first` | 映射 `trip.intent.layoutDensity`；与 beat 正交叠加 |
| 分配 | `slot_assignment.mode` | `greedy`（默认 W1–W3）\| `hungarian`（W4 默认） |
| 特征 | `features.saliency`, `features.tone_harmony`, `features.quality_unified` | 开关与权重引用；定义见 §4.5 |
| Pattern | `pattern_policy.blacklist`, `lte_overrides_disable` | 透传 LTE 紧急开关 |
| 打分 | `scoring_profiles.default/dense_album` | weights + penalties |
| 搜索 | `search.beam_width`, `search.max_evaluations_per_trip`, `search.min_candidate_score` | L2 可调 |
| 多样性 | `diversity.mode`, `diversity.lambda` | off \| mmr \| dpp |
| 自愈 | `self_heal.enabled`, `self_heal.allow_drop` | S3 默认 allow_drop=false |
| 灰度 | `rollout.traffic_percent`, `rollout.allowed_profiles` | L3 紧急/灰度 |

### 4.2 四层自由度模型（CRUD 边界）

| 层级 | 内容 | Create | Update | Delete | 生效 | 审批 |
|------|------|--------|--------|--------|------|------|
| **L0 算法** | stage 逻辑、beam、特征定义 | 研发 PR | 研发 PR | — | 发版 + `algorithm_version` | Code Review |
| **L1 结构** | stage 顺序、硬阈值、分档表 | Git 新 YAML | Git PR | 软删 disabled | merge + validate + golden | CI 门禁 |
| **L2 打分** | weights、penalties、beam 参数 | propose | patch | 禁用 profile | runtime revision | **双人审批** |
| **L3 开关** | 紧急 disable stage/pattern、rollout% | 一键 | 即时 | 撤销 | runtime 即时 | operator（可单人） |

**原则**：

1. 后台 **不出现** Python 表达式或可编程规则流  
2. 单因子 weight 调整 ±0.05 → L2 高自由；±0.20 → 须沙箱；新增因子名 → L0 禁止  
3. 任何 L2 变更携带 `weights_hash`，写入 decision_log  

### 4.3 Decision Log（统一决策日志）

**Schema**（写入 `trip.curation.layoutDecisionLog` 或 sidecar `runs/layout-decisions.jsonl`）：

```json
{
  "strategyId": "lse-default-2026-06",
  "strategyRevision": 42,
  "weightsHash": "a3f8c1…",
  "algorithmVersion": "p15-s2",
  "chapterId": "ch-03",
  "segmentId": "seg-12",
  "window": { "start": 12, "size": 5 },
  "candidates": [
    { "patternId": "screen-mosaic-5-hero-3-2-plus-4", "score": 0.72, "reasons": [] }
  ],
  "rejected": [
    { "patternId": "screen-portrait-5", "reason": "slot_geometry" }
  ],
  "picked": { "patternId": "screen-mosaic-5-hero-3-2-plus-4", "score": 0.72 },
  "layoutState": { "nine_used": 2, "nine_max": 5, "last_kind": "triple", "layout_density": "balanced" },
  "explain": { "topFactors": ["temporal_coherence", "aspect_match"], "penalties": ["face_crop"] }
}
```

**因子归因口径（W0 冻结 · 解释层数学定义）**：

`topFactors` 不是「权重最大的因子」，而是「对本次 score 实际贡献最大的因子」。由于底层存在乘性模型（`mosaic/scorer.py` 为乘性惩罚），加性「权重×值」无法表达乘性贡献，故统一采用 **log-domain 加性分解**：

```text
log(score) = Σ_i  contribution_i
  加性因子:  contribution_i = w_i · f_i               # layout 加性链
  乘性惩罚:  contribution_j = log(1 - p_j · risk_j)    # mosaic 乘性链（≤0）
topFactors  = 按 |contribution| 降序取 Top-K（正向因子）
penalties   = contribution < 0 的项（即乘性惩罚 / 负向因子）
```

> 三套聚合模型可不统一（NG-P17-07），但**归因必须落到统一的 `contribution_i` 口径**；否则 Inspector 的「Top-3 因子」在乘性模型里无定义，会误导运营。`decision_log.explain` 须写入 `contribution` 值而非裸 weight。

**解释层级**：

| 层级 | 受众 | 展示 |
|------|------|------|
| L1 | 用户（可选） | 「本章以拼图为主，强调时间连贯」 |
| L2 | 运营 | Top-3 因子（按 `contribution`）+ 惩罚项 |
| L3 | 研发 | 全量候选 + beam 路径 + state 快照 + 各因子 `contribution` |

### 4.4 与版面密度（P14）的映射

| `trip.intent.layoutDensity` | LSE `density_profile` | 工程效果（示例） |
|-----------------------------|----------------------|------------------|
| `balanced`（默认） | `balanced` | 现网算法，quick_share 忽略 |
| `hero_first` | `hero_first` | 提高单槽/hero 优先；压低九宫 bias |
| `collage_first` | `collage_first` | 提高 mosaic/多槽曝光；放宽九宫下限 |

非法值 **fail-open** → `balanced`（D-LD-03）。

**成功页一行文案表（前端补充 · S-P17-06 / AC-P17-29）**：

| `layoutDensity` | i18n key | 文案（≤24 字，无 CAP 术语） | 展示 |
|-----------------|----------|------------------------------|------|
| `balanced` | — | （不展示） | 隐藏 |
| `hero_first` | `layout.summary.heroFirst` | 「已为你突出大图、放大精彩瞬间」 | 精细制作成功页 |
| `collage_first` | `layout.summary.collageFirst` | 「已为你多图拼贴、记录更多细节」 | 精细制作成功页 |

> **约束**：纯展示、无交互（不破坏零步 AC-P17-23）；带 `aria-label`；文案需过 i18n。**归属待确认**：模板侧仅 `studio-home-v2.html` 含 density，C 端「精细制作成功页」若在前端 app（非模板仓），W1 前须确认改动面与 owner。

### 4.5 智能排版能力增强（规格 · 后台自动）

> 下列能力均在 **curate 管线内默认执行**；通过 Strategy Pack 与 `algorithm_version` 开关，**不要求**用户逐步操作。规格绑定能力 ID（§2.3）。

#### 4.5.1 LSE-CAP-01 · 匈牙利 slot 匹配

| 项 | 规定 |
|----|------|
| **问题** | 贪心 `try_order_for_pattern` 在混排窗内非全局最优 |
| **范围（边界）** | 匈牙利**仅解「给定 `patternId` 下 asset→slot 的局部最优指派」**。`cost[i,j]` 只能容纳**可分解为成对项**的代价：AR 距离 + 人脸裁切 proxy + `salient_retention` 损失。**组合性因子**（`temporal_coherence` / `subject_run` / `diversity` / `layout_rhythm`）无法进代价矩阵，仍由 **beam 负责 pattern 选择**——匈牙利不替代 beam |
| **做法** | 对固定 `patternId` + N 资产构建 `cost[i,j]`，**匈牙利算法**求最小总代价分配 |
| **确定性（D-P17-05）** | 代价并列时按 **`(assetId, slotIndex)` 字典序** tie-break，保证唯一解；预算用**确定性上限**（矩阵规模 `N≤16`、评估次数上限）而非挂钟（见 §4.9）。**禁止用 wall-clock timeout 改变产出**（否则同 trip 在不同负载产出不同 screens） |
| **失败** | 无完美匹配 / 超确定性上限 → **fail-open** 回退贪心，记入 `decision_log.fallbackReason` |
| **配置** | `slot_assignment.mode: hungarian`；`slot_assignment.max_matrix_n: 16`（确定性预算，替代 `timeout_ms`） |
| **验收（主指标）** | 混排 golden fixture **人脸完整率 ≥ 基线 +5pp** 且 `salient_retention` p50 ≥ 基线 +5pp（CAP-01 收益证明） |
| **验收（护栏）** | per-window Kendall τ(贪心,匈牙利) **无灾难性回归**（不要求高相关——高相关反而说明无收益）；超时/降级 fail-open 必有日志 |

#### 4.5.2 LSE-CAP-02 · 显著性裁切打分

| 项 | 规定 |
|----|------|
| **输入** | ingest `focalPoint`、人脸 bbox（若有）；可选轻量 saliency 中心（不强制新 ML 依赖） |
| **特征** | `salient_retention(slot, asset) ∈ [0,1]`：模拟 cover 裁切后主体保留比例 |
| **打分** | 并入 mosaic 惩罚 `salient_crop`（与 `face_crop` 取 max 或加权合并，避免三重惩罚） |
| **LTE 联动** | 探针 `saliency_gate` 非 no-op（延续 IMPLEMENTATION-PHASE16 saliency 门禁） |
| **用户** | 无；仅改善成稿裁切 |

#### 4.5.3 LSE-CAP-03 · 叙事节拍 `beat_profile`

| 项 | 规定 |
|----|------|
| **对标** | 相册书页型节奏、Unfold 叙事序列 |
| **内置 profile** | `classic_magazine`（默认）：章首 hero 权重↑ → 中段 mosaic/多槽↑ → 章末 single/breath 倾向 |
| **实现** | 在 `ScreenLayoutPlannerState` / stage 优先级注入 **位置相关 bias**（非 LLM） |
| **与 density** | `hero_first` / `collage_first` 叠加在 beat 之上，非替代 |
| **配置** | `rhythm.beat_profile: classic_magazine \| flat \| dense_mid` |

#### 4.5.4 LSE-CAP-04 · 跨屏 tone/luminance 连贯

| 项 | 规定 |
|----|------|
| **输入** | ingest `dominantTone` / Lab 指标（已有 `color_metrics`） |
| **实现（不进 beam）** | 相邻屏连贯是**序列依赖**项，**不**进窗内 beam 搜索（会把窗内独立评估变成路径依赖、状态空间爆炸、撞 §4.9 预算）。实现为 **已定序 `screens[]` 上的 look-back-1 贪心软惩罚（后处理重排）**：仅对比当前屏与**前一屏**主色 ΔE / 亮度差 |
| **打分** | look-back 软惩罚并入 score；`tone_continuity`、`luminance_continuity` 默认权重各 **≥0.06**（R-P17-10） |
| **边界豁免** | (1) **章/段边界**相邻屏不施加跨界惩罚；(2) **日夜/室内室外硬切**豁免——判定特征：相邻屏 `takenAt` 间隔 > 阈值 或 Lab `L` 差 > 阈值；豁免后惩罚归 0，避免过度抹平真实场景变化（AC-P17-18） |
| **用户** | 无 |

#### 4.5.5 LSE-CAP-05 · 隐式反馈闭环

| 项 | 规定 |
|----|------|
| **采集**（用户无感） | `replan_screen`、`inline` 删屏/调序、patch screen 换 pattern → `layoutFeedback` 事件 |
| **复用既有基建** | **必须复用** `travelogue/curation/feedback.py` 的 `G1EditRecord` + `g1_edit_distance` 去噪口径，**不另造** edit-distance；`layoutFeedback` 是其 layout 子类型投影 |
| **信号混淆治理（强制）** | 删屏/调序高度混淆（删屏可能是选片问题非 pattern 问题；换版可能误触）。**有效 pairwise label 过滤**：仅 `edit_type=pattern_change`、非 `burstGroup` 误触、且 `distance ∈ [d_lo, d_hi]` 的事件才生成「原 pattern ≺ 新 pattern」label；其余仅作弱信号 telemetry，不进标定样本 |
| **存储** | sidecar `runs/layout-feedback.jsonl` + 聚合至运营 telemetry |
| **不上线** | 不自动改权重；离线导出 feature 矩阵 + **过滤后** pairwise label → **提案** patch → `config_governance` 双人审批 |
| **原则** | D-P17-08：不新增任何「请评价排版」UI |

#### 4.5.6 LSE-CAP-06 · 段内序列优化器

| 项 | 规定 |
|----|------|
| **位置** | Layer 1.5：`sort_bucket` 之后、组屏之前（[智能排版.md](./智能排版.md) §5.3） |
| **软目标** | 同 person/pet/scenery run、时间平滑、aspect run；惩罚人物/风景乱跳 |
| **硬约束** | 全局 `takenAt` 单调；`burstGroupId` 块不可拆（默认）；不跨 `TimeSegment` |
| **算法** | 段长 ≤30：beam/DP；更长：贪心 + 2-opt；预算耗尽 fail-open 保持现序 |
| **用户** | 无 |

#### 4.5.7 LSE-CAP-07 · 章级版式多样性

| 项 | 规定 |
|----|------|
| **做法** | 扩展 MCS `diversity`：除近 2 屏 MMR 外，增加章内 `pattern_entropy` 软目标（DPP 可选） |
| **指标** | 对齐 `layout.chapter.pattern_diversity_p50` North Star |
| **配置** | `diversity.chapter_entropy_target`、`diversity.mode: mmr \| dpp` |

#### 4.5.8 LSE-CAP-08 · QualityFeatures 统一选片

| 项 | 规定 |
|----|------|
| **做法** | 对接算法 V2 Phase E：`sharp_pct`、`aesthetic_pct`（trip 内百分位） |
| **消费** | mosaic 主位、章 hero、burst 保留帧优先用统一特征，非单 `sharpness` 绝对值 |
| **回退** | 无 aesthetic 模型时 `aesthetic_pct` 恒 0.5，行为退化可接受 |

#### 4.5.9 LSE-CAP-09 · 构图角色（P18 候选）

| 项 | 规定 |
|----|------|
| **标签** | `compositionRole`: establishing \| detail \| portrait \| panorama（启发式或 CLIP） |
| **约束** | mosaic 窗软约束「≥1 establishing」；不作为 hard reject |
| **波次** | W5/P18，不阻塞 P17 主线 |

#### 4.5.10 LSE-CAP-10 · layout-only 自动 replan

| 项 | 规定 |
|----|------|
| **触发** | 仅当用户**已发起** re-curate 且 `trip.intent.layoutDensity` 相对上次变化 |
| **范围** | 只跑 LSE+MCS，不重新 ingest/聚类/文案 |
| **非目标** | 不做 C 端显眼「重排版」主按钮；快速分享路径不触发 |
| **契约** | `pipeline.layoutStatus` 标记 `replan_reason=density_change` |

#### 4.5.11 LSE-CAP-13 · Trip 节奏曲线 `pace_profile`

| 项 | 规定 |
|----|------|
| **对标** | Apple Photos Memories 全片「慢→快→慢」或「建立→高潮→收尾」节奏 |
| **与 beat 区别** | `beat_profile` 管**章内**相对位置 bias；`pace_profile` 管**全 trip 章节索引**上的密度倍率曲线 |
| **内置 profile** | `memories_pace`（默认）：首章 0.85×、中段 1.15×、末章 0.90× 作用于 mosaic/多槽倾向；`flat`：全 1.0 |
| **实现** | `pace_multiplier(chapter_index, chapter_total) ∈ [0.7, 1.3]` 乘到 `density_profiles` 与 `beat_profile` bias |
| **配置** | `rhythm.pace_profile: memories_pace \| flat \| slow_open` |
| **用户** | 无；导入后自动应用 |

#### 4.5.12 LSE-CAP-14 · Editorial 联动 `editorial_hints`

| 项 | 规定 |
|----|------|
| **对标** | Flipboard/杂志 App 跨页呼吸、folio 对开时机 |
| **输出契约** | LSE 在 MCS 完成后写入 `trip.curation.editorialHints`（**不**改 `screens[]`） |

```json
{
  "version": 1,
  "chapters": [
    {
      "chapterId": "ch-02",
      "breathHint": { "suggested": true, "afterScreenIndex": 4, "reason": "pace_valley", "viewportScope": ["web", "print", "mobile"] },
      "folioHint": { "suggested": true, "pairScreenIndices": [1, 2], "reason": "tone_cohesive", "viewportScope": ["web", "print"] }
    }
  ]
}
```

> **viewportScope（前端补充）**：`folioHint`（对开）在**移动端无对开语义**，须标 `viewportScope` 排除 `mobile`；前端按当前视口忽略不适用 hint（§4.10.3）。W5 Editorial 消费时，breath 屏插入位置 / folio 对开 CSS 的**渲染契约**须前端参与定义（W5 占位，避免消费期才发现 hint 无法渲染）。

| 项 | 规定 |
|----|------|
| **触发** | `breathHint`：连续高密度屏（≥3 多槽）后 pace 谷值；`folioHint`：相邻屏 tone ΔE \< 阈值且均 landscape hero |
| **Editorial** | **W4 MVP**：仅写入 hints + telemetry；**W5** 起 Editorial **可参考** hint；hint 未采纳须写 `editorialDecisionLog`（S-P17-08） |
| **边界** | NG-P17-03：hint **≠** 强制插入；无 hint 时 Editorial 行为与现网一致 |
| **波次** | W4 MVP 写入；W5 消费联动 |

#### 4.5.13 LSE-CAP-15 · 章内高光窗 `highlight_windows`

| 项 | 规定 |
|----|------|
| **对标** | Google Photos 事件内「精彩瞬间」高密度段 |
| **检测** | 章内滑动窗口（默认 5–12 张）计算 `highlight_score` = sharp_pct + aesthetic_pct + 人脸清晰 bonus；取 top 1–2 窗 |
| **消费** | 高光窗内：`QualityFeatures` 权重 × `highlight_boost`（默认 1.25）；须遵守 §4.8 选片优先级，**不得**覆盖封面链 |
| **硬约束** | 仍遵守时间单调、burst 不拆；高光仅**软加权**非硬筛 |
| **配置** | `highlight_windows.enabled: true`；`window_sizes: [5, 8, 12]`；`boost: 1.25` |
| **用户** | 无；不展示「高光段」标记（telemetry 可观测） |

### 4.6 LayoutFeatures（统一特征层 · W4）

```text
LayoutFeatures（每 asset 或 asset×slot 派生）
  ├─ aspect_distance(slot, asset)
  ├─ sharp_pct / aesthetic_pct        # LSE-CAP-08
  ├─ salient_retention(slot, asset)   # LSE-CAP-02
  ├─ face_crop_risk(slot, asset)
  ├─ tone_delta(prev_screen, asset)   # LSE-CAP-04
  ├─ composition_role_match(window)   # LSE-CAP-09 · 可选
  ├─ highlight_boost(window)          # LSE-CAP-15
  └─ pace_multiplier(chapter)         # LSE-CAP-13

cover_scorer / mosaic_scorer 共用特征名；**封面**走算法 V2 `cover_scoring` 独立链，不重复造分（§4.8）
```

**值域契约（W0 冻结 · 强制）**：NG-P17-07 允许底层保留「乘性 mosaic / 加性 layout / logit cover」三套**聚合模型**，但 `LayoutFeatures` 的**因子值域必须统一**，否则同名因子在两套模型里方向/量纲不一致会造成隐蔽 bug：

| 约束 | 规定 |
|------|------|
| **值域** | 所有特征归一化到 `[0,1]`（penalty 类亦表达为「保留率/合规度」，越大越好） |
| **方向** | 统一为 **越大越好**；惩罚项以 `1 - risk` 形式入特征层，避免「同名因子在加性里正向、在乘性里反向」 |
| **缺失语义** | 模型缺失（如无 aesthetic 模型）→ 该特征恒 `0.5`（中性），不得用 `0` 污染（呼应 §4.5.8 回退） |
| **Validator** | `validator.py` 校验默认 pack 引用的每个特征名存在、值域声明合法（W1 门禁） |

> 此契约是 §4.3「因子可比 / topFactors 可排序」的**前置条件**；未冻结前不得开工 W3 解释层。

### 4.7 `beat_profile` × `pace_profile` 合成（R-P17-15 · W0 冻结）

避免双重计分，合成规则：

```text
effective_density_bias =
  clamp(
    density_profile_bias
    + beat_bias(screen_index_in_chapter)
    + pace_bias(chapter_index, chapter_total)   # W5 起；W3 为 0
  , -0.5, +0.5)

pace_bias 默认关闭（capabilities.pace_profile=false）直至 W5 评审通过。
beat 与 pace 不得同屏叠加超过 |0.5|；Validator 对 Strategy Pack 校验此上限。
```

### 4.8 选片优先级矩阵（S-P17-04 · 防三重加权）

| 场景 | 权威链路 | LSE 角色 |
|------|----------|----------|
| **封面** | 算法 V2 `cover_scoring` | 只读 `QualityFeatures`，**不**用 highlight_boost |
| **章 hero** | curate hero + LSE stage | 可用 `QualityFeatures`；highlight 窗内 **×1.15** 上限 |
| **mosaic 主位** | MCS 窗内打分 | `QualityFeatures` + highlight_boost（≤1.25） |
| **burst 保留帧** | ingest burst 规则 | 不受 highlight 影响 |

### 4.9 性能预算（S-P17-03）

> **确定性原则（D-P17-05 · 凌驾性能优化）**：任何**改变产出 `screens[]`** 的预算都必须是**确定性预算**（trip 规模分档、矩阵规模上限、评估次数上限），**不得**用挂钟（wall-clock）触发降级——否则同 trip 在慢机器 / 高负载下产出不同 screens，违反确定性并使 parity CI 间歇 flaky。Wall-clock **仅可用于 telemetry 告警**，不可改变产出路径。

| 项 | 预算 |
|----|------|
| LSE 引入后 `run_curate` 单 trip 耗时增量 | **≤ +15%**（相对 P16 末态基线）；**W0/W1 须先做性能 spike** 实测各能力增量，按 trip 规模（>200 / >500 张）给出曲线，再据此设档（S-P17-03） |
| 匈牙利单窗 | **确定性上限** `slot_assignment.max_matrix_n: 16`；超限 fail-open 贪心（替代 `timeout_ms`，见 §4.5.1） |
| decision log 写入 | 异步 sidecar，不阻塞主路径 |
| 能力分档（替代运行时降级） | 按 **trip 规模静态选档**：超大 trip 在**进入 curate 前**确定性地关闭高成本能力（顺序 highlight → segment_order → hungarian → tone），档位写入 `decision_log` 与 `capability_flags`，同规模 trip 选档一致 → 产出可复现 |

### 4.10 渲染落地契约（Render Binding · 前端负责人补充 · W3 阻断）

> **动机（已核证缺口）**：`render/context.py` 已输出 `--focal-x/--focal-y`，基础规则 `.layout-slot__img--cover` 也消费它（`object-position: calc(var(--focal-x)*100%) …`）。**但** `journal-screens.css` 中多个 pattern 级规则**硬编码** `object-position: center` / `center 30%` / `top center`，凭特异性覆盖 focal。结果：`LSE-CAP-02` 在打分阶段算出的裁切锚点对这些 pattern **不会在像素上生效**，CAP-02 的用户可感知价值落空。PRD 此前缺「算法产出 → DOM/CSS」绑定契约，特此补入。

#### 4.10.1 焦点/显著性裁切绑定

| 项 | 规定 |
|----|------|
| **数据流** | salient 选定的裁切锚点必须经 `render/context.py` 透传为 slot 级 CSS 变量（复用 `--focal-x/--focal-y`，或新增 `--salient-x/--salient-y` 并约定优先级：salient > focal > 默认） |
| **CSS 收敛** | 凡 `object-fit: cover` 的 slot，`object-position` **必须**消费上述变量；现存 pattern 级 `object-position: center / center 30% / top center` 的**硬编码覆盖须移除或改为读变量**。维护一份**豁免清单**（`object-fit: contain`、整图展示类无需裁切的 pattern 可保留 center） |
| **回退** | 无 focal/salient → 退回 pattern 默认锚点（保持现网观感），不报错 |
| **验收** | 见 AC-P17-30（渲染产物中相关 slot 的 `object-position` 实际反映 focal/salient，截图/计算回归，**非仅打分日志**） |

#### 4.10.2 渲染输入字段隔离（quick_share 零 diff 前置）

| 项 | 规定 |
|----|------|
| **隔离** | C 端渲染**不得读取/依赖** `decisionLog`、`editorialHints`、`capability_flags`、`weightsHash` 等 LSE 可观测字段；这些仅入 sidecar / telemetry |
| **理由** | 否则 LSE 可观测内容变化会让渲染产物 diff，直接破坏 AC-P17-27 |
| **验收** | 见 AC-P17-31（渲染产物 hash 的输入集合不含 LSE 可观测字段） |

#### 4.10.3 视口适配（mobile / 对开）

| 项 | 规定 |
|----|------|
| **tone 相邻语义** | `LSE-CAP-04` 的相邻屏 ΔE 按 **`screens[]` 逻辑序**计算，与视口无关；移动端单列重排不改变逻辑相邻关系 |
| **folioHint 视口适用** | `editorialHints.folioHint`（对开）在**移动端无对开语义**；hint 须带 `viewportScope`（如 `["web","print"]`），前端按视口忽略不适用 hint（NG-P17-03 边界延伸） |
| **零步不变** | 所有渲染绑定均为静态产出，无新增 C 端交互（AC-P17-23 不回归） |

---

## 5. 后台管理

### 5.1 不新建 Admin，扩展 Studio 模板管理

在既有 `templates-admin.html` / `template_admin_handlers` 上新增 **「排版策略 LSE」** 区块（**dev / internal only**，对齐 AC-P16-14；**不对 C 端用户开放**）：

> **与产品原则对齐**：后台能力服务于运营标定、权重审批、回归沙箱；**不是**让用户参与排版的工作台。

| 功能 | 说明 | 最低 RBAC |
|------|------|-----------|
| 策略包列表 | status、version、algorithm_version、weights_hash | viewer |
| 策略详情 | 结构化只读；L2 可编辑字段高亮 | viewer |
| 运行时调参 | propose → pending → approve | operator / admin |
| 决策日志 | 按 trip / chapter / window 检索 | viewer |
| Trip 沙箱 | 选 trip + 换 profile → **pattern 分布条 + 裁切告警**（S-P17-07） | operator · **W3 起** |
| Golden 回归 | 最近 probe 结果、KPI 对比 | viewer |
| 审计 / 回滚 | revision 历史 | admin |

#### 5.1.1 前端实现规格（前端负责人补充 · 可估工）

> 上表为功能清单；以下为前端落地约束，作为 W2 Inspector / W3 沙箱的实现验收依据。

| 项 | 规定 |
|----|------|
| **载体** | 复用 `templates/studio/templates-admin.html` + `template_admin_handlers`，新增「排版策略」Tab，**不新建页面/端口**（NG-P17-09）；internal only，文案可英文 |
| **决策日志渲染** | `decision_log_max_events: 2000` 量级须**服务端分页 + 前端虚拟滚动**，禁止一次性渲染全量；按 trip/chapter/window 检索走查询参数，空结果/超时有明确空态 |
| **pattern 分布条**（S-P17-07） | 横向占比条形图（每 pattern 一段，宽度=曝光占比）；旁标 mosaic5 / hero / single 比例 |
| **裁切告警**（S-P17-07） | 对 `face_crop` / `salient_crop` 惩罚超阈值的屏标黄/红告警色带，点击下钻到该屏 candidate 与 `contribution`（§4.3） |
| **沙箱 diff**（AC-P17-09） | **前/后 screens 并排缩略图对比** + pattern 变更高亮，而非纯 JSON diff；diff 为空时显式「无变化」 |
| **L2 编辑态** | 详情默认只读；L2 可编辑字段高亮，propose 表单做**客户端值域校验**（与 §4.6 值域、`±0.05/±0.20` 沙箱阈值一致），不可 self-approve 在 UI 上灰显 |
| **状态机** | 每视图覆盖 加载 / 空 / 错误 / **无权限（RBAC 降级）** / 鉴权失败（loopback·token·LAN）五态 |
| **可观测隔离** | Inspector 读 sidecar/telemetry，**不**触达 C 端渲染输入（§4.10.2） |

### 5.2 API 契约（W2 Inspector · W3 审批/沙箱）

| 路径 | 方法 | 用途 |
|------|------|------|
| `/__travelogue/layout-strategies` | GET | 策略包列表 |
| `/__travelogue/layout-strategies/{id}` | GET | 详情 + runtime 覆盖 |
| `/__travelogue/layout-strategies/{id}/runtime` | POST | propose patch |
| `/__travelogue/layout-strategies/runtime/approve` | POST | 第二人审批 |
| `/__travelogue/layout-strategies/{id}/decisions` | GET | 决策日志 |
| `/__travelogue/layout-strategies/sandbox` | POST | trip 重放对比 |
| `/__travelogue/layout-strategies/{id}/rollback` | POST | 回滚 revision |

鉴权：loopback 或 `X-Studio-Token`；LAN 须 `studio_allow_lan`（ADR-004 不变）。

### 5.3 审批流

```
operator propose（weights / penalties / rollout / overrides）
        → pendingConfigChanges + audit
        → approve（approver ≠ operator；不可 self-approve）
        → runtime 写入 + weights_hash 更新
        → 7 天 telemetry 对比
        → KPI 劣化 → 自动提案回滚（可选 W4）
```

> **审批语义对齐（W0）**：现有 `config_governance.approve_router_change` 实现要求 `len(approvals) >= 2` **且** `approver != operator`，即落地为 **「提议人 + 2 名审批人」**（共 3 人参与），而非字面「双人」。AC-P17-07 验收以**代码实现语义为准**；若产品要求严格 2 人（提议人即一票），需在 W0 显式调整 `>=2` 阈值并记入 ADR。

> **实现性质标注（避免误判为零代码治理）**：`config_governance._apply_approved_patch` 是**硬编码 if-chain**（patch 键逐个分支处理），新增下列 5 个 `layout_strategy_*` 键属 **L0 代码改动 + 发版**，**不是** L2 纯配置；W1 须在该函数内实现并补单测（含 weight 归一/越界校验）：

- `layout_strategy_weights`
- `layout_strategy_penalties`
- `layout_strategy_rollout`
- `layout_strategy_overrides_disable_stages`
- `layout_strategy_overrides_disable_patterns`

---

## 6. 功能模块拆分（实施架构）

**包路径（R-P17-01）**：`travelogue/layout_engine/`

```
travelogue/layout_engine/
├── __init__.py
├── registry.py              # 加载 Strategy Pack、索引、contentHash
├── adapter.py               # curate 唯一入口（防腐层）
├── policy.py                # 默认 lse_policy.yaml + runtime merge
├── decision_log.py          # 统一 schema + emit/query
├── validator.py             # Strategy Pack 门禁
├── sandbox.py               # trip 重放 diff（W2）
├── features.py              # LayoutFeatures 统一派生（W4）
├── slot_assignment.py       # greedy | hungarian（W4）
├── segment_order.py         # 段内序列优化器（W4）
├── feedback.py              # layoutFeedback 采集与导出（W4）
├── pace.py                  # pace_profile 曲线（W3）
├── highlight_windows.py     # 章内高光窗检测（W4）
├── editorial_hints.py       # breath/folio hint 输出（W4）
├── cli.py                   # validate / probe / sandbox
├── lse_strategy.schema.json
├── lse_policy.yaml          # 全局默认 + rollout
├── strategies/
│   └── default.yaml         # 权威策略包
└── probe/                   # golden trip 回归

# 渐进迁入（不一次性搬家）：
travelogue/curation/screen_planner_stages.py   → layout_engine/stages/
travelogue/curation/screen_layout_state.py     → layout_engine/rhythm.py
travelogue/curation/mosaic/                    → 保留，经 adapter 注入 profile

# 复用（不新建）：
travelogue/templating/
travelogue/layout_templates/                   # LTE 只读消费
travelogue/web/studio_handlers/template_admin_handlers.py
```

| 模块 | 职责 | 新建/复用 |
|------|------|-----------|
| **Registry** | YAML 加载、profile 索引、`list_active_strategies` | 新建 |
| **Adapter** | `plan_chapter_screens` 统一入口；禁止 curate 直读 config 碎片 | 新建 |
| **Decision Log** | 写入/查询/聚合 telemetry | 新建 |
| **Validator** | stage 顺序合法、weight 归一、引用 LTE pattern 存在 | 新建 |
| **Sandbox** | trip 重放 + screens diff | 新建 |
| **Features** | LayoutFeatures 派生；供三 scorer 消费 | 新建 W4 |
| **Slot assignment** | 匈牙利匹配 + fail-open | 新建 W4 |
| **Segment order** | 段内序优化 | 新建 W4 |
| **Feedback** | 隐式事件采集 → 标定导出 | 新建 W4 |
| **Pace** | `pace_profile` 全 trip 节奏倍率 | 新建 W3 |
| **Highlight windows** | 章内 peak 窗检测与加权 | 新建 W4 |
| **Editorial hints** | `editorialHints` 契约输出 | 新建 W4 |
| **Lifecycle / Governance** | 5 态、审批、审计 | **复用 templating** |
| **MCS / screen_planner** | 现有逻辑 | **渐进委托 adapter** |

---

## 7. 配置与迁移

### 7.1 配置键（`config.yaml`）

```yaml
layout:
  strategy_engine:
    enabled: true                    # false → P16 末态
    default_strategy_id: lse-default-2026-06
    policy_path: travelogue/layout_engine/lse_policy.yaml
    runtime_store: data/lse_runtime.json   # 审批后覆盖
    overrides:
      disable_stages: []             # L3 紧急：如 mosaic
      disable_profiles: []
    telemetry:
      emit_per_window: true
      decision_log_max_events: 2000
    feedback:
      enabled: true                  # 隐式采集，无 C 端 UI
      log_path: null                 # 默认 runs/layout-feedback.jsonl
    capabilities:                    # 能力开关（均可后台关，用户无感）
      saliency_scoring: true         # LSE-CAP-02 · W3
      beat_profile: classic_magazine # LSE-CAP-03 · W3
      tone_harmony: true             # LSE-CAP-04 · W3
      hungarian_assignment: false    # LSE-CAP-01 · W4 起默认 true
      segment_order_optimizer: false # LSE-CAP-06 · W4
      implicit_feedback_export: true # LSE-CAP-05 · W4
      pace_profile: false            # LSE-CAP-13 · W5（W3 不开，R-P17-15）
      highlight_windows: false       # LSE-CAP-15 · Plus W4
      editorial_hints: false         # LSE-CAP-14 · Plus W4 MVP

  # 既有键保留，W1 起由 LSE 读取并 deprecated 直写：
  scoring: { ... }                   # → scoring_profiles.default
  template_engine: { ... }           # LTE，不变

mosaic: { ... }                      # W1 起 weights/penalties 可由 LSE profile 覆盖
```

### 7.2 自 `config.yaml` 碎片迁移映射

| 现配置路径 | 迁入 LSE |
|------------|----------|
| `layout.scoring.*` | `scoring_profiles.default` + `search.*` |
| `layout.screen_plan_scope` | `planning.screen_plan_scope` |
| `layout.mixed_proximity_seconds` | `planning.mixed_proximity_seconds` |
| `layout.template_engine.mcs_integration.scoring.diversity` | `diversity.*` |
| `mosaic.weights` / `mosaic.penalties` | `scoring_profiles.default` |
| `mosaic.enabled_window_sizes` | `planning.stages.mosaic.enabled_window_sizes` |
| `ScreenLayoutPlannerState` 分档常数 | `rhythm.nine_grid_limits` |

W1 须 **parity CI**：`enabled=false` 与迁移前 screens 快照一致。

---

## 8. 验收标准（AC）

> **轨道**：**Core** = Phase 17 完成必要条件；**Plus** = 不阻断发布。

| ID | 轨道 | 验收条件 |
|----|------|----------|
| **AC-P17-01** | Core | 存在 `layout.strategy_engine` 配置；`enabled=false` 时与 P16 末态 screens 快照一致。**parity 口径为「逻辑等价」**：在**受控环境**（固定时钟、禁用 `search_budget` 挂钟截断、单线程、固定 seed）下冻结基线比对；**不含**现网 wall-clock 截断这类负载相关的非确定行为（现网 `search_budget.py` 用 `time.monotonic` 门控会改变产出，见 §4.9 / IMPLEMENTATION-PHASE17 §受控 parity） |
| **AC-P17-02** | Core | 默认 Strategy Pack YAML 覆盖现网全部活跃排版参数；parity CI 通过 |
| **AC-P17-03** | Core | `LayoutStrategyEngine.load()` p99 \<1ms（内存索引，类比 AC-P16-12） |
| **AC-P17-04** | Core | 每次 curate 写入 `weightsHash` + `strategyId`（**FR-P17-TRACE**） |
| **AC-P17-05** | Core | 统一 decision log：每章至少 1 条 window 级记录（mosaic 启用时） |
| **AC-P17-06** | Core | Studio internal 可查看策略详情、决策样本、weights_hash |
| **AC-P17-07** | Core | L2 权重变更走双人审批（**W3 起**）；未审批 patch 不生效 |
| **AC-P17-08** | Core | L3 `overrides.disable_stages=[mosaic]` 后新 trip mosaic 曝光为 0 |
| **AC-P17-09** | Core | Trip 沙箱：固定 trip 换 profile 可产出 diff（**W3 起**） |
| **AC-P17-10** | Core | `layoutDensity=hero_first` 单槽屏占比 ≥ balanced +10pp（AC-LD-06） |
| **AC-P17-11** | Core | golden trip 探针纳入 CI（PR warn，release block） |
| **AC-P17-12** | Plus | telemetry 可按 `strategyId` / `profileId` 聚合 pattern_diversity_p50 |
| **AC-P17-13** | Core | `algorithm_version` 变更须显式 bump；audit 持久化 `weightsHash → 权重快照` 映射，**可按 hash 反查**历史日志对应的完整权重（hash 单向，非「解码」） |
| **AC-P17-14** | Core | RBAC：viewer 只读；operator 可 propose；admin 可 approve/rollback |
| **AC-P17-15** | Core | W0 阻断：`lse_strategy.schema.json` + `IMPLEMENTATION-PHASE17.md` + `DESIGN-PHASE17` 齐备 |
| **AC-P17-16** | Core | W3：`salient_retention` 混排 golden 人脸完整率 ≥ 基线 +3pp |
| **AC-P17-17** | Core | W3：`beat_profile=classic_magazine` 章首 hero 率 ≥ `flat` +8pp |
| **AC-P17-17b** | Core | W3 护栏：beat bias 提升章首 hero 率时，**章首 hero 图质量百分位（`QualityFeatures`）不低于 `flat` 基线**——防止为达成 +8pp 强推低质图上 hero（§4.8 优先级矩阵约束） |
| **AC-P17-18** | Core | W3：`tone_harmony=true` 相邻屏 ΔE p50 ≤ 基线 −10%；**日夜硬切豁免**不劣化观感 |
| **AC-P17-19** | Core | W4：匈牙利混排 golden **人脸完整率 ≥ 基线 +5pp 且 `salient_retention` p50 ≥ +5pp**（主指标，证明 CAP-01 收益）；per-window Kendall τ vs 贪心仅作**无灾难性回归护栏**（不要求高相关）；fail-open 回退贪心有 `fallbackReason` 日志；产出确定性可复现（tie-break + `max_matrix_n`，§4.5.1） |
| **AC-P17-20** | Plus | W4/W5：段内序同人 run-length p50 ≥ 基线 +15% |
| **AC-P17-21** | Plus | W4：`layoutFeedback` 可导出 pairwise 样本，无 C 端新 UI |
| **AC-P17-22** | Plus | W4：改 `layoutDensity` 后 re-curate layout-only replan；quick_share 无变化 |
| **AC-P17-23** | Core | C 端导入→成稿 **零步排版**；无新增确认步骤 |
| **AC-P17-24** | Plus | W5：`pace_profile` 中段章 mosaic 曝光 ≥ `flat` +10pp |
| **AC-P17-25** | Plus | W4：写入 `editorialHints`；无 hint 时 Editorial 快照不变 |
| **AC-P17-26** | Plus | W4：高光窗主位质量 ≥ 非高光 +8pp；**封面池不受影响** |
| **AC-P17-27** | Core | **quick_share** 路径 golden **零 diff**（R-P17-20） |
| **AC-P17-28** | Core | LSE 引入后 `run_curate` 耗时增量 ≤ **+15%**（§4.9） |
| **AC-P17-29** | Core | 精细制作成功页：非 balanced 时展示 **一行人话密度摘要**（S-P17-06、§4.4 文案表），无 CAP 术语 |
| **AC-P17-30** | Core | W3 渲染绑定：`CAP-02` 启用后，cover 类 slot 的渲染 `object-position` **实际反映** focal/salient（截图/计算回归，非仅打分日志）；pattern 级硬编码 `center` 覆盖已收敛或列入豁免清单（§4.10.1） |
| **AC-P17-31** | Core | 渲染产物 hash 的输入集合**不含** `decisionLog`/`editorialHints`/`capability_flags`/`weightsHash`；新增 LSE 可观测字段不影响 quick_share 零 diff（§4.10.2、AC-P17-27） |
| **AC-P17-32** | Plus | W5：`editorialHints` 含 `viewportScope`；移动端忽略 `folioHint`，渲染无对开误插（§4.10.3） |

---

## 9. 实施计划（评审修订版）

| 阶段 | 周期 | **P17-Core** 内容 | Plus（资源允许） | 出口 |
|------|------|-------------------|------------------|------|
| **P17-W0** | 设计冻结 | PRD v0.17.3、`lse_strategy.schema.json`、`IMPLEMENTATION-PHASE17.md`（Core 任务）、`DESIGN-PHASE17`、`beat×pace` 公式（§4.7） | — | R-P17-01～20；**AC-P17-15 阻断** |
| **P17-W1** | 1–2 周 | Registry + 单包 Strategy Pack + `adapter.py` + decision log + parity CI | — | AC-P17-01～05 |
| **P17-W2** | 1–2 周 | Studio **Inspector**（只读）+ L3 `overrides` | — | AC-P17-06、08、14 |
| **P17-W3a** | 0.5–1 周 | **先切引擎**：`enabled=true`（纯收敛、不带 CAP）+ 受控 parity + 零步 E2E + quick_share 零 diff（R-P17-05 解耦） | — | AC-P17-01/02/23/27 |
| **P17-W3b** | 1–1.5 周 | **再上算法**：CAP-02/03/04（§4.10 渲染绑定前置）+ golden probe + **审批+沙箱** + shadow 双轨 | dogfood 2 周（R-P17-20） | Core AC 16～18、30、31 |
| **P17-W4** | 2–3 周 | **CAP-01/08** 匈牙利 + QualityFeatures | CAP-05/06/10/14/15 | Core AC 19、28；Plus 20～26 |
| **P17-W5** | 持续 | — | CAP-07/09/13、Editorial 联动、多包 lifecycle、P17-B | Plus / P18 |

**原则**：

1. **切引擎与上 CAP 解耦（R-P17-05）**：W2 前 `enabled=false`；**W3a 先切引擎** `enabled=true`（纯收敛、不带 CAP）须过受控 **parity + 零步 + quick_share** 三连并稳定；**W3b 再逐个开 CAP-02/03/04**，任一回归可独立定位。
2. **W3 100% 切换前先跑 shadow 双轨对照**：单包无 A/B 对照组，仅 parity 不能证明「新行为优于 P16」。复用 `travelogue/templating/shadow.py`，让新策略**影子运行不影响产出**，采集新旧 screens diff 与指标（`pattern_diversity_p50`、`face_intact_rate`、`mosaic5.exposure`）；满足 **dogfood 准入指标**后再 100% 切。
3. **dogfood 准入指标（量化，非「不低于基线」弱观测）**：`face_intact_rate ≥ 基线 +3pp` 且 `pattern_diversity_p50 ≥ 基线` 且**无 P0 视觉回归**（人工盲评样本通过率 ≥ 90%）。
4. W1–W3 **仅** `lse-default-2026-06` 单包（R-P17-16）。
5. Core capabilities 默认开；Plus capabilities 默认关（§7.1）。
6. **标定自动上线不属于 P17**（R-P17-19 → P18）。

---

## 10. 测试计划

### 10.1 单元测试

- Registry：加载、status 过滤、runtime merge、profile 解析
- Validator：非法 stage 顺序、未知 pattern 引用、weight 越界
- Decision log：schema 校验、截断 `decision_log_max_events`
- Parity：`enabled=false` ≡ P16 末态；`enabled=true` + 默认 pack ≡ 迁移前 config 行为
- Rhythm：`nine_grid_limits` 与现 `ScreenLayoutPlannerState` 等价

### 10.2 集成测试

- `run_curate` 经 adapter：decision log 非空、weights_hash 稳定
- 审批流：propose 未批不生效；approve 后 revision+1
- `disable_stages`：mosaic 曝光归零
- `layoutDensity` 三档：golden fixture 密度指标
- 匈牙利匹配：超时回退贪心 + `fallbackReason` 日志
- 段内序：burst 不拆、跨段不重排负例
- 零步排版：E2E 导入→预览无新增确认步骤（AC-P17-23）
- `pace_profile`：首/中/末章倍率可观测；`flat` parity 回归
- `editorial_hints`：有/无 hint 双轨 Editorial 快照
- `highlight_windows`：高光窗不打破时间单调负例
- quick_share：layout golden **零 diff**（AC-P17-27）
- 性能：`run_curate` 增量 ≤15%（AC-P17-28）

### 10.3 回归与 Dogfood

- 扩展 `scripts/phase16_template_eval.py` → `phase17_strategy_eval.py`
- Golden trip **三类各 ≥2**：家庭混排 / 风景横图 / 人像竖图
- 探针：**PR warn，release block**（对齐 P16）
- 盲评样本导出 feature 矩阵（为 W4 标定铺路）

---

## 11. 风险与缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| 与 `screen_planner` 大迁移 | 延期、回归爆炸 | adapter 防腐层；stages 渐进迁，不整文件搬家（ADR-010） |
| config 碎片未收敛 | parity 失败 | W1 强制 parity CI；默认 `enabled=false` 直至通过 |
| 后台误调权重 | 全量成稿劣化 | L2 双人审批 + 沙箱 diff 阈值 + 7 天 KPI  watch |
| LSE/LTE 边界模糊 | 改几何误走 LSE | Validator 禁止 LSE YAML 含 `slots[]` |
| 决策日志体积 | trip.json 膨胀 | sidecar + `max_events` 截断；telemetry 聚合 |
| 标定样本不足 | W4 空转 | 先 Inspector + 沙箱，标定提案人工触发 |
| P17-B 预研干扰主线 | 资源分散 | 仅生成式/LTE 扩展留 P17-B；匈牙利已升格 W4 主线 |
| 能力增强破坏零步体验 | 用户感知「变复杂」 | AC-P17-23 E2E 门禁；C 端不增 UI；quick_share 回归无 diff |
| 隐式反馈隐私/噪声 | 误标定 | 仅采集编辑事件；导出离线；审批后才改权重 |

---

## 12. 指标与 North Star

| 指标 | 定义 | 数据源 | W3 门禁 |
|------|------|--------|---------|
| `layout.chapter.pattern_diversity_p50` | 章内 pattern 种类数 p50 | decision_log | 不低于 P16 基线 |
| `layout.mosaic5.exposure_rate` | 五窗 mosaic 占比 | telemetry | dogfood 可对比 |
| `layout.density_intent_match_rate` | 非 balanced 意图达成率 | density profile + screens 统计 | ≥80%（fixture） |
| `layout.strategy.weights_change_count` | 月内审批通过次数 | audit | 可观测即可 |
| `layout.sandbox.diff_rate` | 沙箱与线上 screens 差异率 | sandbox API | 调参前必跑 |
| `layout.mixed.face_intact_rate` | 混排窗人脸完整率 | golden + saliency | W3 ≥基线+3pp |
| `layout.segment.same_person_run_p50` | 段内同人 run 长度 p50 | segment_order 日志 | W4 ≥基线+15% |
| `layout.feedback.events_per_trip` | 隐式反馈事件数 | layout-feedback.jsonl | 可观测即可 |
| `layout.beat.hero_first_screen_rate` | 章首屏 hero/单槽占比 | decision_log | W3 ≥flat+8pp |
| `layout.pace.mid_chapter_mosaic_rate` | 中段章 mosaic 占比 vs flat | decision_log | W3 ≥flat+10pp |
| `layout.highlight.hero_quality_delta` | 高光窗 vs 非高光主位质量差 | highlight 日志 | W4 ≥+8pp |
| `layout.editorial.hint_adoption_rate` | breath/folio hint 被采纳比例 | editorialDecisionLog | 可观测即可 |

---

## 13. 附录

### 13.1 Strategy Pack YAML 草案（v0）

```yaml
id: lse-default-2026-06
version: 1
status: ga
algorithm_version: p15-s2
displayName: 默认智能排版策略
description: >
  P17 默认策略包：收敛 layout.scoring + mosaic 权重 + 节奏配额。
  行为目标与 P16 末态 parity。

planning:
  screen_plan_scope: day
  mixed_proximity_seconds: 12
  stages:
    enabled: [hero, mosaic, mixed, landscape, portrait, flush, tall]
    mosaic:
      min_trip_photos: 20
      enabled_window_sizes: [3, 4, 5, 6, 8, 9]

rhythm:
  beat_profile: classic_magazine    # LSE-CAP-03 · Core W3
  pace_profile: flat                # LSE-CAP-13 · Plus W5 改为 memories_pace
  pace_curve:                       # W5 启用 memories_pace 时生效
    memories_pace:
      - { chapter_frac_max: 0.25, multiplier: 0.85 }
      - { chapter_frac_max: 0.75, multiplier: 1.15 }
      - { chapter_frac_max: 1.00, multiplier: 0.90 }
  nine_grid_limits:
    - { max_photos: 50, min: 0, max: 1 }
    - { max_photos: 100, min: 2, max: 5 }
    - { max_photos: 200, min: 4, max: 8 }
    - { max_photos: 999999, min: 6, max: 10 }
  consecutive_bans:
    - { kinds: [nine, nine], blocked: true }

slot_assignment:
  mode: greedy                      # W4 起改为 hungarian
  max_matrix_n: 16                  # 确定性预算（替代 timeout_ms，§4.9）

features:
  saliency_scoring: true
  tone_harmony: true
  quality_unified: false            # W4 开启

density_profiles:
  balanced:
    nine_bias: 0.0
    prefer_single: false
    prefer_mosaic: false
  hero_first:
    nine_bias: -0.3
    prefer_single: true
  collage_first:
    nine_bias: 0.3
    prefer_mosaic: true

pattern_policy:
  blacklist: []
  lte_overrides_disable: []

scoring_profiles:
  default:
    weights:
      aspect_match: 0.20
      sharpness: 0.15
      temporal_coherence: 0.15
      hero_separation: 0.10
      subject_run: 0.10
      layout_rhythm: 0.10
      diversity: 0.10
      category_coherence: 0.10
      tone_continuity: 0.08          # LSE-CAP-04 · R-P17-10
      luminance_continuity: 0.06
    penalties:
      face_crop: 0.30
      salient_crop: 0.28             # LSE-CAP-02 · 与 face_crop 合并计分口径
      main_quality: 0.25
      duplicate_density: 0.20
      hero_narrow_tiles: 0.35
      hero_slot_aspect: 0.40
      flat_six_grid: 0.35

segment_order:
  enabled: false                    # W4 开启 · LSE-CAP-06
  max_segment_len: 30
  weights:
    same_person_adjacency: 0.25
    scenery_run: 0.15
    chronological_smoothness: 0.35

feedback:
  enabled: true                     # LSE-CAP-05 · 隐式 only
  export_pairwise: false            # W4 开启离线导出

highlight_windows:
  enabled: false                    # W4 开启 · LSE-CAP-15
  window_sizes: [5, 8, 12]
  boost: 1.25
  max_windows_per_chapter: 2

editorial_hints:
  enabled: false                    # W4 开启 · LSE-CAP-14
  breath_gap_threshold: 3             # 连续多槽屏数触发 breath 建议
  folio_tone_delta_max: 12.0          # Lab ΔE 阈值

search:
  beam_width: 3
  max_evaluations_per_trip: 500     # 确定性上限：达到即停（产出可复现）
  search_timeout_ms: 2000           # 仅 telemetry 告警，不改变产出（§4.9）
  min_candidate_score: 0.35
  max_screens_per_chapter: 12

diversity:
  mode: mmr
  lambda: 0.65

self_heal:
  enabled: true
  allow_drop: false
  max_drop_ratio: 0.05

rollout:
  traffic_percent: 100
  allowed_profiles: [default]
```

### 13.2 P17-B 可选轨（LTE 扩展 · 不阻塞 LSE 主线）

> 匈牙利匹配、隐式反馈、layout-only replan 已升格为 **§4.5 主线**（W3–W4）。本轨仅保留 LTE 几何扩展。

| 方向 | 说明 | 出口条件 |
|------|------|----------|
| **生成式 composite** | guillotine 枚举 + LTE validator 过滤 | 新模板晋升 ga |
| **7 张 4P+3L** | `4×3` 舞台新模板（LTE 侧） | LTE admission 通过 |

Hook 点：`compose.score_window_candidates` 之后、`pick_best_window` 之前；`travelogue/layout_templates/p17_research.py`。

### 13.3 关联 Phase 路线图

```
P15 MCS → P16 LTE → P17 LSE（Core/Plus） → P18（标定上线·构图角色·全册风格）
```

### 13.4 W0 阻断交付物（S-P17-05）

| 交付物 | 路径 | 阻断 |
|--------|------|------|
| JSON Schema | `travelogue/layout_engine/lse_strategy.schema.json` | W1 不开工 |
| 实施清单（Core） | `docs/IMPLEMENTATION-PHASE17.md` | W1 不开工 |
| 设计说明 | `docs/DESIGN-PHASE17-layout-strategy-engine.md` | W1 不开工 |
| beat×pace 公式 | PRD §4.7 | W3 不开 beat/pace 联调 |
| **LayoutFeatures 值域契约** | PRD §4.6 + schema | **W1 不开工**（A：是 §4.3 解释层前置） |
| **因子归因口径（log-domain）** | PRD §4.3 | **W3 解释层不开工** |
| **确定性预算改造**（移除 wall-clock 改产出） | PRD §4.9 / §4.5.1 | **W4 匈牙利不开工**（B：违反 D-P17-05） |
| **性能 spike 报告**（各能力 × trip 规模实测增量） | `docs/IMPLEMENTATION-PHASE17.md` | **W3 能力开启前**（E：+15% 预算需证据） |
| **审批语义对齐 ADR**（提议人+2 审批 vs 严格双人） | ADR + §5.3 | W2 审批落地前 |
| **渲染落地契约**（focal/salient CSS 绑定 + object-position 收敛 + 字段隔离） | PRD §4.10 + `journal-screens.css` | **W3 CAP-02 不上线**（前端：算法白算风险，AC-P17-30/31） |
| **成功页归属确认 + 文案表/i18n** | §4.4 文案表 | AC-P17-29 落地前 |

### 13.5 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.17.6 | 2026-06-07 | 开发负责人评审落地：AC-P17-01 parity 口径改为「受控环境逻辑等价」（剥离 `search_budget` 挂钟非确定行为）；R-P17-05 + §9「切引擎与上 CAP 解耦」（W3 拆 W3a 切引擎 / W3b 上算法）；配套 `docs/IMPLEMENTATION-PHASE17.md`（含与现有代码融合方案、三项 W0 审计、受控 parity 跑法、adapter 参数收束） |
| v0.17.5 | 2026-06-07 | 前端/页面负责人评审落地：§4.10 渲染落地契约（focal/salient CSS 绑定 + object-position 硬编码收敛 + 渲染输入字段隔离 + viewport 适配）；§5.1.1 Inspector 前端实现规格（虚拟滚动/分布条/裁切告警/沙箱并排 diff/五态/RBAC）；§4.4 成功页文案表 + i18n；§4.5.12 `viewportScope` + 渲染消费占位；新增 AC-P17-30/31/32；§13.4 增补 2 项 W0/W3 阻断（渲染绑定、成功页归属）；§17.3 前端评审纪要 |
| v0.17.4 | 2026-06-07 | CTO/算法专家技术评审落地：§4.6 LayoutFeatures 值域契约；§4.3 log-domain 因子归因口径；§4.5.1 匈牙利主指标改人脸/salient + τ 降护栏 + tie-break + 仅解 asset→slot 边界；§4.5.4 tone 改 look-back 后处理 + 边界豁免；§4.5.5 复用 feedback.py 去噪 + 有效 label 过滤；§4.9 确定性预算（移除 wall-clock 改产出）+ 性能 spike；§5.3 审批语义对齐 + 标注 L0 改动；AC-P17-13/17b/19 修订；§9 shadow 双轨 + dogfood 准入；§13.4 增补 5 项 W0 阻断；§17 技术评审纪要 |
| v0.17.3 | 2026-06-07 | 跨职能评审决议：P17-Core/Plus/B 三分（§2.4）；砍并分期（pace→W5、DPP→W5、单包 lifecycle、标定→P18）；§4.7–4.9；AC 分轨 + AC-P17-27～29；§9 修订；§16 纪要 |
| v0.17.2 | 2026-06-07 | 增补 LSE-CAP-13～15：`pace_profile`、Editorial `editorial_hints`、章内 `highlight_windows`；G-P17-17～19、R-P17-11～13、AC-P17-24～26 |
| v0.17.1 | 2026-06-07 | 增补：产品原则（最小用户干扰·零步排版）；§1.4 业内对标；§2.3 能力增强分期；§4.5–4.6 十二项能力规格与 LayoutFeatures；G-P17-10～16、AC-P17-16～23；W3/W4/W5 分期调整；匈牙利升格主线 |
| v0.17.0 | 2026-06-07 | 初稿：智能排版引擎（LSE）PRD；含 Strategy Pack、四层自由度、治理复用、决策日志、后台 API、验收与分期 |

---

## 14. W0 已决议题（原待议 · 已冻结）

| 议题 | 决议 |
|------|------|
| 包名 | **`travelogue/layout_engine/`**（R-P17-01） |
| decision log | **sidecar 默认**，trip 存摘要 hash |
| W3 `enabled=true` | **shadow 双轨对照达准入** → **parity + 零步 E2E + quick_share 零 diff** 三连 → 100% 切；建议 dogfood 2 周（R-P17-20、§9 原则 2–3） |
| QualityFeatures / 匈牙利 | **W4 Core**（非 W3） |
| 特征层统一 | **W4** `CAP-08` |
| 策略包 lifecycle 5 态 | **W5**；W1–W3 单包（R-P17-16） |

**P17-Core 成功标准（发布闸门）**：

1. §8 全部 **Core** AC 通过（含 AC-P17-27、28、29）
2. Plus AC 不阻断发布
3. dogfood `pattern_diversity_p50` 不低于 P16 基线（观测项）

---

## 16. 跨职能评审纪要（2026-06-07）

| 属性 | 内容 |
|------|------|
| **结论** | **有条件通过** — 方向与零步排版原则全员赞成；v0.17.2「15 CAP 同 Phase 交付」**驳回** |
| **参会** | 产品 · 算法 · 架构 · 需求 · UX · 交互 |

### 16.1 决议摘要

| 类别 | 决议 |
|------|------|
| **砍/推迟** | CAP-07 DPP→W5；CAP-09→P18；CAP-11/12→P17-B；pace_profile W3 不开→W5；标定自动上线→P18；多包 lifecycle→W5；Editorial 强制消费→W5 |
| **Core 重点** | W1 骨架 + W2 Inspector + W3 CAP-02/03/04 + W4 CAP-01/08 |
| **Plus** | CAP-05/06/10/14/15、段内序、pace、DPP |
| **补充** | §2.4 三分法、§4.7–4.9、§13.4 W0 阻断、AC 分轨、quick_share 零 diff、成功页人话一行 |
| **额外** | 用户 KPI 与工程 KPI 分报；封面链与 LSE 显式分离（§4.8）；Inspector 用条形图+裁切告警 |

### 16.2 会后行动（1 周内）

| # | 行动 | 状态 |
|---|------|------|
| 1 | PRD → v0.17.3（本文） | ☑ |
| 2 | `lse_strategy.schema.json` 草案 | W0 待办 |
| 3 | `IMPLEMENTATION-PHASE17.md`（Core 任务） | W0 待办 |
| 4 | `DESIGN-PHASE17-layout-strategy-engine.md` | W0 待办 |
| 5 | 成功页一行文案 + Inspector 线框 | W1 前待办 |

---

## 17. CTO / 算法专家技术评审纪要（2026-06-07 · v0.17.4）

| 属性 | 内容 |
|------|------|
| **结论** | **有条件通过**（维持）——方向、分轨、治理复用、零步原则全员肯定；新增 8 项技术修订作为「有条件」的硬条件，其中 4 项升为 W0 阻断 |
| **评审视角** | CTO（架构/工程风险）+ 智能排版算法专家 |
| **代码核对** | `screen_planner.py` 1007 行 God 文件、`mosaic/scorer.py` 乘性、`config_governance` 硬编码 if-chain + `approvals>=2`、`feedback.py` 已有 G1 去噪——均与 PRD 描述一致 |

### 17.1 修订决议（已落地本文）

| # | 问题 | 严重度 | 落地节 |
|---|------|--------|--------|
| A | 打分「半统一」陷阱：topFactors 在乘性模型无定义 | **阻断** | §4.6 值域契约 + §4.3 log-domain 归因 |
| B | 确定性被 wall-clock 破坏（timeout 改产出） | **阻断** | §4.9 确定性预算 + §4.5.1 tie-break/`max_matrix_n` |
| C | 匈牙利 AC（τ≥0.90）与收益目标自相矛盾 | 高 | §4.5.1 + AC-P17-19（主指标改人脸/salient，τ 降护栏） |
| D | tone 连贯进 beam → 复杂度爆炸 | 高 | §4.5.4 改 look-back-1 后处理 + 边界豁免 |
| E | +15% 预算无 spike 证据 + 运行时降级破坏确定性 | 高 | §4.9 静态分档 + W0 性能 spike |
| F | 隐式反馈信号混淆，未引用既有去噪 | 中 | §4.5.5 复用 `feedback.py` + 有效 label 过滤 |
| G | beat bias 可能牺牲 hero 质量 | 中 | 新增 AC-P17-17b 护栏 |
| H | 「双人审批」语义与代码不一致 + 误判零代码治理 | 中 | §5.3 语义对齐 + 标注 L0 改动 + W0 ADR |
| I | weightsHash「可解码」措辞错误 | 中 | AC-P17-13 改「快照 + 可反查」 |
| J | 单包 100% 直切无对照组 | 中 | §9 shadow 双轨 + 量化 dogfood 准入 |

### 17.2 W0 新增阻断（见 §13.4）

LayoutFeatures 值域契约、log-domain 归因口径、确定性预算改造、性能 spike 报告、审批语义 ADR。

### 17.3 前端 / 页面负责人评审纪要（2026-06-07 · v0.17.5）

| 属性 | 内容 |
|------|------|
| **结论** | 维持「有条件通过」；补 6 项前端落地内容，其中**渲染绑定升为 W3 阻断** |
| **代码核对** | `render/context.py` 输出 `--focal-x/y`、基础 CSS 消费正确；但 `journal-screens.css` 多处 pattern 级 `object-position: center/center 30%/top center` **硬编码覆盖** focal → CAP-02 像素层不生效 |

| # | 缺口 | 严重度 | 落地节 |
|---|------|--------|--------|
| 前-1 | salient 裁切算法产出未绑定到 DOM（CSS 硬编码覆盖 focal） | **阻断** | §4.10.1 + AC-P17-30 + §13.4 |
| 前-2 | quick_share 零 diff 缺前端字段隔离约束 | **阻断** | §4.10.2 + AC-P17-31 |
| 前-3 | Inspector 无前端实现规格（2000 events 渲染、分布条、沙箱 diff） | 高 | §5.1.1 |
| 前-4 | 成功页一行文案无文案表/i18n/归属 | 中 | §4.4 文案表 + §13.4 |
| 前-5 | 移动端 / 对开适配缺失（folioHint 无视口语义） | 中 | §4.10.3 + §4.5.12 `viewportScope` + AC-P17-32 |
| 前-6 | editorial_hints → DOM 渲染契约（W5） | 占位 | §4.5.12 |

---

*本文档 v0.17.5 为 **有条件通过**；W1 开工前须完成 §13.4 全部 W0 阻断交付物；§4.10 渲染落地契约为 **W3 CAP-02 上线阻断**。*
