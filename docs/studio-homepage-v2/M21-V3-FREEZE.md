# M21-e1 · Classic 冻结说明（`/classic`）

> **状态（2026-06）**：M21-e2 已执行。full v3（`studio.html/js/css`）已删除；应急入口为 `legacy-freeze/studio.classic.*`。  
> 本文档保留为历史记录与 `/classic` 运维参考。

## 当前冻结范围

- `templates/studio/legacy-freeze/studio.classic.html`
- `templates/studio/legacy-freeze/studio.classic.js`
- `templates/studio/legacy-freeze/studio.classic.css`

## 冻结规则

- 不新增功能、不新增埋点、不做交互重构。
- 仅允许“最小可用”修复：页面可打开、可发起导入、可进入预览。
- 任何改动必须附带 `/classic` smoke 验证记录。

## 最小 smoke（必须通过）

```bash
python -m pytest tests/test_studio_classic_freeze_smoke.py tests/test_studio_home_v2.py -q --tb=short -k "classic"
```

## Nightly 护栏

- `nightly-holdback.yml` 应持续执行 v2 AC + classic smoke。
- 若 classic smoke 失败，按 M21 回滚卡流程处理。
