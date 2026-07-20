# PR · LTN Wave A Trust Baseline → master

**Branch:** `feat/ltn-wave-a-trust-baseline` → `master`  
**Create URL:** https://github.com/warclover/travelogue/pull/new/feat/ltn-wave-a-trust-baseline  
**相对 master：** ahead 23 / behind 0（已与 `origin/master` 对齐，可直接合入）

---

## Summary

- **LTN Wave A**：排版可信基线（fail-loud、CI/本地门禁钩子、H6 reefs）+ 拼图出场链路（C1–C8、hero_reserve、signature routing、slot-role、mosaic explain）
- **叙事合同 B/D**：ADR-020、longshot preserveGroup、双预览 MVP、present 分章分隔、节奏 L0/L1/L2 + classic_magazine peak、layout role / rhythmSignOff
- **运营可观测**：E1 active-set SSOT、E2 weekly dashboard、E3 track docs、E4 asymmetric dense quota
- **Studio 体验补丁**：pick-folder 加固；拼图时间内聚 900→1800s；FirstSuccess 用真实封面图 + 成果摘要条目化（勿带入竖版 preview 卡）

## Test plan

- [x] 分支与 `origin/master` 无落后（`0 behind / 23 ahead`）
- [x] FirstSuccess / home-v2 相关 unit：`tests/unit/web/test_studio_home_v2.py` 等本地绿
- [ ] **CI：本次合入忽略**（额度/排队不挡 merge；以本地套件与狗粮为准）
- [ ] Merge 后 smoke：导入完成页封面仅为照片；文件夹选择器可用；拼图日志/周看板脚本可跑

## Docs

- [PRD-LAYOUT-TRUST-NARRATIVE-V1.md](../PRD-LAYOUT-TRUST-NARRATIVE-V1.md)（v1.2.20）
- [ltn-evidence-baseline-2026-07-20.md](./ltn-evidence-baseline-2026-07-20.md)
- [ltn-dev-feasibility-review-2026-07-20.md](./ltn-dev-feasibility-review-2026-07-20.md)

## Merge notes

- **合入策略**：squash 或 merge commit 均可；**不要求 CI 绿**
- **勿带入**：根目录 `qa-*.png`、`.tmp-*`、未请求的 FTT/CHARTER 本地改动、`.cache/`、`trips/`
- Soft gaps（不挡合入）：AC-D-01 人评签核、AC-C-01 真样本基线、demo hero 稀疏仍待狗粮

## Commits（`origin/master..HEAD`）

1. `ff8bbc5` feat(ltn): Wave A trust baseline — fail-loud, CI gates, H6 reefs
2. `b97b9d2` feat(ltn): H7 geometry audit, H9 fixtures, C1 aux-3 uncouple, C3 prune+4-hero GA
3. `dcfd0d1` feat(ltn): H2 mosaic log Top3 rejects, raw metrics, winner plan marks
4. `e906426` feat(ltn): C5 hero_reserve state machine for opportunity windows
5. `316498c` fix(ltn): close PRD gaps for C1/C3/H8/C5 and AC-C hooks
6. `6c11a13` feat(ltn): C6 Studio mosaic explain — why no collage Top3
7. `d901c3b` feat(ltn): B3 dual preview MVP before longshot export
8. `3dd7c63` feat(ltn): C4 coarse segments and signature routing
9. `52d793b` test(ltn): align C6 explain labels with signature vs contract sources
10. `6bbe5c3` feat(ltn): C4 signature routing on top of template contract
11. `2de45e5` feat(ltn): C7 mosaic tracks and C8 slot-role penalties/gates
12. `67df8b7` feat(ltn): B1 Narrative Contract ADR-020, schema fields, ensure defaults
13. `aba666b` feat(ltn): B2 longshot preserveGroup tiers and B4 present chapter separators
14. `a8dc8f7` feat(ltn): D1 rhythm L0/L1/L2 tokens and D2 classic_magazine peak progress
15. `5124582` feat(ltn): E2 weekly dashboard metrics and E3 track docs
16. `00e4f6b` feat(ltn): D3 layout role table and rhythmSignOff gate
17. `b8364b0` feat(ltn): E4 asymmetric dense quota with soft opportunity
18. `86c2806` feat(ltn): E1 active-set SSOT, derive LEGACY, rollout zeroSince gate
19. `b93d4e7` feat(ltn): dogfood AC checks for B-02 and D-02/D-03
20. `f048447` feat(ltn): close PRD gaps for C-01/C-02/C-07 and weekly metrics
21. `69e9aa0` fix(ltn): harden AC-C-01 numerator and relative baseline gate
22. `a616b2d` fix(studio): harden pick-folder and raise mosaic proximity to 1800s
23. `0ad4f77` fix(studio): polish FirstSuccess cover photo and fact hierarchy
