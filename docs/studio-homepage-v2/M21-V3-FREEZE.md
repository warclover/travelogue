# M21-e1 · v3 冻结说明（`/classic`）

> 目的：在 M21-e2 物理删除前，用一个发布版本把 v3 首页固定在“应急可用”状态，降低误改风险。

## 冻结范围

- `templates/studio/studio.html`
- `templates/studio/studio.js`
- `templates/studio/studio.css`

## 冻结规则

- 不新增功能、不新增埋点、不做交互重构。
- 仅允许“最小可用”修复：页面可打开、可发起导入、可进入预览。
- 任何改动必须附带 `/classic` smoke 验证记录。

## 最小 smoke（必须通过）

```bash
python -m pytest tests/test_studio_home_v2.py -q --tb=short -k "gate_classic_serves_v3"
```

建议附加（legacy 静态门禁）：

```bash
python -m pytest tests/test_studio_homepage_m12.py -q --tb=short -m legacy_homepage -k "homepage_m12_html"
```

## Nightly 护栏

- `nightly-holdback.yml` 应持续执行 `/classic` 最小 smoke。
- 若该用例失败，按 M21 回滚卡流程处理并阻断继续退役。

## 退出条件（进入 M21-e2）

- 至少一个发布版本观察窗口通过。
- `/classic` 未承载常规流程，仅作为应急入口。
- M21-d 测试迁移与 CI 稳定。
