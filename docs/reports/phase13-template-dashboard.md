# Phase 13 模板运营看板（指标口径）

| 属性 | 内容 |
|------|------|
| 阶段 | P13.1 |
| 关联 PRD | [PRD-PHASE13.md](../PRD-PHASE13.md) §14、§9.3 |
| 数据源 | Studio 埋点 jsonl、`phase13-route-eval.json`、后台审计 |
| 更新 | 2026-06-03 |

---

## 1. 核心指标（发布值班每日看）

| 指标键 | 含义 | 建议阈值（PRD §9.3） | 采集来源 |
|--------|------|----------------------|----------|
| `template.render.error_rate` | 按 trip 计渲染失败率 | 灰度 24h `< 0.5%`；1h 回滚 `> 1.0%` | 渲染异常 / pipeline |
| `template.route.fallback_rate` | 智能路由回退默认模板占比 | 24h `< 12%`；GA 72h `< 8%` | `templateSelection.fallbackUsed` |
| `template.route.manual_override_rate` | 手动指定占比 | GA 72h `< 25%` | `templateSelection.mode=manual` |
| `template.route.count{template_id}` | 各模板命中次数 | — | 路由结果聚合 |
| `template.route.confidence_p50/p90` | 路由置信度分位 | 观察用 | `templateSelection.confidence` |

---

## 2. 治理指标（后台）

| 指标键 | 含义 | 告警建议 |
|--------|------|----------|
| `template.admin.crud_count{action}` | CRUD / 生命周期变更次数 | 突增人工复核 |
| `template.admin.replay_count` | 路由回放调试次数 | — |
| `template.admin.rollback_count` | L1/L2/L3 回滚次数 | `> 0` 当日值班跟进 |
| `template.admin.permission_denied_count` | 越权拦截 | 应为 0（除探测） |
| `template.admin.audit_missing_rate` | 无审计的高风险操作占比 | **必须为 0** |
| `template.admin.high_risk_action_count` | 二次确认后成功的高风险操作 | 与变更单对齐 |

---

## 3. 产品体验指标（Studio 埋点）

| 事件 | 用途 |
|------|------|
| `template_selector_impression` | 创建页模板控件曝光 |
| `template_mode_changed` | smart ↔ manual 切换 |
| `template_manual_selected` | 手动选中模板 |
| `template_smart_result_shown` | 智能命中反馈展示 |
| `template_fallback_shown` | 回退提示展示 |
| `template_create_submitted` | 带模板参数创建提交 |

---

## 4. 离线基线脚本

```bash
# 注册表健康 +（可选）单 trip 回放
python scripts/phase13_template_route_eval.py --check-registry-health \
  --write docs/acceptance-records/phase13-route-eval.json

python scripts/phase13_template_route_eval.py --trip-json schemas/fixtures/trip.render_golden.json \
  --write docs/acceptance-records/phase13-route-eval.json

# 审计覆盖
python scripts/phase13_admin_audit_check.py --write docs/acceptance-records/phase13-admin-audit.json

# 闸门一键汇总（推荐发布前）
python scripts/phase13_gate_signoff.py --write docs/acceptance-records/phase13-gate-signoff.json
```

---

## 5. 看板分区建议（内部表格 / 后续 BI）

1. **路由质量**：fallback_rate、confidence 分位、各 `template_id` 占比  
2. **渲染稳定**：error_rate 按模板、长图/主链路失败码 TopN  
3. **治理操作**：rollback、lifecycle 变更、审计条目  
4. **实验模板**：`event-recap` 命中 vs 回退（beta 白名单 cohort）

---

## 6. 与发布闸门关系

| 闸门 | 看板字段 |
|------|----------|
| G6 灰度/回滚 | `fallback_rate`、`error_rate`、rollback_count |
| G3 回放 | `replay_match`、`decisionHash` |
| G7 审计 | `audit_coverage`、`high_risk_confirm_count` |
