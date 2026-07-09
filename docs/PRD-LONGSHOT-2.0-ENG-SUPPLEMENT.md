# Travelogue · 导出长图 2.0 · 工程落地增补（Eng Supplement）

| 属性 | 内容 |
|------|------|
| **主 PRD** | [PRD-LONGSHOT-2.0.md](./PRD-LONGSHOT-2.0.md) v0.3.3 |
| **状态** | **Accepted**（开发负责人建议 · 已写回 PRD §3/§9/§17） |
| **读者** | 后端 / 前端 / QA / 技术 PM |
| **更新日期** | 2026-07-08 |

> 本文档收纳 **开发负责人执行层** 细节：Sprint 拆 PR、DoD、分工、风险 mitigation 操作手册。  
> 其中 **影响范围 / AC / 冻结决策** 的条目已同步进主 PRD；本文仅保留实施时不应丢失的过程性说明。

---

## 1. 与主 PRD 的分工

| 内容类型 | 文档 |
|----------|------|
| 做什么、验收什么、产品决策 | **PRD-LONGSHOT-2.0.md** |
| 任务 ID、文件路径、里程碑周数 | **IMPLEMENTATION-LONGSHOT-2.0.md** |
| 手测 / pytest AC | **ACCEPTANCE-LONGSHOT-2.0.md** |
| 架构三分支、禁 P1、原子 Job | **ADR-016** |
| Guizang 采纳/不采纳对照 | **[research/GUIZANG-LONGSHOT-CROSSREF.md](./research/GUIZANG-LONGSHOT-CROSSREF.md)** |
| Sprint 拆 PR、DoD、分工、Review 清单 | **本文档** |

---

## 2. Sprint 与 PR 策略（Phase A · 4 周）

### Sprint 1（Week 1）— 切分纯函数 + API 护栏

**目标**：无 UI；CLI 尚不可跑通 E2E，但 splitter 可单测。

| PR | 内容 | 合并门槛 |
|----|------|----------|
| PR-1a | `platform_profiles.yaml` + `platform_profiles.py` | 单测 |
| PR-1b | `content_splitter.py`（DP + scale + 6–9 降级） | `test_content_splitter.py` 全绿 |
| PR-1c | `handle_longshot` platform 字段 + 400 校验 | handler 测试 |
| PR-1d | `export_trip_longshot` 路由至 `platform_longshot` 骨架（NotImplemented OK） | `test_export_longshot` 回归 |

**不合并**：Popover UI、Pillow、full capture E2E。

### Sprint 2（Week 2）— 分支 B 后端 E2E

**目标**：CLI 可交付内测。

| PR | 内容 | 合并门槛 |
|----|------|----------|
| PR-2a | `boundary_metrics.py` + RENDER-CONTRACT 条目 | golden trip 集成 |
| PR-2b | `platform_longshot.py` pipeline + `PlatformExportWriter` | AC-LNG2-11 |
| PR-2c | footer + 降 scale 重 capture + 禁 P1 | AC-LNG2-09/12/08 |
| PR-2d | CLI `--platform wechat_moments` | 文档 CLI-SPEC 草稿 |

**内测出口**：`travelogue export-longshot <T-large> --platform wechat_moments`

### Sprint 3（Week 3）— Studio UI

| PR | 内容 | 合并门槛 |
|----|------|----------|
| PR-3a | **新建** `longshot-export-panel.js`；toolbar 仅 import | 无 +200 行进 toolbar |
| PR-3b | 动态 CTA + prefs + Job 请求 | AC-LNG2-07 |
| PR-3c | 成功 Modal publishGuide + 文件列表 | H-A-06；缩略条 **不做** |

### Sprint 4（Week 4）— 硬化 + 灰度

| PR | 内容 | 合并门槛 |
|----|------|----------|
| PR-4a | ACCEPTANCE §4 手测修复 | T-large + T-small 签字 |
| PR-4b | PF-LNG2-01 报告 + 灰度开关 | dogfood |
| PR-4c | NR 全过 | §6 ACCEPTANCE |

**Phase B 另开 Epic**，禁止在 Phase A 分支堆 `slide_postprocess` letterbox 逻辑。

---

## 3. 开发负责人 Definition of Done（Phase A）

