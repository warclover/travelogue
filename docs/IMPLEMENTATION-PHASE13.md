# Travelogue · Phase 13 实施任务清单

| 属性 | 内容 |
|------|------|
| **PRD** | [PRD-PHASE13.md](./PRD-PHASE13.md) v0.13.4 |
| **文档版本** | v0.13.4-IMPLEMENTATION |
| **里程碑** | M50 · 模板系统化与后台治理 |
| **状态** | Gate Ready（M50-REM P0+P1 平台能力已合入；G6/G8 发布日人工项待值班） |
| **更新** | 2026-06-03 |
| **发布闸门** | [phase13-1-release-gate-checklist.md](./reports/phase13-1-release-gate-checklist.md) |

---

## 波次总览

| 波次 | 目标 | 出口 |
|------|------|------|
| **M50-W1** | 模板平台抽象（registry + adapter）与 schema 兼容改造 | `visual-journal` 输出零变化，回归通过 |
| **M50-W2** | 前端创建入口（智能默认 + 手动指定）与路由器 MVP | 创建链路 smart/manual 可用 |
| **M50-W3** | 管理后台 L1/L2（回放 + CRUD + 审计） | 模板治理能力可用且可追踪 |
| **M50-W4** | 第二模板试点 + 灰度发布 + 回滚控制台 | 新模板稳定上线并可一键回退 |

---

## M50-W1 · 平台抽象与兼容（P0）

| ID | 任务 | 文件 | 状态 |
|----|------|------|------|
| M50-1a | 引入模板注册中心（Template Registry） | `travelogue/templates/registry.py`（新） | ☑ |
| M50-1b | 将 `visual-journal` 渲染迁移到 adapter（行为不变） | `travelogue/render/engine.py` | ☑ |
| M50-1c | 解除路径硬编码，支持按模板读取 manifest/template dir | `travelogue/paths.py` `travelogue/services/manifest_limits.py` `travelogue/services/validate.py` | ☑ |
| M50-1d | trip schema：`templateId` 从 const 到 enum，新增 `templateSelection`（向后兼容） | `schemas/trip.schema.json` | ☑ |
| M50-1e | 渲染真值规则：`resolvedTemplateId` 优先，`templateId` 镜像对齐 | `travelogue/render/engine.py` `travelogue/templating/resolver.py` | ☑ |
| M50-1f | 决策冻结基础字段写入（locked/lockedAt/decisionHash） | `travelogue/services/trip_factory.py` `travelogue/templating/router.py` | ☑ |
| M50-1g | 单测：registry、schema 兼容、旧 trip 渲染不回归 | `tests/test_template_registry.py` `tests/test_render.py` | ☑ |

---

## M50-W2 · 前端创建与路由 MVP（P0）

| ID | 任务 | 文件 | 状态 |
|----|------|------|------|
| M50-2a | 创建页新增模板下拉（默认智能） | `templates/studio/studio-home-v2.html` `import-run.js` | ☑ |
| M50-2b | 创建接口支持 `template_mode/template_id` 参数透传 | `import_handlers.py` `studio_pipeline.py` `studio_subprocess.py` | ☑ |
| M50-2c | 模板路由器 MVP（规则优先 + 低置信回退） | `travelogue/templating/router.py` | ☑ |
| M50-2d | 创建后结果反馈文案（smart/manual/fallback） | `templating/router.py` `studio_pipeline.py`（API 字段） | ☑ |
| M50-2e | 项目详情展示模板来源与锁定状态 | `studio_trips.py` · `studio_entry.py` · `shelf.js` · `preview-toolbar.js` | ☑ |
| M50-2f | 前端埋点接入（选择、模式切换、回退） | `analytics.js` · `studio_homepage_telemetry.py` · `import-sheet.js` · `import-run.js` · `first-success.js` | ☑ |
| M50-2g | 单测/接口测试：优先级 `manual > smart > fallback` | `tests/test_template_router.py` `tests/test_studio_template_create.py` | ☑ |

---

## M50-W3 · 管理后台 L1/L2（P0）

