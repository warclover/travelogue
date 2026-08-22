# DPI W3 收口 · AC-DPI-16 / 17 / 23

| 属性 | 内容 |
|------|------|
| **合同** | [PRD-DUAL-PIPELINE-ISOLATION-V1.md](../PRD-DUAL-PIPELINE-ISOLATION-V1.md) v0.2.1 |
| **日期** | 2026-08-22 |
| **里程碑** | W3 · FE 分发 + 文档回写 |
| **夹具** | `schemas/fixtures/trip.render_golden.json`（克隆 + 注入 `edition`） |

独立迭代烟测不进 `test-pr`（IE-DPI-08）。本页留下实跑命令与输出。

## AC-DPI-16 · 改游记轨道不影响作品集 `?v=`

游记 bundle 含 `journal-screens.css`，不含 `portfolio-pages.css`。改一张 `screen-*.yaml` 后只需跑游记侧 `export --sync-journal` / 游记回归；作品集 HTML 的 `?v=` 不吃这份哈希。

2026-08-22 实跑：

```text
journal_has_screens True
journal_has_pages False
portfolio_has_screens False
portfolio_has_pages True
j_v lse16f41315f6a
p_v ls0d3491b16737
```

机器门：`pytest tests/unit/trip/test_asset_version.py::test_ac_dpi_18_bundle_paths_are_pipeline_disjoint -q`（绿）。游记 / 作品集 `?v=` 分算，互不包含对面族 CSS。

## AC-DPI-17 · 改作品集轨道不影响游记 `?v=`

反向：作品集 bundle 含 `portfolio-pages.css`，不含 `journal-screens.css`。改一张 `page-*.yaml` + `--sync-portfolio` 后游记 web / 长图 HTML 的 `?v=` 不变。

同上命令与 `test_ac_dpi_18_bundle_paths_are_pipeline_disjoint`。

## AC-DPI-23 · 误伤在 PR 阶段红灯

故意把游记 contain 选择器或 `page-*` 写进对面产物，由前缀门挡住，不靠人 review。

2026-08-22 实跑 `python scripts/lte_journal_css_audit.py --fail-on-prefix-leak`：

```text
prefixLeak.journalHasPageRules = false
prefixLeak.portfolioHasScreenRules = false
```

绿 = 当前产物无交叉前缀。反例：在 `portfolio-pages.css` 写入 `screen-` 选择器，或在 `journal-screens.css` 写入 `page-`，该命令必红。

## W3 FE 出门

2026-08-22 实跑：

```text
npm run test:js                  # 150 passed（含游记面板快照零 diff）
npm run tsc:preview-toolbar      # exit 0
pytest -m pipeline_isolation -q  # 55 passed
```
