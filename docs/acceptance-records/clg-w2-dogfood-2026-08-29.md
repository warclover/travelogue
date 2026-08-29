# CLG W2 狗粮 · 2026-08-29

| 属性 | 内容 |
|------|------|
| **合同** | [PRD-CROSSING-LONGSHOT-GATE-V1.md](../PRD-CROSSING-LONGSHOT-GATE-V1.md) v0.1.2 · §11 W2 / §13 |
| **Studio** | 本机 `http://127.0.0.1:8767/`（`python -m travelogue studio --port 8767 --trips-dir trips`） |
| **结论** | **QA-CLG-02 / 03 已走通。** 产品 2026-08-29 认本记录，升 **Go**。 |

同夹按 `albumRoot` 认，不按书名。华农作品集的游记是 `demo-49551086fe`《华农油菜花》，不是凯哥那本。

## QA-CLG-02 · 华农作品集过河

打开 `demo-d21946c6a9/index.html?exportPanel=1&exportFace=social`。

| 断言 | 结果 |
|------|------|
| 六卡都在 | 微信群 / 朋友圈 / 小红书 / 公众号 / 单张海报 / 画册印刷 |
| 闸卡 | 微信群、朋友圈 `data-clg-locked=1`，无 `aria-disabled`，副文「要先有一本游记」 |
| 默认主选 | 小红书 `aria-pressed=true` |
| 顶条 | 「这不是在导出作品集。」·「小红书、海报和印刷可以在这里做。长图要在游记里做。」 |
| 徽章 | 「用这些照片」 |
| 确定钮 | 「导出小红书」· 无「导出长图」· 无「点「长图」开始导出」 |
| 按章区 | `data-field=mode` hidden |
| `GET sibling-journal` | 200 · `present=true` · `tripId=demo-49551086fe` |
| 点微信群 | 不改主选；说明层「长图要在游记里做」· 同名书用 `sheetHasBodySameTitle` |
| 打开那本游记 | 落到 `demo-49551086fe/index.html?exportPanel=1` · `data-export-face=journal` · 标题「导出设置」· 六卡可点 · 无闸文案 · 确定「确定」 |
| `POST /edition` | **无** |
| 导出小红书 | `POST /__travelogue/longshot` → **202**（不是 409 / `E_CLG_NEEDS_JOURNAL`） |
| 再看 Dock | 主 CTA「导出作品集」（AC-CLG-10） |

未等到小红书成功句（8 张，未空转完）。开导已被 Studio 接受。

## QA-CLG-03 · 无同夹游记

`demo-81d3442e92`《珠海东澳岛一日游》· `sibling-journal`：`present=false` · `canCreateSibling=true`。

| 断言 | 结果 |
|------|------|
| 点微信群 | 帧 C：去做一本游记 / 先出小红书 |
| 去做一本 | 回首页，向导「确认并开始」· 夹已填 · **游记**预选 |
| 确认句 | 「将新建一本游记，不会覆盖已有作品集《珠海东澳岛一日游》。两本可以同时留在书架上。」 |
| 作品集 | 书架上仍是 `demo-81d3442e92`，未点「开始制作」 |

## 本波补的 W1 缺口

狗粮时发现 F2 仍写「点「长图」开始导出」，且缺主句「这不是在导出作品集。」。已在 `isPortfolioSocialExportFace` 缝上修：藏确认摘要、补 `leadPrimary`。游记 `journalExportPanelSnapshot` 单测仍绿。

## 未做

- 未空转完小红书 8 张成功句
- 未点「开始制作」（避免再造一本珠海游记）
- 未走帧 D / BLK-CLG-05 peek 漏认

## 签字

| 角色 | 结论 | 日期 |
|------|------|------|
| 产品 | ☑ 认本记录，升 Go | 2026-08-29 |
