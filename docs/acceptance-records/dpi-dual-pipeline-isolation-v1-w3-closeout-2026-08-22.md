# DPI W3 收口 · AC-DPI-16 / 17 / 23

| 属性 | 内容 |
|------|------|
| **合同** | [PRD-DUAL-PIPELINE-ISOLATION-V1.md](../PRD-DUAL-PIPELINE-ISOLATION-V1.md) v0.2.1 |
| **日期** | 2026-08-22 |
| **里程碑** | W3 · FE 分发 + 文档回写 |
| **夹具** | `schemas/fixtures/trip.render_golden.json`（克隆 + 注入 `edition`） |

独立迭代烟测不进 `test-pr`（IE-DPI-08）。本页留下实跑命令与输出。

原始 JSON：[attachments/dpi-w3-dogfood-2026-08-22/probe-report.json](./attachments/dpi-w3-dogfood-2026-08-22/probe-report.json)。夹具 `trip.render_golden.json`；改完 YAML / CSS 均 `git checkout` 还原，仓库产物零残留。

## AC-DPI-16 · 真改一张 `screen-*` 轨道

`screen-landscape-3-asymmetric-left.yaml`：`cols: [17, 10]` → `[17, 11]`，然后只跑 `python -m travelogue.layout_templates.cli export --sync-journal`。

| 面 | 基线 `?v=` / sha16 | 改后 | 原始字节 |
|----|-------------------|------|---------|
| 游记 web | `lse16f41315f6a` / `544f08a500ffe9ef` | `lsef128e5d5d0e` / `73525a7f7a41b6dc` | **变了**（证明改动生效） |
| 作品集 web | `ls0d3491b16737` / `4ede5aff14edb588` | 同左 | **零 diff**（含 `?v=`） |

## AC-DPI-17 · 真改一张 `page-*` 轨道

`page-1-hero-port.yaml`：`31.015625` → `30.015625`，然后只跑 `export --sync-portfolio`。

| 面 | 基线 | 改后 | 原始字节 |
|----|------|------|---------|
| 作品集 web | `ls0d3491b16737` / `4ede5aff14edb588` | `lsaa79b9c34225` / `db9e1d13b84fbf30` | **变了** |
| 游记 web | `lse16f41315f6a` / `544f08a500ffe9ef` | 同左 | **零 diff** |
| 游记长图 | `lse16f41315f6a` / `3c02119bcd5ac70b` | 同左 | **零 diff** |

## AC-DPI-23 · 误伤在 PR 阶段红灯

当前产物：`python scripts/lte_journal_css_audit.py --fail-on-prefix-leak` → exit 0，`journalHasPageRules=false` / `portfolioHasScreenRules=false`。

反例（写进 `journal-screens.css` 后必红，再还原）：

```text
.layout-screen__grid--page-dpi-leak { display: none; }

exit 1
prefixLeak.journalHasPageRules = true
journalPageHits = ["page-dpi-leak"]
```

还原后门再绿。

## SHD-DPI-05 · 打开对面 demo

本机 `trips/demo-81d3442e92`（作品集 · 东澳一日游 · 16 页）经 `http://127.0.0.1:18765/index.html` 打开：封面完整，`data-edition="portfolio"`。该目录仍是 DPI 前产物（`journal.css` 仍 `@import journal-screens.css?v=lsbaaadc12673a`）；游记 YAML 探测还原后未重渲染它，肉眼无坏版式。

## W3 FE 出门

2026-08-22 实跑：

```text
npm run test:js                  # 150 passed（含游记面板快照零 diff）
npm run tsc:preview-toolbar      # exit 0
pytest -m pipeline_isolation -q  # 55 passed
```
