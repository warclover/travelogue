# Travelogue · Phase 5 实施清单

| 属性 | 内容 |
|------|------|
| **关联 PRD** | [PRD-PHASE5.md](./PRD-PHASE5.md) v0.5.4 |
| **代号** | P5-Polish · 双路径交付 |
| **更新日期** | 2026-05-30 |

> **状态图例**：☑ 已落地 · ◑ 部分 · ☐ 未开始  
> **Tier 权威排序**：见 PRD §3.3（Tier 0 > Tier 1 > Tier 2）

---

## 里程碑总览

| 里程碑 | 主题 | 波次 | 完成标志 | 状态 |
|--------|------|------|----------|------|
| **M20** | Week 1–2 · 地基（Tier 0） | 波次 1 | UX-P5-80-01 可测 · P5-S6 可组织 | ◑ |
| **M21** | Week 3–4 · 差异化（Tier 1） | 波次 2 | QS-01 8/10 · 卷轴仪式 S2–S4 | ◑ |
| **M22** | 排版实验 + 专业模式（Tier 2） | 波次 3 | C1/R1 · P-EVAL 并行 | ☑ |
| **M23** | 工程债 + Tier 4 预埋 | 波次 3 | MP-1/2 · 文档单轨 | ◑ |

---

## M20-A · 路径 A · 成功页与长图（P5-2.x · P5-L*）

| 任务 ID | PRD | 任务 | 文件/模块 | 状态 |
|---------|-----|------|-----------|------|
| M20-A-01 | P5-2.5 | 成功页 **主 CTA = 生成长图** · 取消 5s auto-open | `studio.html` · `studio.js` | ☑ |
| M20-A-02 | P5-2.7 | 次 CTA「打开卷轴预览」+ 路径提示文案 | 同上 | ☑ |
| M20-A-03 | P5-2.6 | 长图完成 reveal + 微信指引 | `studio.js` · reveal API | ☑ |
| M20-A-04 | P5-L1 | 默认宽度弃 390 → 428/430 · scale=2 | `longshot.py` · `longshot.js` · `longshot.css` | ☑ |
| M20-A-05 | P5-L2 | ≤20MB · 超限分段 + 人话 | `longshot.py` · Studio 结果 `userHint` | ☑ |
| M20-A-06 | P5-L3 | longshot Job stageHint UI | `studio_routes.py` · `studio.js` · `preview-toolbar.js` | ☑ |
| M20-A-07 | P5-L4 | Studio 启动 Playwright warm | `serve.py` · `longshot.py` | ☑ |
| M20-A-08 | P5-3.7 | preview toolbar 极简：返回 · 长图 · 文件夹 · ⋯更多编辑 | `preview-toolbar.js` · `.css` | ☑ |

---

## M20-B · 排版地基（P5-C* · P5-QS-01）

| 任务 ID | PRD | 任务 | 文件/模块 | 状态 |
|---------|-----|------|-----------|------|
| M20-B-01 | P5-C2 | 封面：人像降权 + 饱和度 + **三分法** | `curate_scoring.py` · `color_metrics.py` | ☑ |
| M20-B-02 | P5-C3 | 小相册 degradation · 少分章 | `curate.py` | ☑ |
| M20-B-03 | P5-QS-01 | 10 相册 A/B · 记录 `phase5-layout-sprint.json` | `scripts/phase5_layout_sprint.py` · acceptance-records | ◑ |
| M20-B-04 | P5-C1 | beam 权重全零回退 PHASE3B（D7） | `curate.py` · `layout_scoring.py` | ☑ |

---

## M20-C · 路径 B · 卷轴默认可用（P5-S1/S6/S7）

| 任务 ID | PRD | 任务 | 文件/模块 | 状态 |
|---------|-----|------|-----------|------|
| M20-C-01 | P5-S1 | 按照片数 auto breath：&lt;20 soft · 20–50 flow · &gt;50 cinematic | `render/reading_profile.py` | ☑ |
| M20-C-02 | P5-S7 | share 态：无 Studio toolbar · `?share=1` / `?mode=share` | `studio_chrome.py` · `preview-toolbar.js` · `studio_entry.py` | ☑ |
| M20-C-03 | P5-S6 | 组织 3–5 人定性 · 填 `phase5-scroll-qualitative.json` | 人工 | ☐ |
| M20-C-04 | — | 隐藏/移除用户可见 profile 选择 UI | `preview-toolbar.js` · config UI | ☑ |

