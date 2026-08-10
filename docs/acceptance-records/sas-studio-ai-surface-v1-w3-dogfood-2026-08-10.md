# SAS W3 狗粮与埋点收口 · 2026-08-10

| 属性 | 内容 |
|------|------|
| **主题** | Studio AI Surface V1 |
| **PRD** | v0.2.0 |
| **环境** | 本机 Studio `127.0.0.1:8766` · `TRAVELOGUE_AI_SURFACE=1` / 关闸对照 |
| **样册** | `demo-1bfe89d31c`（大理自驾精选）等 |
| **结论** | **W3 收口通过**（N≥5 会话勾选；不含 AC-SAS-08b） |

## 1. 会话清单（N≥5）

| # | 场景 | 结果 | 备注 |
|---|------|------|------|
| 1 | 开闸 · Dock 见 AI · 打开 Sheet | ☑ | 三层 IA 可见 |
| 2 | 勾选「优先 AI 手写体」不发请求 | ☑ | 网络面板无 title-art/narrate |
| 3 | 杂志文案确认 → 取消 | ☑ | 0 次 narrate |
| 4 | AI ↔ 精修互斥（含 Dock 可点修） | ☑ | `c3bca01c` / menu pointer-events |
| 5 | 关闸 · 诚实态 + 本机连接可开设置 | ☑ | 内联「了解如何开启」 |
| 6 | 精修「在 AI 中打开」深链 | ☑ | W2 |
| 7 | 意图卡 / 建议空态文案 | ☑ | 无 Agent 名；空态 COPY-SAS-05 |
| 8 | COPY-SAS-08 互链文案 | ☑ | AI Sheet + 精修双向 |

> 真实「生成杂志感 / 装帧 resolve / 重新解析」可选手跑（耗 API）；路径与确认框已验。

## 2. 埋点核对

| 事件 | 核对 |
|------|------|
| `ai_sheet_open` / `close` / `action_click` / `action_result` / `gate_view` | allowlist 单测 ☑ |
| `llm_narrate_click` + `source=ai_sheet` | 代码路径 ☑ |
| `has_badge` on open | 打开前采样 ☑ |

```powershell
python -m pytest tests/unit/web/test_sas_ai_sheet_wiring.py -q
```

## 3. 残留（不挡 Done）

| 项 | 说明 |
|----|------|
| AC-SAS-08b | 等 AIR voice |
| OQ-AIR-01 | 正式默认开闸另议 |
| 窄屏溢出菜单产品化 | SHD-SAS-05 已用隐藏文件夹缓解 |
