# ADR-016 · 平台化长图导出：三分支 Pipeline + 切分后处理

| 属性 | 内容 |
|------|------|
| **状态** | 已采纳（评审修订 v0.2） |
| **日期** | 2026-07-08 |
| **决策者** | 产品 + 架构 + 算法评审会 |
| **影响范围** | `travelogue/export/longshot.py`、`platform_profiles.py`、`content_splitter.py`、`slide_postprocess.py`、`export_handlers.py` |
| **关联** | [ADR-005](./005-longshot-server-side.md) · [PRD-LONGSHOT-2.0.md](../PRD-LONGSHOT-2.0.md) · [SHARING.md](../SHARING.md) |
| **前置** | ADR-005 P0/P1 捕获路径；Longshot 1.x 按章分段 |

---

## 背景

Longshot 2.0 需在 **不 fork HTML 模板** 的前提下，支持朋友圈 9 张、小红书 3:4 等平台规格。

评审发现 PRD v0.2.0 假设「一次 full canvas → Python 切分」，与 ADR-005 现有 **按章多次 capture** 路径并存但未显式分叉；且 P1 screenshot fallback 无法提供 card 边界，不能与平台切分组合。

---

## 决策

### D1 · 三分支 Pipeline（冻结）

| 分支 | 条件 | 行为 | P1 fallback |
|------|------|------|-------------|
| **A · wechat_chat** | `platform` 缺省或 `wechat_chat` | **完全沿用** Longshot 1.x：`_resolve_segment_plan` + 按章/单张 capture | **允许**（ADR-005） |
| **B · platform_segment** | `platform ∈ {wechat_moments, xiaohongshu, …}` | **一次 full canvas capture** → boundary 采集 → split → postprocess | **禁止**；P0 失败即 Job failed |
| **C · 客户端降级** | 游记页 FAB / 无 Playwright | 仅 `wechat_chat`；不暴露 platform preset | 不适用 |

**禁止**：在 platform 模式下回退到按章 capture 再假装平台规格。

---

### D2 · Full capture 内存与 scale 策略

| 项 | 规则 |
|----|------|
| 预估 | `scrollHeight × scale × CAPTURE_WIDTH × bpp`；超过 **400MB 内存预算** 时自动 **降 scale** 再 capture |
| 降 scale 后 | **必须** 重新 `boundary_metrics.collect` + 重新 full capture（D-LNG2-23） |
| 硬上限 | 预估仍超预算 → `E_LNG2_CAPTURE_TOO_LARGE`，提示减少照片或改用微信群按章 |
| capture 次数 | platform 模式 **仅 1 次** full `captureMainToBlob`（每次 scale 尝试计 1 次） |

---

### D3 · 边界坐标系

| 坐标 | 来源 |
|------|------|
| CSS px | Playwright `boundary_metrics.collect(page)` → card tops / chapter separators |
| Canvas px | `y_canvas = round(y_css × scale)` |

切分与裁切 **一律使用 canvas 坐标**。

---

### D4 · 切分算法

| 优先级 | 算法 |
|--------|------|
| 主路径 | **DP 最小化段高方差**，切点仅落在合法 boundary |
| 降级 | boundary 候选不足时 **贪心 nearest** |
| 段数 | `wechat_moments`：目标 9；合法切点不足时允许 **6–9 张**（见 PRD D-LNG2-02 修订） |

---

### D5 · 水印

| 模式 | 时机 |
|------|------|
| wechat_chat 按章 | 沿用 DOM / 现有 `apply_chapter_watermark` |
| platform 切分 | **Pillow 后处理** `draw_page_footer(i, n)`，在 slice 写入前绘制 |

---

### D6 · Job 原子性

platform 模式写入 `{title}-{platform}-{nn}.png` 时使用 **`PlatformExportWriter`**：临时后缀 **`.part`** → 全成功 **rename**；失败 **`rollback()`** 删除同 prefix 的 `.part` 与半成品。

---

### D7 · stale 与多产物共存

| 规则 |
|------|
| `longshotStale = true` 当 **任一** `_longshot_files()` 匹配产物 mtime < `trip.json.updatedAt` |
| 不同 platform 产物 **可并存**；不自动删除旧平台文件（v2.0） |

---

## 后果

- **正面**：平台扩展只需 YAML profile + postprocess，不增 HTML 面。
- **负面**：platform 模式单次 capture 内存峰值高于按章路径；超大 trip 需降 scale 或失败。
- **与 ADR-005 关系**：不修改 A 分支；B 分支为 additive。

---

## 版本记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1 | 2026-07-08 | 初稿：三分支 · scale 映射 · 禁 P1 · 原子 Job |
| v0.2 | 2026-07-08 | 评审修订：6–9 张降级 · stale 规则 |
| v0.3 | 2026-07-08 | 开发落地：降 scale 重 boundary · PlatformExportWriter · 写回 PRD D-LNG2-23 |
