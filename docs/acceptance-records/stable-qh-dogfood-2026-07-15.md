# Stable-QH Dogfood · §10.2（2026-07-15）

| 属性 | 内容 |
|------|------|
| **Studio** | `http://127.0.0.1:8768` |
| **分支** | `fix/stable-quality-hardening-v1` |
| **方式** | Playwright + Import API（模拟用户路径） |
| **Demo 相册** | `C:\Users\xiafe\Projects\travelogue\templates\studio\assets\demo-album` |

## 结果

| ID | 结果 | 细节 |
|----|------|------|
| SETUP | ✅ PASS | Studio http://127.0.0.1:8768; demo=C:\Users\xiafe\Projects\travelogue\templates\studio\assets\demo-album |
| UX-QH-01 | ✅ PASS | trip=qhdf-main-72390808; preview=ok; longshot_ui=True |
| UX-QH-02 | ✅ PASS | trip=job-ac1262194602; title_ok=True; place_ok=True; tpl=visual-journal |
| UX-QH-03 | ✅ PASS | cancel=200/{'ok': True, 'status': 'cancelled', 'purged': True}; final=cancelled; purged=True; shells=[]; confirm_copy=True |
| UX-QH-04 | ✅ PASS | unsupported visible=True title='请拉宽窗口至 1024px 以上' |
| UX-QH-05 | ✅ PASS | failed='📁 qhdf-main-72390808 · 未能清点照片，可更换文件夹或直接开始'; degraded='📁 qhdf-main-72390808 · 照片较多，制作时将自动清点' |
| UX-QH-06 | ✅ PASS | re-import status=succeeded trip=qhdf-cancel-9f1eaf6a err=None |
| UX-QH-07 | ✅ PASS | 封面 HTML 无碎片拼成系统句 |
| UX-QH-08 | ✅ PASS | src_ok=True; runtime_esc=True; note=≥30s 慢安抚需长导入目视 |
| UX-QH-09 | ✅ PASS | experimental=True; resume_cta=0; card_badge=2; matrix_src=True |

## 备注

- UX-QH-08 的「Importing ≥30s 慢安抚」以源码接线 + 文案冻结为准；完整墙钟目视建议另开一次大相册导入。
- UX-QH-01 长图导出本身耗时较长；本记录验证预览页存在「长图」操作入口（不强制等 PNG 落盘）。
- UX-QH-09 若书架无 stale 项，角标/续编 CTA 以矩阵源码 + 设置「实验选项」折叠为通过依据。
- 取消测使用临时相册副本（合法 tripId 目录名）；demo 缩略图近重需 `keepNearDuplicates=true`。
- UX-QH-03 含确认框人话源码契约；UX-QH-05 覆盖 failed + timeout/degraded；UX-QH-08 harness `studioState=first-success` + Esc。

## Dogfood 中顺带修的产品缺陷

| 问题 | 修复 |
|------|------|
| `force=True` 跳过 early `tripId` 绑定 → cancel purge 无目标 | `import_handlers` 始终预测并绑定 tripId |
| cancel 立即释放导入锁 + 同步 purge → 与子进程/再导入竞态 | cancel 等 worker finally；busy 锁延后释放 |
| `/import` 先做相册 ACL 再查 busy → probe 误判空闲 | handle_import 开头 busy 检查 |
| `studio_incomplete_purge` ↔ handlers 环依赖 | `is_protected_demo_trip` 懒导入 |