| ID | 任务 | 文件 | 状态 |
|----|------|------|------|
| M50-3a | 后台模板列表与详情（状态/版本/标签/能力） | `template_handlers.py` GET `/__travelogue/templates` | ☑（L1 只读） |
| M50-3b | 后台模板 CRUD（新增/编辑/下线/逻辑删除） | `template_admin_handlers.py` · `admin_store.py` | ☑（生命周期 PATCH + 审计 + ETag；新增模板登记 P14 per PRD §16） |
| M50-3c | 模板状态机约束（experimental/beta/ga/deprecated/disabled） | `lifecycle.py` · `admin_store.py` · Admin API | ☑ |
| M50-3d | 路由回放调试接口（tripId -> decision replay） | `template_handlers.py` POST replay | ☑ |
| M50-3e | 权限模型（admin/operator/viewer）与鉴权中间件 | `travelogue/templating/roles.py` · Admin handlers | ☑ |
| M50-3f | 审计日志落地（CRUD/回放/高风险操作） | `admin_store.py` · `GET .../admin/audit` · `phase13_admin_audit_check.py` | ☑ |
| M50-3g | 高风险操作二次确认（下线/删除/全局切换） | Admin handlers + `templates-admin.html` | ☑ |

---

## M50-W4 · 第二模板试点与发布治理（P1）

| ID | 任务 | 文件 | 状态 |
|----|------|------|------|
| M50-4a | 第二模板接入（建议 `event-recap`） | `templates/event-recap/*` + registry | ☑（共享 VJ 适配器） |
| M50-4b | 模板适配器（curation/render） | `render/engine.py` · `shared_partials_from` | ☑（试点复用 visual-journal） |
| M50-4c | 灰度配置与白名单策略 | `config.yaml.example` · `allowed_templates` · `beta_allowlist` | ☑ |
| M50-4d | 回滚控制台（关闭路由/下线模板/全局回退） | `admin_store.apply_rollback` · `templates-admin.html` | ☑ |
| M50-4e | 线上指标看板（命中率/回退率/错误率） | `scripts/phase13_template_route_eval.py` · `phase13-template-dashboard.md` | ☑ |
| M50-4f | 试点复盘与参数冻结 | `docs/reports/phase13-pilot-retro.md` | ☑ |

---

## 文件映射（主路径）

| 模块 | 关键改动 |
|------|----------|
| `travelogue/render/engine.py` | 多模板渲染入口、真值模板选择、向后兼容 |
| `travelogue/services/validate.py` | 按模板读取 manifest 校验 |
| `travelogue/templates/registry.py` | 模板注册与查询 |
| `travelogue/templating/router.py` | 模板智能匹配与回退 |
| `travelogue/web/studio_handlers/*` | 创建入口参数、后台 CRUD、回放调试 |
| `templates/studio/*` | 创建页模板下拉、反馈文案、后台控制台 UI |
| `schemas/trip.schema.json` | `templateSelection` 扩展与兼容 |

---

## 测试与验收清单（建议命令）

```bash
python -m pytest tests/test_template_registry.py tests/test_template_router.py -v
python -m pytest tests/test_studio_template_create.py tests/test_render_engine.py -v
python -m pytest tests/test_m21_phase5.py tests/test_phase6_remaining.py -v
python -m pytest tests/test_screen_tone.py -v
python -m travelogue demo verify
```

建议新增验收脚本：

```bash
python scripts/phase13_gate_signoff.py --write docs/acceptance-records/phase13-gate-signoff.json
python scripts/phase13_template_route_eval.py --check-registry-health \
  --trip-json schemas/fixtures/trip.render_golden.json --seed-selection \
  --write docs/acceptance-records/phase13-route-eval.json
python scripts/phase13_admin_audit_check.py --write docs/acceptance-records/phase13-admin-audit.json
```

发布闸门检查单：

- `docs/reports/phase13-1-release-gate-checklist.md`（G1–G9 专项闸门 + 阈值表 + 发布日 Gate）

---

## 上线前 Gate 对应任务映射

> 发布前逐项勾选；Gate 编号与 `phase13-1-release-gate-checklist.md` 一致。

