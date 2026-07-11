## Summary

- 落地预览精修体验 V1（P0→P2）：导出拦截「更新并导出」、统一「更新版面」、Dock「精修」图标、首页「导入偏好」
- P1：G1 顶栏横幅 + Sheet 三区「这页 / 这本 / 导出与更多」
- P2：inline 字段旁 ✓、cohort 未开则藏、longshotStale Task Dock、D-REF-18 优先级栈
- 验收：`docs/ACCEPTANCE-PREVIEW-REFINE-V1.md` 条件 Go（SF-02 图标盲测合入后一周内补签）

## Out of scope（Park）

- PK-01 章标题 inline · PK-02 trip.json 乐观锁 · PK-03 阅读视图上 Dock · PK-04 放映移出 Dock
- Share 模式不变（无精修壳）
- 不包含 pipeline-throughput / TECH-ARCHITECTURE 等无关文档

## Test plan

- [x] `python -m pytest tests/unit/web/test_preview_toolbar_v3.py -m "not e2e" -q` → 22 passed
- [x] 本地 Studio 手测：零精修导出、pending 拦截 Modal、更新版面、G1 横幅、导入偏好、Share
- [x] §5 功能保全自检（见 ACCEPTANCE）
- [ ] SF-02：5 人图标盲测 ≥4/5 指认「精修」「长图」（合入后补）

## Docs

- [PRD-PREVIEW-REFINE-V1.md](../blob/feat/preview-refine-v1-p2/docs/PRD-PREVIEW-REFINE-V1.md)
- [ACCEPTANCE-PREVIEW-REFINE-V1.md](../blob/feat/preview-refine-v1-p2/docs/ACCEPTANCE-PREVIEW-REFINE-V1.md)
- [IMPLEMENTATION-PREVIEW-REFINE-V1.md](../blob/feat/preview-refine-v1-p2/docs/IMPLEMENTATION-PREVIEW-REFINE-V1.md)
