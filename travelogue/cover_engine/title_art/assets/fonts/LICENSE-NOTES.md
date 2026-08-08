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

## 2. 鸿雷板书体（简+繁）3.001（`licensed=True` · 可随包分发）

- **中文名**：鸿雷板书体（简+繁）
- **版本**：3.001（`hongleibanshuti`）
- **授权类型**：作者公布的免费商用授权表（含嵌入式应用）
- **授权来源**：
  - 站酷作品页：https://www.zcool.com.cn/work/ZNDMzODk5ODQ=.html
  - 微信公众号授权说明：https://mp.weixin.qq.com/s/LRKYtTIghVSNX2pY4w-mZA
- **商用约束（摘录）**：个人 / 企业免费商用；明确允许「各类嵌入式应用」（含 iOS / Android / 鸿蒙 / Windows / macOS 应用内嵌、网页 / H5 / 小程序等）。**禁止**单独售卖字体文件本身、注册为商标、或声明对该字体享有知识产权。
- **核查时间**：2026-08-08（项目根目录 `字体/` 入库存证 + 授权表截图）
- **核查结论**：✅ 可进生产候选池并随包分发；符合 D-CAL-07「嵌入软件」门槛（高于仅「平面商用」）
- **本地资产**：`assets/fonts/鸿雷板书体（简+繁）3.001.ttf`
- **授权留痕截图**：`assets/fonts/honglei-banshu-license-2026-08-08.png`
- **说明**：已替换池内旧条目「鸿雷板书简体-测试版」（测试版不得商用/不得入默认）；正式版 3.001 简繁合一，可打包进入 app

## 3. Aa剑豪体（`licensed=False` · 未达嵌入门槛，禁止默认）

- 来源为「字由」类字库市集常见字体；通用免费商用条款**不等于**允许随软件嵌入分发，嵌入通常需另行书面授权
- **不**随包分发资产文件（避免误用）；`pick_default_font()` 永不返回本条目
- 状态：⏳ 待取得嵌入授权后再改 `licensed=True` 并随包分发

## 结论

生产默认路径（`pick_default_font()`）当前仍命中 **ZhiMangXing-Regular**（池内第一款 `licensed=True`）。鸿雷板书体 3.001 已核查可嵌入、已随包分发，可在评估 / 切换默认时直接使用；Aa剑豪体保持 `licensed=False`，不随包分发。
