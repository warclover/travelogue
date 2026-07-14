# 帮助与情境引导系统 V1 · 落地说明

| 属性 | 内容 |
|------|------|
| **PRD** | [PRD-HELP-ONBOARDING-V1.md](./PRD-HELP-ONBOARDING-V1.md) **v1.1.1** |
| **波次** | **W0 → W3**（V1 编码收口） |
| **日期** | 2026-07-14 |
| **状态** | 主链 + L2 + 平台 tip 可手测 · 静态门禁已加 · **补丁：Dock→H3 / L1 互斥 / F10** |

## 波次摘要

| 波次 | 内容 |
|------|------|
| **W0** | COPY / seen 全局双写 / `isHelpL1Blocked` / 发群三要素 / FirstSuccess 方案 A |
| **W1** | Import 支架 · FirstSuccess · 长图脉冲+可见 tip · Task Dock 发群 |
| **W2** | 「?」· HelpDrawer H1–H5 · 重播 · T-REFINE-SAVE · 面板冲突 |
| **W3** | **T-PLATFORM-PICK** · 情境反链 H1/H3/H4 |
| **补丁** | pending/stale/next-step Dock → H3；长图 tip 活跃时跳过平台 tip；pending 时延后长图 L1（F10）；重播文案含平台 tip |

## W3 本轮

| 项 | 落点 |
|----|------|
| **T-PLATFORM-PICK** | 首次从微信群切到朋友圈/小红书 → toast + 面板内 coach（合同句）；`platformPickSeen` 与 legacy moments coach 双清/兼容 |
| **情境反链** | Wizard 文件夹 → H1；导出拦截 Modal → H3；**pending/stale/仅更新 next-step Dock → H3**；成功态「怎么发到微信群？」→ H4 |
| **L1 互斥** | `isLongshotHelpActive()` 时 `maybeShowPlatformPickTip` 跳过（不叠 tip） |
| **F10** | `isHelpLongshotDeferred`：layout pending / warn Dock 可见时延后长图 tip，idle 后补评估 |
| **重播** | 同步清 `platformPickSeen` + legacy moments coach；toast 提及平台 tip |

### 关键文件（增量）

- `templates/studio/js/help-onboarding.js`（`maybeShowPlatformPickTip`）
- `templates/studio/preview-toolbar/longshot.js`
- `templates/studio/js/longshot-export-panel.js`
- `templates/studio/studio-modal.js`（`helpItemId`）
- `templates/studio/preview-toolbar-v3-task-dock.js` · import-wizard · HTML/CSS

## AC 勾选

| ID | 结果 |
|----|------|
| AC-HELP-01～07、04a/05a/06a | ✅ |
| **AC-HELP-08** | ✅ T-PLATFORM-PICK |
| AC-HELP-09～17 | ✅（17 需手测 legacy 键） |

**V1 编码未做 / 产品外**

| 项 | 说明 |
|----|------|
| 漏斗周报 | 运营侧；埋点字段已预留 |
| UX-HELP-01/02 可用性复测 | 需真人样本 |
| Coach / tour 库 · 「永不显示」总开关 | 明确不做 |

## 手测 · 平台 tip（W3）

1. 清 `travelogue.studio.help.platformPickSeen` 与 `longshotMomentsCoachSeen`
2. 预览 → 导出设置 ▾ → 从「微信群」点「朋友圈」或「小红书」
3. 见 tip：「会按平台切成多张；页脚有顺序。失败可改回微信群长图」
4. 再切平台不再出现；重播后可再出现

## 埋点

既有 `help_*` + `longshot_platform_change`；平台 tip 走 `help_coach_show|dismiss`（`touchpoint=T-PLATFORM-PICK`）
