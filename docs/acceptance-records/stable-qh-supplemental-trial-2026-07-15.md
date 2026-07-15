# Stable-QH · 补充试用（精修 stale / 慢安抚 / 老 trip）（2026-07-15）

| 属性 | 内容 |
|------|------|
| **Studio** | `http://127.0.0.1:8768` |
| **范围** | 精修→长图可更新；大相册慢安抚；本机 2 本老 trip |

## 结果

| 项 | 结果 | 细节 |
|----|------|------|
| 环境 | ✅ PASS | Studio http://127.0.0.1:8768 |
| 精修→长图可更新词表 | ✅ PASS | trip=qhtrial-p1-eb2232; intent_patch=200; api_stale=True; badge=1; resume_cta=1; bad_vocab=0; dock_hint=True |
| 大相册 Importing ≥30s 慢安抚 | ✅ PASS | job=job-0eb710b6f790; wall_s=29.8; hint_seen=True; hint='比预期久一些，请耐心等待…'; album_n=48; src_ok=True |
| 老 trip 回归 A | ✅ PASS | trip=demo-815dc906d3; title='兴义暑假精修版'; assets=249; preview=True; entry=True; longshot_ui=True; bad_vocab=False |
| 老 trip 回归 B | ✅ PASS | trip=demo-2025-9; title='2025东澳岛9'; assets=129; preview=True; entry=True; longshot_ui=True; bad_vocab=False |

## 说明

- **STALE**：先导长图，等待 >0.5s 宽限后再 PATCH 标题 bump `updatedAt`；书架/API 应出现「长图可更新」，且无「长图待更新」。
- **SLOW**：合成 48 张去重后仍唯一的图；Importing 面板在约 ≥30s 出现「比预期久一些，请耐心等待…」（见到后可 cancel）。
- **OLD**：抽 2 本本机已有 index 的 trip，验预览 HTML + 长图入口 + 无禁用词表。
