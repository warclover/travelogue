# Studio 导出与导入信任 · 结案（2026-08-30）

| 属性 | 内容 |
|------|------|
| **DOC-STATUS** | **closed**（本波关闭 · 不再开实施） |
| **日期** | 2026-08-30 |
| **合同来源** | [功能与交互测试报告-2026-08-30](../功能与交互测试报告-2026-08-30.md)；**未新开 PRD** |
| **分支** | `fix/studio-export-import-trust` |
| **合入** | [#84](https://github.com/warclover/travelogue/pull/84) · merge `91caf71c` |
| **功能提交** | `5a870015` honor explicit chapter export and recover from bad import paths |
| **测试提交** | `8d0fb875` lock chapter export and import recovery on a live Studio |
| **帮助 / 清点合同** | [PRD-HELP-ONBOARDING-V1](../PRD-HELP-ONBOARDING-V1.md) H5；[PRD-STABLE-QUALITY-HARDENING-V1](../PRD-STABLE-QUALITY-HARDENING-V1.md) 清点四态 |

---

## 结论

报告中的 4 条 P1、2 类测试缺口、以及 UX-05 的体积预告均已进 `master`。隔离 Studio 与日常 `trips/` 都核对过：显式「按章分开」会出分段长图；无效本机路径在确认前被阻断。本修复计划关闭，勿再往同一主题加刀。

---

## 交付对照

| 报告项 | 结果 | 落地要点 |
|--------|------|----------|
| **BUG-02** 按章被配方覆盖 | **通过** | `apply_recipe_layout_to_segment_mode()`：仅 `auto` / 缺失才跟 `recipe.layout`；Web 与 CLI 共用 |
| **QA-01** 测试停在设置层 | **通过** | 后端锁最终 `segment_mode`；e2e 锁 manifest `kind` 与文件数 |
| **BUG-01** 示例可「设为首页预览」 | **通过（隔离）** | 成功页 `tripId && !isDemoTrip(result)` 才显示；`setBentoPreviewTripId` 拒绝 demo |
| **BUG-03** 无效路径仍能开始 | **通过** | 永久错误确认页主按钮「更换文件夹」，不能「开始制作」 |
| **BUG-04** 重试死循环 / 无退出 | **通过** | 永久错误主按钮回 pick；所有失败面保留「留在首页」；文案去掉「Sheet」 |
| **QA-02** 四态文案冻源码 | **通过** | 改断言 `wizardFailedVerifyLine` / logic helpers |
| **UX-05** 导出前无尺寸提示 | **部分通过** | 设置面板给出预计张数 / 高度 / 体积；**未做压缩档位** |

优先级合同：用户显式 `full` / `chapter` > 配方默认；`auto` 才跟随 `recipe.layout`（`single`→`full`，`chapter`/`by_chapter`→`chapter`）。仅 `wechat_chat` / 默认平台走这条缝。

---

## 自动化证据

| 层 | 位置 | 断言 |
|----|------|------|
| 配方优先级 | `tests/unit/export/test_output_recipe_resolve.py` | `single`+`chapter` 仍为 chapter；`by_chapter`+`full` 仍为 full；`auto` 跟配方 |
| CLI | `tests/unit/export/test_output_recipe_cli_handlers.py` | CLI 从 `auto` 起步，配方只填默认 |
| 清点四态 | `tests/js/import-wizard-logic.test.mjs` · `test_m3_preview_four_states_copy_frozen` | 永久 / 可恢复文案与按钮，不冻 `import-wizard.js` 字面量 |
| 首页 / 帮助 | `tests/unit/web/test_studio_home_v2.py` · help onboarding JS | 示例成功页隐藏设预览；H5「更换文件夹 / 留在首页」 |
| 真人路径 | `tests/e2e/test_export_import_trust_playwright.py` | 隔离 Studio：示例成功页、永久导入失败恢复、分章产物 |

本地门禁（Windows · Python 3.14 · 用户要求忽略 GitHub CI 账单红）：本 PR 改过的文件 ruff 绿；`npm run test:js` 207 passed。全量 `test-pr` 组有主干既有失败（ruff 79、ASH、import-linter、LSE、CQA 天花板等），**不在本波文件里**，本记录不追。

---

## 隔离 Studio 狗粮

隔离数据目录 + 配方开启。路径与当时手点一致：试用示例、贴不允许路径、预览导出。

| 断言 | 结果 |
|------|------|
| 不允许 / 不存在路径 | 确认页主按钮「更换文件夹」；文案「请更换文件夹」；不能「开始制作」 |
| 点「更换文件夹」 | 回到向导 pick |
| 示例成功页 | 无「设为首页预览」 |
| 永久导入失败 | 主按钮「更换文件夹」；「留在首页」可见；提示无「Sheet」 |
| `recipe.layout=single` + `segmentMode=chapter` | API / 手点均为 `kind: segmented`，至少 3 个文件 |

---

## 日常 Studio 观察

`python -m travelogue studio --no-open --port 8766` · 数据目录 `trips/` · `studio.output_recipe.enabled: true` · `http://127.0.0.1:8766/`。

| 路径 | 结果 |
|------|------|
| 手工路径 `C:/__travelogue_missing_folder__` | 确认页「未能清点照片，请更换文件夹」；主按钮「更换文件夹」；回到 pick |
| 失败面「留在首页」 | 可见，可关浮层回首页 |
| 《斯里兰卡见闻录》预览导出 | 设置：日常分享 / 带文字 / 按章分开；预期「预计导出 **3 张** · 约 4.0 千像素高 · 约 4.5 MB」 |
| `POST /__travelogue/longshot` | `platform=wechat_chat` · `copyDisplay=full` · `segmentMode=chapter` → 202 |
| 成功句 | 「已导出 3 张微信群长图」；toast「已导出 3 张 · 长图」 |
| 产物 | `trips/demo-album/导出文件/longshot-current.json`：`batchId=job-8b064f3e7509` · `kind: "segmented"` · 3 个 PNG |

`longshot-current.json`（日常，2026-08-30T07:42:38Z）：

```json
{
  "schemaVersion": 1,
  "batchId": "job-8b064f3e7509",
  "createdAt": "2026-08-30T07:42:38Z",
  "kind": "segmented",
  "files": [
    "斯里兰卡见闻录-长图-01.png",
    "斯里兰卡见闻录-长图-02.png",
    "斯里兰卡见闻录-长图-03.png"
  ]
}
```

同目录仍留有旧整篇 `斯里兰卡见闻录-长图.png`（约 16 MB），是本波之前的整张导出，**不是**这次产物。

---

## 本波未验 / 不做

| 项 | 说明 |
|----|------|
| 日常「再做一遍」示例 | 撞「该画册正在使用或受保护，无法覆盖导入」。失败面有「重试」+「留在首页」（占用/保护，不是坏路径）。示例成功页日常未完整重走，隔离已验 |
| 普通用户画册「设为首页预览」 | 报告验收要求刷新仍在；本波只锁「示例不出现该钮」。未用非 demo trip 手点持久化 |
| 压缩档位 | UX-05 原文建议；本波只做软预告。分章稳定后再单独立项 |
| 五类错误码 | 本波只做永久 / 可恢复两分类 |
| 作品集 / 批量导出 | 不在本报告范围 |
| 主干 ruff / LSE / CQA 天花板 | 合入前已有，不并进本波 |
| 工作区无关脏文件 | slot-aspect、PRD 草稿、`.tmp/`、截图未打进 #84，本记录也不收 |

若再开工，另开主题，不要续写本文。

---

## 结案声明

用户显式分章不再被 `recipe.layout=single` 静默改回整篇；示例成功页不再提供必然失败的「设为首页预览」；永久本机路径错误在确认前阻断，失败面可换文件夹或留在首页。本修复计划关闭。
