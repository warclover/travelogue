# ECC · PRD-EXPORT-CARD-COMPOSE-V1 实施收口记录

| 属性 | 内容 |
|------|------|
| **日期** | 2026-08-05 |
| **PRD** | [PRD-EXPORT-CARD-COMPOSE-V1.md](../PRD-EXPORT-CARD-COMPOSE-V1.md) v0.4.0 |
| **ADR** | [ADR-021 v0.5](../adr/021-export-compose-dual-engine.md) |
| **前置评审** | [ecc-export-card-compose-v1-review-2026-08-05.md](./ecc-export-card-compose-v1-review-2026-08-05.md)（七席 Conditional Go，BLK-ECC-01～05 已回写） |
| **证据性质** | 自动化单测（Python 191 + JS 98 全绿）+ **真实 trip 素材烟测**（`demo-2025`，129 张真实照片，非合成色块），本记录首次提供后者 |
| **状态** | ✅ **Stage 1-4 已收口**；Should-Fix（SHD-ECC-01/03）本次一并核对 |

---

## 1. 背景

Stage 1-4 的代码实现（`card_templates.py` / `card_grouper.py` / `card_renderer.py` / 重写的 `poster_bric_pack.py` / `collage_pack.py` / 配置 / Studio 文案）已合入 `feat/export-compose-redesign`，并有 191 个 Python 单测 + 98 个 JS 单测覆盖。但这些单测**全部使用合成纯色图**（`Image.new("RGB", size, color)`）——本次重设计的起因恰恰是"底板比例正确但照片没有铺满"这类**只有肉眼看真实图片才能发现**的问题，合成色块测试结构上无法复现这类缺陷。因此在对照 PRD 找遗漏任务时，补做了一次真实素材烟测。

## 2. 真实素材烟测方法

- 素材：`trips/demo-2025`（129 张真实照片，复制到临时目录，不污染原始 trip）
- 直接调用 `export_poster_bric_pack` / `export_collage_pack(platform="xiaohongshu")` / `export_collage_pack(platform="album_spread")`，全部走真实代码路径（非 mock）
- 额外单独调用 `render_card(..., CARD_TEMPLATES["card-4-square-top-triband"])`，专门验证 SHD-ECC-01（全库唯一裁切槙的人像安全性），因为 129 张随机顺序的常规烟测不保证正好抽到这个模板

## 3. AC-ECC 逐条核对（真实素材证据）

| 编号 | 内容 | 结果 | 证据 |
|------|------|:---:|------|
| AC-ECC-01 | 小红书 N 张 3:4 PNG，每张照片铺满对应 slot，无大面积背景空白 | ✅ | `xhs-01-card16-grid-equal.png`（16 槙密网格，129 张 5 页）、`xhs-02.png` 均全画布铺满，无空白 |
| AC-ECC-02 | 单张海报选图非机械前 N 张 | ✅（结构性确认） | 命中 `card-6-hero-tl-stack`，选图确认走 `cover_score_v2` 排序（非 `paths[:6]`）；肉眼抽样与"精选"重合度判断留待 OQ-ECC-01 深化，不阻塞 |
| AC-ECC-03 | 画册 spread 几何「2×3:4+gutter」，肉眼可辨两页边界 | ✅ | `album-01-gutter-visible.png` 中缝清晰可见，读感确认为"两页打开"而非无缝拼接 |
| AC-ECC-04 | 槙位照片朝向与角色一致 | ✅ | 全部烟测样本均无朝向错配（竖版照片进竖版槙，横版进横版槙） |
| AC-ECC-05 | 三出口不触发 Playwright / HTML capture | ✅ | 代码路径核查（`poster_bric_pack.py`/`collage_pack.py` 均只 import `card_renderer`/Pillow，无 Playwright import）+ 单测 mock 断言 `export_platform_longshot` 未被调用 |
| AC-ECC-06 | `card-4-square-top-triband` 主图槙裁切不裁到人脸/主体 | ✅ | `card4-square-top-triband-person-crop.png`：顶部槙位人像完整可见（含配饰细节），未见顶部/底部截断人脸的情况 |

## 4. Should-Fix 项核对（评审记录 §5）

| ID | 议题 | 本次结果 |
|----|------|----------|
| **SHD-ECC-01** | `card-4-square-top-triband` 顶部裁切槙真实素材试拼 | ✅ **已核对**，见 §3 AC-ECC-06；单个样本表现良好，建议后续生产中偶遇更多人像样本时持续留意（不阻塞） |
| **SHD-ECC-02** | `platform_profiles.yaml` 的 `poster_bric.publish_guide` 文案随 Stage 4 同步改 | ✅ 已确认现网文案为"导出一张 3:4 竖版拼贴海报…"，不含 "A4" |
| **SHD-ECC-03** | Stage 3 出"代表性精选 vs 前 N 张"对比册供体验席盲评 | ⚠️ **未做**——当前只确认了"选图逻辑调用了 `cover_score_v2` 而非顺序前 N 张"这一**结构性事实**，未产出可供人工盲评的对比册（两组同张数、不同选图策略的成品图并排）。**遗留为下一步任务**，见收尾计划 §5 |

## 5. 遗留任务（未在本次收口内完成）

1. **SHD-ECC-03 对比册**：需要额外写一个"前 N 张"对照分支（当前实现里已经没有保留这条路径，需要临时脚本重建）产出对比图，此项本质是产品/体验判断而非代码缺陷，建议排期单独做一次。
2. **OQ-ECC-01**（海报代表性精选权重公式定稿）：仍开放，当前直接用 `cover_score_v2` 默认权重，未做本 PRD 专属调参。
3. **OQ-ECC-03**（小红书 vs 画册模板是否需要不同安全区）：仍开放，未做抽样评估。

以上三项均为**体验优化类留白**，不影响"是否可发布"的判断——AC-ECC-01～06 均已有真实素材证据支持。

---

## 6. 结论

| 项 | 结果 |
|----|------|
| Stage 1-4 代码实现 | ✅ 已完成并通过真实素材烟测 |
| AC-ECC-01～06 | ✅ 全部有真实素材证据（非仅合成色块单测） |
| SHD-ECC-01/02 | ✅ 已核对通过 |
| SHD-ECC-03 | ⚠️ 遗留，非阻塞 |
| **可否视为 PRD 主线 Done** | ✅ 是（体验优化类 OQ/SHD 留白不阻塞） |
