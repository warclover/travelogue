# PRD-COVER-CALLIGRAPHY-TITLE-V1 · W3 盲评方案（AC-CAL-BLIND）

| 属性 | 内容 |
|------|------|
| **文档** | [PRD-COVER-CALLIGRAPHY-TITLE-V1.md](../PRD-COVER-CALLIGRAPHY-TITLE-V1.md) §11 W3 · §12.3 AC-CAL-BLIND · D-CAL-05 |
| **状态** | **样本已备 · 待评委**（进度见 [W3 盲评进度](./cover-calligraphy-title-v1-w3-blind-2026-08-08.md)；**不宣称 AC-CAL-BLIND 通过**） |
| **日期** | 2026-08-08 |
| **门禁** | 偏好 ≥55% 才可默认 `meta.titleArt.enabled=true`（路线 B/C **分别计**） |

---

## 0. 目的

W2 已让路线 B 在 4 款白名单风格上可用，但 **D-CAL-05** 要求默认关闭，直到盲评证明艺术字贴纸不劣于现网 CSS Opening 标题。本方案把 AC-CAL-BLIND 操作化，避免「拍脑袋默认开」。

---

## 1. 对比基线（钉死）

| 侧 | 内容 |
|----|------|
| **A · 现网** | `titleArt` 关闭（或 `enabled=false`）时的 Opening HTML/CSS 标题 |
| **B · 路线 B** | `engine=clean-pipeline-v1` 贴纸叠加（含 D-CAL-23 衬底） |
| **C · 路线 C** | `engine=diffusion-fixed-prompt-v1` 贴纸（仅 OCR 通过样本入池；未通过不得进盲评） |

基线是 **现网 CSS 标题**，不是 CAD Mode A（七席已强调）。

---

## 2. 样本池

| 维度 | 要求 |
|------|------|
| 数量 | 路线 B：**≥12** 对；路线 C：**≥8** 对（若可用样本不足则本轮只评 B，C 标「样本不足·延期」） |
| Trip | 真实 trip（非 fixture）；覆盖 4 款白名单风格各 ≥2 |
| 标题长度 | 2～8 字；含地名/人名常见字 |
| 排除 | 路线 C OCR 未过、focal 冲突 fail-open、非白名单风格 |

每对产出两张封面截图（同构图、同浏览器视口），仅标题呈现不同。

---

## 3. 盲评流程

1. **成对展示**：左右随机打乱 A/B（或 A/C），不标注「艺术字/现网」。
2. **题干**：「哪一张封面标题你更愿意直接分享？」单选左 / 右 / 难分（难分计 0.5）。
3. **评委**：≥5 人（产品 + 设计 + 至少 1 名非项目成员）；每人独立，禁止讨论。
4. **计分**：艺术字侧胜场占比 =（艺术字胜 + 0.5×难分）/ 总有效对。
5. **通过线**：路线 B ≥55%；路线 C 单独计，≥55% 才允许把路线 C 升为「可默认尝试」——**即使 C 达标，仍受 OQ-CAL-06 约束**（长期定位高级项，不自动改 `route_c_enabled` 默认值；本门禁只管 `titleArt.enabled` 默认开对路线 B）。

---

## 4. 交付物

| 产物 | 路径建议 |
|------|----------|
| 样本清单 + 截图 | `docs/acceptance-records/attachments/cover-calligraphy-title-v1-w3-blind-YYYY-MM-DD/` |
| 打分表 | 同目录 `scores.csv`（评委匿名化） |
| 结论记录 | `docs/acceptance-records/cover-calligraphy-title-v1-w3-blind-YYYY-MM-DD.md` |

若通过：改配置/文档允许默认 `enabled=true`（仍保留 fail-open）；更新 D-CAL-05 状态。  
若不通过：保持默认关，记录失败维度（风格/标题长度/对比度）供下一轮迭代。

---

## 5. 非目标（本轮不做）

- 不把路线 C 升为默认主路径（OQ-CAL-06 已钉死）
- 不开放 `scroll-head`
- 不替代 AC-CAL-01～13 的工程验收

---

## 6. 执行排期

1. ✅ 从现有 demo trip 挑 12 对路线 B 封面，脚本化开关 `titleArt.enabled` 出图（[`title_art_w3_blind_shots.py`](../../scripts/title_art_w3_blind_shots.py) → [附件目录](./attachments/cover-calligraphy-title-v1-w3-blind-2026-08-08/)）  
2. ⏳ 约 5 名评委各 15～20 分钟盲评（打开 `review.html`，填 `scores.csv`；勿看 `answer-key.csv`）  
3. ⏳ 写结论记录 → 决定是否改默认开启  

**样本已备不等于盲评通过。本文件不宣称 AC-CAL-BLIND 已通过。**
