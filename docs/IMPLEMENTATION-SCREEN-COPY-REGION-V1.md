# IMPLEMENTATION · 屏级文案区 V1（SCR）

| 属性 | 内容 |
|------|------|
| **PRD** | [PRD-SCREEN-COPY-REGION-V1.md](./PRD-SCREEN-COPY-REGION-V1.md) **v0.2.0** |
| **验收** | [ACCEPTANCE-SCREEN-COPY-REGION-V1.md](./ACCEPTANCE-SCREEN-COPY-REGION-V1.md) |
| **评审** | [scr-screen-copy-region-v1-review-2026-08-04.md](./acceptance-records/scr-screen-copy-region-v1-review-2026-08-04.md) |
| **DOC-STATUS** | **active** |
| **更新日期** | 2026-08-04 |

> M0 文档已齐。M1 编码可 Kickoff；合码 Done 前关闭 **BLK-SCR-03～06**。

---

## M0（文档）✅

| 任务 | 状态 |
|------|------|
| PRD v0.2.0 七席回写 | ✅ |
| ACCEPTANCE / IMPLEMENTATION 拆文 | ✅ |
| DOC-STATUS / README 登记 | ✅（随合入） |

---

## M1 切片（建议 PR 序）

### PR-A · 合同与通用 enrich（BLK-05/06 基础）

| 任务 | 说明 |
|------|------|
| LTE schema | 增加可选 `textRegions[]`（maxItems 2） |
| `screen-landscape-1.yaml` | 声明 body/band-bottom（**BLK-03**） |
| L4/L6 lint | 禁止非空 textRegions（可先单测，CI 正式门可 M2） |
| `context.py` | `_enrich_editorial_4mix_copy` → 通用 `_enrich_screen_copy_regions`（按 textRegions / 兼容 4mix presentation） |
| 焦点显现 | draft 空占位仅焦点/加字；读者空隐（**BLK-06**） |
| trip schema description | 泛化 copy 字段说明 |
| 配置 | `screen_copy_region.enabled` fail-loud 未知键 |

### PR-B · 长图 L1（**BLK-04**）

| 任务 | 说明 |
|------|------|
| flatten / longshot 组装 | 非空 `screens[].copy` → 插入 L1 文本块 |
| 顺序 | kicker → 槽卡片 → body（缺省跳过） |
| 尊重 | `copyDisplay` / Moments 强制 photos |
| 单测 | AC-SCR-06 / 08 |

### PR-C · 样式与狗粮

| 任务 | 说明 |
|------|------|
| landscape-1 overlay CSS | 轻量底栏；**勿**复用 4mix 棋盘 padding（F-13） |
| 4mix 回归 | 强制 pattern 工具链：空隐 + 焦点显现（**BLK-05**） |
| 狗粮 GUIDE | 可写屏发现 · Moments 预期说明（SHD-02） |
| AC-SCR-06b / 10 | 手测 + 几何 0px |

**禁止单 PR 塞满 A+B+C+M2。**

---

## M2（后置）

- airy mosaic 第二 SKU  
- Dock「本页文字」  
- AC-11～14  

## M3（延期）

- 单屏 AI 候选  
- absorb  
- AIR L3 联调分家单测强化  

---

## 合码红线

1. **D-SCR-12**：不得改 MCS/TPC 选版读 caption。  
2. **N-SCR-09**：不得借 SCR unpark 4mix。  
3. M1 Done = AC-01～10+06b 绿 + BLK-03～06 关。
