# ECC · SHD-ECC-03「代表性精选 vs 前 N 张」对比册

| 属性 | 内容 |
|------|------|
| **日期** | 2026-08-05 |
| **对应议题** | [七席评审](./ecc-export-card-compose-v1-review-2026-08-05.md) SHD-ECC-03（用户体验席要求："『代表性精选』效果最终要看狗粮盲评，不能只靠公式自证；建议先出 1–2 本对比册再定稿权重细节"） |
| **PRD** | [PRD-EXPORT-CARD-COMPOSE-V1.md](../PRD-EXPORT-CARD-COMPOSE-V1.md) §5.2 / OQ-ECC-01 |
| **素材** | `trips/demo-2025`（129 张真实照片，同一批候选池，两组仅选图策略不同，模板/画布/裁切逻辑完全一致） |
| **方法** | 同一候选池（24 张，`RANK_POOL_LIMIT`）、同一模板（分别固定 `card-6-hero-tl-stack` 与 `card-4-square-top-triband`），仅切换选图策略：**A 组**＝候选池原始顺序取前 N 张（"简单前 N 张"，本 PRD 明确废弃的旧策略）；**B 组**＝`cover_score_v2` 排序取 top N（现网 `poster_bric` 实际使用的策略） |

---

## 对比 1 · 6 槙（`card-6-hero-tl-stack`）

| A 组 · 前 6 张（旧策略，仅供对比，现网已不用） | B 组 · `cover_score_v2` 精选（现网实际效果） |
|---|---|
| ![naive-6](./attachments/ecc-selection-compare-2026-08-05/cmp-naive-6.png) | ![ranked-6](./attachments/ecc-selection-compare-2026-08-05/cmp-ranked-6.png) |

**肉眼观察**：
- A 组混入一张**菜品近景**（蛋饼特写）——作为海报封面槙位明显不合适；另有一张三人围坐、背对/侧对镜头的随手抓拍，画面张力弱。
- B 组 6 张全部是人像出镜、朝向镜头、光线好的"出片"级素材，视觉一致性明显更强，没有菜品/背影/低光这类拉低整体质感的素材混入。
- 结论：**B 组（现网策略）明显优于 A 组**，与 AC-ECC-02"选图非机械前 N 张"的验收意图相符。

## 对比 2 · 4 槙（`card-4-square-top-triband`，全库唯一裁切槙）

| A 组 · 前 4 张（旧策略） | B 组 · `cover_score_v2` 精选（现网实际效果） |
|---|---|
| ![naive-4](./attachments/ecc-selection-compare-2026-08-05/cmp-naive-4.png) | ![ranked-4](./attachments/ecc-selection-compare-2026-08-05/cmp-ranked-4.png) |

**肉眼观察**：
- A 组主槙（顶部近方形裁切槙）落在一张单人全身照上，裁切后人物偏小、背景占比高，"封面感"一般；副槙同样混入菜品近景。
- B 组主槙落在一张**双人近景合影**上，裁切后两人面部清晰完整、构图饱满，裁切没有切到人脸/主体，视觉效果接近真正的杂志封面。这同时是 AC-ECC-06（裁切安全）与 AC-ECC-02（代表性精选质量）的一次联合正向证据。
- 结论：**B 组在"选图质量"与"裁切安全"两个维度都优于 A 组**。

---

## 结论

1. **AC-ECC-02 得到真实素材的肉眼验证**：`cover_score_v2` 排序取 top-N 相比"简单前 N 张"在两组不同槙数/模板的对比中都产出了更适合作封面/海报的素材（避开食物近景、背影、低光等弱代表性素材）。
2. **OQ-ECC-01（具体权重公式）保持开放**：本对比册仅证明"当前 `cover_score_v2` 默认权重已经优于无排序基线"，不代表权重已针对本 PRD 场景精调过；如需进一步优化（例如更强调"人脸朝镜头/微笑"信号），留作后续迭代，不阻塞发布。
3. **SHD-ECC-03 状态**：✅ **已完成**（本对比册即产出物），供体验席后续抽样复核。

---

## 复现方式

```python
from travelogue.export.poster_bric_pack import _poster_candidate_pairs, _rank_by_cover_score, RANK_POOL_LIMIT
from travelogue.export.card_templates import CARD_TEMPLATES
from travelogue.export.card_renderer import render_card, CARD_CANVAS

pairs = _poster_candidate_pairs(trip_dir, limit=RANK_POOL_LIMIT)
naive_paths = [p for p, _ in pairs]          # A 组：原始顺序
ranked_paths = _rank_by_cover_score(pairs)   # B 组：cover_score_v2 排序

template = CARD_TEMPLATES["card-6-hero-tl-stack"]
png_bytes, _ = render_card(naive_paths[:6], template, canvas_wh=CARD_CANVAS)   # A
png_bytes, _ = render_card(ranked_paths[:6], template, canvas_wh=CARD_CANVAS)  # B
```
