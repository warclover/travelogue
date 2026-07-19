# Preview Chrome Unify V1 · 合入准备（2026-07-19）

| 属性 | 内容 |
|------|------|
| **分支** | `feat/preview-chrome-unify-v1` |
| **相对 master** | **1+** 功能提交 + 合入准备文档（本记录同期） |
| **远端** | `origin/feat/preview-chrome-unify-v1` 已推送 |
| **GitHub Actions** | 可能不可用 → **本地 pytest + 狗粮**为准 |
| **PR 正文草稿** | [preview-chrome-unify-v1-PR-BODY.md](./preview-chrome-unify-v1-PR-BODY.md) |
| **验收** | [ACCEPTANCE-PREVIEW-CHROME-UNIFY-V1.md](../ACCEPTANCE-PREVIEW-CHROME-UNIFY-V1.md) · AC-PCU-01～10 Pass |

---

## 1. 必须项 — 已齐

| 项 | 状态 |
|----|------|
| D-PCU-01～12 实现（主路径零打扰 · Dock 分章 · Scheme A · auto-lock · F5） | ✅ |
| 线框 MF-07 Scheme A + CTA 文案 | ✅ |
| Help SF-04 · 窄屏 MF-05（≥40px / 不裁切） | ✅ |
| 合同单测 + Playwright smoke 对齐新 Dock | ✅ |
| 典型用户 A–F 狗粮 | ✅ |

## 2. 不挡合入

| 项 | 说明 |
|----|------|
| SF-05 / SF-06 / SF-07 | 埋点率、质量样例、亮景抽检可后置 |
| `gh auth` | 本机 CLI 未登录时用 Compare URL 开 PR |

## 3. 合入步骤

1. 工作区勿 stage：`config/output_recipe_*`、`qa-*.png`
2. 本地命令绿（见 ACCEPTANCE §3）
3. 开 PR（Compare URL 或 `gh pr create`）：
   - https://github.com/warclover/travelogue/compare/master...feat/preview-chrome-unify-v1?expand=1
   - 正文可粘贴 [PR-BODY](./preview-chrome-unify-v1-PR-BODY.md)
   - 注明 CI skipped（若 Actions 不可用）
4. Merge（squash 或 merge commit 均可）
5. Merge 后 smoke：新建游记 → 预览无黄条 → 长图；「分章」开关

## 4. 开 PR 命令（需 `gh auth login`）

```powershell
cd C:\Users\xiafe\Projects\travelogue
gh pr create --base master --head feat/preview-chrome-unify-v1 `
  --title "feat(studio): Preview Chrome Unify V1 — on-demand chapter panel" `
  --body-file docs/acceptance-records/preview-chrome-unify-v1-PR-BODY.md
```
