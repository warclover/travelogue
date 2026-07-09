# Travelogue · 导出长图 2.0 实施任务清单

| 属性 | 内容 |
|------|------|
| **PRD** | [PRD-LONGSHOT-2.0.md](./PRD-LONGSHOT-2.0.md) v0.3.3 |
| **Eng Supplement** | [PRD-LONGSHOT-2.0-ENG-SUPPLEMENT.md](./PRD-LONGSHOT-2.0-ENG-SUPPLEMENT.md) |
| **ADR** | [016-longshot-platform-export.md](./adr/016-longshot-platform-export.md) |
| **状态** | Draft |
| **更新** | 2026-07-08 |

---

## 落地原则

1. **分支 A 零回归**：`wechat_chat` 不改行为。
2. **分支 B 独立入口**：`export_platform_longshot()`，禁止 P1。
3. **先算法后 UI**：DP + scale 单测绿后再接 Popover。
4. **原子写盘**：失败无残缺 moments/xhs 文件。
5. **Phase A 可独立上线**：灰度 `platforms: ["wechat_moments"]`。
6. **W2 末 CLI 内测**：`export-longshot --platform wechat_moments` 先于 Popover 合并。

---

## 里程碑总览（评审修订工期）

| 里程碑 | 目标 | 周期 |
|--------|------|------|
| **M-LNG2.0 护栏** | API + profile + ADR-016 分支骨架 | **1w** |
| **M-LNG2.1 切分引擎** | boundary + DP + scale 单测 | **1w** |
| **M-LNG2.2 朋友圈** | 分支 B E2E + UI + 原子写盘 | **2w** |
| **M-LNG2.3 小红书** | letterbox + UI | **2w** |
| **M-LNG2.4 后端扩展** | YAML/CLI/stale（**无新前端**） | **1w** |
| **M-LNG2.5 发布** | AC + telemetry + 文档 | **1w** |

**Phase A = M-LNG2.0–2.2 → 4 周**  
**全量 ≈ 8 周**

---

## M-LNG2.0 护栏层（第 1 周）

### 后端

| ID | 任务 | 文件 | 状态 |
|----|------|------|------|
| BE-LNG2-01 | `platform_profiles.yaml`（chat / moments / xhs） | `config/platform_profiles.yaml` | ☑ |
| BE-LNG2-02 | `PlatformProfile` + 校验 | `travelogue/export/platform_profiles.py` | ☑ |
| BE-LNG2-03 | `export_platform_longshot()` 于 **`platform_longshot.py`** | `travelogue/export/platform_longshot.py` | ☑ |
| BE-LNG2-04 | `export_trip_longshot` 路由：platform→B，else→A | `longshot.py` | ☑ |
| BE-LNG2-05 | `handle_longshot` 解析 platform；非法→**400** | `export_handlers.py` | ☑ |
| BE-LNG2-06 | Job result 追加 `platform` / `publishGuide` | `export_handlers.py` | ☑ |
| BE-LNG2-07 | 回归 `test_export_longshot.py` | `tests/` | ☑ |
| BE-LNG2-08 | ADR-016 登记 | `docs/adr/README.md` | ☑ |

### 配置

| ID | 任务 | 文件 | 状态 |
|----|------|------|------|
| CFG-LNG2-01 | `studio.longshot2.enabled` | `config.py` · `config.yaml.example` | ☑ |
| CFG-LNG2-02 | `studio.longshot2.platforms` 灰度列表 | 同上 | ☑ |
| CFG-LNG2-03 | `studio.longshot2.smart_crop.enabled` 默认 false | 同上 | ☑ |

---

## M-LNG2.1 切分引擎（第 2 周）

| ID | 任务 | 文件 | 状态 |
|----|------|------|------|
| BE-LNG2-10 | `boundary_metrics` 输出 `boundaryKinds[]` 与权重映射 | `boundary_metrics.py` | ☑ |
| BE-LNG2-11 | CSS→canvas scale 映射工具 | `content_splitter.py` | ☑ |
| BE-LNG2-12 | `compute_breakpoints_dp(n, height, boundaries)` | `content_splitter.py` | ☑ |
| BE-LNG2-13 | 贪心 fallback + 6–9 张降级 + **boundary weight**（D-LNG2-29） | `content_splitter.py` | ☑ |
| BE-LNG2-14 | `slice_canvas(bytes, breakpoints)` | `content_splitter.py` | ☑ |
| BE-LNG2-15 | 单测：photo cell 不切中间 | `tests/test_content_splitter.py` | ☑ |
| BE-LNG2-16 | 单测：scale=2/3 坐标 | `tests/test_content_splitter.py` | ☑ |
| BE-LNG2-17 | 内存预估 + 自动降 scale | `platform_longshot.py` | ☑ |

---

## M-LNG2.2 朋友圈 Phase A（第 3–4 周）

### 后端

