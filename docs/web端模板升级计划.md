# Travelogue · Web 端模板升级计划

| 属性 | 内容 |
|------|------|
| **依据 PRD** | [web端模板.prd](./web端模板.prd) |
| **架构** | 单模板 `visual-journal` + `layoutEngine: legacy \| screens`（不 fork V2） |
| **差距跟踪** | PRD 附录 C（`C-P1-xx` 任务 ID） |
| **文档版本** | v1.0 |
| **更新日期** | 2026-05-21 |
| **负责人** | 实施中 |

---

## 总目标（约 3～4 个迭代）

| 里程碑 | 交付物 | 用户可见 |
|--------|--------|----------|
| **M0** | `layoutEngine` 契约 + 默认 `legacy` | 行为与现网一致 |
| **M1** | screens 引擎「能渲染」最小路径（竖/横 1·3） | 可选预览，仍非默认 |
| **M2** | 宫格 4/9 + 分屏 ≤9 + cover | PRD 主视觉成立 |
| **M3** | tone + 连拍启发 + 默认切 screens | 可对比、可回退 legacy |

---

## 架构决策

```json
{
  "exportLayout": "web",
  "layoutEngine": "legacy",
  "layoutEngineVersion": "screens-1"
}
```

| 字段 | 值 | 说明 |
|------|-----|------|
| `layoutEngine` | `legacy` \| `screens` | 默认 **`legacy`** |
| `layoutEngineVersion` | 如 `screens-1` | screens 规则版本，便于回归 |
| 与 `exportLayout` | 正交 | `screens` 仅在 `web`（或 `auto`+宽屏）生效；mobile 忽略 |

**CLI（对比用）**：

```powershell
python -m travelogue render <trip> --web-layout legacy
python -m travelogue render <trip> --web-layout screens -o index-screens.html
python -m travelogue curate ... --web-layout screens
```

**不新建** `templates/visual-journal-v2/`；CSS 可拆 `journal-screens.css` 再合并进 `journal.css`，zip 仍交付单一 `journal.css`。

---

## 阶段 0 · 契约与开关（1～2 天）— 无视觉变化

**目标**：管线认得双引擎，现网零回归。

| 任务 | 文件 | 验收 |
|------|------|------|
| C-P1-00 schema | `schemas/trip.schema.json` | `layoutEngine` 可选，默认缺省=legacy |
| C-P1-00 校验 | `validate` / manifest | 非法 engine 报错 |
| C-P1-00 curate | `curate.py` | 写入 `layoutEngine` |
| C-P1-00 render | `engine.py`、`context.py` | legacy 走原分支 |
| C-P1-00 CLI | `cli.py` | `--web-layout` |
| 测试 | 现有测试全绿 | — |

---

## 阶段 1 · Screens 数据 + 最小排版（3～5 天）— M1

### 1.1 数据模型（C-P1-01）

- `chapters[].screens[]`：`screenId`、`patternId`、`slots[]`
- planner 新增 `plan_screens_for_chapter`；`plan_chapter_items` 保留
- render：`legacy` 读 `items[]`；`screens` 读 `screens[]`

### 1.2 最小 pattern（M1）

| patternId | 触发 |
|-----------|------|
| `screen-portrait-3` | 连续竖×3 |
| `screen-portrait-1` | 竖×1 cover 兜底 |
| `screen-portrait-1-landscape-2` | 1 竖 + 2 横（竖左，时间邻近） |
| `screen-landscape-1` | 横×1 |
| `screen-landscape-3` | 横×3 |
| `screen-panorama-1` | 全景×1 |

单屏 ≤9 张；满屏拆下一屏。

### 1.3 模板（C-P1-06、C-P1-07）

- `partials/layout-screen.hbs`
- `partials/chapter.hbs` 分支
- `journal-screens.css`（合并进 `journal.css`）

### 1.4 金样例（C-P1-08 前半）

- `golden-web-screens.html` 静态 demo

**验收**：`layoutEngine=screens` 输出含 `layout-screen--16x9`；legacy 快照不变。

---

## 阶段 2 · 视觉填满 + 宫格（4～6 天）— M2

