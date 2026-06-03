# Travelogue · Phase 13 产品需求文档（PRD · 模板系统与智能路由）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue |
| **文档版本** | v0.13.4-PHASE13 |
| **状态** | Draft（补充架构约束版） |
| **Phase 13 代号** | 「模板系统化」— 从单模板升级为多模板自动匹配与可指定 |
| **前置条件** | [PRD-PHASE12.md](./PRD-PHASE12.md) 已上线（选片质量增强）；`visual-journal` screens 链路稳定 |
| **关联文档** | [TEMPLATE-visual-journal.md](./TEMPLATE-visual-journal.md)、[RENDER-CONTRACT.md](./RENDER-CONTRACT.md)、`render/engine.py`、`services/validate.py` |
| **更新日期** | 2026-06-03 |

> **定位**
>
> - 当前系统是单模板（`visual-journal`）硬编码实现，Phase 13 将其升级为“模板平台能力”。
> - 用户创建时新增模板选择入口：**默认智能匹配**，并支持下拉手动指定模板。
> - 预留后台模板治理入口：支持模板新增、编辑、删除（CRUD）及调试回放（仅管理端可见）。
> - 仍坚持“务实优先”：先完成平台抽象与稳定路由，再扩展模板数量。

---

## 1. 背景与问题

当前代码已具备强渲染与编排能力，但模板能力存在结构性限制：

1. `render_html()` 仅支持 `visual-journal`，其它模板直接报错（`E_RENDER_TEMPLATE`）。
2. `paths.py`、`manifest_limits.py`、`validate.py` 等路径与规则读取绑定 `templates/visual-journal`。
3. `trip.schema.json` 中 `templateId` 为常量，无法表达多模板。
4. 缺少“模板自动路由”与“人工指定优先级”机制。

因此，模板扩展目前属于“复制粘贴工程”，不可持续。

---

## 2. 目标与非目标

### 2.1 目标

| ID | 目标 | 说明 |
|----|------|------|
| **G-P13-01** | 建立模板注册与渲染抽象层 | 支持多个模板并保持向后兼容 |
| **G-P13-02** | 提供智能模板匹配 | 默认自动匹配，低置信回退稳定模板 |
| **G-P13-03** | 提供用户可控入口 | 创建时可在下拉中手动指定模板 |
| **G-P13-04** | 保持现有主链路稳定 | 导入、渲染、长图、放映不回归 |
| **G-P13-05** | 支持后续模板横向扩展 | 游记之外可扩展活动/家庭/运动等 |
| **G-P13-06** | 提供后台模板治理能力 | 支持模板新增、编辑、删除、上下线与调试 |

### 2.2 非目标（本 Phase 不做）

- 不做“模板市场”或 C 端用户自定义模板编辑器（后台治理入口除外）。
- 不做重型在线学习推荐系统（先规则+轻量打分）。
- 不要求首批同时上线大量新模板（先 1-2 个试点模板）。
- 不改动用户导入主流程的“自动生成”本质（选择模板仅创建入口可选）。

---

## 3. 设计原则（硬约束）

| ID | 原则 | 约束说明 |
|----|------|----------|
| **P13-PR-01** | 向后兼容 | 历史 `visual-journal` trip 必须零迁移可渲染 |
| **P13-PR-02** | 智能优先 | 创建默认使用“智能匹配” |
| **P13-PR-03** | 人工可控 | 用户可下拉指定模板并覆盖智能选择 |
| **P13-PR-04** | 低置信保守回退 | 智能匹配不确定时回退稳定模板 |
| **P13-PR-05** | 分层解耦 | 模板注册、路由、策展、渲染、校验分层 |
| **P13-PR-06** | 可观测可回滚 | 模板决策、命中率、失败码可追踪，可一键回退 |
| **P13-PR-07** | 决策可复现 | 模板决策需可冻结、可回放、可解释 |
| **P13-PR-08** | 治理最小权限 | 模板 CRUD 与路由调试仅对授权后台角色开放 |
| **P13-PR-09** | 真值单入口 | 模板读取统一通过 `resolve_effective_template()`，禁止多处直读 |
| **P13-PR-10** | 发布原子性 | 模板发布必须 registry/manifest/adapter/assets 一致可用后才可见 |
| **P13-PR-11** | 并发安全 | 模板状态变更需版本号保护与冲突检测 |

