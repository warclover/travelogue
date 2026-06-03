# M21-e2 提交级草案（Commit Draft）

> 说明：本草案用于观察窗口结束后执行。当前阶段不落地删除提交。

## Commit 1 · retire v3 entry files

### 建议标题

`retire v3 homepage entry files after classic snapshot switch`

### 变更范围

- 删除：
  - `templates/studio/studio.html`
  - `templates/studio/studio.js`
  - `templates/studio/studio.css`

### 提交前验证

```bash
python scripts/studio_m21e2_preflight.py --observed-release --json
python -m pytest tests/test_studio_home_v2.py -q --tb=short -k "gate_classic_serves_v3 or v2_route_redirects_to_root"
```

### 回退方式

- `git revert <commit-1-sha>`

## Commit 2 · remove v3-only orchestration modules

### 建议标题

`remove v3-only studio orchestration modules`

### 变更范围

- 删除：
  - `templates/studio/js/navigation.js`
  - `templates/studio/js/render.js`
  - `templates/studio/js/sheet.js`
  - `templates/studio/js/samples.js`
  - `templates/studio/js/init.js`
  - `templates/studio/js/viewport.js`

### 提交前验证

```bash
python -m pytest tests/test_studio_home_v2.py tests/test_studio_home_v2_ac_playwright.py tests/test_studio_homepage_gate.py tests/test_studio_homepage_gate_security.py tests/test_studio_lcp_measure.py tests/test_studio_lcp_playwright.py -q --tb=short
```

### 回退方式

- `git revert <commit-2-sha>`

## Commit 3 · archive legacy tests and docs references

### 建议标题

`archive legacy homepage tests and update retirement docs`

### 变更范围（按团队决策执行删除或归档）

- `legacy_homepage` 相关测试
- M21 相关执行文档收口（标注已退役）

### 提交前验证

```bash
python scripts/studio_m21e2_preflight.py --observed-release --json
python -m pytest tests -q --tb=short -m "(e2e or playwright_serial) and not legacy_homepage" -k "studio_home_v2 or studio_homepage_gate or studio_lcp"
```

### 回退方式

- `git revert <commit-3-sha>`

---

## 建议执行顺序

1. 跑 preflight 并导出报告。
2. 按 Commit 1 → Commit 2 → Commit 3 顺序执行。
3. 每个 commit 后立即跑对应验证命令并记录结果。
