# ACCEPTANCE · 作品集成册双管线 PFM V1

| 属性 | 内容 |
|------|------|
| **PRD** | [PRD-PORTFOLIO-FOLIO-MODE-V1.md](./PRD-PORTFOLIO-FOLIO-MODE-V1.md) **v0.2.0** · **§14 为源** |
| **实施** | [IMPLEMENTATION-PORTFOLIO-FOLIO-MODE-V1.md](./IMPLEMENTATION-PORTFOLIO-FOLIO-MODE-V1.md) |
| **DOC-STATUS** | **active** |
| **更新日期** | 2026-08-21 |

本页只锁定已开工波次的可执行门。完整 AC 表仍以 PRD §14 为准。

---

## W0 门（本波必须绿）

| ID | 断言 | 证据 |
|----|------|------|
| **AC-PFM-01** | 父开关默认 false；首页主 CTA 文案零改；次链默认 hidden | `test_portfolio_pipeline_defaults_off` · `test_homepage_portfolio_entry_exists_but_hidden_by_default` |
| **AC-PFM-02** | 开旗 + 不选作品集：导入仍游记；Dock「导出长图」、LVP 两卡、主 CTA 零改 | `test_flag_on_journal_import_stays_journal` · `test_journal_chrome_unchanged_when_flag_exists` |
| **AC-PFM-07** | 关旗后新 import `edition=portfolio` → 409 `E_PORTFOLIO_UNAVAILABLE` | `test_import_portfolio_rejected_when_flag_off` |
| **AC-PFM-27** | `layoutEngine` 枚举仍只有 `legacy` / `screens` | `test_layout_engine_enum_has_no_third_value` |
| **AC-PFM-28** | 游记不写 `studio.edition` | `test_apply_import_edition_journal_does_not_write_field` |
| **AC-PFM-05** | 运行时系列目录不在 `docs/templates/reserve/` | `test_official_series_dir_is_not_reserve` · `test_assert_not_reserve_path_rejects_atelier` |

## W1 门（匹配器 + P0 金样本已入库）

| ID | 断言 | 证据 |
|----|------|------|
| **AC-PFM-11** | 空目录 / 空资产 → 硬失败，不静默 journal | `test_compose_portfolio_trip_empty_catalog_hard_fails` · `test_load_official_series_empty_dir_is_empty` |
| **BE-PFM-04** | 游记路径仍 `compose_trip` | `test_curate_fork_source_contract` |
| **AC-PFM-09** | 一页不跨两个 shotGroup | `test_place_groups_never_mixes_shot_groups` · `test_refuse_cross_group_screen` |
| **AC-PFM-29** | kept 超档先升档；升到 32 仍溢出才 cap | `test_select_series_upgrades_when_span_misses` · `test_compose_fixture_overflow_cap` |
| **AC-PFM-08** | 实收 ⊆ kept，且等于 screens 出现的资产 | `test_compose_fixture_upgrades_and_syncs_items` |
| **AC-PFM-31** | 屏数未超 items stub 上限时 items ≡ screens | `test_compose_items_match_screens_when_stub_can_cover` |
| **AC-PFM-03** | ISO-01 游记指纹不含 `studio.edition` | `test_iso01_journal_fingerprint_excludes_studio_edition` |
| **AS-PFM-01** | 现网目录含且仅含 P0 `magazine-16-standard`（16 页、`photo_span [48, 80]`）；拒 `folio-*` | `test_official_catalog_p0_magazine_16` · `test_compose_from_official_magazine_16` · `test_intake_rejects_folio_and_pagecount_mismatch` |
| **ISO-05** | 加载器拒绝 `docs/templates/reserve/` | `test_load_official_series_rejects_reserve_dir` |

P0 序列已入运行时目录。W1 匹配器可对官方 16 页装配。**AS-PFM-02**：75 张 `page-*` 已编译进 LTE（P0 11 张齐）；游记 MCS 不选这些脸。作品集预览 Dock 已可称「导出作品集」；C 端首页主 CTA 仍不得称作品集。夹具 `photo_span [12, 32]` 只测升档，与现网 `[48, 80]` 分开。

## W2 门（page-* 几何）

