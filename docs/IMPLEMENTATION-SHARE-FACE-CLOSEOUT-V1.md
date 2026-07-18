# IMPLEMENTATION · 敢发收口优化 V1

| 属性 | 内容 |
|------|------|
| **对应 PRD** | [PRD-SHARE-FACE-CLOSEOUT-V1.md](./PRD-SHARE-FACE-CLOSEOUT-V1.md) **v1.0.1** |
| **评审** | [跨职能](./acceptance-records/share-face-closeout-v1-review-2026-07-18.md) · Conditional Go · BLK-01～08 |
| **验收** | [ACCEPTANCE-SHARE-FACE-CLOSEOUT-V1.md](./ACCEPTANCE-SHARE-FACE-CLOSEOUT-V1.md) |
| **手测狗粮** | [share-face-closeout-v1-dogfood-CHECKLIST.md](./acceptance-records/share-face-closeout-v1-dogfood-CHECKLIST.md) |
| **线框** | [wireframes/share-face-closeout-v1-wireframe.html](./wireframes/share-face-closeout-v1-wireframe.html) · F1–F5 |
| **试用底稿** | [persona-ux-trial-2026-07-18.md](./acceptance-records/persona-ux-trial-2026-07-18.md) |
| **更新日期** | 2026-07-18 |
| **状态** | **W0+W1+W2 工程合入** · 分支 `feat/share-face-closeout-v1-w0` · 狗粮待签 |
| **估时** | W0 ≈ **2.5–4 人日** · W1 ≈ **1.5–2.5 人日** · W2 ≈ **0.3–0.5 人日** |

---

## 0. 波次摘要

| 波次 | 目标 | Go |
|------|------|-----|
| **Doc/Design** | PRD · 线框 · AC · IMPL · README 索引 | ✅ 2026-07-18 |
| **评审** | 跨职能 Conditional Go；OQ-01～04 关闭；相邻脚注 | ✅ 2026-07-18 |
| **W0** | 假句空槽 · 体面名 · vision_warmup 主句 | ✅ 工程 |
| **W1** | stale「分享图需更新」· Sparse 跳过 G1 · 禁「续」· 无 Key 预期 | ✅ 工程 |
| **W2** | 「媒资」→「照片类型」 | ✅ 工程 |
| **完成宣布** | 真人 N≥5 | ⏳ AC-SFC-15 |

**所有权**

| 能力 | 所有者 |
|------|--------|
| stub 禁词实例 + 空槽硬化 + alt 复读禁 | **本主题**（硬化 FST D-FST-06） |
| displayTitle / `--` / 尾数字回退 fixture | **本主题**（硬化 FST D-FST-09） |
| `vision_warmup` 阶段与降级 | **本主题**（FST 进度诚实增量） |
| stale 唯一主词一字面 | **本主题**（supersede QH R-QH-05） |
| Sparse 默认跳过 G1 | **本主题**（修订 Refine D-REF-09/18） |
| 「媒资」人话 | **本主题** |
| 意图卡 / `kept_n` / Recipe CTA | Share-Ready（本主题只回归） |
| 章名算法全案 | Chapter Naming；本主题挡「续」 |
| 真 LLM 气质 | Copy / WEA |

---

## 1. Doc 波次

| ID | 任务 | 锚点 | 状态 |
|----|------|------|------|
| **DOC-SFC-01** | PRD v1.0.0 | `PRD-SHARE-FACE-CLOSEOUT-V1.md` | ✅ |
| **DOC-SFC-02** | ACCEPTANCE + fixture 表 | `ACCEPTANCE-SHARE-FACE-CLOSEOUT-V1.md` | ✅ |
| **DOC-SFC-03** | IMPLEMENTATION 本文件 | `IMPLEMENTATION-SHARE-FACE-CLOSEOUT-V1.md` | ✅ |
| **DOC-SFC-04** | 线框 F1–F5 | `wireframes/share-face-closeout-v1-wireframe.html` | ✅ |
| **DOC-SFC-05** | 狗粮清单 | `acceptance-records/share-face-closeout-v1-dogfood-CHECKLIST.md` | ✅ |
| **DOC-SFC-06** | README / wireframes 索引 | `docs/README.md` · `wireframes/README.md` | ✅ |
| **DOC-SFC-07** | 相邻脚注：QH R-QH-05 · Refine G1 · FST §4.5 禁词增量 | 相邻 PRD | ✅ |
| **DOC-SFC-08** | 跨职能评审纪要 | `share-face-closeout-v1-review-2026-07-18.md` | ✅ |

---

## 2. W0 任务卡（P0）

### 2.1 后端

| ID | 任务 | 建议锚点 | 估时 | AC | 状态 |
|----|------|----------|------|-----|------|
| **BE-SFC-01** | stub/L0：禁词空槽；弱枚举过滤；禁止标题复读填 caption | `share_face_copy` · narrate / caption / alt | 0.6d | 01·02 | ✅ |
| **BE-SFC-02** | `title_humanize`：连续分隔符折叠；`2025东澳岛9` / `--` fixture；与 FE 同测 | `travelogue/domain/title_humanize.py` | 0.5d | 03 | ✅ |
| **BE-SFC-03** | job status：running 必填 stage/stageHint；进入模型准备 → `vision_warmup` | `studio_pipeline` · clustering | 0.6d | 04·05 | ✅ |
| **BE-SFC-04** | vision 失败降级继续主链 + 人话说明字段 | `_vision_downgrade_notice` → `clusterNotice` toast | 0.3d | 05 | ✅ |

