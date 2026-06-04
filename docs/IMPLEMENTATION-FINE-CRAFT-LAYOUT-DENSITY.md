# Travelogue · 版面密度（精细制作）实施任务清单

| 属性 | 内容 |
|------|------|
| **PRD** | [PRD-FINE-CRAFT-LAYOUT-DENSITY.md](./PRD-FINE-CRAFT-LAYOUT-DENSITY.md) v0.1.1 |
| **功能代号** | M-LD · 版面密度 |
| **状态** | Core Done (M-LD-1) · Hardening Done |
| **更新** | 2026-06-04 |

---

## 落地原则

1. **快速路径零回归**：`quick_share` 不传、不读 `layoutDensity`。  
2. **单入口**：仅 `layout_density_params(trip)` 读 intent。  
3. **MVP 仅 L1+L2**：九宫配额 + 选格顺序；mosaic/beam 放 P1。  
4. **Fail-open**：非法值 → `balanced`；`layoutDensity.enabled=false` → `balanced`。

---

## 里程碑

| 里程碑 | 出口 | AC |
|--------|------|-----|
| **M-LD-1** MVP | 可发布精细选项 + golden | AC-LD-01～13 |
| **M-LD-2** P1 | mosaic 权重、beam | 效应加固 |
| **M-LD-3** P2 | G1 layout replan | — |

---

## M-LD-1 任务墙

| ID | 任务 | 文件 | 状态 |
|----|------|------|------|
| M-LD-1.1 | `intent.layoutDensity` schema | `schemas/trip.schema.json` | ☑ |
| M-LD-1.2 | `apply_intent(layout_density=)` | `travelogue/services/trip.py` | ☑ |
| M-LD-1.3 | `layout_density.py` 单入口 + 配额 | `travelogue/curation/layout_density.py` | ☑ |
| M-LD-1.4 | `ScreenLayoutPlannerState` + 选格顺序 | `screen_layout_state.py`, `screen_planner.py` | ☑ |
| M-LD-1.5 | curate / layout_planner 接线 | `curate.py`, `layout_planner.py` | ☑ |
| M-LD-1.6 | Import API + pipeline + subprocess | `import_handlers.py`, `studio_pipeline.py`, `studio_subprocess.py` | ☑ |
| M-LD-1.7 | `layoutDensity.enabled` 配置 | `config.py`, `config.yaml.example` | ☑ |
| M-LD-1.8 | `intentHints` + telemetry | `intent_hints.py`, `studio_intent_telemetry.py` | ☑ |
| M-LD-1.9 | Import Sheet UI + 提交 + 成功页 | `studio-home-v2.html`, `import-sheet.js`, `import-run.js`, `first-success.js`, `constants.js` | ☑ |
| M-LD-1.10 | 单测 + golden | `test_layout_density.py`, `test_studio_intent.py`, handlers test | ☑ |

**Hardening（2026-06-04）**

| ID | 任务 | 状态 |
|----|------|------|
| H-LD-1 | `intentHints` schema 扩展 + quick_share 清除密度 | ☑ |
| H-LD-2 | `hero_first` 横图候选含 `1`（修复选格未生效） | ☑ |
| H-LD-3 | `collage_first` 大格优先重排 | ☑ |
| H-LD-4 | AC-LD-06/07/13 单测；07 用 50 张 synthetic（80 张密度差上限 &lt;10pp） | ☑ |
| H-LD-5 | `demo-day-3` 等价 fixture + §7.7 `nineQuotaAdjusted` telemetry | ☑ |
| H-LD-6 | AC-LD-08 三档章首 hero / 人脸 contain 单测 | ☑ |

**依赖**：1.1 → 1.2 → 1.3 → 1.4 → 1.5；1.6～1.9 可并行；1.10 最后。

---

## 验收命令

```powershell
python -m pytest tests/test_layout_density.py tests/test_studio_intent.py tests/test_studio_handlers_import_export.py -q
python -m pytest tests/test_screen_layout_planner.py -q
```

---

## 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1.0 | 2026-06-04 | 初稿任务墙 |