| ID | 断言 | 证据 |
|----|------|------|
| **AS-PFM-02** | P0 11 张 `page-*` 在 LTE；`list_active` 不含 `page-*`；`page-10` 未收 | `test_p0_eleven_faces_are_in_lte` · `test_page_faces_are_not_mcs_active` · `test_page_ten_skipped_schema_max` |
| **BE-PFM-11 persist** | 作品集 `page-*` 屏可过 `layoutScreen`；游记拒 `page-*`；H8 枚举不含 `page-*` | `test_p0_composed_screens_are_layout_screen_legal` · `test_journal_trip_rejects_promoted_page_face` · `test_schema_all_pattern_ids_excludes_page_star` |
| **AC-PFM-34** | 作品集阅读 profile 默认 `magazine`；游记默认不变 | `test_portfolio_web_defaults_to_magazine` |
| **AC-PFM-19** | 作品集不弹 OR 意图卡；显式 xhs 仍可解析 | `test_portfolio_ambiguous_does_not_need_intent` · `test_portfolio_explicit_xhs_still_resolves` |
| **N-PFM-15** | `portfolio_pages` 在已知平台、不在 PHASE_A | `test_portfolio_pages_known_not_phase_a` |
| **AC-PFM-17** | 页图 `{title}-portfolio-{nn}`；单页失败跳过且不回滚已成功页 | `test_skip_one_page_keeps_compact_successes` |
| **AC-PFM-37** | 一次动作两件：zip 或页图其一失败，另一件仍产出 | `test_bundle_zip_failure_still_writes_pages` · `test_bundle_pages_failure_still_writes_zip` |
| **ISO-05** | 运行时系列加载器仍拒绝 reserve | `test_load_official_series_rejects_reserve_dir` |
| **AC-PFM-16** | 作品集 Dock 主钮「导出作品集」；游记 init-v3 不含该串 | `test_journal_chrome_unchanged_when_flag_exists` · `tests/js/portfolio-export-logic.test.mjs` |
| **AC-PFM-38** | 成功面主按钮「打开这一本」 | `portfolioSuccessCopy` · `test_journal_chrome_unchanged_when_flag_exists` |
| **AC-PFM-18** | 换种分享默认折叠；xhs/画册不读 `patternId`；游记弹层仍「画册印刷」 | `tests/js/longshot-export-panel.test.mjs` · `test_collage_pack_does_not_read_pattern_id` |

## W3 门（精修成册类型 + 书架 · 本波已锁）

| ID | 断言 | 证据 |
|----|------|------|
| **AC-PFM-20** | 切换确认含「精选保留」与「文字可能无法全部保留」 | `tests/js/portfolio-edition-logic.test.mjs` |
| **AC-PFM-21** | 切换只触发装配段（`refresh_algorithms=False`） | `test_edition_runner_stamps_portfolio_without_refresh` |
| **AC-PFM-06** | 作品集不渲染 LVP「成册风格」（源码按 `isPortfolio` 卸区） | `test_journal_chrome_unchanged_when_flag_exists` · `hooks.isPortfolio` |
| **AC-PFM-22** | 书架作品集弱标；游记行不写身份 | `shelfEditionLine` · `test_shelf_list_exposes_portfolio_edition_and_page_count` |
| **AC-PFM-07** | 关旗改成作品集 409；改回游记始终允许；存量作品集横幅 + 改回；B/C 关旗隐藏 | `test_edition_switch_flag_off_rejects_portfolio` · `test_edition_journal_allowed_when_flag_off` · `test_portfolio_flag_off_banner_and_bc_hidden` · `tests/js/portfolio-edition-logic.test.mjs` |
| **AC-PFM-12** | 精修钉 18 页 → 靠档并显示「非标准页数 · 按 16 页靠档」 | `test_snap_18_to_16_hint` · `test_compose_user_pin_18_snaps_on_official` |
| **AC-PFM-35** | 导入不出页数控件 | `test_homepage_portfolio_entry_exists_but_hidden_by_default` · `v2-wizard-page-count` 不在首页 |
| **AC-PFM-30** | 溢出角标带「改用游记（全收）」 | `overflowJournalCta` · `syncPortfolioOverflowBadge` |
| **AC-PFM-39** | 切身份可回填的回填；回填不上的进 `copyOrphans` 且不静默丢 | `tests/unit/domain/test_copy_migrate.py` · `test_edition_switch_orphans_user_caption` |
| **AC-PFM-36** | 低于派生阈值时作品集卡置灰 + 提示，确认后仍可继续 | `tests/js/import-wizard-logic.test.mjs` · `test_config_exposes_derived_min_kept` |
| **AC-PFM-40** | 作品集 trip 缺 `--platform` 报错并列可选值；`portfolio_pages` 不进批量多选 | `tests/unit/cli/test_portfolio_cli.py` · `test_portfolio_pages_known_not_phase_a` |
| **AC-PFM-33** | 作品集等待态 / 成功面不含「文案 / 正在写」；游记 Wait Tips 与 `STAGE_LABELS.narrate` 字面不动 | `test_portfolio_wait_copy_avoids_writing_phrases` · `tests/js/import-run-logic.test.mjs` · `test_wait_tips_six_cards_match_prd_section4` |
| **AC-PFM-24** | 窄屏仍提示电脑精修/导出；游记 gate 字面不动 | `tests/js/narrow-gate-logic.test.mjs` · `test_portfolio_narrow_gate_keeps_refine_export_on_desktop` · `test_snr_w3_narrow_gate_copy_present` |
| **AC-PFM-13** | Wizard 默认游记；键盘可切到作品集；确认焦点陷阱 | `nextRadioId` · `test_edition_radiogroup_keyboard_and_confirm_trap` |