---

## M20-D · Studio 丝滑与信任（P5-1.x · P5-I* · P5-10.x）

| 任务 ID | PRD | 任务 | 文件/模块 | 状态 |
|---------|-----|------|-----------|------|
| M20-D-01 | P5-1.1 | Loading 保留 masthead + 骨架 | `studio.html` · `studio.css` | ☑ |
| M20-D-02 | P5-I2 | 导入开始时时间预估 | `studio.js` · `studio_stages.yaml` | ☑ |
| M20-D-03 | P5-I1 | ingest 子进度 N/M | `studio_subprocess.py` · `studio.js` | ☑ |
| M20-D-04 | P5-10.1 | E_STUDIO_* 前端人话映射 | `studio.js` · `ERROR-CODES.md` | ☑ |
| M20-D-05 | P5-6.5 | CLIP 默认关 · geo 聚类默认 | `config.yaml.example` · Studio 高级选项 | ☑ |
| M20-D-06 | P5-10.4 | e2e 零编辑 smoke：import→longshot | `scripts/e2e_studio_smoke.ps1` | ☑ |

---

## M21 · Week 3–4 · 差异化（Tier 1）

| 任务 ID | PRD | 任务 | 文件/模块 | 状态 |
|---------|-----|------|-----------|------|
| M21-01 | P5-D1 | curate 一次 → longshot filter ≤10–15 屏（D20） | `longshot_filter.py` · `context.py` | ☑ |
| M21-02 | P5-S2 | 全出血章节分隔屏 | `chapter-separator.hbs` · `journal-screens.css` | ☑ |
| M21-03 | P5-S3 | cover-hero 激进 breath 进场 | `breath.js` · `breath.css` · `breath-gsap.js` | ☑ |
| M21-04 | P5-S4 | epilogue 封底统计屏 | `context.py` · `epilogue-screen.hbs` | ☑ |
| M21-05 | P5-S5 | 卷轴 B 面呼吸屏 curate 插入 | `breath_pauses.py` · `curate.py` | ☑ |
| M21-06 | P5-T2 | 长图 A 面呼吸屏 | `breath_pauses.py` · `longshot.css` | ☑ |
| M21-07 | P5-L5 | 长图封面/封底边界 | `longshot-boundary-footer.hbs` · `longshot.css` | ☑ |
| M21-08 | P5-S8 | screenplay 保留 · Tier 1 不阻塞 | `screenplay.js` | ☑ |
| M21-09 | P5-S9 | cinematic 中端 Android FPS 手测 + 降级 | `breath-gsap.js` | ☑ |
| M21-10 | P5-H2 | 空态 demo 长图缩略 | `studio.html` · demo trips | ☑ |

---

## M22 · Tier 2 · 实验与专业模式

| 任务 ID | PRD | 任务 | 状态 |
|---------|-----|------|------|
| M22-01 | P5-R1 | 节奏感 scoring 维度 | `layout_scoring.py` | ☑ |
| M22-02 | P5-7.4 | Studio 智能排版实验开关 | `studio.html` · `studio.js` · `config.py` | ☑ |
| M22-03 | P5-7.5 | 结构 drawer explain | `chapter_explain.py` · `preview-toolbar.js` | ☑ |
| M22-04 | P5-8.1 | P-EVAL 盲评（不阻塞 Tier 0 发布） | `phase5_blind_review.py` · `peval.py` | ☑ |
| M22-05 | P5-3.3–3.6 | G1/锚点/drawer 专业模式内 | `preview-toolbar.js` · `.css` | ☑ |

---

## M23 · Tier 3/4 · 工程与小程序预埋

| 任务 ID | PRD | 任务 | 状态 |
|---------|-----|------|------|
| M23-01 | P5-12.2 | 验收文档单轨合并 | `ACCEPTANCE.md` · `acceptance-records/README.md` | ☑ |
| M23-02 | P5-12.3 | CLI-SPEC 与 studio/longshot 同步 | `CLI-SPEC.md` | ☑ |
| M23-03 | P5-MP-1 | API-MINIAPP 字段对齐审查 | `API-MINIAPP.md` v0.2 · `test_api_miniapp_sync.py` | ☑ |
| M23-04 | P5-MP-2 | 本地 serve + web-view 手测清单 | `API-MINIAPP.md` §11 · `phase5-webview-manual.json` | ☑ |
| M23-05 | P5-I4 | ingest 断点续传 | `ingest_checkpoint.py` · `ingest.py` | ☑ |
| M23-06 | P5-A1 | studio.js 拆 chunk | ☐ |

