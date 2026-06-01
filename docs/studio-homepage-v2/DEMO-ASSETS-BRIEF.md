# demo-showcase · 京都·雨后 · 设计派单

> **M20-a 前置 Blocker** — 工程不得用占位 SVG 冒充最终素材进 dogfood。

---

## 1. 交付物清单

**Owner**：设计（待指派） · **Trip 源**：京都·雨后 golden trip（与产品选定同一篇）

| # | 资产 | 规格 | 路径 |
|---|------|------|------|
| 1 | 背景静帧 | WebP ≤180KB · 16:9 裁切 | `background.webp` |
| 2 | 长图 | WebP 9:16 全卷 | `longshot.webp` |
| 3 | Scroll 半页 | 每页 WebP · 16:9 **半页**（spread 左或右） | `scroll/{id}-{hash}.webp` |
| 4 | manifest | 符合 schema | `manifest.json` |
| 5 | 缩略 | 工作台 64px 级 | 可复用 cover webp |

**页序列（与 manifest.example.json 一致）**：

1. cover  
2. chapter ×3（Arrival / Alley / Farewell）  
3. epilogue  

→ **5 scroll 半页** · carousel **5 dots** · spread 尾页留白。

---

## 2. 视觉同源要求

- 16:9 scroll、9:16 longshot、background **同一 trip 导出**，禁止 Unsplash / 线框 SVG 上线
- 字体/配色与 Studio editor 输出一致
- 替换任意 webp 时 **递增 `manifest.version`** 并改文件名 hash

---

## 3. 验收

- [ ] `manifest.schema.json` 校验通过
- [ ] 总包 ≤800KB（PRD §12.3）
- [ ] 16:9 / 9:16 均可见 demo-flag（工程层）
- [ ] 设计 sign-off 截图归档 `docs/acceptance-records/`

---

## 4. 时间线（待 PM 确认）

| 里程碑 | 日期 | 阻塞 |
|--------|------|------|
| 切图包 v1 | **TBD** | M20-a 编码 |
| 修订 v2（若有） | M20-b 前 | carousel 真机 |

**临时**：工程可用 `manifest.example.json` + 线框 SVG **仅 dev**；dogfood 必须用真实 WebP。

---

## 5. 派单模板（复制发设计）

```
标题：M20-a demo-showcase「京都·雨后」统一切图包
截止：[DATE]
输出目录：templates/studio/assets/demo-showcase/
Schema：docs/studio-homepage-v2/DATA-CONTRACT.md §1
页数：5 half-pages + 1 longshot + 1 background
约束：WebP · hash 文件名 · 总包 ≤800KB · 与 PRD v2.0.3 示例标题一致
```
