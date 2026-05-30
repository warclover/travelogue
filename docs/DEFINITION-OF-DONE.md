# Travelogue · Definition of Done（里程碑）

| 属性 | 内容 |
|------|------|
| **文档版本** | v0.1 |
| **MVP 完成** | 全部 M1–M7 Done + [ACCEPTANCE.md](./ACCEPTANCE.md) AC-01～07 |
| **Phase 2 完成** | M8–M10 Done + [ACCEPTANCE-PHASE2.md](./ACCEPTANCE-PHASE2.md) AC-P2-01～06 |
| **更新日期** | 2026-05-30 |

---

## 1. 通用 Done 标准（每个 PR / 里程碑）

- [ ] 代码合并至主分支（或约定开发分支）  
- [ ] `python scripts/validate_trip.py` 对相关 **fixtures** 通过（`--level all`）  
- [ ] 新增逻辑有 **pytest** 或脚本测试（见 `TESTING.md`）  
- [ ] 若改 `trip.schema.json` / `manifest.json`：同步 **fixtures + 文档**  
- [ ] `CLI-SPEC.md` 中对应命令已实现或标注 `NOT IMPLEMENTED`  
- [ ] 无 API Key、精确 GPS 写入日志或提交文件  
- [ ] 新增/大改 Python 模块时遵守 **§1.1 模块体量**（软上限，见 [ADR-010](./adr/010-tech-debt-sprint.md)）

### 1.1 模块体量（软上限 · ADR-010）

| 类型 | 建议上限 | 超出时 |
|------|----------|--------|
| 单文件「编排 + 叶逻辑」混装（如旧 `context.py`） | ~800 行 | 拆 `surface` / `chapters` / `assemble` 或域 handlers |
| HTTP 路由 Mixin | ~250 行 | 迁入 `studio_handlers/` |
| 屏规划主文件 | ~400 行 | 阶段迁入 `screen_planner_stages.py` |

> 非 CI 硬门禁；PR 评审时作为还债信号。已有测试（`test_build_render_context`、layout golden 等）须保持通过。

---

## 2. 里程碑清单

### M1 · 导入与数据模型（W1–2）

| 项 | Done 标准 |
|----|-----------|
| TripService | 创建/读/写/列表 trip |
| Schema | `validate_trip.py` L1 通过 |
| Agent 0 最小 | 单文件夹 jpg → WebP w800/w1600 + EXIF |
| Fixture | `trip.ingest_ready.json` 校验通过 |
| 演示 | `travelogue trip new` + `ingest` 文档命令可跑 |

### M2 · 策展（W3）

| 项 | Done 标准 |
|----|-----------|
| Agent 1 | 3–5 章 + pattern + coverCandidates |
| L2 | VR-P01～P05 在 curate 后通过 |
| CLI | `curate`、`lock structure` |
| Fixture | `trip.structure_locked.json` |
| 演示 | 规则分章无需 LLM 可跑 |

### M3 · 渲染 v1（W4）

| 项 | Done 标准 |
|----|-----------|
| Agent 3 render | fixture `copy_locked` → index.html |
| 视觉 | T-02/T-03 人工对照 golden 通过 |
| CSS | journal.css 与 golden.css 一致或子集 |
| CLI | `render`、`validate` |
| 演示 | 浏览器打开无 404 资源 |

### M4 · 视频（W5）

| 项 | Done 标准 |
|----|-----------|
| ffmpeg | clip + poster |
| 规则 | VR-M01～M03 通过 |
| 演示 | 1 个含视频 trip 渲染可播 |

### M5 · 叙事（W6）

| 项 | Done 标准 |
|----|-----------|
| Agent 2 | 按 `NARRATIVE-PROMPTS.md` 填槽 |
| 重试 | 超字数自动修 ≤2 次 |
| CLI | `narrate`、`lock copy` |
| Fixture | `trip.copy_locked.json` |
| 演示 | tone 切换可重生成 |