---

## 4. 用户与产品流程

## 4.1 创建入口（新增）

在前端“新建游记/项目”界面新增模板选择组件：

- 默认值：`智能匹配（推荐）`
- 组件形式：下拉菜单
- 下拉项（首版建议）：
  - `智能匹配（推荐）`
  - `视觉游记（visual-journal）`
  - `活动回顾（event-recap）`（若首版未上线则灰置/隐藏）

> 用户要求确认：默认智能，同时支持人工指定。本 PRD 按此执行。

## 4.2 选择优先级（权威）

1. 用户手动指定模板（最高优先）
2. 智能匹配结果（仅当用户选“智能匹配”）
3. 系统保底回退模板（`visual-journal`）

## 4.3 用户可见反馈

- 智能模式下，在创建成功提示中展示：`已为你匹配：xxx 模板`。
- 手动模式下展示：`已使用：xxx 模板`。
- 若智能失败并回退，显示轻提示：`已回退到默认模板（视觉游记）`。

## 4.4 后台模板治理入口（新增）

为支持快速试验与运维，本 Phase 预留后台调试入口（非 C 端）：

- 模板管理：
  - 新增模板（注册 manifest + 目录绑定）
  - 编辑模板元信息（名称、状态、能力、路由提示）
  - 删除/下线模板（受引用保护，默认逻辑删除）
- 调试工具：
  - 输入 `tripId` 进行模板路由回放（展示特征、分数、reasonCodes）
  - 强制指定模板进行一次性渲染验证（不落库）
  - 查看最近 N 次模板决策日志
- 权限模型（建议）：
  - `template_admin`：可 CRUD 与上下线
  - `template_operator`：可调试回放，不可删除
  - 所有操作写审计日志

---

## 5. 功能规格（系统级）

## 5.1 模板注册中心（Template Registry）

新增注册中心，定义每个模板的标准元信息：

- `template_id`
- `version`
- `template_dir`
- `manifest_path`
- `renderer_adapter`
- `curation_adapter`
- `fallback_template_id`
- `capabilities`（map/voice/video/route 等）

约束：

- 未注册模板不可选。
- 注册中心是模板能力唯一入口，不允许业务侧硬编码模板路径。

发布一致性约束（新增）：

1. 模板对外“可选/可路由”前，必须通过完整健康检查：`registry + manifest + adapter + assets`。
2. 任一检查失败时，模板保持不可见状态，不得半发布。
3. 模板发布与下线操作需记录 `registryVersion`。

## 5.2 模板路由器（Template Router）

输入：trip 素材与元数据特征  
输出：`template_id`, `confidence`, `reason_codes`, `fallback_used`

首版策略：

1. 规则优先（高确定性规则）
2. 轻量打分补充（可解释）
3. 低置信回退 `visual-journal`

首版无需引入训练服务。

## 5.3 模板适配器

### Curation Adapter
- 负责结构规划（章节/屏幕/块组合）

### Render Adapter
- 负责上下文组装与 Handlebars 渲染
- 负责模板静态资源复制与导出兼容

`visual-journal` 作为首个 adapter 完整迁入，功能保持不变。

## 5.4 校验分层

- **L1**：通用 schema 校验（trip 基础结构）
- **L2**：模板 manifest 校验（limits/patterns/rules）
- **L3**：模板能力与素材匹配校验（如地图模板无轨迹）

## 5.5 模板治理能力（CRUD）

模板对象建议引入治理状态机：

- `experimental`（实验）
- `beta`（灰度）
- `ga`（正式）
- `deprecated`（待退役）
- `disabled`（停用）

CRUD 约束：

1. **新增**：必须通过 manifest/schema 静态校验方可注册。
2. **编辑**：版本升级需记录变更说明与操作者。
3. **删除**：若已有 trip 引用，禁止物理删除，改为 `disabled`。
4. **下线**：不再参与新建路由，但历史 trip 仍可渲染。

## 5.6 模板决策冻结与重算策略

为保证可复现性，定义如下规则：

