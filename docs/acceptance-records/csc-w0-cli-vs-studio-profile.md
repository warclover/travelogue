# CSC · `cli_default` vs `studio_default`（R-CSC-HP-02）

| 属性 | 内容 |
|------|------|
| **DOC-STATUS** | **active** |
| **日期** | 2026-07-22 |
| **代码** | `travelogue/orchestrator/studio_profile.py` |
| **Happy Path 身份** | `studio_default`（Recipe `recipe_id=studio_default`） |

---

## 差异表（禁止静默漂移）

| 字段 | `cli_default()` | `studio_default()` | 说明 |
|------|-----------------|--------------------|------|
| `run_clustering` | `False` | `True` | Studio 导入主路径默认跑聚类 |
| `apply_editorial_hints` | `False` | `True` | Studio 应用编辑意图提示 |
| `export_layout` | `"mobile"` | `"auto"` | CLI 偏移动出口；Studio 自动 |
| `apply_layout_on_curate` | `True` | `True` | 相同 |
| `ingest.resume_ingest` | `False` | `True` | Studio 支持断点续导入 |
| `ingest.use_parallel_embed` | `False` | `True` | Studio 默认并行 embed |

`cli_default()` = dataclass 字段默认值（`StudioProfile()`）。  
`run_trip` 在未显式传入 profile 时走 **CLI** 默认；Studio pipeline 必须显式传入 `studio_default()`（或等价）。

## 变更纪律

1. 改任一列默认 → 同步更新本表 + Recipe 快照单测 / `csc-w0-baseline-happy-path-recipe.json`。  
2. **禁止**让 CLI 与 Studio 在未文档化的情况下趋同或分叉。  
3. 产品叙事「这一趟默认路径」**只**指 Studio / `studio_default`，不指 CLI。