1. `pytest tests/unit/export/test_content_splitter.py tests/unit/export/test_export_longshot_platform.py tests/unit/export/test_export_longshot.py` 0 失败  
2. CLI moments @ T-large → 9 张；@ T-small（8–12 张）→ 6–9 张  
3. Studio 灰度下 Popover 同路径可导出  
4. Job 失败无 `.part` / 残缺 `*-moments-*.png`  
5. `wechat_chat` NR 全过（含 P1 仍可用）  
6. ACCEPTANCE §4 H-A-01～13 手测签字（H-A-07 缩略条 **跳过**，见 D-LNG2-24）

---

## 4. 模块实现要点

### 4.1 `platform_longshot.py`（分支 B 唯一入口）

```python
def export_platform_longshot(...) -> LongshotExportResult:
    profile = resolve_profile(...)
    scale = auto_downgrade_scale_if_needed(page_metrics, scale)
    canvas_bytes = capture_full_p0_only(page, scale=scale)  # 无 P1
    boundaries = collect_boundaries(page)  # CSS px
    breakpoints = compute_breakpoints_dp(..., scale=scale)
    with PlatformExportWriter(prefix) as writer:
        for i, (y0, y1) in enumerate slices:
            slice_bytes = crop(canvas_bytes, y0, y1)
            slice_bytes = draw_page_footer(slice_bytes, i + 1, n)
            writer.write(i + 1, slice_bytes)
    return result
```

### 4.2 `PlatformExportWriter`

| 方法 | 行为 |
|------|------|
| `write(nn, bytes)` | 写 `{title}-moments-{nn}.part` |
| `commit()` | rename 全部 `.part` → 最终名 |
| `rollback()` | 删除 prefix 下所有 `.part` 与半成品 |

失败路径 **必须** `rollback()`（Context manager `__exit__`）。

### 4.3 降 scale 流程

```
estimate_memory(scale) > budget
  → scale -= 1
  → re-goto page（可选 refresh layout）
  → re-collect boundaries
  → capture_full
```

**禁止**：降 scale 后仍用旧 boundaries 裁切。

### 4.4 Phase A Pillow 范围

| 允许 | 禁止 |
|------|------|
| `draw_page_footer` | `fit_aspect` letterbox |
| `crop` by y-range（可用 Pillow 或纯 bytes 切片） | smart_crop |

Phase B 再引入 `slide_postprocess.fit_aspect`。

---

## 5. 团队分工（参考 · 2 BE + 1 FE）

| 角色 | Sprint 1–2 | Sprint 3–4 |
|------|------------|------------|
| **BE-A** | boundary_metrics + platform_longshot pipeline | 性能 / 降 scale |
| **BE-B** | content_splitter + profiles + handler + writer | CLI + NR 修复 |
| **FE** | longshot-client platform 字段（PR-1c 可并行） | export-panel + Modal |
| **QA** | Sprint 2 起跟 CLI 内测 | Sprint 4 ACCEPTANCE |

Sprint 1 两人共同 review splitter 单测 fixture。

---

## 6. Code Review 必查项

| # | 检查 |
|---|------|
| R1 | `platform != wechat_chat` 路径 **无** `_capture_p1` 调用 |
| R2 | 降 scale 后 **重新** collect boundaries |
| R3 | except 分支调用 `writer.rollback()` |
| R4 | 未向 `preview-toolbar.js` 新增 >100 行（应进 panel 模块） |
| R5 | boundary selector 变更同步 RENDER-CONTRACT |
| R6 | Phase A PR **无** letterbox / xhs 业务代码 |
| R7 | `content_splitter` 实现 **boundary weight**（D-LNG2-29 · 见 CROSSREF §5） |

---

## 7. 风险 Mitigation 操作手册

| 风险 | 操作 |
|------|------|
| OOM | T-large 纳入 nightly；capture 前 log estimated_bytes |
| 切分切到拼图 | boundary JS 必须含 **photo cell**；不仅 media-card |
| toolbar 膨胀 | PR 拒收：panel 模块 diff 占比 <80% 且 toolbar +200 行 |
| 磁盘多套产物 | 成功 Modal 展示 prefix `-moments-`；v2.1 再议清理 |
| Phase B 质量 | A 上线 1 周后再开 B branch；5 trip 视觉评审 gate |

---

## 8. 延后项（已写入 PRD D-LNG2-24）

| 项 | 版本 |
|----|------|
| 成功 Modal **缩略条** | v2.0.1 |
| 书架记住 platform | v2.1 |
| sparse **品牌尾页** | v2.1（OQ-LNG2-01） |

---

## 9. 版本记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1.0 | 2026-07-08 | 开发负责人建议落地；PRD v0.3.2 已吸纳决策项 |
| v0.1.1 | 2026-07-08 | Guizang 写回：R7 · CROSSREF 链接 |
