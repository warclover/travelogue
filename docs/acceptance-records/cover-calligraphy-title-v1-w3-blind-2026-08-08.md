# PRD-COVER-CALLIGRAPHY-TITLE-V1 · W3 盲评进度（AC-CAL-BLIND）

| 属性 | 内容 |
|------|------|
| **文档** | [PRD-COVER-CALLIGRAPHY-TITLE-V1.md](../PRD-COVER-CALLIGRAPHY-TITLE-V1.md) §11 W3 · §12.3 AC-CAL-BLIND · D-CAL-05 |
| **方案** | [W3 盲评方案](./cover-calligraphy-title-v1-w3-blind-plan-2026-08-08.md) |
| **状态** | **✅ AC-CAL-BLIND 已通过（单一代表性评委协议，2026-08-09）**；`enabled` 默认仍 `false`（是否改默认另行决定，见 §5） |
| **日期** | 2026-08-08（样本）· 2026-08-09（评分与结论） |
| **脚本** | [`scripts/title_art_w3_blind_shots.py`](../../scripts/title_art_w3_blind_shots.py) |

---

## 0. 一句话结论

路线 B 盲评样本池已按方案产出：**12 对**同构图 on/off 封面截图（4 款白名单风格各 ≥2），附打分空表与本地预览页。路线 C 本轮标「样本不足·延期」。**2026-08-09：产品负责人显式决定放宽评委人数门槛（原方案要求 ≥5 人），改为「单一代表性评委（产品负责人本人）即可，因样本标题本身就来自真实用户产出、具有代表性」——本人独立完成全部 12 对盲评打分，折算艺术字侧胜率 91.7%（11/12），远超 ≥55% 门槛，AC-CAL-BLIND 判定通过。详见 §5 结论。**

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

---

## 5. 结论（单一评委协议 · 2026-08-09）

### 5.1 协议变更（明确记录，不含糊）

原 [W3 盲评方案](./cover-calligraphy-title-v1-w3-blind-plan-2026-08-08.md) §3 第 3 条要求「评委 ≥5 人（产品 + 设计 + 至少 1 名非项目成员）」。**2026-08-09，产品负责人显式指示放宽该门槛**：由产品负责人一人独立完成全部 12 对盲评打分即可，理由是样本标题本身来自真实用户产出的真实 trip（非人工编造/挑选的极端案例），本身具有代表性，产品负责人的判断可视为对目标用户群体审美倾向的合理代理。**如实记录局限**：这是 n=1、且评委即产品负责人本人（非独立第三方）的协议，跟原方案「≥5 人 + 至少 1 名非项目成员」的严谨度不在同一量级，属于产品负责人主动承担的方法论简化，不是「凑不到 5 人所以降低标准」的被动妥协——留痕供后续追溯。

### 5.2 打分方式

产品负责人在不知晓 `answer-key.csv`（艺术字/现网哪边在左/右已随机打乱）的情况下，对全部 12 对样本逐一选择「左 / 右 / 难分」，随后用 `answer-key.csv` 折算。原始打分记入 [`scores.csv`](./attachments/cover-calligraphy-title-v1-w3-blind-2026-08-08/scores.csv)（`raterId=owner`）。

### 5.3 结果

| pairId | 风格 | 标题 | 结果 |
|---|---|---|---|
| b01 | band-cut | 初中毕业照 | 艺术字胜 |
| b02 | band-cut | 2019相册精选 | 艺术字胜 |
| b03 | band-cut | 斯里兰卡人文精选 | 艺术字胜 |
| b04 | band-cut | 华农油菜花 | 艺术字胜 |
| b05 | veil-footer | 夏睿彤贵州暑假游 | 艺术字胜 |
| b06 | veil-footer | 夏睿彤年度精选 | **现网 CSS 胜** |
| b07 | veil-footer | 武大 米娜 | 艺术字胜 |
| b08 | veil-footer | 初中毕业照 | 艺术字胜 |
| b09 | contact-stamp | 斯里兰卡见闻录 | 艺术字胜 |
| b10 | contact-stamp | 斯里兰卡风光精选 | 艺术字胜 |
| b11 | folio-overlap | 王丹昙华林半日游 | 艺术字胜 |
| b12 | folio-overlap | 我家云南自驾精选 | 艺术字胜 |

分风格胜率：`band-cut` 4/4（100%）· `veil-footer` 3/4（75%）· `contact-stamp` 2/2（100%）· `folio-overlap` 2/2（100%）。

**总体：艺术字侧胜率 = 11/12 = 91.7%**（(艺术字胜 + 0.5×难分) / 总有效对，本轮 0 例难分）——远超方案定的 ≥55% 门槛。

唯一一例现网 CSS 胜出的 `b06`（veil-footer·夏睿彤年度精选），主观印象是该标题较长（6 字）且贴纸字号在这张构图下偏小，视觉冲击力不如现网大字 CSS 标题；不影响整体结论，留痕供后续 `veil-footer` 长标题字号调优参考，不单独建 OQ（样本量 n=1 不足以定性为系统性问题）。

### 5.4 结论

**AC-CAL-BLIND：判定通过**（91.7% ≥ 55%，四款白名单风格无一低于 55%）。**本结论基于 §5.1 声明的简化协议（单一评委=产品负责人），不是原方案要求的 ≥5 人独立评审**——如果后续需要更高强度的证据（例如对外宣传"经用户测试验证"），建议补一轮真正的多人独立评审；作为内部产品决策依据，本结论已被产品负责人接受为充分。

**本记录本身不改变 `titleArt.enabled` 的默认值**——AC-CAL-BLIND 通过只是解除了 D-CAL-05「盲评未过不得默认开」这个阻塞条件，是否要现在就把默认值从 `false` 改成 `true` 是另一个需要单独拍板的产品决策（涉及全量用户的默认体验变化，比这次评审本身影响更大），留给下一步单独确认。