1. 首次路由完成后写入 `templateSelection`（含 routerVersion、reasonCodes）。
2. 当 `templateSelection.mode=manual` 时，禁止自动重算模板。
3. 当 trip 进入 `copy_locked` 或等价锁定状态后，默认禁止模板重算。
4. 仅在“未锁定 + 智能模式 + 明确触发重算”时允许重算，并保留历史记录。

锁定语义对齐（新增）：

- `template_locked = true` 的判定统一来自业务锁状态聚合函数，不允许前后端各自解释。
- `copy_locked`、`pipeline.locks.copy=true`、同等业务冻结态均映射到 `template_locked=true`。

## 5.7 模板发现与分发能力（Discovery）

借鉴 Canva / Notion 模板平台实践，模板系统需具备基础发现能力：

- 标准元信息：`category`, `tags`, `style`, `complexity`, `bestFor`。
- 模板列表排序维度：推荐、热门、最新、团队常用。
- 创建下拉中的模板展示遵循“已上线 + 当前可用 + 用户有权限”。
- 后台可配置“推荐模板集”，用于创建页默认曝光顺序。

约束：

1. 未进入 `ga` 或未灰度命中的模板，不进入 C 端可选下拉。
2. 模板标签必须来自受控词表，避免自由文本污染检索。

## 5.8 可编辑护栏（Guardrails）

借鉴 Canva 模板锁定策略，确保“可编辑但不易改坏”：

- 锁定结构元素：章节容器、关键布局栅格、法律/版权文案位（若有）。
- 开放内容元素：标题、正文、图片/视频替换、可编辑 caption。
- 占位符规范：模板必须提供文本/图片占位提示，避免空白块。

渲染与编辑约束：

1. 模板需声明 `editableScopes` 与 `lockedScopes`。
2. 编辑器侧仅允许修改 `editableScopes` 内字段。
3. 若模板不声明护栏信息，禁止上架到 `ga`。

## 5.9 模板准入审核与质量门槛

借鉴 CapCut / Notion 审核实践，模板发布前需通过准入：

- 结构正确性：能完整渲染，不出现空容器或断链。
- 素材鲁棒性：对长文本/竖图/横图/多视频场景不崩版。
- 可复用性：不绑定私有路径，不依赖本地临时资产。
- 合规性：命名、描述、版权与敏感内容符合平台规范。

准入流程（后台）：

1. 静态校验（manifest/schema/目录完整性）
2. 自动渲染回归（黄金样例 + 边界样例）
3. 人工评审（设计与可用性）
4. 进入 `experimental` 或 `beta`

## 5.10 前端工作项（P13 必做）

为确保模板系统可用且可理解，前端需完成以下任务：

### 创建页（C 端）

1. 新增模板选择组件（下拉）：
   - 默认：`智能匹配（推荐）`
   - 可选：已上线且有权限模板
2. 模式切换行为：
   - `smart`：展示自动匹配说明
   - `manual`：展示模板说明与适配场景
3. 创建结果反馈：
   - 智能命中、手动指定、回退默认三种提示文案

### 项目详情页（C 端）

1. 展示当前模板与来源（smart/manual/fallback）。
2. 展示模板锁定状态（如 `copy_locked` 后不可重算）。
3. 支持受控入口进行模板策略调整（按权限与锁定状态）。

### 异常态与降级态

1. 路由失败、模板不可用、权限不足需有明确提示。
2. 任何异常均可回退默认模板，创建流程不中断。

### 前端埋点（与指标对齐）

- `template_selector_impression`
- `template_mode_changed`
- `template_manual_selected`
- `template_smart_result_shown`
- `template_fallback_shown`
- `template_create_submitted`

## 5.11 管理后台（Admin Console）建设要求（P13 起）

从 P13 开始，模板系统进入平台化阶段，需建设管理后台（仅管理端）：

### 核心模块

1. **模板管理**
   - 模板列表/筛选（状态、分类、版本、更新时间）
   - 新增/编辑/下线/逻辑删除
   - 版本对比与变更记录
2. **路由调试**
   - 按 `tripId` 回放模板决策
   - 展示特征摘要、confidence、reasonCodes、fallback 过程
   - 支持“一次性强制模板预览渲染”（不落库）
