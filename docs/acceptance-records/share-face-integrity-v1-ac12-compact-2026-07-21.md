# AC-SFI-12 · 紧凑档脚本门（仙本那）· 2026-07-21

| 属性 | 内容 |
|------|------|
| **AC** | AC-SFI-12（脚本半门） |
| **样本** | `trips/demo-1d4f92d534`（仙本那 · DES-SFI-01 真册） |
| **附件** | [default JSON](./attachments/sfi-ac12-semporna-default.json) · [compact 对比](./attachments/sfi-ac12-semporna-compact-compare.md) |
| **工程** | 紧凑档撤呼吸停顿 + 章头/封面/hook/辑封收紧；屏缝 4px 不动 |

## 脚本结果

| 指标 | 默认 | 紧凑 |
|------|------|------|
| 非照片纵向占比 | **11.3%** | **3.0%** |
| 相对降幅 | — | **73.2%** |
| 目标 | — | ≥40% ∧ ≤6.8%（基线×0.6） |
| **脚本门** | — | ✅ 通过 |

## 杠杆说明

真册默认档非照片纵向中，约十余处 `breath-pause-card`（各 ~120px）为主要可压空间。紧凑档：

1. 渲染层不再 `interleave_breath_items`，并跳过既有 `breath-pause` 项  
2. CSS 隐藏残留 breath；压 hook / 封面 panel / 辑封 padding  
3. 第 2 章起章头 ≤48px（既有）

屏缝 4px、首章全头、B2 组感（`preserve_stack`→徽标而非 flatten）保持。

## 仍开

- **5 席盲评**敢发偏好 ≥3/5（模板：[compact-blind-TEMPLATE](./share-face-integrity-v1-compact-blind-TEMPLATE.md)）  
- 产品手测 AC-SFI-13 / 狗粮 W0–W2  
- 主题完成门 AC-SFI-15
