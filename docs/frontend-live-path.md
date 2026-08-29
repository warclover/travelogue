# 前端活路径（RCL W0）

权威清单。合同以 [PRD-READABLE-CORE-LINE-V1.md](./PRD-READABLE-CORE-LINE-V1.md) §7 为准。W0 登记 + lint；W3 已在 §7.2 名单文首打 `LIVE` / `READER` 状态头。

**G-RCL-01**：下一支改 `assemble.py` / `journal_chapters.py` / `_stage_build_chapters_compose` 的功能 PR，合并前 RCL W0 必须在主干。

## 闭包根（写死 · BLK-RCL-09）

机器门只准这两个常量，禁止第三根，禁止「或现网真实入口」：

- `templates/studio/preview-toolbar.js`
- `templates/studio/homepage-v2/bootstrap.js`

```
python scripts/lint_frontend_live_path.py
```

闭包里出现未登记文件 → 红。清单标 `FROZEN` 却被 LIVE 闭包 import → 红。清单可以多登记（READER / FROZEN / CSS），机器只约束闭包 ⊆ 清单。

状态枚举只有 `LIVE` / `READER` / `FROZEN` / `GENERATED`。文件名含 `v3` **不**表示废弃。

## 闭包外必登（纠正误删）

| 文件 | 状态 | 被谁 import | 禁止事项 |
|------|------|-------------|----------|
| `templates/visual-journal/longshot.js` | READER | 读者面 journal.hbs | 禁止与 Studio `preview-toolbar/longshot.js` 合并 |
| `templates/studio/legacy-freeze/studio.classic.js` | FROZEN | classic 冻结壳 | 禁止被 LIVE 入口 import |
| `templates/visual-journal/journal.css` | LIVE | journal.hbs / 作品集页（共享变量） | 共享、不分家；W3 目录在 marker 前 |
| `templates/visual-journal/journal-screens.css` | LIVE | journal.hbs | 禁止 `page-*`；不拆第三份族文件 |
| `templates/visual-journal/portfolio-pages.css` | LIVE | 作品集页 | 禁止 `screen-*`；不拆第三份族文件 |

## LIVE 闭包（双入口走读）

