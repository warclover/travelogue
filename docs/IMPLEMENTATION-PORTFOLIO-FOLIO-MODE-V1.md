# IMPLEMENTATION · 作品集成册双管线 PFM V1

| 属性 | 内容 |
|------|------|
| **PRD** | [PRD-PORTFOLIO-FOLIO-MODE-V1.md](./PRD-PORTFOLIO-FOLIO-MODE-V1.md) **v0.2.0** |
| **验收** | [ACCEPTANCE-PORTFOLIO-FOLIO-MODE-V1.md](./ACCEPTANCE-PORTFOLIO-FOLIO-MODE-V1.md) |
| **DOC-STATUS** | **active** |
| **分支** | `feat/pfm-portfolio-folio-mode-v1` |
| **状态** | **W0 进行中** · W1 骨架（空目录硬失败）· W3 入口 DOM 已埋、默认隐藏 |
| **更新日期** | 2026-08-20 |

---

## 0. 实施原则

1. **默认关旗 ≡ 现网 GA。** 导入两击、Dock「导出长图」、LVP 两卡零改。
2. **身份是 `trip.studio.edition`，不是第三引擎。** `layoutEngine` 仍只有 `legacy` / `screens`。禁止 `folio` / `surface` 作存储标识符。
3. **游记不写 `studio.edition`。** 缺省即 journal。
4. **无正式系列不得称作品集。** 空目录 → `E_PORTFOLIO_UNAVAILABLE`，禁止静默掉回 journal 却仍标作品集。
5. **引擎不读** `docs/templates/reserve/`。W1 出门挡 AS-PFM-01（P0 `magazine-16-standard` 入现网目录）。

---

## 1. 波次任务卡

### W0 · 命名 / schema / flag（进行中）

| ID | 任务 | 状态 |
|----|------|------|
| BE-PFM-01 | 父开关 `studio.portfolio_pipeline` 默认全关 | **Done** |
| BE-PFM-02 | trip schema：`edition` / `portfolio` / `copyOrphans`；不动 `layoutEngine` | **Done** |
| BE-PFM-03 | import payload 接受 `edition`；关旗 409 | **Done** |
| FE-PFM-01 | Wizard Step 2 身份分段 DOM（默认 hidden） | **Done**（关旗不露） |
| FE-PFM-03 | 首页次链 DOM（`homepage_entry=false` 不露） | **Done** |

**验证**

```powershell
python -m pytest tests/unit/config/test_edition.py tests/unit/web/test_portfolio_pipeline.py tests/unit/layout_engine/test_editorial_series.py tests/unit/web/test_import_wizard_payload_contract.py -q
node --test tests/js/import-wizard-logic.test.mjs
```

**回滚**：删 `travelogue/config/edition.py`、`editorial_series` 包、父开关字段；还原 import / curate / 首页 DOM。关旗路径与现网一致，无用户面回滚。

### W1 · 匹配器骨架（挡 AS-PFM-01）

| ID | 任务 | 状态 |
|----|------|------|
| BE-PFM-04 | `run_curate` 身份分叉；游记 `compose_trip` 签名零改 | **Done** |
| BE-PFM-05/10 | `editorial_series` 包 + 正式目录加载器（跳过 `folio-*`） | **骨架** · 目录空 |
| BE-PFM-08 | 无系列 → `E_PORTFOLIO_UNAVAILABLE` | **Done**（正确硬失败） |
| BE-PFM-09 | import-linter：mosaic / layout_templates 不得反向依赖 | **Done** |
| BE-PFM-06/07/21/22 | 组→页、装填、溢出、items 同源 | **Blocked** · AS-PFM-01 |

界面与文档在正式系列入库前一律说「版式试验」，不得称作品集（D-PFM-26）。

### W2 / W3 / W4

见 PRD §12–§13。W2 挡 TSU `page-*` 入库。W3 Dock / 精修 / 书架待预览路径。W4 狗粮盲评后才考虑 `homepage_entry`。
