# Phase 13 试点复盘与参数冻结（event-recap · P13.1）

| 属性 | 内容 |
|------|------|
| 阶段 | P13.1 模板系统化首版 |
| 试点模板 | `event-recap`（PRD §16 拍板） |
| 复盘日期 | 2026-06-03 |
| 状态 | **参数冻结（Shadow → 小流量前）** |

---

## 1. 交付范围核对

| 能力 | 状态 | 说明 |
|------|------|------|
| 模板注册中心 + 健康检查 | ✅ | `registry-v2`，双模板健康全绿 |
| 真值单入口 `resolve_effective_template` | ✅ | 渲染/校验走 resolver |
| 创建 smart/manual + 路由 MVP | ✅ | Studio v2 下拉 + import API |
| 决策冻结 + 回放 | ✅ | `decisionHash` + replay API |
| 后台生命周期 / 回滚 / 审计 | ✅ | `templates-admin.html` + Admin API |
| event-recap 渲染试点 | ✅ | 共享 `visual-journal` 适配器与 partials |
| 动态「新增模板」CRUD | ⏭️ P14+ | PRD §16：P13 仅仓库内受控目录，不开放在线注册 |

---

## 2. 试点策略（event-recap）

1. **生命周期**：注册默认为 `experimental`；灰度前由 Admin 晋升为 `beta`。  
2. **渲染路径**：`render_adapter=visual-journal`，`shared_partials_from` / `shared_assets_from` 指向主模板，避免重复资产。  
3. **路由规则**：单日 + 视频占比 ≥ 35% → 倾向 `event-recap`；健康/允许列表失败则回退 `visual-journal`。  
4. **C 端可见性**：仅 `beta` 且命中 `beta_allowlist_trip_ids`（或晋升 `ga`）后进入创建下拉。

---

## 3. 冻结参数（2026-06-03）

```yaml
template_router:
  enabled: true
  default_template: visual-journal
  confidence_threshold: 0.65
  allow_manual_override: true
  allowed_templates:
    - visual-journal
    - event-recap
  beta_allowlist_trip_ids: []   # 灰度时填入试点 tripId 或留空走全量 beta

template_admin:
  default_role_loopback: template_admin
  require_role_on_lan: true
```

**路由快照版本（回放必带）**

| 字段 | 冻结值 |
|------|--------|
| `routerVersion` | `p13-r1` |
| `routerConfigVersion` | `cfg-2026-06-03-01` |
| `featureSnapshotVersion` | `feat-v1` |
| `registryVersion` | `registry-v2` |

---

## 4. 自动化验收摘要

| 检查项 | 结果 | 证据 |
|--------|------|------|
| 单测 P13 套件 | ✅ 33+ passed | `pytest tests/test_template_*.py tests/test_event_recap_template.py` |
| Registry 健康 | ✅ | `phase13-route-eval.json` → `registryHealthOk: true` |
| 回放（fixture trip） | ✅ | `replay_match: true`（有 `templateSelection` 时） |
| 审计脚本 | ✅ | `phase13-admin-audit.json` 可生成 |
| 闸门汇总 | ✅ | `phase13-gate-signoff.json` |

---

## 5. 风险与后续

| 风险 | 缓解 | 负责人 |
|------|------|--------|
| event-recap 与 VJ 视觉未分化 | 试点仅验证路由与治理；样式差异化放 P14 | 产品 |
| beta 白名单配置遗漏 | 发布 checklist G6 + 配置双人复核 | 值班 |
| 指标未接 BI | 先用脚本 + jsonl 手工汇总 | 工程 |

**下一里程碑建议**

1. 配置 `beta_allowlist_trip_ids` 小流量观察 24h（G6 前置）。  
2. 通过后晋升 `event-recap` → `ga` 或扩大 beta。  
3. P14 评估独立 partials/样式与模板市场能力。

---

## 6. 签字（可选）

| 角色 | 姓名 | 日期 |
|------|------|------|
| 开发负责人 | | |
| 发布值班 | | |