3. **发布治理**
   - 模板状态流转（experimental -> beta -> ga -> deprecated -> disabled）
   - 灰度策略配置（流量比例、白名单）
   - 一键回滚（按模板或全局）
4. **审计与报表**
   - 操作审计日志（谁在何时改了什么）
   - 模板效果看板（命中率、回退率、错误率、采纳率）

### 权限与安全

建议最小角色模型：

- `template_admin`：CRUD、上下线、灰度与回滚
- `template_operator`：调试回放、只读分析
- `viewer`：只读看板

安全要求：

1. 后台接口默认鉴权，建议内网或管理域访问。
2. 高风险操作（删除、下线、全局切换）需要二次确认。
3. 支持审计追踪与按操作回放。

---

## 6. 数据模型与接口变更

## 6.1 trip.json 字段扩展（建议）

```json
{
  "templateId": "visual-journal",
  "templateSelection": {
    "mode": "smart",
    "requestedTemplateId": null,
    "resolvedTemplateId": "visual-journal",
    "confidence": 0.91,
    "reasonCodes": ["R_TIME_GEO_STORY"],
    "fallbackUsed": false,
    "routerVersion": "p13-r1",
    "routerConfigVersion": "cfg-2026-06-03-01",
    "featureSnapshotVersion": "feat-v1",
    "registryVersion": "registry-v3",
    "locked": false,
    "lockedAt": null,
    "decisionHash": "sha256:..."
  }
}
```

说明：

- `mode`: `smart | manual`
- `requestedTemplateId`: 用户手动指定时有值
- `resolvedTemplateId`: 最终生效模板
- `locked`: 模板决策冻结标记
- `routerConfigVersion/featureSnapshotVersion/registryVersion`: 回放复现必需快照版本

## 6.2 schema 变更

- `templateId` 从 `const` 改为 `enum`（首版模板集）
- 新增 `templateSelection` 定义（可选，向后兼容）

## 6.3 创建接口（Studio/后端）变更

新增创建参数：

- `template_mode`：`smart | manual`（默认 `smart`）
- `template_id`：手动模式必填，智能模式可空
- `recompute_template`：调试接口可选；生产创建接口默认 `false`

## 6.4 真值模型（权威）

为避免前后端不一致，定义单一真值：

1. `templateSelection.resolvedTemplateId` 为最终渲染模板真值。
2. `templateId` 作为兼容镜像字段，渲染前需与 `resolvedTemplateId` 对齐。
3. 当两者不一致时，记录告警并以 `resolvedTemplateId` 为准。

实现约束（新增）：

4. 渲染、校验、导出、后台展示统一调用 `resolve_effective_template(trip)` 获取模板。
5. 除 `TripService` 同步镜像外，业务模块禁止直接写 `templateId`。

---

## 7. 首批模板范围（务实版）

## 7.1 P13 必做

- `visual-journal`（迁移到注册中心，不改视觉输出）

## 7.2 P13 可选试点（二选一，建议做 1 个）

- `event-recap`（活动回顾）
  - 适配单日活动、多视频、高光总结
  - 相对地图型模板实现成本更低，适合作为第二模板试点

---

## 8. 后台智能匹配规则（首版）

示例特征：

- 时空：跨天数、跨地点数、轨迹连续性
- 内容：人物占比、视频占比、语音占比、食物/活动标签占比
- 语义：caption/transcript 关键词（活动、家庭、徒步等）

示例策略（首版）：

- 多天+多地+路线清晰 -> 倾向 `visual-journal` / map 类
- 单天+高视频占比+活动关键词 -> 倾向 `event-recap`
- 不满足任何高置信规则 -> 回退 `visual-journal`

## 8.1 reasonCodes 标准化（首版）

为保证可解释与可观测，reasonCodes 采用稳定枚举：

- `R_MANUAL_OVERRIDE`：用户手动指定
- `R_ROUTE_MULTI_DAY`：多天多地路线特征显著
- `R_EVENT_VIDEO_HEAVY`：活动型且视频占比高
- `R_LOW_CONFIDENCE_FALLBACK`：低置信回退默认模板
- `R_TEMPLATE_DISABLED_FALLBACK`：目标模板下线导致回退

要求：

