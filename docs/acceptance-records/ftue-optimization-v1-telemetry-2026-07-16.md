# FTUE Optimization V1 · 埋点补全与扫尾记录

| 属性 | 内容 |
|------|------|
| **日期** | 2026-07-16 |
| **分支** | `feat/ftue-optimization-v1-w0` |
| **对照** | [PRD-FTUE-OPTIMIZATION-V1.md](../PRD-FTUE-OPTIMIZATION-V1.md) v1.1.0 · §7 埋点 |

## 本轮补全

| 项 | 状态 |
|----|------|
| FE/BE allowlist：`ftue_demo_album_*` · `ftue_reveal_folder` · `longshot_success_share_hint_shown` · `help_funnel_reveal_folder` | ✅ |
| `ftue_demo_album_success` 在示例导入成功分支发射 | ✅ |
| `ftue_reveal_folder`：书架 / Task Dock / preview drawer | ✅ |
| demo 次钮对齐 PRD「重新生成（将覆盖）」 | ✅ |
| L0G 用户面「开始导入」→「开始制作」交叉扫尾 | ✅ |

## DoD 勾选（过程）

### W0

- [x] 线框 F1–F3/F7 已对照合入（代码）
- [x] 空态 / 向导示例路径合同测绿（人手狗粮仍建议补一次）
- [x] 中文 title → tripId 文件名单测
- [x] README 三步可见
- [x] 不宣称「仅 W0 = 主题完成」（W1 已合）

### W1

- [x] 线框 F4–F6 对照（发群以 Help 三要素为准）
- [ ] 人手 5 步狗粮第 4 步「敢发」（建议合并前再跑一次）
- [x] Help FirstSuccess 方案 A / L0 静态合同绿

### W2

- [x] BE-04 trips CLI > env > config + INFO
- [x] stub Copy 润色

### W3

- [ ] 便携包 / Installer 干净机手测（可选，不挡主链）

## 备注

`longshot_success_share_hint_shown` 此前 FE/BE 均有调用但不在白名单，属静默丢弃；本轮修复后可写入 `~/.travelogue/telemetry/studio-homepage-events.jsonl`。