## W3 收口 + 隔离 + 证据（本波已锁）

| ID | 断言 | 证据 |
|----|------|------|
| **FE-PFM-06 / AC-PFM-02** | 游记导出 Dock / ▾ 开旗前后零 diff；夹具不含「导出作品集」 | `journalExportPanelSnapshot` · `tests/js/longshot-export-panel.test.mjs` |
| **BE-PFM-16 / AC-PFM-06 / 16 / 30** | GET entry / 书架同一份 chrome：主 CTA、溢出行、LVP 可见 | `edition_chrome` · `test_build_entry_exposes_portfolio_edition` · `test_shelf_and_entry_share_overflow_chrome` |
| **BE-PFM-20 / AC-PFM-21** | telemetry 打 edition / seriesId / pageCountSource / overflow.count；游记不加 edition | `test_portfolio_telemetry_fields_only_on_portfolio` |
| **BE-PFM-18 / AC-PFM-03 / 04 / 27** | 游记指纹字段级对照；xhs / album 卡序；全库无第三 layoutEngine | `test_iso01_flag_on_journal_fingerprint_field_equal` · `tests/unit/export/test_pfm_collage_isolation.py` · `test_iso07_repo_has_no_third_layout_engine_value` |
| **BE-PFM-14 / AC-PFM-18** | 作品集 trip 导出 xhs，plan 不读 `screens[].patternId` | `test_ac_pfm_18_portfolio_xhs_plan_does_not_read_pattern_id` |
| **AC-PFM-10** | 槽 ≥5 且组规模不足 → 降级少槽，不硬塞 | `test_ac_pfm_10_dense_page_degrades_when_group_too_small` |
| **AC-PFM-32** | 作品集正文无图注 / 章导语节点；封面封底书名地点仍在 | `test_ac_pfm_32_portfolio_body_omits_caption_and_lead` |
| **AC-PFM-14** | 作品集 + 快速仍两击 | `wizardHitsToStart` · `tests/js/import-wizard-logic.test.mjs` |
| **AC-PFM-23** | C 端可见串禁 edition / PFM / MCS / page-* | `test_ac_pfm_23_c_end_visible_copy_has_no_jargon` |
| **ISO-04** | 作品集 × 显式微信群 **不得拍** 5 槽以上 `page-*`（几何门保持）。**Studio 开导改判见 [CLG](./PRD-CROSSING-LONGSHOT-GATE-V1.md)**：作品集 × 微信群 / 朋友圈 → `E_CLG_NEEDS_JOURNAL` | `tests/unit/export/test_pfm_collage_isolation.py` · Studio 单测改判见 CLG BE-CLG-02 |
| **ISO-06** | 作品集拒 LVP；切身份不改 `layoutVibe` | `test_iso06_lvp_rejects_portfolio_trip` · `tests/unit/config/test_edition.py` |
| **AS-PFM-03** | **已升格 · 五档入库**（8/12/16/20/28；24/32/36 未入）。工坊对账原文不变；运行时仍拒 reserve | [对账纪要](./acceptance-records/pfm-as-pfm-03-atelier-reconcile-2026-08-21.md) · [MSP 后继](./acceptance-records/pfm-as-pfm-03-msp-promote-2026-08-21.md) · `test_atelier_series_audit.py` |

## W4 门（协议已锁 · 人评未开）

| ID | 断言 | 证据 |
|----|------|------|
| **AC-PFM-25** | 金样成对盲评「像一本」三问胜出 | [GUIDE](./acceptance-records/pfm-local-dogfood-GUIDE.md) · [模板](./acceptance-records/pfm-blind-review-TEMPLATE.md) · [W4 定点](./acceptance-records/pfm-w4-kickoff-2026-08-22.md) · **尚未打分** |
| **D-PFM-06** | 盲评过门前 `homepage_entry` 保持 false | `test_homepage_portfolio_entry_exists_but_hidden_by_default` |
