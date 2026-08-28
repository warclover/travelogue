# ACCEPTANCE · 作品集主路径 PFO V1

| 属性 | 内容 |
|------|------|
| **PRD** | [PRD-PORTFOLIO-FLOW-OPTIMIZATION-V1.md](./PRD-PORTFOLIO-FLOW-OPTIMIZATION-V1.md) **v0.2.1** · **§14 为源** |
| **实施** | [IMPLEMENTATION-PORTFOLIO-FLOW-OPTIMIZATION-V1.md](./IMPLEMENTATION-PORTFOLIO-FLOW-OPTIMIZATION-V1.md) |
| **线框签核** | [pfo-f9-f11-signoff-2026-08-25.md](./acceptance-records/pfo-f9-f11-signoff-2026-08-25.md) |
| **DOC-STATUS** | **active** |
| **更新日期** | 2026-08-25 |

本页只锁已开工波次的可执行门。完整表以 PRD §14 为准。

---

## W1 门（假 pending + 人话张数）

| ID | 断言 | 证据 |
|----|------|------|
| **AC-PFO-06** | `preview_ready` 作品集打开预览：无「更新版面」主待办 | `css_stale` / edition stamp 单测 · `refreshStaleHint` |
| **AC-PFO-08** | 推荐不把空页 / M̂ 当 `kept_n` | `test_editorial_series` · edition-logic JS |
| **AC-PFO-09** | 薄档确认不含「你有 M 张」 | `portfolio-edition-logic` |
| **AC-PFO-19** | 作品集 stale 不读 `journal-screens.css` | `tests/unit/layout_engine/test_lte_css_stale.py` |
| **AC-PFO-15** | `pytest -m pipeline_isolation` 绿 | 每波 |

## W2 门（规格 + 成功面 + 面板）

| ID | 断言 | 证据 |
|----|------|------|
| **AC-PFO-01** | 向导第一眼：人话句 + 默认自动 + 开始；未展开无 8–36 横排 | `#v2-wizard-page-spec` · chips `hidden` |
| **AC-PFO-02** | 游记无规格区；import 无 `pageCount` | `buildPageCountFields("journal")` → `{}` |
| **AC-PFO-03** | 用户钉 32：`pageCountSource=user`，不因 M 升档 | `test_apply_import_edition_pins_user_page_count` · `test_compose_user_pin_32_stays_when_kept_overflows` |
| **AC-PFO-05** | FirstSuccess 打开 ∥ 导出并列；导出开同一 Dock 面板 | `first-success.js` · `consumeExportPanel` |
| **AC-PFO-10** | 主产物高亮；六种分组降级；印刷副文 | `portfolio-export-logic.test.mjs` |
| **AC-PFO-11** | 游记导出面板快照零改 | `dual-pipeline-panel.test.mjs` |
| **AC-PFO-16** | 帮助/精修无「导入时不会问」 | `features.js` 源扫 |
| **AC-PFO-17** | 作品集成功面不走 `wechat_chat` autoExport | `isPortfolioResult` 分支 |
| **AC-PFO-18** | 去精修 / 成功面不含「逐页」「换每一页」「换图改版式」 | 源扫 HTML + `first-success.js` |
| **AC-PFO-20** | 合入附件含已签 F9–F11 | **已关** · 本签核页 |

## W3 门（未开）

| ID | 断言 | 证据 |
|----|------|------|
| 真夹狗粮 | ≥1 本不进精修完成导出；对照游记无回归 | 手测 · 未开 |
| OQ-PFO-05 | ≥3 本后再议 `0.67` 进选档 | **禁止提前** |
