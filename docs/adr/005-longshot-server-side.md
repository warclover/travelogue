# ADR-005 · 服务端长图：captureMainToBlob 优先 + 分级 fallback

| 属性 | 内容 |
|------|------|
| **状态** | 已采纳（**v0.3 修订**） |
| **日期** | 2026-05-27 |
| **决策者** | 产品 + 技术负责人 |
| **影响范围** | `travelogue/export/longshot.py`、`cli.py`、Studio longshot Job |
| **关联** | [PRD-PHASE2.md](../PRD-PHASE2.md) §8、[SHARING.md](../SHARING.md) |
| **修订** | v0.1 禁止 screenshot；v0.2 增加 P1 fallback、scale 双默认、高度分段 |

---

## 背景

1. Phase 2 主分享路径：**服务端 PNG** → 微信直发。  
2. 理想路径：Playwright 加载 `index-longshot.html`，调用 `TravelogueLongshot.captureMainToBlob`（与 F-EXP-07 像素同源）。  
3. **风险**：`page.evaluate` 回传大 Blob（50MB+）可能失败；headless 下 `longshot.js` DOM 操作与有头浏览器不完全一致；目前仅 `longshot_smoke.py` 小规模验证。  
4. v0.1「禁止 screenshot」在 PRD 阶段堵死后路；评审改为 **分级 fallback**。

---

## 决策

### D1 · 三级捕获路径

| 优先级 | 路径 | 触发 |
|--------|------|------|
| **P0** | `captureMainToBlob` → base64 / bytes 回传 Python | 默认尝试 |
| **P1** | Playwright `locator('main').screenshot()`（390px viewport，**非** `full_page=True` 整文档） | P0 失败、blob 过大、超时 |
| **P2** | 客户端 html2canvas（F-EXP-07，`index-longshot.html` 手动或已有按钮） | Playwright 未安装；M9 前 interim |

**产品要求**：

- P1 触发时 **必须** 显示 UI 文案（F-LNG-10）：「已使用兼容模式导出，与预览可能有细微差异。」（不仅是日志）。  
- **Phase 2 完成前**：≥5 个真实 trip 上 P0 成功率 **≥80%**；否则不宣称「服务端长图主路径稳定」。  
- P0 稳定后，P1 保留为保底，不强制移除。

---

### D2 · HTTP 来源（v0.3.1 · Studio vs CLI 分支）

| 模式 | Playwright 访问 URL |
|------|---------------------|
| **Studio**（8766 已运行） | `http://127.0.0.1:{port}/{tripId}/index-longshot.html` — **复用现有 serve**，不再起第二个 HTTP |
| **CLI**（无 serve） | 临时 `ThreadingHTTPServer` 服务 trip 目录（与 `export/pdf.py` 同模式） |

`export/longshot.py` 接口：`export_longshot(trip_dir, *, base_url: str | None = None, port: int = 0)`。`base_url` 非空时跳过临时 server。

**M9 附加**：Playwright **browser 单例**（懒启动，60s 空闲自动 `close`），避免反复「保存长图」冷启动 3–5s。

### D3 · 分段规则（高度优先，张数兜底）

**不再**使用固定「45 张」作为唯一阈值（该数字来自客户端 html2canvas，不适用于服务端内存）。

| 条件 | 行为 |
|------|------|
| 单次 capture **预估或实际**输出高度 **≤ 5000px** | 单文件 `{title}-longshot.png` |
| 预估高度 **> 5000px** | **按章**多次 capture → `{title}-ch{nn}.png` |
| **兜底**：单章 media-card **> 60 张** | 强制按章（防极端竖图堆叠） |

**禁止**：Python 侧拼接超长单图。

产品文案仍可写「图多时多张发微信」（与客户端 >45 禁用整篇 **语义** 一致，实现以高度为准）。

---

### D4 · scale 双默认（v0.3 · 微信场景）

| 项 | 值 |
|----|-----|
| **CLI** 默认 `--scale` | **1**（390px 宽；CI / 开发者快路径） |
| **Studio UI** 默认 | **2**（780px 宽；标注「推荐 · 适合手机」） |
| 可选 | `--scale 3` 标注「超高清 · 较慢」 |
| 性能目标 | CLI scale=1 **≤ ~25s**；Studio scale=2 **≤ ~40s**（PF-P2-02c） |

**理由（v0.3 修订）**：390px 在 2026 年主流手机全屏阅读偏糊；scale=2 体积仍远低于微信 25MB 限制，清晰度显著提升。CLI 保持 scale=1 以缩短自动化与调试时间。

---

### D8 · 按章 PNG 页码水印（P2 · backlog）

按章导出时，可选在 PNG 底部叠加半透明页码（如 `2/5`），便于微信多图发送时群友识别顺序。实现：`longshot.py` Pillow 后处理；**不**阻塞 M9。

---

### D5 · 客户端 html2canvas

| 路径 | 角色 |
|------|------|
| P0/P1 服务端 | Phase 2 **主验收**（AC-P2-02） |
| P2 客户端 F-EXP-07 | Playwright 不可用时的 Plan B；AC-07 回归 |

---

### D6 · 隐私

长图 / Studio 按钮：**不** 要求 `privacy.confirmedAt`。zip 高级导出仍要求。

---

### D7 · CLI

| 项 | 值 |
|----|-----|
| 命令 | `travelogue export-longshot <trip>` |
| 默认 | `--scale 1` · `--format png`（Studio UI 默认 scale=2，见 D4） |
| 依赖 | `travelogue[playwright]` + `playwright install chromium` |
| 失败 | `E_LNG_PLAYWRIGHT` + 中文指引；可提示 P2 客户端路径 |

---

## 后果

### 正面

- P0 追求像素一致；P1 降低交付风险。  
- Studio scale=2 默认提升手机阅读清晰度；CLI scale=1 保留快路径。  
- 高度分段比固定张数更鲁棒。

### 负面

- P0/P1 输出可能有细微像素差异；需日志区分。  
- 按章多张 PNG 需 UI 说明（路径面板 + 可选页码水印）。

---

## 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1 | 2026-05-27 | 初稿：仅 captureMainToBlob；固定 45 张；scale=2 |
| v0.2 | 2026-05-27 | fallback 分级；scale=1；高度分段 |
| v0.2.1 | 2026-05-27 | F-LNG-10 兼容模式 UI 提示（必选） |
| v0.3 | 2026-05-27 | scale 双默认；Studio 路径面板；页码水印 P2 |
| v0.3.1 | 2026-05-27 | D2 base_url 分支；Playwright browser 单例 |
