# Travelogue · 验收标准（单轨入口）

| 属性 | 内容 |
|------|------|
| **文档版本** | v1.3 |
| **适用范围** | MVP 基线 + Phase 2–21 累计验收 · Phase 22 工程准备 |
| **当前发布闸门** | **[Phase 5](./ACCEPTANCE-PHASE5.md)** 基线 + **[Phase 6](./ACCEPTANCE-PHASE6.md)** 稳态 + **P21 回归**（见 §2） |
| **工程 Sprint** | [integration-sprint-checklist-2026-06-13.md](./reports/integration-sprint-checklist-2026-06-13.md) |
| **关联** | [IMPLEMENTATION-PHASE5.md](./IMPLEMENTATION-PHASE5.md) · [PRD-PHASE5.md](./PRD-PHASE5.md) · [IMPLEMENTATION-PHASE6.md](./IMPLEMENTATION-PHASE6.md) · [PRD-PHASE6.md](./PRD-PHASE6.md) · [IMPLEMENTATION-PHASE21.md](./IMPLEMENTATION-PHASE21.md) |
| **更新日期** | 2026-06-13 |

> **P5-12.2 单轨合并**：本文档为验收入口；各 Phase 细则仍保留在分册中，**不再**以 MVP v0.1 清单单独作为发布闸门。

---

## 1. 阅读顺序

