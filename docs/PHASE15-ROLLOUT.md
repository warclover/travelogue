# Phase 15 · 启用说明（无用户期 · 直接全开）

> 当前无线上用户，**不做灰度分档**。默认配置即全窗 MCS（`mosaic.enabled=true`、`unified_mode=true`）。

PRD：[PRD-PHASE15-photo-mosaic-evolution.md](./PRD-PHASE15-photo-mosaic-evolution.md)  
验收：[ACCEPTANCE-PHASE15.md](./ACCEPTANCE-PHASE15.md)

## 1. 默认配置（`config.yaml` / `config.yaml.example`）

```yaml
mosaic:
  enabled: true
  unified_mode: true
  enabled_window_sizes: [3, 4, 5, 6, 8, 9]
  scorer_version: "p15-s2"
  min_candidate_score: 0.35   # 开发可临时改为 0.0 提高 MCS 曝光
  fallback_to_legacy: true
```

PRD 别名 `layout.mosaic_v2` 与顶层 `mosaic:` 等价（顶层优先）。

## 2. 行为说明

| 开关 | 效果 |
|------|------|
| `mosaic.enabled=true` | curate 走 `compose_trip` + 规划循环 MCS 钩子 |
| `unified_mode=true` | 3/4/5/6/8/9 窗均候选打分（非仅 5 窗） |
| `unified_mode=false` | 仅 5 窗 MCS（保留开关，无用户期不用） |
| `mosaic.enabled=false` | 整段回退 legacy planner |

## 3. 验收（合入 / 本地自检）

```bash
python scripts/phase15_acceptance_bundle.py
pytest tests/ -k mosaic -q
```

可选本地相册（`trips/{id}/trip.json` 存在时）：

```bash
python scripts/phase15_curate_replay.py mao maomi linzhi \
  --write docs/acceptance-records/phase15-curate-replay-local.json
```

## 4. 可观测

- Trip：`curation.mosaicDecisionLog`、`curation.layoutMetrics`
- 本机：`~/.travelogue/telemetry/template-metrics.jsonl`（`mosaic/telemetry.py`）

## 5. 有用户后再考虑

- 分档灰度、`unified_mode` 渐进、`min_candidate_score` 校准
- 监控自动回滚、`replan_screen` Studio 接入口
- mobile MCS
