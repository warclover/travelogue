# Phase 15 · 启用说明（无用户期 · 直接全开）

> 当前无线上用户，**不做灰度分档**。默认配置即全窗 MCS（`mosaic.enabled=true`、`unified_mode=true`）。

PRD：[PRD-PHASE15-photo-mosaic-evolution.md](./PRD-PHASE15-photo-mosaic-evolution.md)  
验收：[ACCEPTANCE-PHASE15.md](./ACCEPTANCE-PHASE15.md)

## 0. 新 clone 检查清单（MCR · P0-b）

1. 确认本地 `config.yaml` 含完整 `mosaic:` 段，或对照 `config.yaml.example` 自行追加。
2. **MCR P0-a 修复后**：即使缺少 `mosaic:` 段，`load_config` 也会回退 `MosaicConfig` dataclass 默认（`enabled_window_sizes: [4, 5, 6, 9]`），不再 silent 缩成仅 5 窗。
3. 可选自检：`python scripts/mosaic_config_diag.py --strict`（window 6 应为 enabled）。
4. 行为验收（本机有 trip 时）：`python scripts/mcr_eval_recurate.py chuanzang-studio` → 留档 `.cache/mcr-eval/`。
5. usage 一致性（mosaic 族）：`python scripts/check_usage_consistency.py --family mosaic`。
6. 缺 `mosaic:` 段调试：`TRAVELOGUE_CONFIG_VERBOSE=1` 下 `load_config` 会 INFO dataclass 默认窗宽。
7. **不要**将本地 `config.yaml` 提交到 git（已在 `.gitignore`）。

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
- 监控自动回滚；Studio `PATCH /__travelogue/trips/{id}/screens/{screenId}/replan` 已接（含 items 同步）
- mobile MCS
