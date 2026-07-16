# IMPLEMENTATION · 新用户首次成功路径优化 V1

| 属性 | 内容 |
|------|------|
| **对应 PRD** | [PRD-FTUE-OPTIMIZATION-V1.md](./PRD-FTUE-OPTIMIZATION-V1.md) **v1.1.0** |
| **评审** | [acceptance-records/ftue-optimization-v1-review-2026-07-15.md](./acceptance-records/ftue-optimization-v1-review-2026-07-15.md) · Conditional Go · MF 已回写 |
| **线框** | [wireframes/ftue-optimization-v1-wireframe.html](./wireframes/ftue-optimization-v1-wireframe.html) · F1–F8 |
| **更新日期** | 2026-07-15 |
| **状态** | **W0 编码进行中**（2026-07-16 · 分支 `feat/ftue-optimization-v1-w0`） |
| **估时** | W0 ≈ **3 人日** · W1 ≈ **3–4 人日**（含 Help/Facade 回归） |

---

## 0. 波次摘要

| 波次 | 目标 | Go |
|------|------|-----|
| **W0** | 敢试：空态不灰 · 向导示例 · 文件名 · README | AC-FTUE-01～05b · 11 · 12 · R01 |
| **W1** | 敢发：成功面 · 发群 · 冷启动 · 系统句 · Dock tip | AC-FTUE-06～10 · 08′ |
| **W2** | trips 日志 · stub 用词 · Copy 会签 | 不挡主题主链 |
| **W3** | 便携包 / Installer 联调手测 | 可选 |

**所有权**：发群 / 脉冲 / FirstSuccess = **兑现** Help + Export Facade；本主题增量 = 空态 CTA · 示例一键 · 文件名 · 冷启动 stageHint · 能力卡字面覆盖。

---

## 1. W0 任务卡（Kickoff）

### 1.1 前端

| ID | 任务 | 建议锚点 | 估时 | AC |
|----|------|----------|------|-----|
| **FE-FTUE-01** | 无用户作品时 **不渲染** `#v2-bench-resume`（非 disabled） | `templates/studio/homepage-v2/bento.js` · `studio-home-v2.html` | 0.3d | 02 · R01 |
| **FE-FTUE-02** | 向导 pick：同屏「用示例照片试一次」→ `useDemoAlbum: true`；已存在 → 打开 / 重新生成（默认打开） | `import-wizard.js` · `import-run.js` · wizard CSS/HTML | 1.0d | 04 · 05 · 05b |
| **FE-FTUE-03** | 能力卡 §4.2 冻结 COPY；「其他导入」上传去「试用」 | `capability-card.js` · wizard 文案 | 0.3d | 03 |

### 1.2 后端

| ID | 任务 | 建议锚点 | 估时 | AC |
|----|------|----------|------|-----|
| **BE-FTUE-01** | 长图输出名改为 `{tripId}-ch{nn}.png`；中文 title 单测无 mojibake；UI 仍显示 title | `travelogue/export` / longshot 命名 · unit test | 0.6d | 11 |

### 1.3 文档

| ID | 任务 | 锚点 | 估时 | AC |
|----|------|------|------|-----|
| **DOC-FTUE-01** | README 顶部三步 + 折叠深链 | `README.md` | 0.2d | 12 |
| **DOC-FTUE-02** | WORKSHOP 可选依赖表（Playwright / HEIC / vision） | `docs/WORKSHOP.md` | 0.15d | 12 |
| **DOC-FTUE-03** | 空态狗粮命令 + trips 优先级 | `WORKSHOP` / `DEVELOPMENT` | 0.15d | — |
| **DOC-FTUE-04** | Installer F-INS-FIRST-01 → F-INS-FIRST-01′ | `PRD-DESKTOP-INSTALLER-V1.md` | 0.1d | — |
| **DOC-FTUE-05** | L0G / Help 交叉引用：能力卡 CTA → FTUE §4.2 | L0G ACCEPTANCE / Help §12.4 脚注 | 0.2d | — |

### 1.4 W0 完成定义

- [ ] 线框 F1–F3/F7 已对照合入  
- [ ] 空态 dogfood：无继续上次 DOM；向导可一键示例至 FirstSuccess  
- [ ] 中文 title 导出文件名无乱码  
- [ ] README 三步可见  
- [ ] **不**宣称「首访成稿主题完成」（发群在 W1）

### 1.5 W0 建议测试