1. reasonCodes 版本化，随 `routerVersion` 记录。
2. telemetry 与报表维度使用同一枚举，不得自由文本拼接。

---

## 9. 配置与运维开关

建议新增配置：

```yaml
template_router:
  enabled: true
  default_template: visual-journal
  confidence_threshold: 0.65
  allow_manual_override: true
  allowed_templates:
    - visual-journal
    - event-recap
```

运维能力：

- 可强制全局模板（应急）
- 可关闭路由器回到单模板
- 可灰度放量新模板

## 9.1 配置治理与审批

为避免误配，模板路由配置变更需满足：

1. 配置变更走受控发布（禁止在线热改生产主配置）。
2. 关键参数（阈值、白名单、默认模板）需双人复核。
3. 配置生效需记录版本号与生效时间，支持按版本回滚。

## 9.2 迁移与回滚策略（必备）

迁移分三步：

1. 只引入 registry，不改变渲染结果（影子模式）。
2. 打开创建页智能/手动选择，仍以 `visual-journal` 为主。
3. 灰度第二模板并观测 fallback/error 指标。

回滚策略：

- 一级回滚：关闭路由器（所有新建使用默认模板）
- 二级回滚：下线新增模板（保留历史渲染能力）
- 三级回滚：切回单模板兼容路径（应急）

并发保护（新增）：

- 模板状态更新需携带版本号（ETag/Revision），冲突时拒绝写入并提示重试。
- 下线模板与创建并发时，创建请求以“提交时模板可用性检查”结果为准，不得使用已下线模板。

## 9.3 非功能需求（NFR / SLO）

建议首版目标：

- 路由耗时：`P95 < 120ms`（不含重特征离线计算）
- 渲染失败率：`< 0.5%`（按 trip 计）
- 智能回退率：灰度期可放宽，GA 目标 `< 8%`
- 可用性：模板决策服务可用性 `>= 99.9%`
- 可恢复性：配置回滚后 5 分钟内恢复稳定

灰度放量阈值（新增，权威）：

1. 放量前置条件：连续 24h `template.render.error_rate < 0.5%` 且 `fallback_rate < 12%`。
2. GA 前置条件：连续 72h `fallback_rate < 8%` 且 `manual_override_rate < 25%`。
3. 触发回滚条件：任意 1h 窗口 `error_rate > 1.0%` 或 `fallback_rate > 20%`。

---

## 10. 验收标准（AC）

| ID | 验收条件 |
|----|----------|
| **AC-P13-01** | 创建页可见模板下拉，默认“智能匹配” |
| **AC-P13-02** | 手动指定模板后，最终渲染使用指定模板 |
| **AC-P13-03** | 智能模式可输出 `resolvedTemplateId/confidence/reasonCodes` |
| **AC-P13-04** | 低置信场景回退 `visual-journal` 且流程不中断 |
| **AC-P13-05** | 历史 trip（无新字段）可正常渲染 |
| **AC-P13-06** | 长图/放映/呼吸动效链路无回归 |
| **AC-P13-07** | 模板决策 telemetry 可按 trip 查询 |
| **AC-P13-08** | 后台可执行模板新增、编辑、下线；删除受引用保护 |
| **AC-P13-09** | 支持模板路由回放调试（输入 tripId 可复现决策） |
| **AC-P13-10** | `manual` 模式与 `copy_locked` 场景下模板决策不会被自动重算 |
| **AC-P13-11** | 模板下拉仅展示“有权限且已上线”的模板，排序可配置 |
| **AC-P13-12** | 模板编辑护栏生效：锁定区域不可编辑，可编辑区域可正常保存 |
| **AC-P13-13** | 新增模板需通过准入审核流程后方可进入 `ga` |
| **AC-P13-14** | 创建页完整覆盖 smart/manual/fallback 三种结果反馈文案 |
| **AC-P13-15** | 管理后台支持模板 CRUD、状态流转与逻辑删除保护 |
| **AC-P13-16** | 管理后台支持按 `tripId` 路由回放，结果与线上决策一致 |
| **AC-P13-17** | 高风险后台操作具备审计日志与二次确认机制 |
| **AC-P13-18** | 模板发布满足原子性校验，不出现“可选但不可渲染”状态 |
| **AC-P13-19** | 所有模板读取路径走 `resolve_effective_template()`，无双写分叉 |
| **AC-P13-20** | 并发场景下（下线/创建/渲染）行为符合版本冲突与可用性规则 |