| Gate | 闸门名称 | 任务 ID | 责任模块 | 验收命令 / 动作 |
|------|----------|---------|----------|-----------------|
| **G1** | 真值单入口 | M50-1e、M50-1b | `travelogue/render/engine.py` · `travelogue/services/trip.py` | `pytest tests/test_template_registry.py tests/test_render_engine.py -q -k effective`；`rg templateId travelogue/render travelogue/services` |
| **G2** | 发布原子性 | M50-1a、M50-3c | `travelogue/templates/registry.py` · `travelogue/templating/lifecycle.py` | `pytest tests/test_template_registry.py -q -k "health or publish"`；`phase13_template_route_eval.py --check-registry-health` |
| **G3** | 回放可复现 | M50-1f、M50-3d | `travelogue/services/trip_factory.py` · `template_debug_handlers` | `pytest tests/test_template_router.py -q -k replay`；`phase13_template_route_eval.py --trip <ID> --replay` |
| **G4** | 冻结语义 | M50-1f、M50-2c | `trip_factory` · `travelogue/templating/router.py` | `pytest tests/test_template_router.py -q -k "freeze or manual or locked"` |
| **G5** | 并发竞态 | M50-3c、M50-3b | `lifecycle.py` · `template_admin_handlers` | `pytest tests/test_template_registry.py tests/test_studio_template_create.py -q -k concurrent`；见 §并发测试场景矩阵 |
| **G6** | 灰度与回滚 | M50-4c、M50-4d | `travelogue/config.py` · 后台回滚控制台 | `phase13_template_route_eval.py --metrics-window 24h`；见 §高风险操作演练 |
| **G7** | 权限审计 | M50-3e、M50-3f、M50-3g | `travelogue/web/auth/*` · `studio_telemetry` · Admin UI | `phase13_admin_audit_check.py`；人工核对二次确认弹窗 |
| **G8** | 前端三态 | M50-2a、M50-2d、M50-2e、M50-2f | `templates/studio/*` | `pytest tests/test_studio_template_create.py -q`；创建页人工走查 smart/manual/fallback |
| **G9** | 向后兼容 | M50-1d、M50-1g | `schemas/trip.schema.json` · 回归套件 | `pytest tests/test_render_engine.py tests/test_m21_phase5.py tests/test_screen_tone.py -q`；`travelogue demo verify` |

**出口判定**：G1–G9 全部通过 + §5 发布日 Gate 勾选 → 允许 Go；任一项 No-Go 则维持 Shadow 或回滚至 L1。

---

## 并发测试场景矩阵

> 对应 PRD §13.2 并发回归；建议在 M50-W3 合入前完成自动化或脚本化复现。

| # | 场景 | 并发操作 A | 并发操作 B | 期望结果 | 关联 Gate |
|---|------|------------|------------|----------|-----------|
| **C1** | 模板下线 vs 创建 | Admin 将模板置 `disabled` | 用户同时提交创建（manual 指定该模板） | 创建以提交时刻检查为准：拒绝或回退 `visual-journal`，不半落库 | G5、G8 |
| **C2** | 双 Admin 编辑冲突 | Admin-A 编辑元信息 vN | Admin-B 基于 vN-1 提交 | 后写者 409，提示刷新重试；无脏 registry | G5、G7 |
| **C3** | 发布中 vs 路由 | 模板 health check 进行中 | 路由器尝试选中该模板 | 未通过 health 的模板不参与路由、不出现在下拉 | G2、G5 |
| **C4** | 渲染 vs manifest 更新 | 正在 `render_trip` | Admin 更新 manifest 版本 | 渲染使用启动时 registry 快照；不因半更新失败 | G2、G5 |
| **C5** | 全局回滚 vs 新建 | 运维关闭 `template_router.enabled` | 大量新建 smart 请求 | 全部走默认模板；无中间态抛错 | G6 |
| **C6** | 冻结 vs 重算触发 | trip 已 `copy_locked` | 调试接口带 `recompute_template=true` | 拒绝重算，保留原 `decisionHash` | G4、G3 |
| **C7** | 灰度白名单 vs 非白名单用户 | 模板仅 beta 白名单 | 非白名单用户 smart 创建 | 不命中 beta 模板，回退或仅 `visual-journal` | G6、G8 |

建议命令（落地后）：

```bash
python -m pytest tests/test_template_registry.py tests/test_studio_template_create.py -v -k "concurrent or conflict or etag"
```

---

## 高风险操作演练（回滚演练）

> 发布前在预发/Staging 完成至少一次表格演练并归档记录（操作者、时间、结果）。

