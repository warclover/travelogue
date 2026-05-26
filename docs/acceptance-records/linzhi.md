# 验收记录 · linzhi（林芝）

| 属性 | 内容 |
|------|------|
| **tripId** | linzhi |
| **状态** | G1 已跑通 · AC-07 待发群确认 |
| **更新** | 2026-05-26 |

---

## 素材与流水线

| 项 | 值 |
|----|-----|
| 素材总数 | 231 assets |
| 进 screens / 长图 | 92 张 |
| 章数 | 4 |
| layoutEngine | screens |
| 叙事 | DeepSeek narrate（92 条 asset caption） |
| export zip | `trip-linzhi.zip`（~112 MB） |

---

## 耗时（待填）

| 阶段 | 耗时 |
|------|------|
| 导入 + curate | |
| layout | |
| narrate | ~28s（LLM） |
| render --dual | ~5s |
| export | ~3.5 min |
| **导入 → 愿导出** | |

---

## AC 自检

| ID | 项 | 状态 | 备注 |
|----|-----|------|------|
| AC-07 | 长图发微信群 | ☐ | 推荐：按章 2× + 隐藏不准图注 |
| AC-05 | 另一台手机开 zip | ☐ | |
| AC-06 | 导出图无精确 GPS | ☐ | |
| AC-03 | 愿分享给朋友 | ☐ | 图注需人工微调 |

---

## G2 文案修正工作流

```powershell
python -m travelogue serve trips/linzhi
# index-longshot.html：图注：关 / 编辑图注 / 删空图注 → skipCaption
python -m travelogue narrate linzhi --chapter-id ch-02 --regenerate --provider deepseek
```

- 删空图注 → `assets[].skipCaption=true`，narrate 不再重写
- inline 保存 → 自动 re-render sidecar（F-ED-03）

---

## 发群反馈（待填）

| 问题 | 反馈 |
|------|------|
| 能否读完 | |
| 图注是否干扰 | |
| 文件是否过大 | |
| 其他 | |
