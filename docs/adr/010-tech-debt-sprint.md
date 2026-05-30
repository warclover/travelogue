# ADR-010 · 架构还债 Sprint（Phase 5 后渐进拆分）

| 属性 | 内容 |
|------|------|
| **状态** | 已采纳 |
| **日期** | 2026-05-30 |
| **决策者** | 技术负责人 |
| **影响范围** | `travelogue/web/`、`travelogue/runtime.py`、`travelogue/layout_contract/`、`travelogue/curation/`、`travelogue/render/`、`cli.py` |
| **关联** | [ADR-004](./004-studio-hub-server.md)（单进程 Studio 不变）、[ADR-002](./002-smart-layout-v2-integration.md)（布局黄金样本） |

---

## 背景

1. 架构深度审查指出若干 **God 文件**（`studio_routes`、`context`、`screen_planner` 等）与 **构造点分散**（多处裸 `TripService()`）、**布局与编排循环依赖** 等问题。  
2. Phase 5 功能已稳定，需在 **不破坏 ADR-004 单进程 Studio**、**不替换 jsonschema / 不引入 pydantic 全库迁移** 的前提下渐进还债。  
3. 目标：可测试的模块边界、统一运行时上下文、渲染与屏规划可读性，而非一次性「大重构」。

---

## 决策

### D1 · Studio HTTP：handlers 包 + 薄 Mixin

| 项 | 决定 |
|----|------|
| **结构** | `travelogue/web/studio_handlers/` 按域拆分（import、job、trip、export、config、static 等）；`studio_routes.py` 仅鉴权与 dispatch |
| **不变** | `serve.py` 仍从 `studio_routes` 导入路径常量；**不**新建独立 Hub 或第二端口（遵守 ADR-004） |

---

### D2 · 运行时：`AppContext` 为唯一服务构造入口

| 项 | 决定 |
|----|------|
| **类型** | `travelogue/runtime.py`：`AppContext`、`app_context_from_handler()`（Studio）、`app_context_for_trips_dir()` / `app_context_for_trip_json()`（CLI） |
| **规则** | 新代码 **禁止** 裸 `TripService()`；`studio_pipeline` 与 handlers 经 `studio_ctx(handler).trip_service()` 访问 |
| **CLI** | `cli.py` 已对齐；cluster 子命令使用 `app_context_for_trips_dir` |

---

### D3 · 布局契约：`layout_contract` 破环

| 项 | 决定 |
|----|------|
| **包** | `travelogue/layout_contract/`：`LAYOUT_PLAN_VERSION`、`format_layout_summary` |
| **依赖** | `curation/curate.py` 从此导入；`services/layout.py` **re-export** 保持对外兼容 |

---

### D4 · 编排钩子：`studio_hooks` + `run_trip`

| 项 | 决定 |
|----|------|
| **模块** | `travelogue/orchestrator/studio_hooks.py` |
| **用法** | `run_trip(..., studio_hooks=...)`；`studio_pipeline` 在 narrate/render 段传入 `StudioHooks` |

---

### D5 · 屏规划：阶段模块 + 单入口

| 项 | 决定 |
|----|------|
| **阶段** | `travelogue/curation/screen_planner_stages.py`：`ChapterPlanContext`、具名 stage（hero、mixed、mosaic、landscape、portrait、flush、tall、generic chunk 等） |
| **入口** | `ChapterScreenPlanner.create(...).plan()`；`plan_screens_for_chapter()` 在 `screen_planner.py` 保持 **薄包装** |
| **回归** | `skip_screen_asset_ids` 含 hero 时仍须从 id 集合移除，但不生成 hero 屏（见 `test_skip_web_cover_skips_chapter_hero_screen`） |

---

### D6 · 渲染分层：`context_types` + `surface` + `chapters`

| 项 | 决定 |
|----|------|
| **契约** | `travelogue/render/context_types.py`：叶节点与 `TripRenderContext` / `ChapterRenderContext` 等 `TypedDict` |
| **表面** | `travelogue/render/surface.py`：`SurfaceContext`、`resolve_surface_context` |
| **章节** | `travelogue/render/chapters.py`：`ChaptersRenderBundle`、`build_chapters_render_context` |
| **组装** | `travelogue/render/assemble.py`：`build_render_context`；`context.py` 保留叶节点 builder，**文件末尾** re-export chapters + assemble API |
| **循环依赖** | `engine` 相关 import 放在 `assemble.build_render_context` **函数内**；`chapters.py` 对 `context` 叶 builder 使用 **函数内 lazy import** |

---

### D7 · 刻意不做（本 Sprint 边界）

| 排除项 | 说明 |
|--------|------|
| 全库 `Protocol` / dacite / pydantic 替换 jsonschema | 成本高、收益分散 |
| `screen_planner.py` 整文件类迁移 | 已用 stage 拆分替代 |
| `config.py` dacite 简化 | 暂缓 |
| 新 Web 框架或 Studio 双进程 | 违反 ADR-004 |

---

## 后果

- **正面**：单文件行数下降、测试域更清晰、新功能有明确落点（handler / stage / render 子模块）。  
- **负面**：import 路径增多；部分模块依赖 **末尾 re-export** 与 lazy import，阅读时需跳文件。  
- **验证**：`test_studio_*`、`test_build_render_context`、`test_reading_folio`、layout golden、screen planner 相关 pytest 为合并门槛。

---

## 后续可选（非本 ADR 承诺）

- `context.py` 叶节点 builder 按媒体类型再拆子模块（仅当单文件再次逼近软上限）  
- `config.py` dacite 简化（仍暂缓）
