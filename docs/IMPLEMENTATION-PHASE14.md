# Travelogue · Phase 14 实施任务清单

| 属性 | 内容 |
|------|------|
| **PRD** | [PRD-PHASE14.md](./PRD-PHASE14.md) v0.14.1 |
| **阶段代号** | Phase 14 · 双模式导入（快速分享 / 精细制作） |
| **状态** | In Progress |
| **更新** | 2026-06-04 |

---

## 落地原则（开发阶段）

1. **不损升级**：旧请求、旧 trip、旧成功页可回退。  
2. **先护栏后功能**：先 schema/API 兼容，再上 UI。  
3. **fail-open**：新增字段失败不阻断主流程。  
4. **快速路径优先**：先保证“选夹→生成→长图”不回归。

---

## 里程碑总览

| 里程碑 | 目标 | 出口 |
|--------|------|------|
| **M14.0 护栏层** | schema/API/回退开关就绪 | 旧请求全兼容、测试绿 |
| **M14.1 UI 壳层** | 双 Tab + 放大弹窗 + 快速模式默认 | 可手工跑通两模式入口 |
| **M14.2 数据与消费** | 新字段落盘与 brief 消费 | `trip.json` 可见字段且渲染不报错 |
| **M14.3 成功页分流** | 按 mode 分层 CTA（禁自动跳转） | 行为符合 PRD D14-07 |
| **M14.4 回归与文档** | 自动化 + 人工验收 + 文档对齐 | AC-P14 全通过 |

---

## M14.0 护栏层（P0）

| ID | 任务 | 文件 | 状态 |
|----|------|------|------|
| M14-0a | 扩展 `intent` schema：`dateRange`、`travelNotes`（均 optional） | `schemas/trip.schema.json` | ☑ |
| M14-0b | `TripService.apply_intent()` 扩展参数（`date_range`、`travel_notes`），保持双写不变量 | `travelogue/services/trip.py` | ☑ |
| M14-0c | Import payload 兼容解析：新增 `mode/dateRange/travelNotes/featuredDir/materialDir`，旧字段无改动 | `travelogue/web/studio_handlers/import_handlers.py` | ☑ |
| M14-0d | 子进程透传新增字段 | `travelogue/web/studio_subprocess.py` | ☑ |
| M14-0e | pipeline 接收新增参数并写入 `intent`（不改变原有默认值） | `travelogue/web/studio_pipeline.py` | ☑ |
| M14-0f | 增加本地回退开关（开发联调用） | `travelogue/config.py` `config.yaml.example` | ☑ |

---

## M14.1 UI 壳层（P0）

| ID | 任务 | 文件 | 状态 |
|----|------|------|------|
| M14-1a | Import Sheet 结构升级为双 Tab（快速分享默认） | `templates/studio/studio-home-v2.html` | ☑ |
| M14-1b | 导入弹窗尺寸升级（宽高、滚动分区、断点） | `templates/studio/studio-home-v2.css` | ☑ |
| M14-1c | Tab 切换状态管理与焦点管理 | `templates/studio/homepage-v2/import-sheet.js` | ☑ |
| M14-1d | 草稿缓存：切换/关闭/重开不丢内容 | `templates/studio/homepage-v2/import-sheet.js` | ☑ |
| M14-1e | 字段帮助与示例 chip（编辑一句话） | `templates/studio/studio-home-v2.html` `templates/studio/studio-home-v2.css` | ☑ |
| M14-1f | 命名替换：懒人/专业 -> 快速分享/精细制作 | `templates/studio/studio-home-v2.html` `templates/studio/homepage-v2/*.js` | ☑ |

---

## M14.2 数据与消费（P0）

| ID | 任务 | 文件 | 状态 |
|----|------|------|------|
| M14-2a | `buildImportPayload()` 注入 mode + 新字段 | `templates/studio/homepage-v2/import-run.js` | ☑ |
| M14-2b | `startV2Import` / 上传导入携带新增字段（可缺省） | `templates/studio/homepage-v2/import-run.js` | ☑ |
| M14-2c | 后端写入 `intent.folders` 手动覆盖值（保留自动检测兜底） | `travelogue/web/studio_pipeline.py` | ☑ |
| M14-2d | 叙事 brief 注入 `travelNotes/dateRange`（长度与 fail-open 约束） | `travelogue/services/narrative_brief.py` | ☑ |
| M14-2e | 日期校验（start/end）与错误文案返回 | `templates/studio/homepage-v2/import-sheet.js`（前端）+ `import_handlers.py`（后端兜底） | ☑ |