| ID | 任务 | 文件 | 状态 |
|----|------|------|------|
| BE-LNG2-20 | 分支 B：single P0 full capture | `export_platform_longshot()` | ☑ |
| BE-LNG2-21 | platform 模式 **禁用 P1** | `export_platform_longshot()` | ☑ |
| BE-LNG2-22 | split → `draw_page_footer(i,n)`（Pillow） | `slide_postprocess.py` | ☑ |
| BE-LNG2-23 | **`PlatformExportWriter`** 原子写盘 | `platform_longshot.py` | ☑ |
| BE-LNG2-24 | 命名 `{title}-moments-{nn}` | 同上 | ☑ |
| BE-LNG2-25 | >20MB：降 scale → **重 boundary + 重 capture**（≤2 次） | `platform_longshot.py` | ☑ |
| BE-LNG2-26 | progress 分阶段权重 | 同上 | ☑ |
| BE-LNG2-27 | 集成测试 AC-LNG2-01/02/11/12/13 | `tests/test_export_longshot_platform.py` | ☑ |

### 前端

| ID | 任务 | 文件 | 状态 |
|----|------|------|------|
| FE-LNG2-01 | **新建** `longshot-export-panel.js` | `templates/studio/js/` | ☑ |
| FE-LNG2-02 | 平台 seg：微信群 / 朋友圈 / 小红书 | 同上 | ☑ |
| FE-LNG2-03 | 朋友圈二级：预计 9 张 · 耗时提示 | 同上 | ☑ |
| FE-LNG2-04 | `preview-toolbar.js` 接入 panel 模块 | `preview-toolbar.js` | ☑ |
| FE-LNG2-05 | 动态 CTA 文案 | `preview-toolbar.js` | ☑ |
| FE-LNG2-06 | `buildLongshotRequest` + platform | `longshot-client.js` | ☑ |
| FE-LNG2-07 | 成功 Modal：**publishGuide + 文件列表**（无缩略条 · D-LNG2-24） | `preview-toolbar.js` · task-dock | ☑ |
| FE-LNG2-08 | 首次朋友圈 coach mark | `longshot-export-panel.js` | ☑ |
| FE-LNG2-09 | wireframe 对齐手测 | `wireframes/studio-longshot-export-v2.html` | ☐ |
| FE-LNG2-10 | Playwright Popover 测试 | `tests/test_preview_toolbar_v3.py` | ☐ |

**Phase A 出口**：灰度 moments · AC-LNG2-01~02/05/07/10~13

---

## M-LNG2.3 小红书 Phase B（第 5–6 周）

| ID | 任务 | 文件 | 状态 |
|----|------|------|------|
| BE-LNG2-30 | `fit_aspect(3:4, letterbox)` → 1080×1440 | `slide_postprocess.py` | ☑ |
| BE-LNG2-31 | smart_crop（flag 后） | `slide_postprocess.py` | ☑ |
| BE-LNG2-32 | auto slideCount **§6.4.3 Guizang 校准**（D-LNG2-31） | `platform_profiles.py` | ☑ |
| BE-LNG2-33 | letterbox 1080×1440 + **safe area warn**（D-LNG2-30） | `slide_postprocess.py` | ☑ |
| BE-LNG2-34 | `{title}-xhs-{nn}` + AC-LNG2-03/04 | `platform_longshot.py` | ☑ |
| FE-LNG2-20 | 张数 seg + 自定义 1–18 | `longshot-export-panel.js` | ☑ |
| FE-LNG2-21 | 填充 letterbox / smart_crop（后者受 flag） | 同上 | ☑ |
| FE-LNG2-22 | 小红书 publishGuide | `longshot-client.js` | ☑ |

---

## M-LNG2.4 后端扩展 Phase C（第 7 周 · 无新 UI）

| ID | 任务 | 文件 | 状态 |
|----|------|------|------|
| BE-LNG2-40 | ins / weibo / douyin_cover profiles | `platform_profiles.yaml` | ☐ |
| BE-LNG2-41 | custom profile（CLI only） | `platform_profiles.py` | ☐ |
| BE-LNG2-42 | `_longshot_files()` glob 扩展 | `studio_trips.py` | ☑ |
| BE-LNG2-43 | stale 测试 AC-LNG2-06 | `tests/test_studio_trips.py` | ☑ |
| BE-LNG2-44 | CLI flags | `cli/render_cmds.py` | ☑ |
| BE-LNG2-45 | SHARING.md §2.5 · CLI-SPEC | `docs/` | ☑ |

---

## M-LNG2.5 发布（第 8 周）

| ID | 任务 | 状态 |
|----|------|------|
| QA-LNG2-01 | `ACCEPTANCE-LONGSHOT-2.0.md` | ☑ |
| QA-LNG2-02 | 1.x 全量回归 | ☐ |
| QA-LNG2-03 | M14 书架回归 | ☐ |
| QA-LNG2-04 | linzhi 86 张 moments 手测 | ☐ |
| QA-LNG2-05 | xhs 导入 App 手测 | ☐ |
| QA-LNG2-06 | P95 耗时报告 · G-LNG2-07/09 | ☐ |
| DOC-LNG2-01 | Telemetry 事件登记 | ☑ |

---

## 明确不改（v2.0）

- `shelf-longshot.js` 默认 preset
- `longshot.js` 客户端 capture
- `trip.json` schema
- Phase C 前端「更多平台」菜单

---

## 版本记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1.0 | 2026-07-08 | 初稿 |
| **v0.2.0** | **2026-07-08** | 对齐 PRD v0.3.2 |
| v0.2.1 | 2026-07-08 | Guizang：boundaryKinds · weight · xhs safe area · slideCount 校准 |
