# M21-e2 最终删除变更草稿（不执行）

> 目的：给出可直接评审/执行的分批次 changeset 方案。本文仅是草案，不在观察窗口内执行删除。

## 总体策略

- 分 **3 批次** 提交，避免一次删净导致回退困难。
- 每批次都附带“必跑验证”和“快速回退点”。
- 执行前需满足：`studio_m21e2_preflight.py --observed-release --json` 返回 `ready=true`。

## Batch 1 · 物理删除 v3 入口文件

### 变更范围

- 删除：
  - `templates/studio/studio.html`
  - `templates/studio/studio.js`
  - `templates/studio/studio.css`

### 执行命令（建议）

```bash
python scripts/studio_m21e2_delete_plan.py
# 确认后：
git rm templates/studio/studio.html templates/studio/studio.js templates/studio/studio.css
```

### 必跑验证

```bash
python -m pytest tests/test_studio_home_v2.py -q --tb=short -k "gate_classic_serves_v3 or v2_route_redirects_to_root"
python -m pytest tests/test_studio_handlers_config_static.py -q --tb=short
```

### 回退点

- 直接 `git revert` 本批次提交。

## Batch 2 · 删除仅 v3 依赖的编排模块

### 变更范围

- 删除：
  - `templates/studio/js/navigation.js`
  - `templates/studio/js/render.js`
  - `templates/studio/js/sheet.js`
  - `templates/studio/js/samples.js`
  - `templates/studio/js/init.js`
  - `templates/studio/js/viewport.js`

### 执行命令（建议）

```bash
git rm templates/studio/js/navigation.js templates/studio/js/render.js templates/studio/js/sheet.js templates/studio/js/samples.js templates/studio/js/init.js templates/studio/js/viewport.js
```

### 必跑验证

```bash
python -m pytest tests/test_studio_home_v2.py tests/test_studio_home_v2_ac_playwright.py tests/test_studio_homepage_gate.py tests/test_studio_homepage_gate_security.py tests/test_studio_lcp_measure.py tests/test_studio_lcp_playwright.py -q --tb=short
```

### 回退点

- 直接 `git revert` 本批次提交。

## Batch 3 · legacy 测试与文档收口

### 变更范围

- 清理或归档 `legacy_homepage` 相关测试（按团队决策：删除/迁移/保留历史套件）。
- 更新 M21 文档与 runbook，标注“v3 已物理退役，`/classic` 仅快照资产”。

### 建议优先清理的测试文件

- `tests/test_studio_a11y_p4.py`
- `tests/test_studio_p8_regression.py`
- `tests/test_studio_phase5_tier0.py`
- `tests/test_studio_p9_qa_matrix.py`
- `tests/test_studio_homepage_m12.py`
- `tests/test_studio_ux_p3.py`（v3 用例）
- `tests/test_m21_h2_sample_longshots.py`

### 必跑验证

```bash
python scripts/studio_m21e2_preflight.py --observed-release --json
python -m pytest tests -q --tb=short -m "(e2e or playwright_serial) and not legacy_homepage" -k "studio_home_v2 or studio_homepage_gate or studio_lcp"
```

### 回退点

- 文档/测试层回退可独立于 Batch 1/2 执行。

## 发布说明草稿

- 主入口：`/`（v2）
- 应急入口：`/classic`（deprecated，快照资产）
- 兼容入口：`/v2`（302 到 `/`）
- v3 开发态文件与编排模块已从仓库移除
