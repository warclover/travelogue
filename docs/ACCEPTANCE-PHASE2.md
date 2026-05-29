# Travelogue · Phase 2 验收标准

> **单轨入口**：[ACCEPTANCE.md](./ACCEPTANCE.md) · 当前发布闸门：[ACCEPTANCE-PHASE5.md](./ACCEPTANCE-PHASE5.md)

| 属性 | 内容 |
|------|------|
| **文档版本** | v0.3.1 |
| **完成定义** | AC-P2-01a/b～06 + NR-P2-01；M8a+M8b+M9+M10 Done |
| **更新日期** | 2026-05-27 |

---

## 1. 验收原则

1. **受测者**：非项目维护者；**未读过 WORKSHOP**；**未使用过 travelogue CLI**。  
2. **启动方式（M8）**：受测者 **双击 `scripts/start-studio.bat`**；之后 **仅 Web**（AC-P2-03）。维护者仅负责首次双击，不代操作 Studio 内步骤。  
3. **数据**：≥2 次真实相册（1 次 ≤80 张；1 次可触发 **高度 >5000px** 或 **章 >60 卡** 分段）。  
4. **照片上限**：验收相册 ≤ **250** 张（Studio 技术上限；推荐 sweet spot 50–100 张）。  
5. **NR-P2-01**：每个 Phase 2 PR 合并前全量 pytest 0 失败。

---

## 2. 发布闸门

| ID | 标准 | 里程碑 | 通过 |
|----|------|--------|------|
| **AC-P2-01a** | 双击 bat → Studio Web → 看到预览 **≤ 5 分钟** | **M8b** | ☐ |
| **AC-P2-01b** | 全流程（选图→改字→**UI 长图**→找到 PNG→发微信）**≤ 20 分钟** | **M9** | ☐ |
| **AC-P2-02** | 服务端 PNG 发微信群可读 | **M9** | ☐ |
| **AC-P2-03** | 受测者不输入 PowerShell/CLI；仅双击 bat + Web | **M8b** | ☐ |
| **AC-P2-04** | 第二次打开 → **最近链接（M8）或 trip 列表（M10）** → 继续编辑 | M8/M10 | ☐ |
| **AC-P2-05** | 无 LLM Key → stub 全流程 | M8+ | ☐ |
| **AC-P2-06** | zip 仅「高级导出」 | **M10** | ☐ |
| **NR-P2-01** | 全量 pytest 0 失败 | 每 PR | ☐ |

---

## 3. 性能闸门（权威定义 · PRD §12.2 引用此处）

| ID | 标准 | 条件 | 通过 |
|----|------|------|------|
| **PF-P2-01** | 相册 → 预览 | ≤250 张 stub | ≤ **3 分钟** | ☐ |
| **PF-P2-01b** | 首次预览 | AC-P2-01a | ≤ **5 分钟** | ☐ |
| **PF-P2-02** | export-longshot（CLI） | scale=**1** | ≤ **25 秒** | ☐ |
| **PF-P2-02b** | export-longshot 高清 | scale=2 | ≤ **60 秒** | ☐ |
| **PF-P2-02c** | Studio UI 默认长图 | scale=**2** | ≤ **40 秒** | ☐ |
| **PF-P2-03** | Studio 冷启动 → `/` | | ≤ **3 秒** | ☐ |

---

## 4. 长图（M9）

| ID | 标准 | 通过 |
|----|------|------|
| **LS-P2-01** | 5 真实 trip · P0 成功率 ≥80% | 运行 `python scripts/phase2_longshot_stability.py <trips>` | ☐ |
| **LS-P2-02** | P1 触发时有 **F-LNG-10** UI 文案 | ☐ |
| **LS-P2-03** | 高度 >5000px → 按章；无 OOM | ☐ |
| **LS-P2-04** | 预览页 **UI 长图按钮** → 成功 **路径面板**（非仅 toast） | ☐ |
| **LS-P2-05** | 「在文件夹中显示」经 **`POST /reveal`** 打开 explorer | ☐ |

---

## 5. Studio UX（M8）

| ID | 标准 | 通过 |
|----|------|------|
| **UX-P2-01** | 空态：价值主张 + 样例长图 + 特性标签 | ☐ |
| **UX-P2-02** | stage 文案含预估时间（如「约 1–2 分钟」） | ☐ |
| **UX-P2-03** | 预览页 **← 返回工作台** 可回到 `/` | ☐ |
| **UX-P2-04** | 编辑提示条可见（可 dismiss）；受测者能改标题 | ☐ |
| **UX-P2-05** | >100 张照片导入前出现 soft warning | ☐ |
| **UX-P2-06** | **`index-longshot.html` 无 Studio Chrome 注入** | ☐ |

---

## 6. 功能矩阵（摘要）

| ID | 要点 |
|----|------|
| F-STU-06 | M8：`GET /trips` + 最近链接；M10：列表 UI |
| F-STU-10～14 | Studio Chrome、空态、stageHint、照片软引导 |
| F-LNG-05 | **M9** 最小长图按钮；**M10** 完整 toolbar |
| F-LNG-09 | CLI scale=1；Studio UI scale=2 默认 |
| F-LNG-11 | M9 成功路径面板 |
| F-LNG-04 | 高度/60 卡分段（非固定 45） |
| F-LNG-10 | P1 兼容模式 UI 提示 |
| F-NAR-P2-04 | **M10** stub 图注 |

---

## 7. 里程碑增量（M8 → M9 → M10）

| 项 | M8 | M9 | M10 |
|----|-----|-----|-----|
| Job cancel | Ctrl+C 免责 | 同左 | `POST /cancel` + `cancelled` |
| pipeline | 线程 + sleep(0) | 同左 | 子进程 |
| trip UI | 极简链接 + 返回 Chrome | 同左 | 完整列表 |
| 长图 | — | **最小按钮 + 路径面板** | 完整 toolbar + stale 提示 |
| zip | — | — | 高级导出 |
| stub 图注 | — | — | **F-NAR-P2-04** |

---

## 8. 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.2.1 | 2026-05-27 | bat 入口；250 张；性能闸门权威化；F-LNG-10 |
| v0.3 | 2026-05-27 | AC 里程碑拆分；M9 长图 UI/路径；Studio UX 闸门；PF-P2-02c |
| v0.3.1 | 2026-05-27 | M8a/b；UX-P2-06 allowlist；LS-P2-05 reveal；409 body |
