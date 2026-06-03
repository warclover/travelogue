# Phase 13 迁移与发布 Runbook

| 属性 | 内容 |
|------|------|
| **版本** | v0.13.7 |
| **日期** | 2026-06-03 |
| **关联** | [IMPLEMENTATION-PHASE13.md](../IMPLEMENTATION-PHASE13.md) · [phase13-1-release-gate-checklist.md](./phase13-1-release-gate-checklist.md) |

---

## 三步迁移（生产前）

### 1. Shadow（仅记录、不改渲染）

```yaml
template_router:
  enabled: true
  shadow_mode: true
```

验收：`template.route.count` 有增量；`resolvedTemplateId` 与现网渲染一致。

### 2. 小流量灰度

- 开启 `enabled: true`，`shadow_mode: false`
- `allowed_templates` 仅 `visual-journal`；`event-recap` 保持注释或 `beta` + 白名单
- 观察 24h：`fallback_rate`、`template.render.error_rate`

```bash
python scripts/phase13_metrics_window.py --hours 24 --write docs/acceptance-records/phase13-metrics-24h.json
```

### 3. GA / 扩大 allowed_templates

- 准入 `run_admission_check` 通过后晋升 `beta` → `ga`
- 取消 `event-recap` 注释或加入 `display_order`
- 归档：`python scripts/phase13_gate_signoff.py --write docs/acceptance-records/phase13-gate-signoff.json`

---

## 预发回滚演练（OPS）

```bash
python scripts/phase13_rollback_drill.py --write docs/acceptance-records/phase13-rollback-drill.json
```

生产态演练（写入项目 `runs/template_admin_state.json`）：

```bash
python scripts/phase13_rollback_drill.py --use-project-state --write docs/acceptance-records/phase13-rollback-drill-prod.json
```

演练后核对 `runs/template_admin_state.json` 中 `runtime.template_router_enabled` 与线上一致。

---

## G6 / G8 发布日人工项

| Gate | 动作 | 归档 |
|------|------|------|
| **G6** | 72h 指标窗口（勿用 `--dev-relaxed`） | `phase13-metrics-72h.json` |
| **G8** | Studio 创建页 smart/manual/fallback 走查 | [phase13-g8-studio-walkthrough.md](./phase13-g8-studio-walkthrough.md) 签字 |

```bash
# 生产：真实 72h 窗口（勿 --empty-window / --dev-relaxed）
python scripts/phase13_metrics_window.py --hours 72 --write docs/acceptance-records/phase13-metrics-72h.json

# 仅字段校验模板（CI / 归档结构，不代表生产通过）
python scripts/phase13_metrics_window.py --hours 72 --empty-window \
  --write docs/acceptance-records/phase13-metrics-72h-gate-template.json

python scripts/phase13_g8_automation_check.py --merge-signoff \
  --write docs/acceptance-records/phase13-g8-signoff.json
```

---

## 在线注册 / 下线 API（值班）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/__travelogue/templates/admin/register` | body: `{ "templateId": "..." }` |
| POST | `/__travelogue/templates/admin/delete` | `{ "templateId", "confirmHighRisk": true }` |
| PATCH | `/__travelogue/templates/admin/{id}/metadata` | `displayName` / `category` / `tags` |

权限：`template_admin`；只读列表/看板：`viewer`。

**治理台 UI**：`http://127.0.0.1:8766/templates-admin`（元信息 PATCH、注册、逻辑删除、72h 看板）。
