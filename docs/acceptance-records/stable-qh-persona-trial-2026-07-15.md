# Stable-QH · 典型用户实用试用（2026-07-15）

| 属性 | 内容 |
|------|------|
| **Studio** | `http://127.0.0.1:8768` |
| **方式** | Playwright UI + Import API（模拟 5 类典型用户） |
| **样片** | `C:\Users\xiafe\Projects\travelogue\templates\studio\assets\demo-album` |

## 画像与结果

| 画像 | 结果 | 细节 |
|------|------|------|
| 环境 | ✅ PASS | Studio http://127.0.0.1:8768; demo photos=6 |
| P1 首次旅行者 · 无 Key 主路径 | ✅ PASS | trip=qhtrial-p1-eb2232; preview=True; longshot_ui=True |
| P2 好奇试用者 · 示例转化 | ✅ PASS | convert_cta=True; wizard_open=True; upload=succeeded; trip=job-48682d9ec740 |
| P3 旁路精细偏好 | ✅ PASS | trip=job-889df0725aba; title_ok=True; place_ok=True; tpl_ok=True |
| P4 信任 · 取消与再导入 | ✅ PASS | cancel=200/purged=True; shells=[]; reimport=True; confirm=True |
| P5 回访 · 书架与词表 | ✅ PASS | shelf_cards≈22; bad_vocab=0; experimental=True; reopen_longshot=True |

## 剧本说明

1. **P1** 导入→预览卷轴→确认「长图」操作入口（不强制 PNG 落盘）。
2. **P2** 首页示例转化 CTA / Wizard 打开；上传小文件夹成册。
3. **P3** 精细 + 手动模板 + 自定义标题，成册后核对 trip.json。
4. **P4** 导入中取消→书架无空壳→同夹再导入成功。
5. **P5** 回访首页书架有册；无「长图待更新」；设置含「实验选项」。

## 残留（真人补签）

| 项 | 状态 | 说明 |
|----|------|------|
| 系统「选文件夹」原生对话框 | ☐ 待真人 | 本轮用 `TRUST_LOCAL_ALBUM` **粘贴路径**等价走通导入 |
| 长图 PNG 真导出 | ✅ 工程补签 | `POST /__travelogue/longshot` → trip=`qhtrial-p1-eb2232` · 朋友圈 7 张 PNG（`captureMethod=p0`） |
| ≥30s Importing 慢安抚墙钟 | ☐ 可选 | 源码接线已在 dogfood UX-QH-08 覆盖 |
| 真 LLM Key 文案气质 | ☐ 可选 | 本轮 forceStub |

### 长图补签细节（2026-07-15）

- Job `job-29f2adf8e87f` · `status=succeeded` · platform=`wechat_moments`
- 产出：`试用·周末短途-moments-01.png` … `07.png`（均落盘于 `trips/qhtrial-p1-eb2232/`）

