# Travelogue · Definition of Done（里程碑）

| 属性 | 内容 |
|------|------|
| **文档版本** | v0.1 |
| **MVP 完成** | 全部 M1–M7 Done + [ACCEPTANCE.md](./ACCEPTANCE.md) AC-01～06 |
| **更新日期** | 2026-05-19 |

---

## 1. 通用 Done 标准（每个 PR / 里程碑）

- [ ] 代码合并至主分支（或约定开发分支）  
- [ ] `python scripts/validate_trip.py` 对相关 **fixtures** 通过（`--level all`）  
- [ ] 新增逻辑有 **pytest** 或脚本测试（见 `TESTING.md`）  
- [ ] 若改 `trip.schema.json` / `manifest.json`：同步 **fixtures + 文档**  
- [ ] `CLI-SPEC.md` 中对应命令已实现或标注 `NOT IMPLEMENTED`  
- [ ] 无 API Key、精确 GPS 写入日志或提交文件  

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