---

## 11. 风险与缓解

| 风险 | 影响 | 缓解策略 |
|------|------|----------|
| 智能匹配误判 | 用户体验不稳定 | 低置信回退 + 人工指定覆盖 |
| 多模板引入回归 | 渲染失败/样式错乱 | adapter 分层 + golden 回归 |
| schema 改造影响旧数据 | 存量 trip 不可渲染 | 向后兼容字段 + 默认值兜底 |
| 运营配置误操作 | 模板错配 | 白名单校验 + 开关回滚 |
| 后台 CRUD 误操作 | 模板不可用或污染线上 | 状态机约束 + 审计日志 + 逻辑删除 |
| 决策漂移不可复现 | 排障困难 | 冻结策略 + decisionHash + 路由回放工具 |
| 后台权限配置不当 | 越权操作风险 | 最小权限角色模型 + 高风险操作二次确认 |

---

## 12. 里程碑计划（建议）

| 波次 | 周期 | 内容 | 出口 |
|------|------|------|------|
| **P13-W1** | 1 周 | 注册中心 + visual-journal adapter 迁移 + schema 兼容改造 | 输出不变，回归通过 |
| **P13-W2** | 1 周 | 前端创建下拉（智能默认+手动指定）+ 后端参数打通 + 路由器 MVP | 智能/手动双模式可用 |
| **P13-W3** | 1 周 | 后台模板治理入口（CRUD + 回放调试）+ 权限与审计 | 模板运维可控可追踪 |
| **P13-W4** | 1 周 | 第二模板试点（建议 event-recap）+ 灰度 + telemetry 看板 | 试点模板可稳定生成 |

后台建设分层建议（与里程碑并行）：

- **Admin-L1（P13-W2）**：只读看板 + 路由回放
- **Admin-L2（P13-W3）**：模板 CRUD + 状态流转 + 审计
- **Admin-L3（P13-W4）**：灰度发布 + 回滚控制台

---

## 13. 测试计划

### 13.1 单元测试

- registry 注册与查找
- router 决策与回退
- `manual > smart > fallback` 优先级
- schema 向后兼容
- decision freeze / recompute 规则

### 13.2 集成测试

- `render_html/render_trip` 多模板路径
- longshot/present/draft 三模式回归
- Studio 创建接口参数回归
- 后台模板 CRUD（新增/编辑/下线/逻辑删除）回归
- 路由回放接口与线上决策一致性
- 并发场景回归（模板下线 vs 创建、模板编辑 vs 渲染、回滚窗口读写一致性）

### 13.3 验收测试

- 创建页交互（默认智能、可手动切换）
- 智能匹配结果可追踪
- 旧 trip 与新 trip 混合回归

---

## 14. 监控与指标

新增指标建议：

- `template.route.count{template_id}`
- `template.route.fallback_rate`
- `template.route.manual_override_rate`
- `template.route.confidence_p50/p90`
- `template.render.error_rate{template_id}`
- `template.admin.crud_count{action,operator}`
- `template.admin.replay_count`
- `template.admin.audit_missing_rate`
- `template.admin.high_risk_action_count`
- `template.admin.rollback_count`
- `template.admin.permission_denied_count`
- `template.discovery.impression_count{template_id}`
- `template.discovery.select_count{template_id}`
- `template.guardrail.violation_block_count`
- `template.review.pass_rate`

产品效果指标：

- 智能模式采纳率
- 手动改选率
- 首次编辑时长
- 导出完成率
- 管理后台介入率（手动干预比例）
- 管理后台调试成功率（回放可复现比例）

## 14.1 安全与审计要求（后台治理）

- 模板管理接口默认仅内网或后台鉴权访问。
- 所有模板 CRUD 与回放调试操作记录审计日志（操作者、时间、变更 diff）。
- 禁止未授权角色进行模板删除/下线。
- 调试回放默认只读，不得直接改写线上 trip。

## 14.2 模板质量运营指标（新增）

