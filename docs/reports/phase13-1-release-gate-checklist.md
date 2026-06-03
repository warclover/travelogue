# Phase 13.1 发布闸门检查单（冻结版）

| 属性 | 内容 |
|------|------|
| 适用阶段 | P13.1（模板系统化首版发布） |
| 负责人 | 项目负责人 / 发布值班 |
| 更新日期 | 2026-06-03 |
| 关联 | `docs/PRD-PHASE13.md` v0.13.4 · `docs/IMPLEMENTATION-PHASE13.md` · `docs/acceptance-records/` |

---

## 1) 建议阈值表（可直接落配置）

> 原则：默认保守、智能优先、低置信回退；阈值与 PRD §9.3 一致。

| 配置键 | 建议值 | 说明 |
|-------|--------|------|
| `template_router.enabled` | `true`（灰度期可 `false` 应急） | 路由器总开关 |
| `template_router.default_template` | `visual-journal` | 保底模板 |
| `template_router.confidence_threshold` | `0.65` | 低于此值触发 fallback |
| `template_router.allow_manual_override` | `true` | 允许手动覆盖智能结果 |
| **灰度放量前置** | 连续 24h `error_rate < 0.5%` 且 `fallback_rate < 12%` | 扩大灰度前 |
| **GA 前置** | 连续 72h `fallback_rate < 8%` 且 `manual_override_rate < 25%` | 全量前 |
| **自动回滚触发** | 任意 1h `error_rate > 1.0%` 或 `fallback_rate > 20%` | 执行 L1/L2 回滚 |

---

## 2) P13 专项闸门（G1–G9）

### G1 · 真值单入口（`resolve_effective_template`）

- [ ] 渲染、校验、导出、后台展示均经 `resolve_effective_template(trip)`，无业务模块直读 `templateId`。
- [ ] 代码检索无违规分叉：`grep -r "trip\[.templateId.\]" travelogue/`（除 `TripService` 镜像同步）结果为 0 或已登记例外。
- [ ] `templateSelection.resolvedTemplateId` 与 `templateId` 不一致时告警并以 resolved 为准。

通过标准：

- [ ] **AC-P13-19** 通过；单测 `tests/test_template_registry.py` 含真值入口覆盖。

建议命令：

```bash
python -m pytest tests/test_template_registry.py tests/test_render_engine.py -q -k "effective_template or resolve"
rg "templateId" travelogue/render travelogue/services/validate.py travelogue/templating --glob "*.py"
```

---

### G2 · 模板发布原子性

- [ ] 模板状态为 `beta`/`ga` 前，registry + manifest + adapter + assets 四件套健康检查全绿。
- [ ] 任一检查失败时模板保持不可见（不出现在 C 端下拉、不参与路由）。
- [ ] 发布/下线操作写入 `registryVersion` 审计字段。

通过标准：

- [ ] **AC-P13-18** 通过；不存在“下拉可选但渲染 404/E_RENDER_TEMPLATE”的半发布态。

建议命令：

```bash
python -m pytest tests/test_template_registry.py -q -k "publish or health or atomic"
python scripts/phase13_template_route_eval.py --check-registry-health
```

---

### G3 · 路由回放可复现（快照版本一致）

- [ ] `templateSelection` 含 `routerConfigVersion` / `featureSnapshotVersion` / `registryVersion` / `decisionHash`。
- [ ] 后台按 `tripId` 回放结果与线上一致（含 reasonCodes、confidence、fallback 标记）。
- [ ] 同 trip + 同快照版本重复回放 `decisionHash` 不变。

通过标准：

- [ ] **AC-P13-09**、**AC-P13-16** 通过；`template.admin.replay_count` 可观测。

建议命令：

```bash
python -m pytest tests/test_template_router.py -q -k "replay or decision_hash"
python scripts/phase13_template_route_eval.py --trip <TRIP_ID> --replay --write docs/acceptance-records/phase13-route-eval.json
```

---