| 步骤 | 演练项 | 操作 | 预期 | 关联 |
|------|--------|------|------|------|
| **R1** | L1 关闭路由器 | `template_router.enabled=false` | 新建 trip 全部 `visual-journal`；已有 trip 渲染不变 | G6、回滚卡片 L1 |
| **R2** | L2 单模板下线 | 将 `event-recap` 置 `disabled` | 新建不可选；历史 trip 仍可渲染 | G2、G6 |
| **R3** | L3 平台应急 | 配置 + 代码路径切回仅 `visual-journal` adapter | 5 分钟内错误率回落；监控 `template.render.error_rate` 下降 | G6 |
| **R4** | 自动回滚触发模拟 | 注入/模拟 1h `fallback_rate > 20%` | 告警触发 → 值班执行 L1；记录 `template.admin.rollback_count` | PRD §9.3 |
| **R5** | 高风险后台操作 | 未二次确认尝试「全局默认模板切换」 | 操作 blocked；审计有 `high_risk_action_count` 无成功写入 | G7 |
| **R6** | 回放一致性抽检 | 抽 3 个线上 tripId 后台回放 | `decisionHash` 与 `phase13-route-eval.json` 一致 | G3 |

演练记录建议路径：`docs/acceptance-records/phase13-rollback-drill.json`（脚本待 M50-W4 补充时可手写 checklist 归档）。

---

## 发布策略（按风险分级）

1. **Shadow 模式**：路由结果仅记录，不影响渲染。
2. **Small % 灰度**：智能匹配对小流量生效，观察 fallback/error。
3. **扩大灰度**：保持回滚开关可用。
4. **GA**：稳定后放量并冻结关键参数。

---

## 回滚卡片（执行口径）

| 级别 | 触发条件 | 动作 |
|------|----------|------|
| L1 | 路由异常升高 | 关闭 `template_router.enabled`，全部回退默认模板 |
| L2 | 单模板故障 | 将该模板状态置 `disabled`，保留历史渲染 |
| L3 | 平台级回归 | 切回单模板兼容路径（仅 `visual-journal`） |

---

## 风险与缓解

| 风险 | 缓解 |
|------|------|
| 多模板导致渲染回归 | adapter 分层 + golden 回归 + 分波次上线 |
| 智能匹配不稳定 | decision freeze + reasonCodes + replay |
| 后台误操作 | 最小权限 + 二次确认 + 审计日志 |
| 配置漂移 | 版本化配置 + 双人复核 + 可回滚 |

---

## 剩余任务清单（M50-REM · 对照 PRD v0.13.4）

> 状态：**☑** 已完成 · **◐** 部分 · **☐** 未做 · **⊘** 明确延期（P14/流程）

### P0 · 发布前建议完成

| ID | 任务 | 状态 | 落点 |
|----|------|------|------|
| M50-REM-01 | trip 级模板决策日志（AC-P13-07） | ☑ | `templating/decision_log.py` · `runs/template_decisions.jsonl` |
| M50-REM-02 | 回放写审计 | ☑ | `template_handlers.handle_template_replay` |
| M50-REM-03 | `lockedAt` 写入 | ☑ | `router.apply_template_selection` |
| M50-REM-04 | `recompute` 调试 API | ☑ | `POST /__travelogue/templates/recompute` |
| M50-REM-05 | 并发矩阵自动化 C1/C2/C6/C7 | ☑ | `tests/test_template_concurrent.py` |
| M50-REM-06 | templateId 镜像不一致告警 | ☑ | `resolver.sync_template_id_mirror` |
| M50-REM-07 | 创建页 smart/manual 说明 | ☑ | `import-sheet.js` · `modeHints` API |
| M50-REM-08 | 详情受控调整模板策略 | ☑ | `PATCH /__travelogue/trips/{id}/template` |
| M50-REM-09 | Admin 决策日志查询 | ☑ | `GET /__travelogue/templates/decisions?tripId=` |
| M50-REM-10 | 回放特征摘要 | ☑ | `replay_template_decision` · Admin 回放 UI |
| M50-REM-11 | 强制预览（不落库） | ☑ | `POST /__travelogue/templates/preview` |
| M50-REM-12 | 下拉排序可配置（AC-P13-11） | ☑ | `template_router.display_order` |

### P1 · 质量与治理深化