---

## M14.3 成功页分流（P0）

| ID | 任务 | 文件 | 状态 |
|----|------|------|------|
| M14-3a | Import 结果携带 `mode` 并落到 job.result | `travelogue/web/studio_subprocess.py` `travelogue/web/studio_jobs.py` | ☑ |
| M14-3b | 成功页按 mode 决定主 CTA（快速=长图；精细=卷轴） | `templates/studio/homepage-v2/first-success.js` | ☑ |
| M14-3c | 关闭自动倒计时跳转（精细模式首版禁用） | `templates/studio/homepage-v2/first-success.js` | ☑ |
| M14-3d | 预览失败时主 CTA 自动回退长图并提示 | `templates/studio/homepage-v2/first-success.js` | ☑ |

---

## M14.4 回归与文档（P0）

| ID | 任务 | 文件 | 状态 |
|----|------|------|------|
| M14-4a | 补单测：import 新字段解析与兼容 | `tests/test_studio_handlers_import_export.py` `tests/test_studio_intent.py` | ☑ |
| M14-4b | 补单测：`apply_intent` 新字段写入与清空 | `tests/test_studio_intent.py` | ☑ |
| M14-4c | 补前端行为测试（可先最小 smoke） | `tests/test_studio_home_v2.py`（新增 smoke） | ☑ |
| M14-4d | 同步验收文档与发布检查 | `docs/ACCEPTANCE-PHASE14.md` | ☑ |

---

## 文件改动映射（主路径）

| 模块 | 改动点 |
|------|--------|
| `studio-home-v2.html/css` | 双 Tab + 大弹窗 + 新字段 UI |
| `homepage-v2/import-sheet.js` | Tab 状态、字段校验、草稿缓存 |
| `homepage-v2/import-run.js` | mode/new fields 请求组装 |
| `homepage-v2/first-success.js` | 成功页分流与禁自动跳转 |
| `studio_handlers/import_handlers.py` | 新字段解析与兼容 |
| `studio_subprocess.py` | 新字段透传与结果携带 mode |
| `studio_pipeline.py` | intent 写入与手动 folder override |
| `services/trip.py` | `apply_intent` 新字段 |
| `services/narrative_brief.py` | brief 消费 travelNotes/dateRange |
| `schemas/trip.schema.json` | intent 子字段扩展 |

---

## 开发自测命令（建议）

```bash
pytest tests/test_studio_entry.py tests/test_studio_intent.py tests/test_studio_preview_m16.py -q
pytest tests/test_studio_chrome.py tests/test_studio_stages.py -q
python -m travelogue studio
```

手工冒烟（必须）：

1. 快速分享：选夹 -> 开始制作 -> 成功页主 CTA=保存长图  
2. 精细制作：填写 `travelNotes/dateRange` -> 开始制作（专业） -> 成功页主 CTA=卷轴预览  
3. 导入失败重试：字段与 mode 不丢失  
4. 1366×768 下弹窗可完整提交

---

## 风险与缓解

| 风险 | 缓解 |
|------|------|
| 双模式引入复杂度导致回归 | M14.0 护栏层先行；每里程碑都跑快速路径回归 |
| 弹窗放大影响低分辨率可用性 | 断点策略 + 分区滚动 + 固定主 CTA |
| 新字段 schema 与历史 trip 冲突 | optional 字段 + migrate-on-write |
| 成功页旧倒计时逻辑残留 | M14.3 明确移除或按 mode 强制禁用 |

---

## 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.14.0 | 2026-06-04 | 初稿：按 PRD-PHASE14 v0.14.1 拆分 M14.0~M14.4 |
| v0.14.2 | 2026-06-04 | M14.0~M14.3 全完成；M14.4 已补后端与领域单测，前端自动化待补 |
| v0.14.3 | 2026-06-04 | 补齐前端最小 smoke（双模式 DOM/接线/成功页回退） |