---

## 建议执行顺序（PRD §3.4）

### Week 1–2 · 地基（当前）

```
M20-A-01/02  成功页双 CTA + 取消 auto-open
M20-C-01     auto breath profile
M20-B-01/02  封面 C2 + 小相册 C3
M20-A-08     toolbar 极简
M20-D-01/02  Loading + 时间预估
M20-B-03     排版冲刺启动（10 相册清单）
```

### Week 3–4 · 差异化

```
M21-01       longshot filter
M21-02–05    卷轴仪式 + 双呼吸屏
M21-07       长图封底
M20-A-04–06  L1/L2/L3
```

### 并行 · Tier 4

```
M23-03/04    API 对齐 + web-view 手测文档
```

---

## 发布闸门（对应 ACCEPTANCE-PHASE5.md）

| 类别 | 必达 |
|------|------|
| **路径 A** | UX-P5-80-01 · P5-2.5/2.6 · L1–L4 · C2/C3 |
| **路径 B** | P5-S1/S7 · UX-P5-SCROLL-01 · P5-QS-01 |
| **工程** | P5-10.4 e2e · P5-12.3 |

**Tier 1（S2–S4）不阻塞路径 A 发布。**

---

## 配套验收记录（待填）

| 文件 | 用途 |
|------|------|
| [phase5-zero-edit.json](./acceptance-records/phase5-zero-edit.json) | UX-P5-80-01 计时 |
| [phase5-scroll-qualitative.json](./acceptance-records/phase5-scroll-qualitative.json) | UX-P5-SCROLL-01 定性 |
| [phase5-layout-sprint.json](./acceptance-records/phase5-layout-sprint.json) | P5-QS-01 排版冲刺（框架已建，待填 10 相册） |

---

## 变更记录

| 日期 | 说明 |
|------|------|
| 2026-05-30 | 初稿：M20–M23 · 对齐 PRD v0.5.4 |
| 2026-05-30 | **Week 1 启动**：M20-A-01/02 ☑ · M20-C-01 ☑ · `test_reading_auto_breath.py` |
| 2026-05-30 | **Tier 0 批次**：M20-A-08 · M20-B-01/02 · M20-C-02 ☑ · P5-QS-01 框架 · 相关测试 |
| 2026-05-30 | **M21 Tier 1**：D1 filter · S2–S5 · T2 · L5 · S3/S4/S9 · `test_m21_phase5.py` |
| 2026-05-30 | **M20-A L1–L4**：428px · 20MB 分段 · stageHint · Playwright warm |
| 2026-05-30 | **M20 收尾**：A-03 微信指引 · B-04 C1 · D-01–06 · C-04 确认无 profile UI |
| 2026-05-30 | **M21-10 + 波次2 UX**：P5-H2 真实长图缩略 · H1 帮助重播 · I3 上传体积 · 1.5 示意图 · 5.2 250+ 说明 |
| 2026-05-30 | **P5-3.1 / R1 / I4**：preview modal · 节奏 scoring · ingest 断点续传 |
| 2026-05-30 | **M22-02 P5-7.4**：Studio 高级选项 · 智能排版实验开关 → `layout.scoring.enabled` |
| 2026-05-30 | **M22-03 P5-7.5**：结构 drawer · layoutDecisionLog 排版 explain |
| 2026-05-30 | **M22-04/05**：P-EVAL 盲评脚本 · G1 banner · 锚点 narrate · drawer 焦点陷阱 |
| 2026-05-30 | **M23-01 P5-12.2**：ACCEPTANCE.md 单轨入口 · acceptance-records 索引 |
| 2026-05-30 | **M23-02 P5-12.3**：CLI-SPEC v0.4 · studio/longshot/HTTP 路由同步 |
| 2026-05-30 | **M23-03 P5-MP-1**：API-MINIAPP v0.2 字段对齐 · schema 兄弟键无冲突 · `test_api_miniapp_sync.py` |
| 2026-05-30 | **M23-04 P5-MP-2**：API-MINIAPP v0.3 §11 本地 web-view 手测清单 MP-WV-01～11 · `phase5-webview-manual.json` |