| ID | 任务 | 状态 | 说明 |
|----|------|------|------|
| M50-REM-13 | 独立 Curation Adapter | ☑ | `curation_adapter.py` + `run_curate` 写入 `templateHints` |
| M50-REM-14 | L3 模板能力 vs 素材校验 | ☑ | `l3_validate.py` · `validate_trip(level=all)` |
| M50-REM-15 | Discovery（分类/标签/推荐集） | ☑ | manifest `templateMeta` · `discovery.py` · Admin 筛选 |
| M50-REM-16 | Guardrails editableScopes | ☑ | manifest + `guardrails.py` · GA health 门禁 |
| M50-REM-17 | 准入审核流水线 | ☑ | `admission.py` · Admin 准入按钮/API |
| M50-REM-18 | Shadow 迁移模式 | ☑ | `shadow.py` · `template_router.shadow_mode` |
| M50-REM-19 | §14 指标接入 runtime | ☑ | `metrics.py` · render/route 埋点 · Admin dashboard |
| M50-REM-20 | 后台元信息 CRUD / 版本 diff | ☑ | `template_admin_crud.py` · PATCH metadata · 版本 diff API |
| M50-REM-21 | 实时效果看板 UI | ☑ | `GET .../admin/dashboard` + Admin UI |
| M50-REM-22 | G6/G8 发布日人工 Gate | ☑（dev） | `phase13_p0_release_finalize.py` · G8 signed(dev-automated) · 72h clean window |
| M50-REM-23 | 预发 R2–R4 回滚演练归档 | ☑ | `scripts/phase13_rollback_drill.py` → `phase13-rollback-drill.json` |
| M50-REM-24 | longshot/放映 P13 专项回归 | ☑ | `tests/test_template_p13_surfaces.py` |
| M50-REM-25 | 预览栏模板调整 UI | ☑ | `preview-toolbar.js` PATCH template |

### P2 · 明确延期

| ID | 任务 | 归属 |
|----|------|------|
| M50-REM-26 | 在线注册新模板目录 API | ☑（M50 最小集） | `POST .../admin/register` · `template_admin_crud.py` |
| M50-REM-27 | 模板市场 / C 端上传 | PRD §17 非目标 |

---

## PRD 差距对照（v0.13.4 严格口径 · 2026-06-03）

> **图例**：☑ 已满足 · ◐ 部分/依赖人工 · ☐ 未做 · ⊘ PRD 非目标或明确延期  
> 自动化 Smoke：`phase13-gate-signoff.json` → `go: true`（不替代发布日 G6/G8）。

### AC-P13-01 … AC-P13-20

| AC | 条件摘要 | 状态 | 差距说明 |
|----|----------|------|----------|
| **01** | 创建页默认智能 + 下拉 | ☑ | G8 Playwright G8-08 + HTTP G8-01/02/03b |
| **02** | 手动指定渲染一致 | ☑ | `test_studio_template_create` · `create_trip(manual)` |
| **03** | smart 输出 selection 字段 | ☑ | `test_template_router` · `trip_factory` |
| **04** | 低置信回退不中断 | ☑ | router + 前端 `first-success.js` 文案 |
| **05** | 历史 trip 可渲染 | ☑ | `test_template_p13_surfaces` legacy 用例 · G9 套件 |
| **06** | 长图/放映/呼吸无回归 | ☑ | surfaces + **breath** + `test_template_p13_screen_tone` |
| **07** | 决策 telemetry 可查 | ☑ | `decision_log` · Admin decisions API |
| **08** | 后台增删改下线 | ☑ | lifecycle PATCH · register/delete/metadata |
| **09** | tripId 回放 | ☑ | `POST .../replay` · `phase13-route-eval` |
| **10** | manual/locked 不重算 | ☑ | `test_template_concurrent` C6 |
| **11** | 下拉权限+排序可配 | ☑ | `list_for_consumer` · `display_order` · `discovery_sort_mode` |
| **12** | 编辑护栏 | ☑ | `guardrails` · `copy_patch` · `test_guardrails_copy_patch` |
| **13** | 准入后才 ga | ☑ | `admission` + `review.py` + Admin 评审 API/UI；晋升 GA 需 `approved` |
| **14** | 三态反馈文案 | ☑ | G8-09 FirstSuccess · G8-06/07 埋点 |
| **15** | Admin CRUD+状态机 | ☑ | `/templates-admin` + Admin API |
| **16** | 回放与线上决策一致 | ☑ | `replay_match` in gate signoff |
| **17** | 审计+二次确认 | ☑ | `append_audit` · 428 confirm · rollback drill R5 |
| **18** | 发布原子性 | ☑ | `check_template_health` · consumer 过滤 unhealthy |
| **19** | 真值单入口 | ☑ | `resolve_effective_template` · registry 测试 |
| **20** | 并发规则 | ☑ | C1–C7 含 **C4** `test_template_concurrent` |

### 并发矩阵 §13.2

