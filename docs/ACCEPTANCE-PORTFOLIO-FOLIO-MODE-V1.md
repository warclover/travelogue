# ACCEPTANCE · 作品集成册双管线 PFM V1

| 属性 | 内容 |
|------|------|
| **PRD** | [PRD-PORTFOLIO-FOLIO-MODE-V1.md](./PRD-PORTFOLIO-FOLIO-MODE-V1.md) **v0.2.0** · **§14 为源** |
| **实施** | [IMPLEMENTATION-PORTFOLIO-FOLIO-MODE-V1.md](./IMPLEMENTATION-PORTFOLIO-FOLIO-MODE-V1.md) |
| **DOC-STATUS** | **active** |
| **更新日期** | 2026-08-20 |

本页只锁定已开工波次的可执行门。完整 AC 表仍以 PRD §14 为准。

---

## W0 门（本波必须绿）

| ID | 断言 | 证据 |
|----|------|------|
| **AC-PFM-01** | 父开关默认 false；首页主 CTA 文案零改；次链默认 hidden | `test_portfolio_pipeline_defaults_off` · `test_homepage_portfolio_entry_exists_but_hidden_by_default` |
| **AC-PFM-07** | 关旗后新 import `edition=portfolio` → 409 `E_PORTFOLIO_UNAVAILABLE` | `test_import_portfolio_rejected_when_flag_off` |
| **AC-PFM-27** | `layoutEngine` 枚举仍只有 `legacy` / `screens` | `test_layout_engine_enum_has_no_third_value` |
| **AC-PFM-28** | 游记不写 `studio.edition` | `test_apply_import_edition_journal_does_not_write_field` |
| **AC-PFM-05** | 运行时系列目录不在 `docs/templates/reserve/` | `test_official_series_dir_is_not_reserve` · `test_assert_not_reserve_path_rejects_atelier` |

## W1 门（骨架）

| ID | 断言 | 证据 |
|----|------|------|
| **AC-PFM-11** | 空正式目录 → 硬失败，不静默 journal | `test_compose_portfolio_trip_empty_catalog_hard_fails` |
| **BE-PFM-04** | 游记路径仍 `compose_trip` | `test_curate_fork_source_contract` |

匹配器 / 溢出 / items 同源（AC-PFM-08～12、27～30 其余）挡 AS-PFM-01，本波不测绿。
