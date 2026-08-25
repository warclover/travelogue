# IMPLEMENTATION · 作品集主路径 PFO V1

| 属性 | 内容 |
|------|------|
| **PRD** | [PRD-PORTFOLIO-FLOW-OPTIMIZATION-V1.md](./PRD-PORTFOLIO-FLOW-OPTIMIZATION-V1.md) **v0.2.1** · **§12 为源** |
| **验收** | [ACCEPTANCE-PORTFOLIO-FLOW-OPTIMIZATION-V1.md](./ACCEPTANCE-PORTFOLIO-FLOW-OPTIMIZATION-V1.md) |
| **线框** | [v1.2 F9–F11 已签](./wireframes/portfolio-folio-mode-v1-wireframe.html) · [签核](./acceptance-records/pfo-f9-f11-signoff-2026-08-25.md) |
| **DOC-STATUS** | **active** |
| **状态** | **W1+W2 编码已清** · W3 真夹狗粮未开 · 不批无条件 Go |
| **更新日期** | 2026-08-25 |

任务卡以 PRD §12 为准。本页只记落点与状态。

---

## 0. 实施原则

1. 向导是共享壳，规格区走身份 seam。禁止抄一套 portfolio wizard。
2. 游记零改：import 不带 `pageCount`，FirstSuccess 仍可 `autoExport=wechat_chat`。
3. `0.67` 只进「大约」文案，不准选档。
4. 导出点法对齐六种；默认产物仍是这一本。禁止复制一份 longshot 面板 HTML。
5. 成功面 / 帮助不承诺逐页换图。

---

## 1. 波次

| 波次 | 状态 | 落点 |
|------|------|------|
| **W1** | **Done** | `css_stale.py` 作品集读 `portfolio-pages.css` · edition job `stamp_render_bundle` · 角标人话 · 空页不进唯一 `pageCountHint` |
| **W2** | **Done** | 向导 `#v2-wizard-page-spec` · `apply_import_edition(..., page_count=)` · FirstSuccess 打开∥导出 · `?exportPanel=1` · 精修文案去掉「导入时不会问」 |
| **W3** | **未开** | ≥1 本真夹不进精修完成导出；≥3 本再谈估计比进选档 |
| **W4** | 可选 | 热更新 / 导出后续导（FE-PFO-08/09） |

---

## 2. 关键路径

| 面 | 文件 |
|----|------|
| 规格纯函数 | `templates/studio/homepage-v2/import-wizard-logic.js` |
| 向导 DOM | `templates/studio/studio-home-v2.html` · `import-wizard.js` |
| 导入落盘 | `travelogue/config/edition.py` · `studio_pipeline.py` · `import_handlers.py` |
| 成功面 | `templates/studio/homepage-v2/first-success.js` |
| 导出面板消费 | `templates/studio/preview-toolbar/longshot.js` `consumeExportPanel` |
| 精修文案 | `templates/studio/preview-toolbar/features.js` |

---

## 3. 验证

```powershell
python -m pytest tests/unit/config/test_edition.py tests/unit/web/test_portfolio_pipeline.py tests/unit/layout_engine/test_editorial_series.py -q
node --test tests/js/import-wizard-logic.test.mjs tests/js/portfolio-export-logic.test.mjs tests/js/dual-pipeline-panel.test.mjs
python -m pytest -m pipeline_isolation -q
```
