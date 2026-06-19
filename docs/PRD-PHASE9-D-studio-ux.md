# Phase 9 · 附录 D · Studio 与 UX 规格

| 属性 | 内容 |
|------|------|
| **主文档** | [PRD-PHASE9.md](./PRD-PHASE9.md) |
| **代号** | P9-D |
| **关联** | [PRD-STUDIO-HOMEPAGE.md](./PRD-STUDIO-HOMEPAGE.md)、[PRD-PHASE3.md](./PRD-PHASE3.md) §6.4、[PRD-STUDIO-DUAL-LAYOUT.md](./PRD-STUDIO-DUAL-LAYOUT.md) |
| **更新** | 2026-06-02 |

---

## 1. UX 原则

| ID | 原则 |
|----|------|
| **UX-P9-01** | **静默执行**：用户不点击「开始筛选」；cull 是 ingest 子步骤 |
| **UX-P9-02** | **无被筛图 UI**：不提供 Gallery、列表、缩略图、恢复按钮 |
| **UX-P9-03** | **一行摘要**：完成时告知「经挑选 N 张进入排版」 |
| **UX-P9-04** | **不增 stageCount**：仍 4 段 Job |
| **UX-P9-05** | **Fail-open**：cull 失败不阻断 Job；WARN + 全量 eligible |
| **UX-P9-06** | **cullUserLine** 为成功 toast **第二行**，不替换第一行（D-P9-15） |
| **UX-P9-07** | **P9-F1**：Import Sheet 提供「智能挑选照片」checkbox（默认勾选）；关闭时 FirstSuccess 展示 N/M 双数字，不出现「经挑选」 |

---

```text
Studio 首页
  Idle → Importing（现有）
    └─ ingest 阶段内嵌 cull（无独立 UI 块）

FirstSuccess / 预览入口
  └─ 可选一行 cull 摘要（非阻断）

不新增：
  ✗ /excluded-photos
  ✗ 预览侧栏「已隐藏 N 张」
  ✗ G1 结构页筛图控件
```

---

## 3. Importing 态

### 3.1 stage 模型（不变）

仍 `{stageIndex}/{stageCount} {主文案}（{stageHint}）` · 见 PRD-PHASE3 §6.4.2。

### 3.2 ingest · stageHint 映射（扩展）

在 **现有** ingest 文案基础上，cull 阶段插入子 hint（**不**单独成 stage）：

| 条件 | stageHint 示例 |
|------|----------------|
| 默认 ingest | `已处理 45/120 张`（P5-I1 既有） |
| cull 进行中（可选 W2） | `正在挑选照片…` |
| cull + P1 ML 慢 | `正在评估照片质量…` |
| 完成 ingest（内部） | —（摘要移至完成态） |

**实现**：`studio_pipeline.py` 在 ingest progress 回调中，当 `phase=cull` 时覆盖 hint；若未实现细粒度，**合并**为一条：

```text
正在导入并挑选照片（已处理 45/120 张）
```

### 3.3 分级慢提示（继承 Phase 3）

|cull+ingest 累计| 慢提示 |
|----------------|--------|
| >30s | 「照片较多，正在去重和挑选，请稍候」 |
| >3min | 「首次质量分析可能较慢，可稍后回来查看」 |

---

## 4. Job 完成态 / FirstSuccess

### 4.1 主摘要行（必须 · D-P9-15）

**位置**：Job 成功 toast。

**布局**（两行）：

```text
第一行（既有）：游记已生成 / 打开预览 …
第二行（新增）：经挑选 {layoutEligibleCount} 张进入排版
```

双文件夹时第二行：

```text
经挑选 {layoutEligibleCount} 张进入排版（精选 {featuredCount} 张已为您保留）
```

**禁止**用 cull 摘要替换第一行；**禁止**写「已删除 N 张」。

### 4.2 分项（可选 · 折叠 / CLI 优先）

**Studio MVP**：**不**在 FirstSuccess 展示分项，避免「被删了哪些」暗示。

**CLI `format_ingest_report`**（必须）：

```text
导入 +97 张，跳过 31 张
  经挑选: 97 张进入排版
  连拍/相似组: 18
  模糊: 5
  质量筛选: 6
  截图/缩略图: 2
```

