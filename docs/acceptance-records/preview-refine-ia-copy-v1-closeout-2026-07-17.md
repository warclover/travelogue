# 精修 IA / 导出合并 · 落地收口（2026-07-17）

| 属性 | 内容 |
|------|------|
| **线框** | [preview-refine-ia-copy-v1-wireframe.html](../wireframes/preview-refine-ia-copy-v1-wireframe.html) v1.2 · [export-settings-popover-v1-wireframe.html](../wireframes/export-settings-popover-v1-wireframe.html) v1.1 |
| **承接** | [IMPLEMENTATION-PREVIEW-REFINE-UX-V1.1.md](../IMPLEMENTATION-PREVIEW-REFINE-UX-V1.1.md) M2 演进 |
| **分支** | `feat/share-ready-optimization-v1-w0` |
| **关键提交** | `201f338` 三区 IA + ▾ copy；`e9fb363` 更多输出 + F5 文案 |
| **状态** | **工程落地完成** · 自动化绿 · 窄窗手测建议合入前再扫一眼 |

---

## 1. 定案对照

| 项 | 结果 |
|----|------|
| 精修三区：这页 \| 封面 \| 这本 | ✅ 顶栏无「导出」、无独立「封底」Tab |
| 封面区内分段封面 \| 封底 | ✅ bookends 挂封面 Tab；情境默认封底→封面+封底分段 |
| F5 人话表 | ✅ 空态/拼图/图说词/范围/清晰度等已对齐 |
| F6 文案范围必显（不弱化） | ✅ ▾「长图要不要字」+ 图注/导语；精修无第二套可写控件 |
| 更多输出 | ✅ ▾ 折叠 zip / 文件夹；这本·进阶仍可达阅读/放映/LLM |
| prefs / `copyDisplay` 单源 | ✅ 改 ▾ 同步 DOM；导出请求带当前值 |

---

## 2. 自动化证据

| 检查 | 结果 |
|------|------|
| `test_v4_preview_toolbar_playwright_smoke` | ✅ |
| `test_preview_toolbar_v3` + refine/bookends 相关单测 | ✅ |
| `test_arc14c_export_longshot_starts_from_dock` | ✅ |
| 手测脚本：▾ copy 同步 + 封底情境默认 + 长图 `copyDisplay` | ✅（2026-07-17） |

---

## 3. 合入前建议手测（约 10 分钟）

1. 滚到封底 → 开精修 → 落在「封面」且分段「封底」，可点缩略图  
2. ▾ 切「纯照片」→ 预览字层消失 → 再「带文字」+ 开关图注/导语  
3. 发微信群 → 确定 → 金色按钮导出 → 成功面可达  
4. 窄窗（≈360）打开 ▾：平台卡横排可读、无一字竖排  

---

## 4. 非目标（本拍未做）

- 顶栏第四 Tab「封底」  
- Dock 金色主 CTA 重做  
- 意图卡 / Output Recipe 人格卡改版  