| 任务 | 内容 |
|------|------|
| C-P1-06 深化 | cover 拼图；单竖 contain + `--screen-tone` 占位 |
| C-P1-03 | 横/竖/方 4·6·9 宫格 |
| C-P1-02 | 满屏重置算法 |
| C-P1-05 | gallery：scroll 独占章 vs 多屏 mosaic（拍板） |
| manifest | screens pattern 白名单 |

**验收**：W-T02～W-T05。

---

## 阶段 3 · 智能与默认（3～4 天）— M3

| 任务 | 内容 |
|------|------|
| C-P1-04 | `orientationSummary` 启发分屏 |
| C-P2-02 | 连拍 `groupId` / 时间阈值 → 4/9 |
| C-P2-01 | `--screen-tone` 采色 |
| 默认 | config/demo 可默认 screens；CLI 保留 legacy |
| 文档 | `LAYOUT-PLANNER.md`、`RENDER-CONTRACT.md` |

---

## 阶段 4 · 收尾（可选）

- 双引擎 CI / `dom_compare`
- legacy deprecated 警告
- PRD 附录 C 状态更新

---

## 文件改动地图

```text
schemas/trip.schema.json
travelogue/curation/layout_planner.py
travelogue/curation/curate.py
travelogue/render/context.py
travelogue/render/engine.py
travelogue/cli.py
templates/visual-journal/partials/layout-screen.hbs
templates/visual-journal/partials/chapter.hbs
templates/visual-journal/journal-screens.css
templates/visual-journal/golden-web-screens.html
tests/test_screen_layout_planner.py
docs/LAYOUT-PLANNER.md
docs/RENDER-CONTRACT.md
```

---

## 风险与对策

| 风险 | 对策 |
|------|------|
| 改坏 legacy | screens 新函数/新 CSS 命名空间 |
| longshot 不认新 DOM | M2 后适配或 screens 长图暂禁 |
| 旧 trip | 缺省 `layoutEngine=legacy` |
| 工期膨胀 | 混排 v2 不做 |

---

## 2 周砍 scope 备选

保留：M0+M1+竖三 cover+横单/横三+金样例+CLI 对比。  
延后：6/9 宫格、tone 采色、groupId、默认改 screens。

---

## 每周节奏

| 周 | 交付 |
|----|------|
| W1 | M0 + M1 + golden-web-screens |
| W2 | M2 宫格 + cover + 分屏 |
| W3 | M3 + 文档 + CI |
| W4 | longshot/打印 + 默认 screens |

---

## 实施进度（勾选）

- [x] M0 · C-P1-00 契约与 CLI（`layoutEngine`、`--web-layout`、`--index-name`）
- [x] M1 · C-P1-01 schema screens
- [x] M1 · plan_screens_for_chapter + 5 patterns（`screen_planner.py`）
- [x] M1 · layout-screen.hbs + CSS（`journal-screens.css`）
- [x] M1 · render 分支 + 测试（`test_screen_layout_planner.py`、`test_render_screens_engine`）
- [x] M1 · golden-web-screens.html
- [x] M2 · 宫格 4/6/9 + cover 深化（screens-2）
- [x] M3 · tone 采色 + orientation 启发 + burst + config `layout.web_layout_engine`
- [x] M4 · 双引擎回归 `tests/test_dual_layout_engine.py` + `compare-web-layout.ps1`
- [x] M4 · README Web 双引擎说明；screens 禁用长图
- [x] M4 · G1 屏级摘要 `format_layout_summary`
- [x] M4 · `tripId` ASCII slug（相册目录名 / `demo_trip_id_from_album`）
- [x] M4 · 日桶组屏 `screen_plan_scope: day` + `mixed_proximity_seconds`
- [x] M4 · config 默认 `web_layout_engine: screens`（`config.yaml.example`）
- [ ] M4 · 真图 A/B 人工验收（见 [web-screens-ab-checklist.md](./web-screens-ab-checklist.md)）

---

## 版本记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0 | 2026-05-21 | 初版；与 PRD v0.1.1 对齐 |
| v1.1 | 2026-05-21 | M2/M3 实施：screens-2、宫格、tone、config |
