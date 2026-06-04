# Travelogue · Phase 15 对标调研（Benchmark · 自动拼图与相册编排）

| 属性 | 内容 |
|------|------|
| **文档版本** | v0.15.0-BENCHMARK |
| **状态** | Draft |
| **关联 PRD** | [PRD-PHASE15-photo-mosaic-evolution.md](./PRD-PHASE15-photo-mosaic-evolution.md) |
| **更新日期** | 2026-06-04 |

---

## 1. 调研范围

本轮调研聚焦“自动选片 + 自动编排 + 可编辑控制”三类能力，覆盖：

1. Google Photos（Memories）
2. Apple Photos（Memory Movie / Apple Intelligence）
3. Canva（模板与尺寸适配）
4. Adobe Express（Grid 与模板编辑）
5. Shutterfly（Auto Create Photo Book）
6. Mixbook（Auto-Create / Auto-Layout）

---

## 2. 核心发现（可复用）

## 2.1 行业共识

1. **自动先给成品**：先自动生成 80%-90% 可用结果，再允许人工微调。
2. **混合决策优于单一路径**：规则做兜底，模型/评分做排序。
3. **用户控制必须可达**：支持删图、换图、换布局、关闭某类回忆。
4. **可解释与回退是上线前提**：决策可回放，低置信可降级。

## 2.2 反模式（应避免）

1. 仅靠硬规则命中，导致模板覆盖窄、感知单一。
2. 只做算法不做可观测，无法调参与排障。
3. 只做自动化不做用户控制，容易被认为“黑盒”。

---

## 3. 竞品实践与本项目对比

| 能力域 | 竞品实践 | Travelogue 现状 | 差距判定 |
|------|----------|-----------------|----------|
| 自动草稿 | Shutterfly/Mixbook 一键出完整书稿，可继续编辑 | 可自动编排，但局部窗口（5 张）命中窄 | **中** |
| 决策机制 | Google/Apple 规则 + 智能排序混合 | `screen_planner_stages` 以阶段命中即返回为主 | **高** |
| 可解释性 | 多提供用户可见控制与系统可解释信号 | 缺 top3 候选与 winner reason 结构化日志 | **高** |
| 用户控制 | 可移除单图、重命名/移除记忆、替换布局 | 尚无“换个布局”入口 | **中** |
| 模板平台化 | Canva/Adobe 模板化 + 栅格化 + 护栏 | 已有 pattern/grid 基础，配置化不足 | **中** |
| 安全回退 | 低置信/异常可降级默认路径 | 有 legacy 路径，但缺低分回退标准字段 | **中** |

---

## 4. 面向 Phase 15 的借鉴映射

## 4.1 必做（P0）

1. **候选集 + 统一打分**
   - 参考：Google/Apple 的“多信号融合”
   - 落地：`try_mosaic_five -> generate_five_candidates + pick_best_candidate`

2. **决策日志标准化**
   - 参考：商业产品普遍具备可解释调参闭环
   - 落地：记录 `top3Patterns/top3Scores/winnerReasonCodes/fallbackReason`

3. **低分回退机制**
   - 参考：自动化产品默认保守回退
   - 落地：`winnerScore < threshold => fallback legacy`

## 4.2 应做（P1）

1. **5 张模板家族化**
   - 参考：Mixbook/Adobe 的多布局覆盖
   - 落地：新增 4-6 个 5 张 pattern，支持次优匹配

2. **节奏去重惩罚**
   - 参考：叙事产品强调整体节奏而非单页最优
   - 落地：`f_pattern_novelty` 抑制重复 pattern 连发

3. **单页重选接口**
   - 参考：Shutterfly/Mixbook 的“自动后可改”
   - 落地：预留 `replan_screen(screenId, strategy=alt_topk)` API

## 4.3 可选（P2）

1. `intent` 驱动布局偏好（风景/人像/纪实）
2. A/B 权重自动调优与离线回放看板
3. 轻量用户可见解释（如“已按连拍与横竖比例优化”）

---

## 5. 对 Phase 15 主 PRD 的回填建议

已建议并回填到主 PRD 的关键条款：

1. 新增 AC：记录 top3 候选与 winner reasonCodes
2. 新增 AC：winner 低分自动回退并记录 `fallbackReason=low_score`
3. 新增指标：`layout.mosaic_v2.low_score_fallback_rate`

建议继续补充（下一版可加）：

1. AC：`top3` 候选日志覆盖率 >= 99.9%
2. AC：回放一致性（同输入同 scorerVersion 结果一致）
3. AC：A/B 对比下 pattern 重复率下降目标（如 >= 15%）

---

## 6. 参考来源

1. Google Photos 官方博客（Memories）  
   - https://blog.google/products-and-platforms/products/photos/new-memories-features-look-back/  
   - https://blog.google/products-and-platforms/products/photos/google-photos-memories-view/
2. Apple 官方 Newsroom / Support（Apple Intelligence in Photos）  
   - https://www.apple.com/cf/newsroom/2024/06/introducing-apple-intelligence-for-iphone-ipad-and-mac/  
   - https://support.apple.com/guide/mac-help/use-apple-intelligence-in-photos-mchl35c53342/mac
3. Canva Help（Resize / Magic Resize）  
   - https://www.canva.com/help/resize/
4. Adobe Express（Grids / Collage）  
   - https://experienceleague.adobe.com/en/docs/creative-cloud-enterprise-learn/cce-learning-hub/expressoverview/expresshowto/grids
5. Shutterfly（Auto Create Photo Book）  
   - https://www.shutterfly.com/a/auto-create-photo-book/
6. Mixbook（Auto-Create）  
   - https://www.mixbook.com/inspiration/auto-create-make-photo-books-in-minutes

