# Lite Copy v1.1 · 灰度与回滚 Runbook

| 属性 | 内容 |
|------|------|
| **PRD** | [PRD-COPY-OPTIMIZATION.md](./PRD-COPY-OPTIMIZATION.md) v1.1.0 |
| **代号** | `lite-copy-v1.1` · `curation.copyStyle.phase` |
| **更新** | 2026-06-09 |

---

## 1. 开启（推荐顺序）

1. 合并 COPY-P0～P3 代码并跑通 `python -m travelogue demo verify`
2. 在 `config.yaml` 启用 narrative 块（见 `config.yaml.example` §narrative）
3. 对试点 trip 执行 narrate / decorLine 生成，确认 `trip.curation.copyStyle.phase == lite-copy-v1.1`
4. 运行 `python scripts/copy_opt_acceptance.py`，归档 `docs/acceptance-records/copy-opt-metrics.json`
5. 人工完成盲评 30 章（`copy-opt-blind-review.json`）

### 推荐配置

```yaml
narrative:
  scope: frame
  decor_line_enabled: true
  decor_line_voice_first: true
  decor_line_llm_enabled: true   # 生产显式开启；代码默认 false
  decor_line_visual_facts_enabled: true
  decor_line_min_fact_count: 2
```

---

## 2. 观测指标

| 指标 | 来源 | 说明 |
|------|------|------|
| `decor_line_fill_rate` / `empty_rate` | `curation.copyMetrics` | 观测，非硬门禁 |
| `copy_total_chars` | 同上 | 全书 hook+decorLine+epilogue |
| `intent_adoption_rate` | 同上 | Studio copyIntent 填写占比 |
| `photos_only_rate` | `clientEventCounts` | 预览页纯照片切换比 |
| `inline_edit_retention_rate` | 同上 | edited 保护 |
| `generic_phrase_hits` | 同上 | 套话命中 |

客户端事件：`preview_open` · `photos_only_on` · `photos_only_off`  
API：`POST /__travelogue/trips/{tripId}/copy-telemetry`

---

## 3. 一键回滚

| 目标 | 操作 |
|------|------|
| 关闭 decorLine 生成 | `decor_line_enabled: false` |
| 恢复 lead/caption 满生成 | `scope: full` |
| 关闭 LLM decor 候选 | `decor_line_llm_enabled: false` |
| 关闭 visual facts | `decor_line_visual_facts_enabled: false` |

回滚后重新 narrate；用户 `edited: true` 字段不会被覆盖。

---

## 4. 验收门禁

- **AC-COPY-01**：离线脚本 `copy_total_chars_median ≤ 120`
- **AC-COPY-17**：盲评 ≥80%（人工）
- **AC-COPY-18**：`photos_only_rate` 不高于基线 +10%（需足够 preview 样本）
- **NR-COPY-***：`pytest` + `demo verify`

---

## 5. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0.0 | 2026-06-09 | 初稿：配置、指标、回滚、验收 |
