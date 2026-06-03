# Phase 13 验收入口（模板系统化）

| 属性 | 内容 |
|------|------|
| PRD | [PRD-PHASE13.md](./PRD-PHASE13.md) v0.13.4 |
| 实施 | [IMPLEMENTATION-PHASE13.md](./IMPLEMENTATION-PHASE13.md) v0.13.3 |
| 发布闸门 | [reports/phase13-1-release-gate-checklist.md](./reports/phase13-1-release-gate-checklist.md) |

---

## 自动化验收（推荐顺序）

```bash
python -m pytest tests/test_template_registry.py tests/test_template_router.py \
  tests/test_studio_template_create.py tests/test_template_admin_store.py \
  tests/test_event_recap_template.py tests/test_render.py -q

python scripts/phase13_gate_signoff.py --write docs/acceptance-records/phase13-gate-signoff.json
python scripts/phase13_template_route_eval.py --check-registry-health \
  --trip-json schemas/fixtures/trip.render_golden.json --seed-selection \
  --write docs/acceptance-records/phase13-route-eval.json
python scripts/phase13_admin_audit_check.py --write docs/acceptance-records/phase13-admin-audit.json
```

`phase13-gate-signoff.json` 中 `go: true` 为开发环境 Smoke通过；**发布日仍须** checklist §5 值班签字与 24h/72h 指标窗口。

---

## AC 索引

完整 AC 列表见 PRD §10（AC-P13-01 … AC-P13-20）。闸门 G1–G9 与任务映射见 IMPLEMENTATION §上线前 Gate 对应任务映射。