```powershell
# 空态 Studio
$empty = Join-Path $env:TEMP "travelogue-ftue-w0"
New-Item -ItemType Directory -Force -Path $empty | Out-Null
$env:TRAVELOGUE_STUDIO_TRUST_LOCAL_ALBUM = "1"
python -m travelogue studio --no-open --host 127.0.0.1 --port 8771 --trips-dir $empty

# 单测（落地后补充具体模块名）
python -m pytest tests/unit -q -k "longshot_output_name or ftue or demo_album" --tb=line
```

手测：清 localStorage → F1 → F2 → 示例成稿 → 查 png 文件名。

---

## 2. W1 任务卡

| ID | 任务 | 建议锚点 | 估时 | AC |
|----|------|----------|------|-----|
| **FE-FTUE-04** | 成功面入口矩阵：Dock / 书架 / fallback 均 `resolvePublishGuide`；**不**新 Modal 栈 | `preview-toolbar-v3-task-dock.js` · `shelf-longshot.js` · `formatLongshotResult` | 1.2d | 08 · 08′ · 09 · 10 |
| **FE-FTUE-05** | 仅 Dock 脉冲+tip；文内「保存长图」降强调 | `help-onboarding.js` · `longshot.js` · visual-journal | 0.4d | Help 回归 |
| **FE-FTUE-06** | 导入进度吃 `preparing_vision` 等 stageHint | `import-run.js` | 0.3d | 07 |
| **FE-FTUE-07** | 封面 DOM 无系统句 | render 输出 / 预览断言 | 0.3d | — |
| **FE-FTUE-08** | FirstSuccess / 成功后「用自己的照片」转化句 | `first-success.js` | 0.2d | 转化探针 |
| **BE-FTUE-02** | stageHint 枚举与管线埋点 | `studio_pipeline` / jobs | 0.5d | 07 |
| **BE-FTUE-03** | example / bootstrap vision 默认 | `config.yaml.example` · desktop bootstrap | 0.2d | 06 |
| **BE-FTUE-05** | templateFeedback 不进 `meta.hook` | narrate / render | 0.4d | — |
| **BE-FTUE-06** | 书架 formatter 发群句对齐 | export format helpers | 0.4d | 09 |

### 2.1 W1 完成定义

- [ ] 线框 F4–F6 对照  
- [ ] 人手 5 步狗粮（评审纪要 §9）第 4 步「敢发」  
- [ ] Help FirstSuccess 方案 A / L0 无 Key 回归绿  

---

## 3. W2 / W3（后置）

| ID | 内容 | 波次 |
|----|------|------|
| **BE-FTUE-04** | trips：CLI > config；可选打日志；env 现状文档化 | W2 |
| stub「碎片」等用词 | Copy 会签 | W2 |
| 便携包手测 | 对齐 Installer Gate | W3 |

---

## 4. 埋点映射

| FTUE 事件 | 优先复用 |
|-----------|----------|
| 能力卡 CTA | 现网 `capability_card_cta`（action 扩展） |
| 成功面发群提示 | `longshot_success_share_hint_shown` |
| `ftue_demo_album_*` | 新增（向导示例漏斗） |
| `ftue_reveal_folder` | 新增或复用 reveal 既有事件 |

---

## 5. 风险与注意

| 风险 | 缓解 |
|------|------|
| 开发机 `vision: true` 误判 W0 变慢 | W0 狗粮用默认 / 显式关 vision |
| 只设 `TRAVELOGUE_TRIPS_DIR` 空态测不准 | **必须** `--trips-dir` |
| 文件名改 tripId 后用户找文件 | 成功面展示中文标题 + reveal |
| 与 L0G 字面双合同 | DOC-FTUE-05 同步脚注；以 FTUE §4.2 为用户面权威 |
| 示例去重与 FirstSuccess 漏接 | FE-02 含打开已有路径手测 |

---

## 6. 状态板（编码进度）

| ID | 状态 |
|----|------|
| FE-FTUE-01～03 | ✅ 代码已改（待狗粮手测） |
| BE-FTUE-01 | ✅ `default_longshot_output_name` → tripId |
| DOC-FTUE-01～03 | ✅ README / WORKSHOP |
| DOC-FTUE-04～05 | ✅ Installer / L0G / Help（评审回写时已改） |
| FE-FTUE-04～08 | ⬜ W1 |
| BE-FTUE-02/03/05/06 | ⬜ W1 |

---

## 7. 版本记录

| 日期 | 说明 |
|------|------|
| 2026-07-15 | 首版：对照 PRD v1.1.0 · Ready for Kickoff W0 |