1. **发布前必查** → [§2 当前发布闸门](#2-当前发布闸门phase-5)  
2. **按 Phase 深入** → [§3 分 Phase 验收文档](#3-分-phase-验收文档)  
3. **MVP 对照** → [§4 MVP → Phase 对照](#4-mvp--phase-对照)  
4. **计时 / 盲评数据** → [acceptance-records/](./acceptance-records/README.md)  
5. **历史 MVP 细项** → [附录 A](#附录-a--mvp-基线详情-v01)

---

## 2. 当前发布闸门（P5 基线 + P6 稳态 + P21 回归）

**产品体验权威**：[ACCEPTANCE-PHASE5.md](./ACCEPTANCE-PHASE5.md) · **稳态与治理**：[ACCEPTANCE-PHASE6.md](./ACCEPTANCE-PHASE6.md)

> **2026-06-13 对齐**：工程已合入 Phase 21（拼图密度预算）；发布闸门仍为 P5 用户路径，叠加 P6 质量闭环与 P21 layout 回归。真实分享验收（AC-07）与盲评基线见 [Integration Sprint](./reports/integration-sprint-checklist-2026-06-13.md) W1。

### 2.1 产品路径（继承 Phase 5）

| 类别 | 必达 | 记录 |
|------|------|------|
| **路径 A · 零编辑** | UX-P5-80-01 · AC-P5-A-01～03 · AC-P2-02 微信可读 | [phase5-zero-edit.json](./acceptance-records/phase5-zero-edit.json) |
| **路径 B · 卷轴** | AC-P5-B-01/02 · UX-P5-SCROLL-01 | [phase5-scroll-qualitative.json](./acceptance-records/phase5-scroll-qualitative.json) |
| **排版地基** | AC-P5-C-01 · AC-P5-C-02（QS-01 ≥8/10） | [phase5-layout-sprint.json](./acceptance-records/phase5-layout-sprint.json) |
| **Studio 体验** | AC-P4-HP-01～06 · AC-P4-A11Y-03 | [ACCEPTANCE-PHASE4.md](./ACCEPTANCE-PHASE4.md) §4 |
| **真实分享（人工闸）** | AC-07 长图发群 · AC-03 愿分享 | [acceptance-records/linzhi.md](./acceptance-records/linzhi.md) |
| **不阻塞发布** | AC-P5-B-03～05 · P-EVAL · beam 实验 | [phase5-peval.json](./acceptance-records/phase5-peval.json) |

### 2.2 工程稳态（Phase 6 + P21）

| 类别 | 必达 | 记录 / 命令 |
|------|------|-------------|
| **质量闭环** | AC-P6-01～08 · BR-P6 回滚演练 | [ACCEPTANCE-PHASE6.md](./ACCEPTANCE-PHASE6.md) |
| **P21 回归** | mosaic density budget · rhythm 规则不破坏 golden | `python scripts/quality_gate.py` · curate baseline OK |
| **自动化 smoke** | P5-10.4 e2e · CLI-SPEC 同步 | `scripts/e2e_studio_smoke.ps1` |
| **canonical trips** | maomi validate + longshot-smoke | [acceptance-records/maomi.md](./acceptance-records/maomi.md) |
| **已知债务** | linzhi `pipeline.runs[]` schema 漂移 | Phase 22 schema 迁移 · 见 [PRD-PHASE22](./PRD-PHASE22-storage-platform.md) |

### 自动化（发布前建议）

```powershell
python scripts/quality_gate.py
python -m pytest tests/test_studio_a11y_p4.py tests/test_studio_entry.py tests/test_reading_p5.py tests/test_reading_auto_breath.py -q
python scripts/e2e_studio_smoke.ps1
python -m travelogue validate trips/maomi/trip.json
python -m travelogue longshot-smoke trips/maomi
```

---

## 3. 分 Phase 验收文档

| Phase | 文档 | 实施清单 | 状态 | 关键 KPI |
|-------|------|----------|------|----------|
| **MVP** | 附录 A（本文） | [PRD-MVP.md](./PRD-MVP.md) | 已冻结 · 基线 | AC-01～07 |
| **2 · Studio** | [ACCEPTANCE-PHASE2.md](./ACCEPTANCE-PHASE2.md) | [IMPLEMENTATION-PHASE2.md](./IMPLEMENTATION-PHASE2.md) | 已并入 P5 | AC-P2-02 长图微信可读 |
| **3 · 聚类** | [ACCEPTANCE-PHASE3.md](./ACCEPTANCE-PHASE3.md) | [IMPLEMENTATION-PHASE3.md](./IMPLEMENTATION-PHASE3.md) | 已并入 P5 | I-G2 · cache |
| **4 · 意图** | [ACCEPTANCE-PHASE4.md](./ACCEPTANCE-PHASE4.md) | [IMPLEMENTATION-PHASE4.md](./IMPLEMENTATION-PHASE4.md) | 代码 ☑ · 手测并行 | P-EVAL · HP/A11Y |
| **5 · Polish** | **[ACCEPTANCE-PHASE5.md](./ACCEPTANCE-PHASE5.md)** | [IMPLEMENTATION-PHASE5.md](./IMPLEMENTATION-PHASE5.md) | **产品路径闸门** | UX-P5-80-01 · SCROLL-01 |
| **6 · Stability** | [ACCEPTANCE-PHASE6.md](./ACCEPTANCE-PHASE6.md) | [IMPLEMENTATION-PHASE6.md](./IMPLEMENTATION-PHASE6.md) | **工程稳态闸门** | AC-P6-01~08 · BR-P6 |
| **21 · Mosaic 密度** | — | [IMPLEMENTATION-PHASE21.md](./IMPLEMENTATION-PHASE21.md) | ☑ 已合入 master | density budget · max_mosaic_slots |
| **22 · 存储纪律** | [ACCEPTANCE-PHASE22.md](./ACCEPTANCE-PHASE22.md) | [IMPLEMENTATION-PHASE22.md](./IMPLEMENTATION-PHASE22.md) | 待 Kickoff | G-P22-01～08 · ADR-008 |
| **9 · Quality Gate** | [ACCEPTANCE-PHASE9.md](./ACCEPTANCE-PHASE9.md) | [IMPLEMENTATION-PHASE9.md](./IMPLEMENTATION-PHASE9.md) | **W1 Done** | G-P9-W1 · NR-P9-04 |
| **12 · Silent Autonomy** | [ACCEPTANCE-PHASE9.md](./ACCEPTANCE-PHASE9.md) §5.1（P12 指标扩展） | [IMPLEMENTATION-PHASE12.md](./IMPLEMENTATION-PHASE12.md) | **In Progress** | L1/L2/L3 fallback · branch coverage · cpuMs |
| **13 · Template System** | [ACCEPTANCE-PHASE13.md](./ACCEPTANCE-PHASE13.md) | [IMPLEMENTATION-PHASE13.md](./IMPLEMENTATION-PHASE13.md) | **Gate Ready** | G1–G9 · event-recap 试点 |

---

## 4. MVP → Phase 对照

| MVP ID | 继承 / 等价 Phase AC | 说明 |
|--------|----------------------|------|
| **AC-01** | AC-P2-01a · AC-P5-A-02 | 真实相册 → 可预览 / 长图 |
| **AC-02** | AC-P2-01b → **UX-P5-80-01** | 20min → Phase 5 零编辑 **≤15min** |
| **AC-03** | UX-P5-SCROLL-01 · 定性 | 愿分享 → 卷轴「哇」反应 |
| **AC-04** | F-VID-* · AC-P5 回归 | 含视频 trip |
| **AC-05** | AC-P2-02 · AC-P5-A-03 | 微信可读（长图 PNG） |
| **AC-06** | F-EXP-05 · validate | 无精确 home GPS |
| **AC-07** | AC-P2-02 · P5-L1/L2 | 保存长图发群 |

功能矩阵 **F-TRIP / F-ING / F-CUR** 等仍见 [附录 A](#附录-a--mvp-基线详情-v01)；新功能以 Phase 2–5 AC 为准。

---

## 5. 验收记录目录

机器可读记录与 trip 手测笔记：[acceptance-records/README.md](./acceptance-records/README.md)

---

## 附录 A · MVP 基线详情 (v0.1)

> **历史基线** · 2026-05-19 起稿。发布闸门已上移至 [Phase 5](#2-当前发布闸门phase-5)；下列细项供回归与对照，**单独勾选不再阻断发布**。

### A.1 验收原则

1. **真实数据**：至少 3 次不同旅行素材，非虚构样张。  
2. **可复现**：记录 `tripId`、模板版本、`trip.json` version、日期。  
3. **可演示**：每条 AC 保留截图或 zip 路径（本地即可）。  
4. **人工闸口**：须走 G1（结构）与 G3（隐私）；G2 可合并到预览改字。

### A.2 发布闸门（MVP 原始 · 已由 Phase 5 取代）

| ID | 标准 | 验证方法 | 通过 |
|----|------|----------|------|
| **AC-01** | 用 **3 次真实旅行** 各生成 1 篇可导出游记 | 3 个 `trips/{id}/` 均有 `index.html` + zip | ☐ |
| **AC-02** | 平均从导入到「愿导出」**< 20 分钟** | 记录 3 次起止时间取平均 | ☐ |
| **AC-03** | 至少 **2 篇** 愿发给非开发者朋友 | 对方能打开且正向反馈 | ☐ |
| **AC-04** | 至少 **1 篇** 含短视频且循环/ poster 正常 | 含 `type:video` 的 trip | ☐ |
| **AC-05** | 导出 zip 在 **另一台手机微信** 内可读 | 传 zip → 解压或托管链接 → 滑动浏览 | ☐ |
| **AC-06** | 导出展示图 **无精确 home GPS** EXIF | 抽检导出 jpg/webp EXIF | ☐ |
| **AC-07** | 「保存长图」得到竖版 PNG，并 **发到微信群** 群友可读 | 保存 → 发群 → 他人反馈 | ☐ |

**AC-07 推荐路径（2026-05）**：`travelogue serve` → Studio 保存长图 → 发微信群。

### A.3 功能验收矩阵（按需求 ID）

#### Trip 与导入

| 需求 ID | 验收步骤 | 通过 |
|---------|----------|------|
| F-TRIP-01 | `trip new` 生成 `trips/{tripId}/` 与合法 `trip.json` | ☐ |
| F-TRIP-02 | `pipeline.status` 随流程变化且可 `status` 查看 | ☐ |
| F-TRIP-03 | 能列出并重新打开历史 trip | ☐ |
| F-ING-01 | jpg/png/heic/webp 可导入 | ☐ |
| F-ING-02 | 原图在 `source/`，不破坏相册原目录 | ☐ |
| F-ING-03 | 有/无 EXIF 均不崩溃 | ☐ |
| F-ING-04 | >250 张提示拒绝或分批 | ☐ |
| F-ING-05 | mp4/mov ≤15s 可导入 | ☐ |
| F-ING-06 | 生成 w800/w1600 WebP | ☐ |

#### 策展

| 需求 ID | 验收步骤 | 通过 |
|---------|----------|------|
| F-CUR-01 | 跨天自动分章候选 | ☐ |
| F-CUR-02 | 地点为城市级字符串 | ☐ |
| F-CUR-03 | 连拍去重后数量减少 | ☐ |
| F-CUR-05 | 3–5 章且 `patternId` 合法 | ☐ |
| F-CUR-06 | 提供 3 封面候选并可改 `coverAssetId` | ☐ |

#### 叙事

| 需求 ID | 验收步骤 | 通过 |
|---------|----------|------|
| F-NAR-01 | title/hook 符合 manifest 字数 | ☐ |
| F-NAR-03 | 切换 tone 可重生成 | ☐ |
| F-NAR-05 | 无禁用词表命中 | ☐ |
| F-NAR-06 | 不合规 JSON 被拒绝或自动修 | ☐ |

#### 视频

| 需求 ID | 验收步骤 | 通过 |
|---------|----------|------|
| F-VID-01 | 循环片段 3–8s 静音 | ☐ |
| F-VID-04 | trip 内 ≤3 视频 | ☐ |

#### 编辑与导出

| 需求 ID | 验收步骤 | 通过 |
|---------|----------|------|
| F-ED-03 | 改字后重渲染生效 | ☑ · `serve` 保存后 auto re-render |
| F-ED-04 | 浏览器可预览 | ☐ |
| F-EXP-01 | 相对路径、离线可开 | ☐ |
| F-EXP-02 | 无 JS 仍可阅读主内容 | ☐ |
| F-EXP-03 | `preview.jpg` 9:16 存在 | ☐ |
| F-EXP-04 | zip 解压即 `index.html` | ☐ |
| F-EXP-05 | 未 `privacy.confirmedAt` 不可 export | ☐ |
| F-EXP-07 | 保存长图 · screens trip 用 longshot | ☐ |
| F-EXP-07b | 默认 export zip 含 longshot bundle | ☐ |

### A.4 模板与渲染验收

| ID | 标准 | 通过 |
|----|------|------|
| T-01 | `templateId` 为 `visual-journal` | ☐ |
| T-08 | `layoutEngine=screens` 时章内为 `layout-screen--16x9` | ☑ |
| T-09 | 竖三列 `screen-portrait-3` 使用 **cover** | ☑ |
| T-10 | 单屏 ≤9 张，横/竖 4·9 宫格可触发 | ☑ |
| T-11 | `layout` 闸口展示屏级摘要 | ☑ |
| T-12 | legacy 与 screens 双引擎 CI 回归 | ☑ |

对照金样例：`templates/visual-journal/golden.html`、`golden-web-screens.html`。

### A.5 Agent 流水线 · 非功能 · 记录表

见 Phase 3–5 自动化测试与 [acceptance-records/](./acceptance-records/README.md)。

**Trip 手测**： [linzhi.md](./acceptance-records/linzhi.md) · [mao.md](./acceptance-records/mao.md)

### A.6 缺陷分级

| 级别 | 定义 | 是否阻断 |
|------|------|----------|
| P0 | 无法完成导入/渲染/导出；隐私泄漏 | 是 |
| P1 | 版式严重错乱、文案幻觉地点 | 是 |
| P2 | 样式细节、单张图失败 | backlog |
| P3 | 文案润色、动效 | backlog |

---

## 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.2 | 2026-06-03 | 新增 Phase 12 指标验收入口（引用 ACCEPTANCE-PHASE9 §5.1） |
| v1.1 | 2026-05-30 | 补充 Phase 6 验收入口与开发准备链接 |
| v1.0 | 2026-05-30 | **P5-12.2 单轨合并** · Phase 5 发布闸门 · MVP 降为附录 A |
| v0.1 | 2026-05-19 | P0 验收清单，对齐 visual-journal v0.2 |
