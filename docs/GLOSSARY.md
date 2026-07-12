# Travelogue · 术语消歧（M-C6 · ARC-14）

> 一页登记仓库内易混淆的 **「v3」** 指代。Homepage holdback 对照组已改名 **`classic`**（M-C6 第二段）；query/session 仍兼容读入 legacy `v3`。

| 名称 | 指代 | 代码 / 配置锚点 | 关联 PRD |
|------|------|-----------------|----------|
| **Classic 首页（holdback 对照组）** | Studio 首页 holdback **对照组**：旧版 classic 壳（非 Homepage v2 主路径） | `studio_homepage_gate.py` · `homepageVariant=classic`（兼容 `v3`）· session `travelogue.studio.homepageVariant` | [PRD-STUDIO-HOMEPAGE-v2.md](./PRD-STUDIO-HOMEPAGE-v2.md) |
| **Import Wizard v3** | 居中 Dialog 导入向导（唯一生产入口） | `templates/studio/studio-home-v2.html` · `import-wizard.js` · `import-entry.js` | [PRD-IMPORT-SHEET-v3-WIZARD.md](./PRD-IMPORT-SHEET-v3-WIZARD.md) |
| **Preview Toolbar v3** | 预览页统一 Sheet + Task Dock 布局代际 | `preview-toolbar-v3-sheet.js` · `preview-toolbar-v3-task-dock.js` · `preview-toolbar.js` | [PRD-PHASE5.md](./PRD-PHASE5.md) · [preview-toolbar-v3-wireframe.html](./wireframes/preview-toolbar-v3-wireframe.html) |
| **Preview Refine V1（精修体验）** | 在 v3/v4 壳上重组编辑心智：验货默认、「精修」侧栏、统一「更新版面」、导出拦截 pending；首页「导入偏好」分词 | P0–P2 已落地（拦截/改名/图标 · 三区 IA · G1 横幅 · inline ✓ · stale Dock）；SF-02 盲测合入后补 | [PRD-PREVIEW-REFINE-V1.md](./PRD-PREVIEW-REFINE-V1.md) · [ACCEPTANCE-PREVIEW-REFINE-V1.md](./ACCEPTANCE-PREVIEW-REFINE-V1.md) · [preview-refine-v1-wireframe.html](./wireframes/preview-refine-v1-wireframe.html) |

**注意**：上述「v3」三者互不依赖；讨论「v3」时请标明表格中的列名，避免把 Wizard 与 classic 对照组混为一谈。**精修 V1** 是体验代际名，不是又一个「v3」。