- 模板被选择率（智能命中 + 手动选择）
- 模板生成后一次通过率（无需大改直接导出）
- 模板编辑放弃率（进入编辑后未导出）
- 模板护栏拦截率（结构破坏尝试）
- 模板回退率（被禁用/低置信导致）

---

## 15. 竞品能力 -> P13 条款映射表

| 竞品能力 / 最佳实践 | 竞品参考 | P13 对应条款 | 本项目落地口径 |
|--------------------|----------|--------------|----------------|
| 自动生成首稿 + 可微调 | Shutterfly Auto-Fill、Mixbook Auto-Create | `4.1`、`5.2`、`8` | 智能默认路由并保留人工指定，先自动后微调 |
| 模板可编辑护栏（锁定关键结构） | Canva Brand Templates Locks | `5.8`、`10(AC-P13-12)` | 锁结构、放内容，防止“改坏模板” |
| 模板治理状态机（实验/灰度/正式/退役） | Notion Marketplace + 平台化治理实践 | `5.5`、`11` | 模板全生命周期受控管理 |
| 模板上架前审核门槛 | CapCut 模板审核、Notion 上架规范 | `5.9`、`10(AC-P13-13)` | 静态校验 + 自动回归 + 人工评审 |
| 模板发现分发（分类/标签/推荐） | Canva/Notion 模板库 | `5.7`、`14` | 下拉与后台推荐集基于受控标签和上线状态 |
| 智能推荐可解释（reason codes） | Google Photos / 平台推荐可解释实践 | `8.1`、`6.1` | 输出 reasonCodes 与 routerVersion，支持审计 |
| 回放调试与决策可复现 | 平台运维通行做法 | `4.4`、`5.6`、`9.2` | 支持 trip 级回放，锁定后不漂移 |
| 强回滚能力 | 高可用平台运维实践 | `9.2`、`9.3` | 三级回滚：关路由/下线模板/回单模板 |
| 权限与审计闭环 | 企业模板平台治理常规 | `4.4`、`14.1` | `template_admin/operator` + 全操作审计 |
| 指标化运营（模板效果持续优化） | 模板平台增长实践 | `14`、`14.2` | 选择率、一次通过率、护栏拦截率等持续追踪 |

> 注：竞品能力用于提炼“可复用原则”，不直接复制具体交互或视觉表现。

---

## 16. 待确认问题拍板（本次冻结）

以下争议项在 P13 直接拍板，作为实施约束：

1. `templateId` 字段策略：
   - P13/P14 保留 `templateId` 作为兼容镜像字段；
   - 真值为 `templateSelection.resolvedTemplateId`；
   - P15 再评估是否移除镜像写入。
2. 模板资产来源策略：
   - P13 仅支持仓库内受控模板目录，不支持外部动态加载；
   - 外部模板接入需在后续阶段单独评审签名与完整性方案。
3. 管理后台权限域：
   - P13 复用现有 Studio 鉴权体系并扩展角色；
   - 不新建独立账号系统，减少复杂度与交付风险。
4. 第二模板试点：
   - P13 固定采用 `event-recap`；
   - 不做动态替换试点对象，确保评估口径一致。

---

## 17. 明确排除项

- 不做 C 端用户自定义模板上传与编辑
- 不做在线学习推荐平台
- 不在 P13 同时上线 4+ 新模板
- 不重写现有 visual-journal 样式体系
- 不开放无权限控制的模板管理入口

---

## 18. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.13.4 | 2026-06-03 | 补充开发负责人审阅建议：真值单入口、发布原子性、回放快照版本、并发安全、灰度阈值与并发测试要求 |
| v0.13.3 | 2026-06-03 | 补充前端任务与管理后台规划：创建页交互、结果反馈、后台 CRUD/回放/审计、权限模型与分层建设建议 |
| v0.13.2 | 2026-06-03 | 补充竞品最佳实践映射：Discovery、Guardrails、模板准入审核、运营指标与“竞品能力 -> P13 条款映射表” |
| v0.13.1 | 2026-06-03 | 补充关键架构项：模板 CRUD 后台治理入口、决策冻结、真值模型、NFR/SLO、迁移回滚、权限审计 |
| v0.13.0 | 2026-06-03 | 初稿：模板系统化方案，含“智能默认 + 手动下拉指定”创建入口要求 |

