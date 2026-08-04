# ADR-021 · 导出双引擎：Slice 叙事切片 + Compose 固定画布拼贴

| 属性 | 内容 |
|------|------|
| **状态** | 已采纳（实现中 · `feat/export-compose-redesign`） |
| **日期** | 2026-08-04 |
| **关联** | [ADR-016](./016-longshot-platform-export.md) · 导出系统重设计计划 |
| **影响范围** | `compose_canvas.py` · `collage_pack.py` · `poster_bric_pack.py` · `longshot.py` · Studio 导出面板 · Output Recipe |

---

## 背景

ADR-016 假设「一次 full canvas → 切分 / fit_aspect」即可覆盖朋友圈、小红书等平台。实测与产品定义不符：

- 小红书需要的是 **N 张竖版 3:4 拼贴海报**，不是杂志长卷截屏再压比例。
- 单张海报应对齐 **A4**；画册应对齐 **≈2.8:1 横版跨页**。
- 朋友圈与九宫格语义重复；Studio 只保留 **长图连读 ≤9 段**。
- 微信群长图行为正确，应冻结。

---

## 决策

### D1 · 用户可见五出口

| 出口 | platform | 引擎 |
|------|----------|------|
| 微信群 | `wechat_chat` | Slice-A（ADR-016 A，**零改**） |
| 朋友圈 | `wechat_moments` | Slice-B（长卷切分，不锁比例，不截断屏） |
| 小红书 | `xiaohongshu` | **Compose** 多页 3:4 |
| 单张海报 | `poster_bric` | **Compose** 单页 A4 |
| 画册印刷 | `album_spread` | **Compose** 多页 2.8:1 |

Studio **下线** `moments_grid`；CLI 暂留兼容。

### D2 · Compose 内核

- `compose_fixed_canvas`：bric 布局 → 固定画布 contain 居中。
- `collage_pack`：分页 + 多文件原子写（`PlatformExportWriter`）。
- **禁止** 对 Compose 目标走 Playwright full capture + `fit_aspect`。

### D3 · 相对 ADR-016

- Branch A：不变。
- Branch B：仅服务仍属「长卷切片」的平台（当前主路径：`wechat_moments`；Phase C CLI 可选保留）。
- `xiaohongshu` **迁出** Branch B，进入 Compose。
- Branch D / GCS：升级为 Compose 家族（poster / xhs / album）。

---

## 后果

- **正面**：出口语义与真实发帖/印刷物件对齐；拼贴复用一套内核。
- **负面**：旧 `*-xhs-*` 杂志切片与新拼贴海报同名前缀，需靠 job 产物与成功态区分。
- **迁移**：Output Recipe Ambiguous 卡仅「发群 / 朋友圈连读」；更多出口走导出设置面板。

---

## 版本记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1 | 2026-08-04 | 初稿并随 `feat/export-compose-redesign` 落地（编号 ADR-021，避开 Bookends ADR-017） |
