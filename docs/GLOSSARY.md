# Travelogue · 术语消歧（M-C6 · ARC-14）

> 一页登记仓库内易混淆的 **「v3」** 指代。改名（如 `homepageVariant=v3` → `classic`）推迟至 Import Wizard v3 全量稳定后（G-WIP-03）。

| 名称 | 指代 | 代码 / 配置锚点 | 关联 PRD |
|------|------|-----------------|----------|
| **Classic 首页 v3** | Studio 首页 holdback **对照组**：旧版 classic 壳（非 Homepage v2 主路径） | `studio_homepage_gate.py` · `homepageVariant=v3` · session `travelogue.studio.homepageVariant` | [PRD-STUDIO-HOMEPAGE-v2.md](./PRD-STUDIO-HOMEPAGE-v2.md) |
| **Import Wizard v3** | 居中 Dialog 导入向导（`importWizardV3Enabled`） | `templates/studio/studio-home-v2.html` · `import-wizard.js` · `studio-home-v2.css` Import Wizard 区块 | [PRD-IMPORT-SHEET-v3-WIZARD.md](./PRD-IMPORT-SHEET-v3-WIZARD.md) |
| **Preview Toolbar v3** | 预览页统一 Sheet + Task Dock 布局代际 | `preview-toolbar-v3-sheet.js` · `preview-toolbar-v3-task-dock.js` · `preview-toolbar.js` | [PRD-PHASE5.md](./PRD-PHASE5.md) · [preview-toolbar-v3-wireframe.html](./wireframes/preview-toolbar-v3-wireframe.html) |

**注意**：上述三者互不依赖；讨论「v3」时请标明表格中的列名，避免把 Wizard 与 classic 对照组混为一谈。
