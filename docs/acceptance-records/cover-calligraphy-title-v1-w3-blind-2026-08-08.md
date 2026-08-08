# PRD-COVER-CALLIGRAPHY-TITLE-V1 · W3 盲评进度（AC-CAL-BLIND）

| 属性 | 内容 |
|------|------|
| **文档** | [PRD-COVER-CALLIGRAPHY-TITLE-V1.md](../PRD-COVER-CALLIGRAPHY-TITLE-V1.md) §11 W3 · §12.3 AC-CAL-BLIND · D-CAL-05 |
| **方案** | [W3 盲评方案](./cover-calligraphy-title-v1-w3-blind-plan-2026-08-08.md) |
| **状态** | **样本已备 · 待评委**（**不宣称通过**；`enabled` 默认仍 `false`） |
| **日期** | 2026-08-08 |
| **脚本** | [`scripts/title_art_w3_blind_shots.py`](../../scripts/title_art_w3_blind_shots.py) |

---

## 0. 一句话结论

路线 B 盲评样本池已按方案产出：**12 对**同构图 on/off 封面截图（4 款白名单风格各 ≥2），附打分空表与本地预览页。路线 C 本轮标「样本不足·延期」。**AC-CAL-BLIND 尚未凑齐 ≥5 名评委，不得改默认 `enabled=true`。**

### 0.1 产品初评（2026-08-08 · owner）

| 段 | 反馈 |
|----|------|
| **b01–b04（band-cut）** | 艺术字贴图有问题 → 初评记现网 CSS 胜 |
| **后面约 6 对** | 艺术字胜出（记入 `scores.csv` 的 b05–b10；b11/b12 待确认） |

**band-cut 根因（已修，样本已重出）：**

1. D-CAL-23 把米白纸签烧进 PNG 后，配色仍按照片 ROI 采样 → 深色区误选**浅墨**，浅墨压浅纸几乎不可读  
2. `titleArt=on` 时原生 `.cover-opening__panel` 纸签底仍在 → **双层纸签叠影**

### 0.2 产品三点优化（2026-08-08）

| 点 | 落地 |
|----|------|
| **去印章** | 默认 `TEMPLATE_PLAIN`，不再画红圈「旅」 |
| **颜色/大小** | 各风格 `native_ink` 对齐原生标题色；字号与 CSS `max-*` 按风格收紧 |
| **位置** | `anchor=left` + CSS `translate(0,-50%)`；`veil-footer` 改回下半原生标题区 |

样本已 `--force` 重出；请刷新 `review.html` 复看。

---

## 1. 样本池

| 项 | 内容 |
|----|------|
| 目录 | [`attachments/cover-calligraphy-title-v1-w3-blind-2026-08-08/`](./attachments/cover-calligraphy-title-v1-w3-blind-2026-08-08/) |
| 成对文件 | `b01`…`b12` 的 `*-art.png` / `*-css.png`（共 24 张） |
| 清单 | `manifest.json` / `manifest.csv` |
| 打分表 | `scores.csv`（`choice` = `left` \| `right` \| `tie`） |
| 答案钥 | `answer-key.csv`（**评委不可见**） |
| 预览 | 打开同目录 `review.html` |

风格覆盖（脚本 `SAMPLE_PLAN`）：`band-cut`×4 · `veil-footer`×4 · `contact-stamp`×2 · `folio-overlap`×2。

出图注意：直出 `trips/*/index.html` 时没有 Studio `shell.css`，需在截图前隐藏 `.screenplay-toolbar` 与 `.folio-plate-meta`，并去掉 `data-debug`，避免评委看到草稿栏 / Plate 角标。

---

## 2. 评委操作（待办）

1. 打开 `review.html`，按题干独立选「左 / 右 / 难分」。
2. 把选择写入 `scores.csv`（每人一行或按 `raterId` 分行；禁止看 `answer-key.csv`）。
3. ≥5 人完成后，用答案钥折算艺术字侧胜场占比：（艺术字胜 + 0.5×难分）/ 总有效对。
4. 路线 B ≥55% 才可讨论默认 `enabled=true`；未达标则保持关并记录失败维度。

---

## 3. 非结论

- **未**改 `travelogue/config/studio.py` / 默认 `titleArt.enabled`
- **未**宣称 AC-CAL-BLIND 通过
- 路线 C 盲评本轮不做（OCR / OQ-CAL-06）

---

## 4. 复现

```text
python scripts/title_art_w3_blind_shots.py
python scripts/title_art_w3_blind_shots.py --limit 1   # 冒烟
```
