# Quality gate（PR / CI）

本清单用于防止 schema drift、layout regression 与 Studio 错误处理回退。

## PR 自检

- [ ] 修改写入 `trip.json` 的字段时，已同步 `schemas/trip.schema.json`
- [ ] 涉及 layout / beam / consecutive pattern 时，已跑 `tests/test_layout_search.py`
- [ ] 涉及 scoring 权重时，已跑 `tests/test_layout_scoring.py`
- [ ] 涉及 Studio HTTP handler 时，已跑 `tests/test_studio_handlers_trip.py`
- [ ] 涉及 P7 telemetry（`pipeline.timings`、`embedStats`）时，已确认 schema 与 `travelogue/web/studio_telemetry.py` 摘要字段一致
- [ ] 未向客户端返回未过滤的 `str(exc)`（500 应使用 `E_SERVER` + 固定 message）

## 本地门禁

```bash
python scripts/quality_gate.py
```

可选：对真实 trip 做端到端验收（需 `trips/{id}/trip.json` 存在）：

```bash
python scripts/e2e_trip_acceptance.py linzhi mao
```

## CI 对应

| 步骤 | 工作流 job | 说明 |
|------|------------|------|
| `scripts/quality_gate.py` | `validate` | layout/scoring/studio 回归 + fixture schema |
| `scripts/validate_trip.py … --level all` | `validate` | 标准 fixture 校验 |
| 全量 pytest | 本地 / nightly | PR fast 子集不含 vision/e2e |

## P7 telemetry（已 schema 化）

| 字段 | Schema 路径 | 写入方 |
|------|-------------|--------|
| `pipeline.timings` | `#/$defs/pipeline.properties.timings` | `studio_pipeline.py`, `orchestrator/run.py` |
| `curation.clustering.embedStats` | `#/$defs/tripClustering.properties.embedStats` | `clustering.py` / CLIP encoder |
| `curation.clustering.embedSkipped` | `#/$defs/tripClustering.properties.embedSkipped` | `clustering.py` |

Studio 读取摘要：`GET /__travelogue/trips/{id}/entry` → `telemetry`、`aesthetic` 字段（见 `build_entry`）。

审美分项（PA-T10）：`GET /__travelogue/trips/{id}/aesthetic` → 成册各图 top-3 维度（见 `studio_aesthetic.py`）。

PA 验收（SRCC / 盲评导出）：`python scripts/pa_aesthetic_acceptance.py --trip-dir trips/{id}`。

离线诊断（封面 / 选片 / 版式，需 `trips/{id}/trip.json`）：

```bash
python scripts/_audit_cover_pick.py demo-1506104ebf
python scripts/_audit_cull_gap.py demo-1506104ebf
python scripts/_audit_trip_patterns.py demo-1506104ebf
```