### M6 · 导出（W7）

| 项 | Done 标准 |
|----|-----------|
| zip | 解压可开 index.html |
| preview.jpg | 9:16 1080 宽 |
| 隐私 | 无 confirm 则 `E_EXPORT_PRIVACY` |
| CLI | `export --confirm-privacy` |
| EXIF | 导出图无精确 GPS（AC-06） |

### M7 · 自用验收（W8）

| 项 | Done 标准 |
|----|-----------|
| AC | [ACCEPTANCE.md](./ACCEPTANCE.md) 六条全 ☑ |
| 记录 | 3 次 trip 填验收表 §7 |
| Backlog | P1/P2 问题清单入库 |

### M8a · 架构跑通（Phase 2 · W1）

| 项 | Done 标准 |
|----|-----------|
| serve --studio + StudioMixin | 单端口 8766；dispatcher 在 `studio_routes.py` |
| Pipeline + Job | `--pick-folder` → rendered；stageHint 分档 |
| API | import（409+existingTripId）+ status |
| 回归 | 无 `--studio` 时 serve 与 MVP 一致 |
| 出口 | 维护者 CLI 可预览 |

### M8b · Studio Web（Phase 2 · W2）

| 项 | Done 标准 |
|----|-----------|
| studio.html | 空态 + 选图 + stageHint + soft warning |
| Studio Chrome | allowlist 注入；**longshot 面不注入**（UX-P2-06） |
| API | GET /trips + 最近链接 |
| 验收 | AC-P2-01a；AC-P2-03；UX-P2-* |

### M9 · 可分享闭环（Phase 2 · W2–3）

| 项 | Done 标准 |
|----|-----------|
| export-longshot | P0 captureMainToBlob + P1 fallback |
| 分段 | 高度 >5000px；单章 >60 卡兜底 |
| scale | CLI 默认 1；**Studio UI 默认 2** |
| Studio 长图 UI | chrome 最小按钮 + 路径面板 + **POST /reveal** |
| Playwright | base_url 复用 8766；browser 单例 |
| 稳定性 | LS-P2-01：5 trip P0 ≥80%；LS-P2-04 |
| 验收 | **AC-P2-01b**；AC-P2-02 |

### M10 · 工作台成熟化（Phase 2 · W3–4）

| 项 | Done 标准 |
|----|-----------|
| trip 列表 | 完整 UI（M8 已有 API + 最近链接） |
| 工具栏 | preview-toolbar 替换 chrome；zip 高级；stale 长图提示 |
| pipeline | 子进程 + 失败重试/返回工作台 |
| 验收 | AC-P2-04（完整）；AC-P2-06 |

### M11 · PyInstaller（Phase 2 · **P2 backlog**）

| 项 | Done 标准 |
|----|-----------|
| exe | 可选；**不阻塞** Phase 2 完成 |
| 原生选文件夹 | IFileDialog（非 tkinter M8） |

---

## 3. Agent 阶段 Done（横切）

| Agent | Done 当… |
|-------|----------|
| 0 | `MEDIA-PIPELINE.md` 图片节 + 去重 + 状态 ingest_ready |
| 1 | `VALIDATION-RULES` VR-P* + G1 lock |
| 2 | `NARRATIVE-PROMPTS` + edited 尊重 + G2 lock |
| 3 | `RENDER-CONTRACT` + L3 文件存在检查 + export |

---

## 4. 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1 | 2026-05-19 | 初稿 |
| v0.2 | 2026-05-27 | 新增 M8–M11（Phase 2；v0.2 评审修订） |
| v0.3 | 2026-05-27 | Studio Chrome；M9 长图 UI/路径；AC 里程碑拆分 |
| v0.3.1 | 2026-05-27 | M8a/b；allowlist；reveal；409 body |
| v0.3.2 | 2026-05-30 | §1.1 模块体量软上限（ADR-010 还债） |