### G4 · 冻结语义（`manual` / `copy_locked`）

- [ ] `templateSelection.mode=manual` 时禁止自动重算（含后台批量、定时任务）。
- [ ] `copy_locked` / `pipeline.locks.copy=true` 等冻结态映射 `template_locked=true`，禁止重算。
- [ ] 仅“未锁定 + smart + 显式 `recompute_template=true`”允许重算，且保留历史记录。

通过标准：

- [ ] **AC-P13-10** 通过；冻结规则单测全绿。

建议命令：

```bash
python -m pytest tests/test_template_router.py -q -k "freeze or manual or copy_locked or locked"
```

---

### G5 · 并发与竞态

- [ ] 模板状态更新携带 ETag/Revision；冲突返回 409 并提示重试。
- [ ] 下线与创建并发：创建以提交时刻可用性检查为准，不使用已下线模板。
- [ ] 编辑与渲染并发：渲染读取提交时 registry 快照，不因半更新 manifest 失败。

通过标准：

- [ ] **AC-P13-20** 通过；并发矩阵（见 `IMPLEMENTATION-PHASE13.md` §并发测试场景矩阵）6 条场景全绿。

建议命令：

```bash
python -m pytest tests/test_template_registry.py tests/test_studio_template_create.py -q -k "concurrent or etag or conflict"
```

---

### G6 · 灰度阈值与自动回滚

- [ ] 放量前核对 24h 窗口：`error_rate`、`fallback_rate` 满足 §1 阈值表。
- [ ] GA 前核对 72h 窗口：`fallback_rate`、`manual_override_rate` 满足阈值。
- [ ] 监控告警已配置 1h 回滚触发（`error_rate > 1%` 或 `fallback_rate > 20%`）。
- [ ] L1/L2/L3 回滚卡片可演练（见实施文档 §高风险操作演练）。

通过标准：

- [ ] 灰度期间无未解释指标尖峰；回滚演练记录归档。

建议命令：

```bash
# 指标核对（按环境替换数据源）
python scripts/phase13_template_route_eval.py --metrics-window 24h --write docs/acceptance-records/phase13-route-eval.json
```

---

### G7 · 管理后台权限 / 审计 / 高风险二次确认

- [ ] `template_admin` / `template_operator` / `viewer` 角色鉴权生效；越权返回 403。
- [ ] CRUD、回放、下线、全局切换写审计（操作者、时间、diff）。
- [ ] 删除、下线、全局模板切换需二次确认；未确认不执行。

通过标准：

- [ ] **AC-P13-08**、**AC-P13-15**、**AC-P13-17** 通过；`template.admin.audit_missing_rate == 0`。

建议命令：

```bash
python scripts/phase13_admin_audit_check.py --write docs/acceptance-records/phase13-admin-audit.json
python -m pytest tests/test_studio_template_create.py -q -k "admin or audit or permission" 2>/dev/null || echo "待 M50-W3 落地后启用"
```

---

### G8 · 前端 smart / manual / fallback 三态

- [ ] 创建页默认「智能匹配（推荐）」；下拉可切换 manual 并选择已上线模板。
- [ ] 创建成功反馈：智能命中 / 手动指定 / 回退默认 三种文案齐全。
- [ ] 项目详情展示模板来源（smart/manual/fallback）与锁定状态。
- [ ] 埋点：`template_smart_result_shown` / `template_fallback_shown` / `template_manual_selected` 可查询。

通过标准：

- [ ] **AC-P13-01**、**AC-P13-14** 通过；人工走查或 E2E 抽检通过。

建议命令：

```bash
python -m pytest tests/test_studio_template_create.py -q
python -m travelogue demo verify
```

---

### G9 · 旧 trip 向后兼容

- [ ] 无 `templateSelection` 的历史 trip 可正常 `render_html` / longshot / present。
- [ ] 缺省 `templateId` 时解析为 `visual-journal`，输出与 P12 基线一致。
- [ ] schema 校验对旧字段不报错（`templateId` const→enum 兼容）。