### 4.3 max_photos WARN（方案 B）

**触发**：`cullSummary.maxPhotosExceeded=true`

**展示**：非阻断 toast / FirstSuccess 次要行（`studio__toast--warn`）：

```text
共 {layoutEligibleCount} 张进入排版，超过建议上限 {maxPhotosLimit} 张，生成可能较慢
```

**不** 提供「减少照片」行动按钮（MVP）。

---

## 5. 前端改动清单

| 文件 | 改动 |
|------|------|
| `travelogue/web/studio_pipeline.py` | ingest 子阶段 hint；写入 `cull_user_line` 到 Job meta |
| `travelogue/web/studio_jobs.py` | `Job` 可选字段 `cullUserLine`（或嵌 `stats`） |
| `templates/studio/studio.js` | 成功 toast **追加** `cullUserLine` 第二行 |
| `travelogue/media/ingest_report.py` | CLI 分项 |
| `templates/studio/studio.css` | 无必须样式（复用 toast） |

### 5.1 API · Job status 扩展

`GET /__travelogue/job/{id}/status` 响应 **可选** 增加：

```json
{
  "stage": "ingest",
  "stageHint": "正在导入并挑选照片（已处理 45/120 张）",
  "cullUserLine": null,
  "stats": {
    "cull_layout_eligible": 97
  }
}
```

完成时：

```json
{
  "stage": "done",
  "cullUserLine": "经挑选 97 张进入排版（精选 15 张已为您保留）",
  "cullWarn": "共 297 张进入排版，超过建议上限 250 张…"
}
```

### 5.2 线框 / 视觉

**不** 新 wireframe 页；在 [wireframes/studio-homepage-wireframe.html](./wireframes/studio-homepage-wireframe.html) Importing 态 **注释** 增补 hint 变体 1 条（维护者参考）：

```html
<!-- P9: 正在导入并挑选照片（已处理 45/120 张） -->
```

---

## 6. 预览页 / G1

| 区域 | Phase 9 |
|------|---------|
| 预览 toolbar | **无** cull 控件 |
| G1 结构确认 | **无** 被筛列表 |
| intent 摘要（Phase 4） | 可追加 **eligible 计数** 一句（P2 可选） |

---

## 7. 高级设置

**MVP 不暴露** `cull.enabled` / `keep_ratio_floor` 于 Studio D′ 折叠（invisible 产品策略）。

维护者仅 `config.yaml` 调参；与 Phase 3 clustering 高级折叠 **独立**。

---

## 8. 无障碍与 i18n

| 项 | 要求 |
|----|------|
| toast | `role=status`；可读完整句 |
| 动态 title | Importing 仍 `正在生成…` · **不** 写「删除 N 张」 |
| 文案 | 中文优先；避免「剔除/删除」用 **「挑选」** |

---

## 9. 验收（AC-P9-UX）

| ID | 条件 |
|----|------|
| **AC-P9-UX-01** | Importing **无** 新 route / 新 modal |
| **AC-P9-UX-02** | Job 成功展示 `cullUserLine` |
| **AC-P9-UX-03** | **无** 被筛照片任何入口（Playwright 断言 DOM 无 `excluded`/`hidden-photos` 类） |
| **AC-P9-UX-04** | maxPhotos WARN 非阻断 |
| **AC-P9-UX-05** | cull 失败 Job 仍 success + 无 cullUserLine 或降级文案 |
| **AC-P9-UX-06** | compact 390px toast 不溢出（继承 P5 规范） |
| **AC-P9-UX-07** | P9-F1：checkbox 默认勾选；关闭时成功态无「经挑选」、有 N/M（见 [PRD-PHOTO-CULL-USER-TOGGLE.md](./PRD-PHOTO-CULL-USER-TOGGLE.md) AC-F1-*） |

---

## 10. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.9.2 | 2026-06-19 | UX-P9-07 · AC-P9-UX-07（P9-F1） |
| v0.9.1 | 2026-06-02 | D-P9-15 两行 toast · W1 无 cull stageHint 细粒度 |
| v0.9.0 | 2026-06-02 | 初稿 |
