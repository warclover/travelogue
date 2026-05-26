# Travelogue · MVP 验收标准

| 属性 | 内容 |
|------|------|
| **文档版本** | v0.1 |
| **适用范围** | P0 本地工坊 MVP |
| **完成定义** | 下文 **AC-01～AC-06** 全部通过 |
| **关联** | `CHARTER.md` §8、`PRD-MVP.md` §12 |
| **更新日期** | 2026-05-19 |

---

## 1. 验收原则

1. **真实数据**：至少 3 次不同旅行素材，非虚构样张。  
2. **可复现**：记录 `tripId`、模板版本、`trip.json` version、日期。  
3. **可演示**：每条 AC 保留截图或 zip 路径（本地即可）。  
4. **人工闸口**：须走 G1（结构）与 G3（隐私）；G2 可合并到预览改字。

---

## 2. 发布闸门（必须全部 ☑）

| ID | 标准 | 验证方法 | 通过 |
|----|------|----------|------|
| **AC-01** | 用 **3 次真实旅行** 各生成 1 篇可导出游记 | 3 个 `trips/{id}/` 均有 `index.html` + zip | ☐ |
| **AC-02** | 平均从导入到「愿导出」**< 20 分钟** | 记录 3 次起止时间取平均 | ☐ |
| **AC-03** | 至少 **2 篇** 愿发给非开发者朋友 | 对方能打开且正向反馈 | ☐ |
| **AC-04** | 至少 **1 篇** 含短视频且循环/ poster 正常 | 含 `type:video` 的 trip | ☐ |
| **AC-05** | 导出 zip 在 **另一台手机微信** 内可读 | 传 zip → 解压或托管链接 → 滑动浏览 | ☐ |
| **AC-06** | 导出展示图 **无精确 home GPS** EXIF | 抽检导出 jpg/webp EXIF | ☐ |
| **AC-07** | 「保存长图」得到竖版 PNG，并 **发到微信群** 群友可读（无需链接） | 保存 → 发群 → 他人反馈 | ☐ |

**MVP 完成**：上表 **AC-01～AC-07** 全部为 ☑。

**AC-07 推荐路径（2026-05）**：`travelogue serve` → `index-longshot.html` → 隐藏/编辑图注 → **按章 2×** 导出 → 发微信群。

---

## 3. 功能验收矩阵（按需求 ID）

### 3.1 Trip 与导入

| 需求 ID | 验收步骤 | 通过 |
|---------|----------|------|
| F-TRIP-01 | `trip new` 生成 `trips/{tripId}/` 与合法 `trip.json` | ☐ |
| F-TRIP-02 | `pipeline.status` 随流程变化且可 `status` 查看 | ☐ |
| F-TRIP-03 | 能列出并重新打开历史 trip | ☐ |
| F-ING-01 | jpg/png/heic/webp 可导入 | ☐ |
| F-ING-02 | 原图在 `source/`，不破坏相册原目录 | ☐ |
| F-ING-03 | 有/无 EXIF 均不崩溃 | ☐ |
| F-ING-04 | >250 张提示拒绝或分批 | ☐ |
| F-ING-05 | mp4/mov ≤15s 可导入 | ☐ |
| F-ING-06 | 生成 w800/w1600 WebP | ☐ |

### 3.2 策展

| 需求 ID | 验收步骤 | 通过 |
|---------|----------|------|
| F-CUR-01 | 跨天自动分章候选 | ☐ |
| F-CUR-02 | 地点为城市级字符串 | ☐ |
| F-CUR-03 | 连拍去重后数量减少 | ☐ |
| F-CUR-05 | 3–5 章且 `patternId` 合法 | ☐ |
| F-CUR-06 | 提供 3 封面候选并可改 `coverAssetId` | ☐ |

### 3.3 叙事

| 需求 ID | 验收步骤 | 通过 |
|---------|----------|------|
| F-NAR-01 | title/hook 符合 manifest 字数 | ☐ |
| F-NAR-03 | 切换 tone 可重生成 | ☐ |
| F-NAR-05 | 无禁用词表命中 | ☐ |
| F-NAR-06 | 不合规 JSON 被拒绝或自动修 | ☐ |

### 3.4 视频

| 需求 ID | 验收步骤 | 通过 |
|---------|----------|------|
| F-VID-01 | 循环片段 3–8s 静音 | ☐ |
| F-VID-04 | trip 内 ≤3 视频 | ☐ |

### 3.5 编辑与导出

