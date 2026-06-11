# Phase 19 · LQU 运维 Runbook

> 对应 IMPLEMENTATION-PHASE19 S6-07 · PRD R-P19-505。  
> **默认态**：subset / highlight 绑定 / 章级 mosaic DP 均 **关闭**；设计师 SKU rollout 15%。

## 1. 快速判据（何时回滚）

| 信号 | 阈值 | 动作 |
|------|------|------|
| curate 失败率上升 | 较 P16 baseline +2% | L1：关 subset + highlight |
| `explicit_fallback` 率 | > 5%（8 本 golden） | L2：节奏 post-check → `log` |
| 人评 / judge 胜率 | Sprint Gate 未达 60% | 保持 kill switch 关；SKU rollout → 0% |
| curate P95 | > +15% vs P16 | 关 `mosaic.chapter_dp_enabled`；再跑 `p19_curate_profile.py` |

## 2. 配置回滚（`config.yaml`）

### L1 · 选片与 highlight（S6）

```yaml
curate:
  subset:
    enabled: false          # R-P19-505 kill switch
  highlight_opener_binding: false
```

无需重跑历史 trip；下次 curate 即恢复全量进排版池。

### L2 · 章级 mosaic DP（S5）

```yaml
mosaic:
  chapter_dp_enabled: false
```

### L3 · 节奏硬约束（S3）

```yaml
layout:
  rhythm:
    post_check_mode: log    # 由 enforce 降为仅审计
```

候选生成阶段过滤仍生效；仅关闭 enforce 路径的硬性拒绝。

### L4 · 设计师 SKU rollout（S4/S5）

在模板 YAML 中将 `rollout.percent` 设为 `0`（无需改代码）：

- `travelogue/layout_templates/templates/screen-spread-folio.yaml`
- `travelogue/layout_templates/templates/screen-asymmetric-hero.yaml`
- `travelogue/layout_templates/templates/screen-whitespace-hero.yaml`
- `travelogue/layout_templates/templates/screen-justified-row.yaml`

`rollout.percent: 0` 的模板不会进入 MCS 候选（`lte_adapter._lte_extra_rollout_eligible`）。

部署后执行：

```bash
python -m travelogue.layout_templates.registry --refresh-cache   # 若项目有等价刷新步骤
# 或重启 Studio / curate worker 以重载 registry.cache.json
```

## 3. 验证命令

```bash
# S6 单元
python -m pytest tests/test_p19_curate_subset.py tests/test_p19_highlight_binding.py -q

# 节奏审计（8 本 golden）
python scripts/p19_rhythm_audit.py

# curate 性能对比 P16
python scripts/p19_curate_profile.py --compare-p16

# subset spike（单本）
python scripts/p19_subset_spike.py --trip-id demo-1506104ebf
```

## 4. 归档

| 事件 | 记录文件 |
|------|----------|
| Sprint Gate | `docs/acceptance-records/p19-sprint-gates.json` |
| 终验 AC 表 | `docs/acceptance-records/p19-final.json` |
| judge 校准 | `docs/acceptance-records/p19-judge-calibration.json` |

## 5. Gate 通过后默认开启顺序

1. `curate.subset.enabled: true`（三档削减自动判定）
2. `curate.highlight_opener_binding: true`
3. `mosaic.chapter_dp_enabled: true`（混排 trip 灰度）
4. 设计师 SKU `rollout.percent` 按 Sprint Gate 逐步上调

每步需在 8 本 golden 上更新 `p19-final.json` 并附 judge / 人评结果。
