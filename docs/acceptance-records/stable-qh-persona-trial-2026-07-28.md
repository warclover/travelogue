# Stable-QH · 典型用户实用试用（2026-07-28）

| 属性 | 内容 |
|------|------|
| **Studio** | `http://127.0.0.1:8766` |
| **方式** | Playwright UI + Import API（模拟 5 类典型用户） |
| **样片** | `C:\Users\xiafe\Projects\travelogue\templates\studio\assets\demo-album` |

## 画像与结果

| 画像 | 结果 | 细节 |
|------|------|------|
| 环境 | ✅ PASS | Studio http://127.0.0.1:8766; demo photos=6 |
| P1 首次旅行者 · 无 Key 主路径 | ✅ PASS | trip=qhtrial-p1-f238e0; preview=True; longshot_ui=True |
| P2 好奇试用者 · 示例转化 | ✅ PASS | convert_cta=True; wizard_open=True; upload=succeeded; trip=job-5684425c038a |
| P3 旁路精细偏好 | ✅ PASS | trip=job-33adbbf0d09d; title_ok=True; place_ok=True; tpl_ok=True |
| P4 信任 · 取消与再导入 | ✅ PASS | cancel=200/purged=True; shells=[]; reimport=True; confirm=True |
| P5 回访 · 书架与词表 | ✅ PASS | shelf_cards≈18; bad_vocab=0; experimental=True; reopen_longshot=True |

## 剧本说明

1. **P1** 导入→预览卷轴→确认「长图」操作入口（不强制 PNG 落盘）。
2. **P2** 首页示例转化 CTA / Wizard 打开；上传小文件夹成册。
3. **P3** 精细 + 手动模板 + 自定义标题，成册后核对 trip.json。
4. **P4** 导入中取消→书架无空壳→同夹再导入成功。
5. **P5** 回访首页书架有册；无「长图待更新」；设置含「实验选项」。

## 残留（真人补签）

- 系统「选文件夹」对话框与微信发出长图 PNG：需真人。
- 大相册 ≥30s Importing 慢安抚墙钟目视：可选。
- 真 LLM Key 文案气质：本轮 forceStub，不评文案质量。
- 长图工程补签：见本文件「残留」表（`/__travelogue/longshot` → moments PNG）。