| 需求 ID | 验收步骤 | 通过 |
|---------|----------|------|
| F-ED-03 | 改字后重渲染生效 | ☑ · `serve` 保存后 auto re-render（`--no-rerender` 可关） |
| F-ED-04 | 浏览器可预览 | ☐ |
| F-EXP-01 | 相对路径、离线可开 | ☐ |
| F-EXP-02 | 无 JS 仍可阅读主内容 | ☐ |
| F-EXP-03 | `preview.jpg` 9:16 存在 | ☐ |
| F-EXP-04 | zip 解压即 `index.html` | ☐ |
| F-EXP-05 | 未 `privacy.confirmedAt` 不可 export | ☐ |
| F-EXP-07 | 点击「保存长图」下载竖版 PNG；**screens trip 用 `index-longshot.html`**；须 `travelogue serve`（非 file://）；支持按章 + 隐藏图注 | ☐ |
| F-EXP-07b | 默认 export zip 含 longshot bundle；`--no-longshot` 可剔除 | ☐ |

---

## 4. 模板与渲染验收

| ID | 标准 | 通过 |
|----|------|------|
| T-01 | `templateId` 为 `visual-journal` | ☐ |
| T-02 | 手机宽 <768px：9:16 + overlay 标题 | ☐ |
| T-03 | Web ≥768px：16:9 + 标题在图下 | ☐ |
| T-04 | `exportLayout: mobile` 强制竖版意图 | ☐ |
| T-05 | 主图 `srcset` 或等价多档（实现后） | ☐ |
| T-06 | 视频章不违反 manifest（封面无视频等） | ☐ |
| T-07 | 有语音时展示 voice-bar；转写可折叠 | ☐ |
| T-08 | `layoutEngine=screens` 时章内为 `layout-screen--16x9` | ☑ · `tests/test_dual_layout_engine.py` |
| T-09 | 竖三列 `screen-portrait-3` 使用 **cover** 拼满 | ☑ · `golden-web-screens.html` |
| T-10 | 单屏 ≤9 张，横/竖 4·9 宫格可触发 | ☑ · `tests/test_screen_layout_planner.py` |
| T-11 | `layout` 闸口展示屏级摘要（`format_layout_summary`） | ☑ |
| T-12 | legacy 与 screens 双引擎 CI 回归不互损 | ☑ · `tests/test_dual_layout_engine.py` |

对照金样例：`templates/visual-journal/golden.html`（legacy）、`golden-web-screens.html`（screens）。

**Web A/B 真图**：`.\scripts\compare-web-layout.ps1 trips\<id>` → `index-legacy.html` vs `index-screens.html`。

---

## 5. Agent 流水线验收

| ID | 标准 | 通过 |
|----|------|------|
| A-01 | 未 `structure_locked` 时 `narrate` 被拒绝 | ☐ |
| A-02 | Agent 不输出 HTML 字符串到 trip.json | ☐ |
| A-03 | `edited: true` 字段重跑 narrative 不覆盖 | ☐ |
| A-04 | 同 trip.json 重渲染 HTML 一致 | ☐ |
| A-05 | 分批 ingest 产生 `ingestBatchId`（实现后） | ☐ |

---

## 6. 非功能抽检

| ID | 标准 | 通过 |
|----|------|------|
| NF-01 | 30 图 trip 的 zip < 25MB（可配置） | ☐ |
| NF-02 | 封面图 < 500KB | ☐ |
| NF-03 | `config.yaml` 与 Key 未进入 git | ☐ |
| NF-04 | Chrome + 微信内置浏览器 smoke test | ☐ |

---

## 7. 验收记录表（每次真实 trip）

复制下表填写 3 次：

| 字段 | Trip 1 | Trip 2 | Trip 3 |
|------|--------|--------|--------|
| tripId | | | |
| 素材张数 / 视频数 | | | |
| 导入耗时 | | | |
| G1 后删图数 | | | |
| 叙事耗时 | | | |
| 总耗时（导入→愿导出） | | | |
| 是否愿分享 | | | |
| AC-04 含视频 | | | |
| 备注 | | | |

**Trip 1 林芝（进行中）**：见 [acceptance-records/linzhi.md](./acceptance-records/linzhi.md)。

---

## 8. 缺陷分级（验收期间）

| 级别 | 定义 | 是否阻断 MVP |
|------|------|----------------|
| P0 | 无法完成导入/渲染/导出；隐私泄漏 | 是 |
| P1 | 版式严重错乱、文案幻觉地点 | 是 |
| P2 | 样式细节、单张图失败 | 否，记 backlog |
| P3 | 文案润色、动效 | 否 |

---

## 9. 签字（自用）

| 角色 | 姓名 | 日期 | 结论 |
|------|------|------|------|
| 产品/负责人 | | | 通过 / 不通过 |

---

## 10. 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1 | 2026-05-19 | P0 验收清单，对齐 visual-journal v0.2 |