### 2.2 前端

| ID | 任务 | 建议锚点 | 估时 | AC | 状态 |
|----|------|----------|------|-----|------|
| **FE-SFC-01** | Importing 壳映射 `vision_warmup` 主句；双空兜底「正在处理…」 | `import-run-logic.js` · constants | 0.4d | 04 | ✅ |
| **FE-SFC-02** | 封面 / 书架 / FirstSuccess 读 `displayTitle`；humanize 对齐 BE | `title-humanize.js` | 0.4d | 03 | ✅ |

### 2.3 测试 / 数据

| ID | 任务 | 估时 | AC | 状态 |
|----|------|------|-----|------|
| **QA-SFC-01** | 单测：FX-SFC-01～05（禁词 / 脏名）；章名「续」→ W1 | 0.4d | 01～03 | ✅ |
| **QA-SFC-02** | **可测锁（BLK-06）**：`TRAVELOGUE_SFC_VISION_WARMUP_DELAY_MS` + 降级 notice 单测 | 0.5d | 04·05 | ✅ |
| **DATA-SFC-01** | demo-album 假句清洗（竖幅/抬头看见；章名「续」→「（2）」） | 0.3d | 01·02 | ✅ |

### 2.4 W0 完成定义

- [x] 线框 F1–F3 对照合入（工程对齐）  
- [x] AC-SFC-01～05 工程列绿  
- [x] demo/示例分享面抽检无竖幅/抬头看见/弱枚举  
- [x] **不**宣称主题完成（W1/W2 / 狗粮仍开）  

---

## 3. W1 任务卡（P1）

| ID | 任务 | 建议锚点 | 估时 | AC | 状态 |
|----|------|----------|------|-----|------|
| **FE-SFC-03** | stale 主词全链路 →「分享图需更新」；Help 深链同步 | `bento.js` · `shelf.js` · task-dock · `help-onboarding.js` | 0.5d | 06 | ✅ |
| **BE-SFC-05** | Sparse 快速分享默认跳过 G1；实验选项可开 | `sparse_g1.py` · `studio_pipeline` | 0.4d | 08·09 | ✅ |
| **BE-SFC-06** | 章名禁「续」（生成器已禁；契约锁） | `chapter_titles` · `test_sfc_w1_contracts` | 0.3d | 07 | ✅ |
| **FE-SFC-04** | FirstSuccess 无 Key 预期文案（禁杂志文案已完成） | `HELP_COPY.firstSuccessNext` | 0.2d | 11 | ✅ |
| **QA-SFC-03** | 单测：Sparse 门控 · stale 词扫描 · FirstSuccess 禁词 | 0.4d | 06·08·09·11 | ✅ |

### 3.1 W1 完成定义

- [x] 线框 F4–F5 对照（工程对齐）  
- [x] AC-SFC-06～09 · 11 工程列绿  
- [x] 用户面无「长图可更新」主词  

---

## 4. W2 任务卡（P2）

| ID | 任务 | 建议锚点 | 估时 | AC | 状态 |
|----|------|----------|------|-----|------|
| **FE-SFC-05** | 「媒资」→「照片类型」 | `preview-toolbar/features.js` | 0.2d | 10 | ✅ |
| **QA-SFC-04** | DOM 禁词扫描含精修态 | `test_sfc_w1_contracts` | 0.1d | 10 | ✅ |
| **DOC-SFC-07** | 相邻 PRD 脚注回写（若评审要求） | QH / Refine / FST | 0.2d | — | ✅ W0 |

---

## 5. 埋点（PRD §7）

| 事件 | 接入点 | 状态 |
|------|--------|------|
| `sfc_vision_warmup_shown` | import-run stage 切换 | ✅ FE+BE 白名单 |
| `sfc_stub_blanked` | narrate/render 空槽 | ⏳ 白名单已预留（未发射） |
| `sfc_title_fallback` | import success `titleNoiseFallback` | ✅ FE+BE |
| `sfc_g1_suppressed_sparse` | FirstSuccess（sparse 跳过） | ✅ FE+BE |
| `sfc_stale_label_impression` | 书架/Dock 角标 | ⏳ 白名单已预留（未发射） |

---

## 6. 建议编码顺序

1. **BE-SFC-03 / FE-SFC-01**（进度空=像坏了，优先）  
2. **BE-SFC-01 + DATA-SFC-01**（分享面假句）  
3. **BE-SFC-02 / FE-SFC-02**（体面名）  
4. **FE-SFC-03**（stale 人话）  
5. **BE-SFC-05**（Sparse G1）  
6. **FE-SFC-05**（词表）  

---

## 7. 风险与依赖

| 项 | 说明 |
|----|------|
| FST 已合入底线 | 本主题补 fixture 与未兑现路径，避免重复造轮子 |
| OpenCLIP/HF | `vision_warmup` 文案不得出现 HF/权重文件名 |
| QH 结案词 | 改名需全文扫描，防 Help 死链 |
| 评审 OQ | OQ-SFC-01～03 未关前，东澳岛回退与 stale 一字面以 PRD 默认为准 |

---

## 8. Kickoff 检查单

- [x] 跨职能 Conditional Go（2026-07-18）  
- [x] OQ-SFC-01～04 关闭  
- [x] 相邻 PRD 脚注（QH / Refine / FST）  
- [x] 分支：`feat/share-face-closeout-v1-w0`  
- [x] W0 任务卡认领并完成工程  
- [ ] 狗粮场次预约（AC-SFC-15）  
- [x] W1/W2 工程合入  