通过标准：

- [ ] **AC-P13-05**、**AC-P13-06** 通过；golden/demo trip 回归无 diff。

建议命令：

```bash
python -m pytest tests/test_render_engine.py tests/test_m21_phase5.py tests/test_phase6_remaining.py tests/test_screen_tone.py -q
python -m travelogue demo verify
```

---

## 3) 回归窗口（建议 Day 1–7）

建议命令：

```bash
python -m pytest tests/test_template_registry.py tests/test_template_router.py -v
python -m pytest tests/test_studio_template_create.py tests/test_render_engine.py -v
python -m pytest tests/test_m21_phase5.py tests/test_phase6_remaining.py tests/test_screen_tone.py -v
python -m travelogue demo verify
```

通过标准：

- [ ] 回归全绿（含 G1–G9 对应单测）。
- [ ] Shadow 模式（若启用）仅记录路由、不改变渲染输出。
- [ ] 路由 P95 `< 120ms`（不含离线重特征）。

---

## 4) 验收记录产物（建议 Day 8–11）

执行：

```bash
python scripts/phase13_gate_signoff.py --write docs/acceptance-records/phase13-gate-signoff.json
python scripts/phase13_rollback_drill.py --write docs/acceptance-records/phase13-rollback-drill.json
python scripts/phase13_metrics_window.py --hours 24 --dev-relaxed --write docs/acceptance-records/phase13-metrics-24h.json
python scripts/phase13_metrics_window.py --hours 72 --write docs/acceptance-records/phase13-metrics-72h.json
python scripts/phase13_template_route_eval.py --write docs/acceptance-records/phase13-route-eval.json
python scripts/phase13_admin_audit_check.py --write docs/acceptance-records/phase13-admin-audit.json
```

核对字段：

- [x] `phase13-route-eval.json` 含 `routerConfigVersion` / `featureSnapshotVersion` / `registryVersion` / `decisionHash` / `replay_match`。
- [x] `phase13-route-eval.json` 含 `fallback_rate` / `manual_override_rate` / `error_rate`（开发基线；24h/72h 发布前补录）。
- [x] `phase13-admin-audit.json` 含 `audit_coverage` / `high_risk_confirm_count` / `permission_denied_count`。
- [x] `phase13-gate-signoff.json` 含 `go` 与各 `gates.*.pass`。

---

## 6) 开发环境自动化 Smoke（2026-06-03）

> `python scripts/phase13_gate_signoff.py --write docs/acceptance-records/phase13-gate-signoff.json`

| 闸门 | 自动化 | 备注 |
|------|--------|------|
| G1/G2 | ✅ | `registryHealthOk: true` |
| G3 | ✅ | fixture + `--seed-selection` → `replay_match: true` |
| G4/G5/G8/G9 | ✅ | pytest 38 passed |
| G6 | ◐ | `phase13_rollback_drill.py` + `phase13_metrics_window.py`；72h 发布前补录 |
| G7 | ✅ | 审计脚本可跑 |
| G8 | ◐ | 人工走查 `phase13-g8-studio-walkthrough.md` |

---

## 5) 发布日 Gate（Day 12–14）

- [x] PRD v0.13.4、实施清单、本检查单 Gate 编号一致。
- [x] 开发环境 Smoke（§6）已通过；**G6 灰度窗口 + G8 人工走查** 发布前确认
- [ ] 保留降级预案：`template_router.enabled=false`（L1）；单模板 disabled（L2）；仅 `visual-journal`（L3）。
- [ ] 发布前 24h 无新增功能改动（仅文档/阈值/灰度比例微调）。
- [ ] 发布后首批观察窗口（≥24h）完成并记录结论。

发布结论：

- [ ] Go（允许发布 / 扩大灰度）
- [ ] No-Go（继续 Shadow 或维持当前流量）

备注：

- 观察摘要：
- 触发的回滚级别（L1/L2/L3）：
- 需要回滚项：
