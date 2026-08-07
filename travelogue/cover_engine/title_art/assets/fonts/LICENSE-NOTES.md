# 字库授权核查记录（D-CAL-07 · §9）

> 覆盖 `travelogue/cover_engine/title_art/fonts.py` 的 `FONT_POOL`。
> 与 `arttext-miniapp/assets/fonts/LICENSE-NOTES.md`（Phase 1 早期计划稿，列的是「演示佛系体/禹卫书法行书简体/云墨书法字体」三款候选，与实际落地池不一致，未完成核查）区分——**本文件是当前生产候选池的权威核查记录**。

## 1. ZhiMangXing-Regular（`licensed=True` · 生产默认字库）

- **中文名**：钟齐志莽行书
- **作者 / 出品方**：上海钟齐字库公司，依书法家韦志莽先生毛笔书法开发；收录于 Google Fonts 开源字体项目
- **授权类型**：SIL Open Font License, Version 1.1（OFL 1.1）
- **授权来源**：https://github.com/google/fonts/blob/master/ofl/zhimangxing/OFL.txt（`Copyright 2018 The Zhi Mang Xing Project Authors`）
- **商用约束**：个人 / 企业均可免费商用，**无需**署名或知会作者；可随软件打包分发、修改；**禁止**单独出售字体文件本身；衍生字体须继续以 OFL 1.1 发布
- **核查时间**：2026-08-07（[cover-calligraphy-title-v1 W1 视觉验收](../../../../../docs/acceptance-records/cover-calligraphy-title-v1-w1-visual-review-2026-08-07.md)）
- **核查结论**：✅ 可进生产候选池，符合 D-CAL-07 门禁
- **本地资产**：`assets/fonts/ZhiMangXing-Regular.ttf`（随包分发，`fonts.py:_ASSET_DIR` 优先加载，不依赖操作系统预装字体）

## 2. Aa剑豪体（`licensed=False` · 未核查，禁止默认）

- 来源为「字由」类字库市集常见字体，通常需订阅会员才可商用，未核查具体条款
- **不**随包分发资产文件（避免误用）；`pick_default_font()` 永不返回本条目
- 状态：⏳ 待核查（若需启用，须补齐条款核查后改 `licensed=True` 并随包分发资产）

## 3. 鸿雷板书简体-测试版（`licensed=False` · 未核查，禁止默认）

- 文件名含「测试版」，明确非最终商用授权版本
- **不**随包分发资产文件
- 状态：⏳ 待核查（若需启用，须先确认作者是否发布过正式商用授权版本）

## 结论

生产默认路径（`pick_default_font()`）当前**仅**命中 ZhiMangXing-Regular，授权清晰、无歧义、随包资产可随时加载——满足 D-CAL-07 与 §9「字库 | 商用授权核查留痕」的验收要求。另两款候选保持 `licensed=False`，未随包分发，不影响生产渲染。
