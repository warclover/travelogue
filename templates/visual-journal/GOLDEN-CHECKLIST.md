# Visual Journal 金样例验收清单

> 每次改 `journal.css` / `golden.html` 后勾选。对应 `docs/ACCEPTANCE.md` 模板项 T-01～T-07。

## 文件与角色

| 文件 | 用途 |
|------|------|
| `golden.html` + `golden.css` + `longshot.js` | 开发预览（顶栏 + 三态布局 + **保存长图**） |
| `golden-share.html` | 用户 zip 形态：`journal.css`、无 banner/script、`data-export="share"` |
| `golden-minimal.html` | 空状态：无 hook、无 lead、无 voice、无 caption |
| `cover-share.html` | `preview.jpg` 版式对照（`#cover-share-canvas` 1080×1920） |
| `journal.css` | **唯一**用户交付样式 |

生成命令：

```powershell
python C:\Users\xiafe\projects\travelogue\scripts\gen_demo_assets.py
python C:\Users\xiafe\projects\travelogue\scripts\gen_golden_variants.py   # share + minimal + cover-share
```

勿运行 `gen_golden_html.py`（已废弃，会覆盖手写 `golden.html`）。

---

## P0 · 结构与契约

- [ ] 四章 pattern：`open` / `moment` / `gallery` / `close` 各一章，无混搭
- [ ] 附录章 `chapter--appendix` 单独演示 `media-row`
- [ ] `gallery` 仅 `media-scroll`，章末无多余 `media-card`
- [ ] `open` 为 2×`media-card`，章内无 `media-row`
- [ ] 每章有 `data-chapter-id`、`data-pattern`；可选 `data-memory-anchors`
- [ ] 主图使用 `<img srcset>`，非 `background-image` 渐变
- [ ] `<html data-export="draft">`（golden）/ `share`（golden-share）
- [ ] 用户 zip 不含 `golden-banner`、布局切换脚本；**默认含** longshot bundle（`--no-longshot` 可关）
- [ ] `golden-share.html` 仍 **无** 长图脚本（私密 HTML / 小程序态参考，见 `SHARING.md`）
- [ ] 金样例 / draft 游记「保存长图」可导出 PNG（9:16 · 390px；横滑章纵向展开）
- [ ] `vendor/html2canvas.min.js` 已随仓库提交，离线可截（无需 CDN）

## P0 · 块与空状态

- [ ] `golden-minimal`：`hook-line:empty` 不占位
- [ ] 无 `chapter-lead` 时不撑高（`:empty`）
- [ ] 可无 caption、可无 `figcaption`/voice
- [ ] 视频卡有 `media-card--video` + 播放角标，无 voice-bar
- [ ] 语音 5 处：`voice-bar` + 折叠 `voice-transcript`（CSS 图标，非 emoji）

## P1 · 双形态

- [ ] 断点 768px / `48rem`：手机 9:16 overlay，Web 16:9 图下标题
- [ ] `data-layout="mobile|web"` 强制比例与配色
- [ ] `html[data-layout="web"]` 强制浅色纸感
- [ ] `media-scroll` 有 `scroll-snap`，横滑露半张

## P1 · 分享与封面

- [ ] `golden-share.html` 与 golden 正文 DOM 同构（仅去预览壳与 `data-editable`）
- [ ] `cover-share.html` 与 ADR `preview.jpg` 字段层级一致（地点 / 日期 / 标题 / hook）
- [ ] 首图 `loading="eager"`，其余 `lazy`

## 预览

```powershell
start "" "C:\Users\xiafe\projects\travelogue\templates\visual-journal\golden.html"
start "" "C:\Users\xiafe\projects\travelogue\templates\visual-journal\golden-share.html"
start "" "C:\Users\xiafe\projects\travelogue\templates\visual-journal\golden-minimal.html"
start "" "C:\Users\xiafe\projects\travelogue\templates\visual-journal\cover-share.html"
```

---

## 版本

| 日期 | 说明 |
|------|------|
| 2026-05-19 | v0.2.1 金样例：journal/golden 拆分、真实 WebP、share/minimal/cover-share |