| 文件 | 状态 | 被谁 import | 禁止事项 |
|------|------|-------------|----------|
| `templates/studio/cohort-drawer.js` | LIVE | drawers.js | — |
| `templates/studio/homepage-v2/advanced-options.js` | LIVE | bootstrap.js, import-run.js | — |
| `templates/studio/homepage-v2/bento-preview-deeplink.js` | LIVE | bootstrap.js | — |
| `templates/studio/homepage-v2/bento-preview-migrate.js` | LIVE | bento-tabs.js, bento-preview-picker.js | — |
| `templates/studio/homepage-v2/bento-preview-picker-logic.js` | LIVE | bento-preview-picker.js | — |
| `templates/studio/homepage-v2/bento-preview-picker.js` | LIVE | bootstrap.js, bento-tabs.js, bento.js +1 | — |
| `templates/studio/homepage-v2/bento-stale.js` | LIVE | bento-tabs.js, bento.js, shelf.js | — |
| `templates/studio/homepage-v2/bento-tabs.js` | LIVE | shelf-menu.js, first-success.js, bento.js +2 | — |
| `templates/studio/homepage-v2/bento.js` | LIVE | harness.js, bootstrap.js, bento-tabs.js +3 | — |
| `templates/studio/homepage-v2/bootstrap.js` | LIVE | studio-home-v2.html | 首页现行入口；闭包根写死 |
| `templates/studio/homepage-v2/carousel-logic.js` | LIVE | carousel.js, phone-strip.js | — |
| `templates/studio/homepage-v2/carousel.js` | LIVE | bento.js | — |
| `templates/studio/homepage-v2/curate-client.js` | LIVE | bento-stale.js | — |
| `templates/studio/homepage-v2/dev-panel.js` | LIVE | bootstrap.js, settings-panel.js | — |
| `templates/studio/homepage-v2/error-pipeline.js` | LIVE | bootstrap.js | — |
| `templates/studio/homepage-v2/first-success.js` | LIVE | import-failed.js, harness.js, bootstrap.js +1 | — |
| `templates/studio/homepage-v2/harness.js` | LIVE | bootstrap.js, trips-client.js, settings-panel.js +1 | — |
| `templates/studio/homepage-v2/homepage-cta-logic.js` | LIVE | homepage-cta.js | — |
| `templates/studio/homepage-v2/homepage-cta.js` | LIVE | bento.js | — |
| `templates/studio/homepage-v2/import-entry.js` | LIVE | import-failed.js, harness.js, bootstrap.js +3 | — |
| `templates/studio/homepage-v2/import-failed.js` | LIVE | harness.js, bootstrap.js, import-run.js | — |
| `templates/studio/homepage-v2/import-run-logic.js` | LIVE | import-run.js | — |
| `templates/studio/homepage-v2/import-run.js` | LIVE | import-failed.js, harness.js, bootstrap.js +1 | — |
| `templates/studio/homepage-v2/import-wizard-logic.js` | LIVE | import-wizard.js | — |
| `templates/studio/homepage-v2/import-wizard.js` | LIVE | homepage-cta.js, import-entry.js | — |
| `templates/studio/homepage-v2/layout-tier.js` | LIVE | carousel.js, phone-strip.js, bento.js | — |
| `templates/studio/homepage-v2/lightbox.js` | LIVE | bootstrap.js | — |
| `templates/studio/homepage-v2/manifest.js` | LIVE | carousel.js, bootstrap.js, lightbox.js +4 | — |
| `templates/studio/homepage-v2/phone-strip.js` | LIVE | bento.js | — |
| `templates/studio/homepage-v2/settings-panel.js` | LIVE | bootstrap.js, advanced-options.js, shelf.js | — |
| `templates/studio/homepage-v2/shelf-actions-logic.js` | LIVE | shelf.js, bento-stale.js | — |
| `templates/studio/homepage-v2/shelf-longshot.js` | LIVE | shelf-menu.js, shelf-outputs.js, first-success.js | — |
| `templates/studio/homepage-v2/shelf-menu.js` | LIVE | shelf.js | — |
| `templates/studio/homepage-v2/shelf-outputs-logic.js` | LIVE | shelf-outputs.js | — |
| `templates/studio/homepage-v2/shelf-outputs.js` | LIVE | shelf-menu.js, shelf.js | — |
| `templates/studio/homepage-v2/shelf-ticket-logic.js` | LIVE | shelf.js | — |
| `templates/studio/homepage-v2/shelf.js` | LIVE | import-failed.js, harness.js, bootstrap.js +2 | — |
| `templates/studio/homepage-v2/storage-settings.js` | LIVE | settings-panel.js | — |
| `templates/studio/homepage-v2/store.js` | LIVE | shelf-menu.js, carousel.js, import-failed.js +27 | — |
| `templates/studio/homepage-v2/theme.js` | LIVE | bootstrap.js | — |
| `templates/studio/homepage-v2/trip-preview.js` | LIVE | bootstrap.js, bento-preview-migrate.js, bento-tabs.js +3 | — |
| `templates/studio/homepage-v2/trips-client.js` | LIVE | shelf-menu.js, bootstrap.js, trip-preview.js +4 | — |
| `templates/studio/homepage-v2/unsupported.js` | LIVE | bootstrap.js | — |
| `templates/studio/homepage-v2/variant-guard.js` | LIVE | import-failed.js, bootstrap.js, first-success.js +2 | — |
| `templates/studio/homepage-v2/viewport-logic.js` | LIVE | unsupported.js, narrow-gate.js | — |
| `templates/studio/homepage-v2/wait-tips-copy.js` | LIVE | help-onboarding.js, wait-tips.js | — |
| `templates/studio/homepage-v2/wait-tips.js` | LIVE | help-onboarding.js, import-run.js | — |
| `templates/studio/js/advanced.js` | LIVE | settings-panel.js | — |
| `templates/studio/js/ai-surface-dark-copy.js` | LIVE | help-drawer.js, core.js, drawers.js +4 | — |
| `templates/studio/js/ai-surface.js` | LIVE | import-failed.js, help-drawer.js, core.js +10 | — |
| `templates/studio/js/analytics.js` | LIVE | shelf-menu.js, share.js, carousel.js +41 | — |
| `templates/studio/js/bucket.js` | LIVE | bootstrap.js | — |
| `templates/studio/js/capability-card.js` | LIVE | home-stub-banner.js, bootstrap.js | — |
| `templates/studio/js/constants.js` | LIVE | shelf-menu.js, store.js, import-failed.js +17 | — |
| `templates/studio/js/copy-dictionary.js` | LIVE | longshot-client.js, output-recipe-logic.js, preview-toolbar-v3-task-dock.js +5 | — |
| `templates/studio/js/copy-page-url.js` | LIVE | unsupported.js, narrow-gate.js | — |
| `templates/studio/js/dom.js` | LIVE | advanced.js, storage-settings.js, errors.js +2 | — |
| `templates/studio/js/errors.js` | LIVE | import-failed.js | — |
| `templates/studio/js/export-preset-facade.js` | LIVE | longshot-export-panel.js | — |
| `templates/studio/js/help-drawer.js` | LIVE | bootstrap.js, import-wizard.js, preview-toolbar-v3-task-dock.js +4 | — |
| `templates/studio/js/help-onboarding.js` | LIVE | bookends.js, help-drawer.js, home-stub-banner.js +9 | — |
| `templates/studio/js/home-stub-banner.js` | LIVE | import-failed.js, bootstrap.js, first-success.js +1 | — |
| `templates/studio/js/http.js` | LIVE | shelf-menu.js, bookends.js, output-recipe.js +23 | — |
| `templates/studio/js/job-poll.js` | LIVE | shelf-menu.js, curate-client.js, longshot-client.js +6 | — |
| `templates/studio/js/journal-dock-logic.js` | LIVE | dock.js | 游记 dock 逻辑；勿铺 is_portfolio |
| `templates/studio/js/llm-settings.js` | LIVE | import-failed.js, bootstrap.js | — |
| `templates/studio/js/longshot-client.js` | LIVE | share.js, shelf-outputs.js, longshot-client-fallback.js +3 | — |
| `templates/studio/js/longshot-export-panel.js` | LIVE | dock.js, longshot.js, shelf-longshot.js | — |
| `templates/studio/js/longshot-ready.js` | LIVE | shelf-actions-logic.js, longshot.js, shelf-longshot.js | — |
| `templates/studio/js/output-recipe-logic.js` | LIVE | output-recipe.js | — |
| `templates/studio/js/output-recipe.js` | LIVE | longshot.js, shelf-longshot.js | — |
| `templates/studio/js/portfolio-dock-logic.js` | LIVE | dock.js | 作品集 dock 逻辑；勿铺 is_portfolio |
| `templates/studio/js/portfolio-edition-logic.js` | LIVE | shelf-menu.js, import-wizard.js, features.js +2 | — |
| `templates/studio/js/portfolio-export-logic.js` | LIVE | shelf-menu.js, narrow-gate-logic.js, dock.js +14 | — |
| `templates/studio/js/state.js` | LIVE | errors.js, dom.js | — |
| `templates/studio/js/studio-exit.js` | LIVE | init-v3.js, settings-panel.js | — |
| `templates/studio/js/title-humanize.js` | LIVE | import-run-logic.js, longshot-client-fallback.js, dom.js | — |
| `templates/studio/preview-toolbar-v3-sheet.js` | LIVE | init-v3.js | 文件名含 v3 ≠ 废弃 |
| `templates/studio/preview-toolbar-v3-task-dock.js` | LIVE | init-v3.js | 文件名含 v3 ≠ 废弃 |
| `templates/studio/preview-toolbar.js` | LIVE | journal.hbs / present shell | 现行预览入口；勿当死代码删 |
| `templates/studio/preview-toolbar/ai-sheet.js` | LIVE | init-v3.js | — |
| `templates/studio/preview-toolbar/bookends.js` | LIVE | init-v3.js | — |
| `templates/studio/preview-toolbar/bootstrap.js` | LIVE | preview-toolbar.js | LIVE 装配壳 |
| `templates/studio/preview-toolbar/chapter-panel.js` | LIVE | init-v3.js | — |
| `templates/studio/preview-toolbar/core.js` | LIVE | bookends.js, narrative-posture.js, chapter-panel.js +3 | — |
| `templates/studio/preview-toolbar/dock.js` | LIVE | init-v3.js | 身份分发只留 mount + journal/portfolio DockLogic |
| `templates/studio/preview-toolbar/drawers.js` | LIVE | chapter-panel.js, init-v3.js, features.js | — |
| `templates/studio/preview-toolbar/dual-preview.js` | LIVE | longshot.js | — |
| `templates/studio/preview-toolbar/features.js` | LIVE | init-v3.js | 本波不拆 |
| `templates/studio/preview-toolbar/init-v3.js` | LIVE | preview-toolbar.js | 文件名含 v3 ≠ 废弃 |
| `templates/studio/preview-toolbar/inline-edit.js` | LIVE | core.js, longshot.js, init-v3.js +1 | — |
| `templates/studio/preview-toolbar/longshot-client-fallback.js` | LIVE | longshot.js | — |
| `templates/studio/preview-toolbar/longshot-logic.js` | LIVE | longshot.js | — |
| `templates/studio/preview-toolbar/longshot.js` | LIVE | init-v3.js / features.js | 本波不拆 |
| `templates/studio/preview-toolbar/narrate-diff.js` | LIVE | init-v3.js | — |
| `templates/studio/preview-toolbar/narrative-posture.js` | LIVE | init-v3.js | — |
| `templates/studio/preview-toolbar/narrow-gate-logic.js` | LIVE | narrow-gate.js | — |
| `templates/studio/preview-toolbar/narrow-gate.js` | LIVE | bootstrap.js, init-v3.js | — |
| `templates/studio/preview-toolbar/preview-mode.js` | LIVE | share.js, bookends.js, init-v3.js +1 | — |
| `templates/studio/preview-toolbar/share.js` | LIVE | bootstrap.js, init-v3.js | — |
| `templates/studio/preview-toolbar/shell.js` | LIVE | share.js, bookends.js, core.js +7 | — |

