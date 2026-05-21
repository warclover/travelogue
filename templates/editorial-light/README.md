# Editorial Light 模板 · v0.1 线框

## 预览

在资源管理器中双击打开，或：

```bash
start "" "C:\Users\xiafe\projects\travelogue\templates\editorial-light\wireframe.html"
```

## 文件

| 文件 | 说明 |
|------|------|
| `wireframe.html` | 可浏览的完整页面线框（示例：京都五日） |
| `wireframe.css` | 线框样式（虚线框 + 块标签，非最终视觉） |
| `BLOCKS.md` | 17 个块的字段、约束、验收说明 |
| `manifest.json` | Pattern 与全局 limits（供 Agent / 渲染器校验） |

## 下一步

1. 用真实旅行照片替换占位，验证节奏是否仍顺眼  
2. 定稿 `trip.json` schema（与 `data-block` 一一对应）  
3. 从线框 CSS 拆出 `tokens.css` + 正式 `layout.css`（去掉 `.wf-*`）
