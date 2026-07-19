# PR · Preview Chrome Unify V1

**Branch:** `feat/preview-chrome-unify-v1` → `master`  
**Create URL:** https://github.com/warclover/travelogue/pull/new/feat/preview-chrome-unify-v1

---

## Summary

- 主路径零结构打扰：去掉默认黄 G1 横幅 / 底舱 G1 / 独立「可先预览」badge；管道态进 Dock D-STAT
- Dock 增加选修「分章」+ Scheme A（墨炭壳 + CTA `#c4a574`）；Help `?` 并入 Dock
- F5 轻面板：跳章 / 说明 / 重生 / 完成·确认并继续；默认路径服务端 auto-lock；实验 `g1ConfirmStructure` ON 自动开面板且无黄条
- Help 文案提及「分章」；窄屏触控 ≥40px、Dock 不溢出视口

## Test plan

- [x] `python -m pytest tests/unit/web/test_help_onboarding_v1.py tests/unit/web/test_preview_toolbar_v3.py tests/unit/web/test_studio_ux_p3.py -q`
- [x] 本地狗粮：典型用户 A–F（见 ACCEPTANCE）
- [ ] **CI**：若 Actions 额度耗尽 → **以本地套件为准**（PR 备注）
- [ ] Merge 后 smoke：新建快速分享 → 预览无黄条 → 长图；点「分章」开关面板

## Docs

- [ACCEPTANCE-PREVIEW-CHROME-UNIFY-V1.md](../ACCEPTANCE-PREVIEW-CHROME-UNIFY-V1.md)
- [product-note](./preview-chrome-unify-v1-product-note-2026-07-19.md) · [decisions](./preview-chrome-unify-v1-decisions-2026-07-19.md) · [review](./preview-chrome-unify-v1-review-2026-07-19.md)
- [wireframe](../wireframes/preview-chrome-unify-v1-wireframe.html)

## Merge notes

- **勿带入**：`config/output_recipe_*`、根目录 `qa-*.png`
- 覆盖 Refine「默认 G1 醒目横幅」主路径合同（PRD 脚注已补）
- Soft gaps（不挡合入）：SF-05 埋点率 / SF-06 质量样例 / SF-07 亮景抽检

## Commits

1. `dc2c13a` feat(studio): unify preview chrome with on-demand chapter panel
2. （合入准备）验收/PR 正文 + 合同测试对齐 Dock 40px·分章·侧栏让位