| 场景 | 状态 | 落点 / 缺口 |
|------|------|-------------|
| C1 | ☑ | `test_template_concurrent` |
| C2 | ☑ | revision conflict |
| C3 | ☑ | unhealthy 排除 consumer/路由 |
| **C4** | ☑ | `test_concurrent_render_stable_registry_while_manifest_disk_changes` |
| C5 | ☑ | `enabled=false` 全默认 |
| C6 | ☑ | copy_locked |
| C7 | ☑ | beta allowlist |

### PRD 章节级遗漏（非 AC 编号）

| 条款 | 状态 | 建议落点 |
|------|------|----------|
| §5.1 发布/下线记 `registryVersion` | ☑ | `lifecycle_update` 审计含 `registryVersion` / `templateVersion` |
| §5.7 排序：热门/最新/团队常用 | ☑ | `latest` / `popular` / `team` + `discovery_sort_mode` |
| §5.9 准入「自动渲染回归」 | ☑ | `admission` **golden_render** 步 |
| §5.9 准入「人工评审」 | ☑ | `POST .../admin/review` submit/approve/reject |
| §9.1 配置双人复核 UI | ☑ | `templates-admin` pending 列表 + 审批按钮 |
| §9.3 路由 P95 &lt; 120ms | ☑ | `aggregate_metrics` · `phase13_metrics_window` **route_duration_p95_ms** |
| §14 `permission_denied_count` | ☑ | `roles.require_template_role` · audit 脚本读取 |
| §14 `audit_missing_rate` | ☑ | `phase13_admin_audit_check` 按 lifecycle 审计采样 |
| §14 `review.pass_rate` | ☑ | `aggregate_metrics.rates.review_pass_rate` |
| §14.2 产品效果指标 | ⊘ | 采纳率/一次通过率等 — PRD 运营长期项 |
| §13.2 Studio **HTTP** 创建集成 | ☑ | `test_studio_import_template_mode` |
| event-recap **独立视觉** | ⊘ | PRD §16 试点固定 recap；`render_adapter` 仍 VJ（M50-W4 口径） |
| **G6** 生产 72h 指标 | ◐ | 字段模板 `phase13-metrics-72h-gate-template.json`（`--empty-window`）；**生产真实窗口待值班** |
| **G8** 签字 | ☑（dev） | `phase13_g8_walkthrough_automated.py --playwright` · 11/11 含浏览器项 |
| **OPS** 预发演练归档 | ☑ | `phase13-rollback-drill-staging.json`（隔离 state 自动化） |

### 建议下一批实现（按优先级）

| 优先级 | ID | 任务 |
|--------|-----|------|
| P0 | M50-GAP-01 | ◐ | `phase13_release_day_checklist.py`；**人工签字** + **生产 72h** 待值班 |
| P1 | M50-GAP-02 | ☑ C4 并发测试 |
| P1 | M50-GAP-03 | ☑ golden_render + lifecycle 审计 registryVersion |
| P1 | M50-GAP-04 | ☑ permission_denied 指标 |
| P2 | M50-GAP-05 | ☑ templates-admin 双人审批 UI |
| P2 | M50-GAP-06 | ☑ import template_mode HTTP 测试 |
| P2 | M50-GAP-07 | ☑ route P95 rollup + metrics 窗口检查 |

---

## 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.13.7 | 2026-06-03 | PRD v0.13.4 严格差距表：AC-01~20、并发 C4、§14 指标、发布日 G6/G8 |
| v0.13.6 | 2026-06-03 | 发布收尾：rollback drill 脚本、G6 metrics 窗口、AC-P13-06 surfaces 测试、G8 走查单 |
| v0.13.5 | 2026-06-03 | M50-REM P0：决策日志、recompute/preview/decisions API、并发测试、创建说明、详情 PATCH |
| v0.13.4 | 2026-06-03 | 验收闭环：gate signoff 脚本、acceptance JSON、ACCEPTANCE-PHASE13、pilot-retro、dashboard |
| v0.13.3 | 2026-06-03 | event-recap 试点、角色鉴权、审计/回滚 API、验收脚本、templates-admin.html |
| v0.13.2 | 2026-06-03 | M50-2e/2f 详情与埋点；M50-3b 生命周期 Admin API（revision 冲突 + 高风险确认） |
| v0.13.1 | 2026-06-03 | 可执行性增强：Gate↔任务映射、并发矩阵（7 条）、回滚演练表；对齐 `phase13-1-release-gate-checklist.md` |
| v0.13.0 | 2026-06-03 | 初稿：按 PRD-PHASE13 v0.13.4 拆分 M50-W1/W2/W3/W4 与前后端+后台三线实施任务 |

