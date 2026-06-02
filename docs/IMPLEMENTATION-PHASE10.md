# Travelogue · Phase 10 实施任务清单

| 属性 | 内容 |
|------|------|
| **PRD** | [PRD-PHASE10-food-grid.md](./PRD-PHASE10-food-grid.md) v0.10.0 |
| **前置** | [PRD-PHASE9-E-subject-bridge.md](./PRD-PHASE9-E-subject-bridge.md) §6 |
| **验收** | [ACCEPTANCE-PHASE10.md](./ACCEPTANCE-PHASE10.md) |
| **状态** | Done |
| **更新** | 2026-06-02 |

---

## 任务总览

| ID | 任务 | 文件 | 状态 |
|----|------|------|------|
| P10-0 | 文档落地（实现/验收） | `docs/IMPLEMENTATION-PHASE10.md` `docs/ACCEPTANCE-PHASE10.md` | ☑ |
| P10-1 | mundane 检测与 run-length | `travelogue/curation/subject_tagging.py` | ☑ |
| P10-2 | 新增 `try_food_grid` stage | `travelogue/curation/screen_planner_stages.py` | ☑ |
| P10-3 | screen planner helper + 透传参数 | `travelogue/curation/screen_planner.py` | ☑ |
| P10-4 | 配置项 `enable_food_grid` | `travelogue/config.py` `config.yaml.example` `config.demo.yaml` | ☑ |
| P10-5 | curate wiring | `travelogue/curation/curate.py` `travelogue/curation/layout_planner.py` | ☑ |
| P10-6 | Food Grid 单测覆盖（PRD §6） | `tests/test_food_grid.py` | ☑ |
| P10-7 | 桥接层补充单测 | `tests/test_subject_tagging_bridge.py` | ☑ |
| P10-8 | 验收命令执行与记录 | pytest + demo verify | ☑ |
| P10-9 | Phase 10.1 预埋（多桶配置，不改变默认） | `subject_tagging.py` `screen_planner*.py` `config.py` | ☑ |
| P10-10 | 候选/重排链路参数透传回归（10.1） | `tests/test_layout_candidates.py` `tests/test_layout_search.py` | ☑ |
| P10-11 | 预览调试 badge（可选，默认隐藏） | `templates/visual-journal/journal-screens.css` | ☑ |
| P10-12 | PRD AC-P10-02 对齐（demo verify） | `docs/ACCEPTANCE-PHASE10.md` `scripts/phase10_food_grid_acceptance.py` | ☑ |

---

## 文件映射

| 模块 | 改动 |
|------|------|
| `subject_tagging.py` | `is_mundane_clusterable()` + `mundane_run_length()`（支持 allowed_buckets）+ mundane 词表 |
| `screen_planner_stages.py` | `try_mundane_grid()`（兼容 `try_food_grid`）+ 章末 flush + stage 顺序插入 |
| `screen_planner.py` | `_make_food_grid_screen()`、`FOOD_GRID_LAYOUT_HINT`、参数透传 |
| `config.py` | `CurateConfig.enable_food_grid` + `mundane_grid_buckets` + default helper |
| `layout_planner.py` | screens attach 路径透传 `enable_food_grid` |
| `curate.py` | 从 `cur_cfg.enable_food_grid` 传递到 chapter build |
| `tests/test_food_grid.py` | P10 MVP 用例 |
| `tests/test_subject_tagging_bridge.py` | `is_mundane_clusterable` 回归 |

---

## 备注

- P10 默认仅启用 `food` 桶；Phase 10.1 以配置 `mundane_grid_buckets` 方式预埋 `sign/ticket/shop`。
- `enable_food_grid=false` 通过配置回退原行为。
- PRD 对照总计 12 项任务，当前状态：**12/12 已完成，0 未完成**。
