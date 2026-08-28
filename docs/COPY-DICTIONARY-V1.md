# Travelogue · 界面术语表 V1

| 属性 | 内容 |
|---|---|
| **DOC-STATUS** | frozen |
| **版本** | v1.0.0 |
| **状态** | Sprint 0 冻结 · 竖切开工前合同 |
| **机器源** | `travelogue/domain/copy_dictionary.py` · `templates/studio/js/copy-dictionary.js` |
| **关联** | [导出预设门面](./PRD-EXPORT-PRESET-FACADE-V1.md) · [首次预览行动层级](./PRD-FIRST-PREVIEW-ACTION-HIERARCHY-V1.md) · [首访可信](./PRD-FIRST-SESSION-TRUST-V1.md) · [帮助系统](./PRD-HELP-ONBOARDING-V1.md) |
| **漏斗** | [Studio 埋点](./studio-homepage-v2/TELEMETRY.md) §7 · `scripts/studio_funnel_baseline.py` |

> 本表冻结对象名、动作名和意图名。Sprint 1 只改竖切三处文案（引导、工具栏、成功反馈），不另起一套词典。

## 1. 五层用词

| 层级 | 用词 | 规则 |
|---|---|---|
| 动作 | 导出 | 所有主动作出产物的按钮与进度文案 |
| 对象 | 按结果说人话 | 长图 / 卡片 / 画册。禁止用「分享图」统称三种产物 |
| 意图 | 日常分享 / 内容创作 / 画册跨页 | 只在 journal 导出面出现，沿用 EPF |
| 渠道 | 微信群、朋友圈、小红书、公众号、单张海报、画册印刷 | 只表示用途或预设，不替代功能名 |
| 成功主句 | 已导出 N 张{用途}{产物} | 例：已导出 5 张朋友圈长图。禁止写「分享图已导出」 |

## 2. 身份化导出主按钮

| edition | 主文案 | aria |
|---|---|---|
| journal | 长图 | 导出长图 |
| portfolio | 导出作品集 | 导出作品集 |

不得把两套身份压成「导出分享图」。用途展开写成「导出到：微信群」，不把「发微信群」写成按钮能力。

## 3. 禁词与旧说法

新文案禁止：

- 用「分享图」同时指长图、卡片和画册
- 用渠道名当主动作（「发微信群」）
- 依赖视觉位置的说明（「灰色按钮」「右上角」）
- 把检查预览叫「验货」（帮助检索可保留旧说法）

帮助搜索必须继续命中旧说法：微信、长图、分享图、发微信群、验货。

书架 L1 徽章用「长图已就绪 / 长图需更新」（CARD-01）。帮助检索仍须命中旧说法「分享图」。

## 4. Sprint 1 才改的三处

| 表面 | 文件 | 目标 |
|---|---|---|
| 引导 | `templates/studio/js/help-onboarding.js` | L1 提示与工具栏主文案一致；去掉「验货」 |
| 工具栏 | `templates/studio/preview-toolbar/longshot.js` | journal 主按钮跟 §2；渠道不进短标签 |
| 成功反馈 | `templates/studio/js/longshot-client.js` · Task Dock | 一个成功容器；主句按 §1 |

成功面继续遵守 FST：主动作是「在文件夹中显示」，不教微信。

## 5. 非目标

- 不改 Writer、平台尺寸或产物字节
- 不改作品集默认面与 F2
- 不在本表发明第七种导出
- 不把本表写成杂志正文禁词表（分享面禁词仍以 FST §4.5 为准）
