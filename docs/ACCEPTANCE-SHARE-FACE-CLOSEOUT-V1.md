# 敢发收口优化 V1 · 验收清单

| 属性 | 内容 |
|------|------|
| **对应 PRD** | [PRD-SHARE-FACE-CLOSEOUT-V1.md](./PRD-SHARE-FACE-CLOSEOUT-V1.md) **v1.0.1** |
| **评审纪要** | [跨职能](./acceptance-records/share-face-closeout-v1-review-2026-07-18.md) · Conditional Go |
| **实施清单** | [IMPLEMENTATION-SHARE-FACE-CLOSEOUT-V1.md](./IMPLEMENTATION-SHARE-FACE-CLOSEOUT-V1.md) |
| **手测狗粮** | [share-face-closeout-v1-dogfood-CHECKLIST.md](./acceptance-records/share-face-closeout-v1-dogfood-CHECKLIST.md) · F1–F5 |
| **线框** | [wireframes/share-face-closeout-v1-wireframe.html](./wireframes/share-face-closeout-v1-wireframe.html) · F1–F5 |
| **试用底稿** | [persona-ux-trial-2026-07-18.md](./acceptance-records/persona-ux-trial-2026-07-18.md) |
| **状态** | **W0 工程列绿** · 手测/狗粮待签 · W1/W2 未开工 |
| **日期** | 2026-07-18 |

> **验收原则**
>
> 1. 环境：Windows · Studio · Chrome/Edge；脏名用例建议独立 `--trips-dir`。  
> 2. W0 / W1 / W2 分门挡；**W0 ≠ 主题完成**。  
> 3. 本主题硬化 FST 敢秀底线、修订 QH stale 主词、修订 Sparse G1；**不**重验 Recipe / 意图卡全案（见非回归）。  
> 4. 手测「产品」列须 **非实现者** 勾选。  
> 5. 对外宣布完成前：真人 N≥5（AC-SFC-15 · 建议含 U1 / U3 / U7）。

---

## 1. 里程碑完成度

| 里程碑 | 文档 | 编码 | 说明 |
|--------|------|------|------|
| **PRD + AC + IMPL + 线框** | ✅ 2026-07-18 | — | Doc 包 |
| **跨职能评审 + 相邻脚注** | ✅ 2026-07-18 | — | Conditional Go · BLK 已回写 |
| **W0** | ✅ 合同 | ✅ 工程 | 假句空槽 · 体面名 · vision_warmup |
| **W1** | ✅ 合同 | ⏳ | stale 人话 · Sparse G1 · 章名续 · 无 Key 预期 |
| **W2** | ✅ 合同 | ⏳ | 「照片类型」词表 |
| **完成宣布** | ✅ 合同 | ⏳ | 真人 N≥5 |

---

## 2. W0 · AC-SFC（敢秀 + 不假死）

| ID | 标准 | 方法 | 工程 | 产品手测 |
|----|------|------|------|----------|
| **AC-SFC-01** | forceStub / 示例成片：PRD §4.2 禁词命中数 = 0（含竖幅 / 抬头看见 / 弱枚举） | 单测 fixture + 手测 F2 | ✅ | ⏳ |
| **AC-SFC-02** | 可见图注不得整册复读杂志全名填坑（同屏 ≥3 张完全相同且=杂志名 → 失败） | 单测 / DOM 扫描 + 手测 F2 | ✅ | ⏳ |
| **AC-SFC-03** | 脏名 fixture（`2025东澳岛9`、`武大--米娜`）→ 封面与书架无裸 `--`、无尾数字目录腔 | FE/BE humanize 同测 + 手测 F3 | ✅ | ⏳ |
| **AC-SFC-04** | 人为延长 vision 准备：UI ≥1s 内出现「正在准备识图」类主句；stage/hint 不得双空 >1s | `TRAVELOGUE_SFC_VISION_WARMUP_DELAY_MS` 注入 + 手测 F1 | ✅ | ⏳ |
| **AC-SFC-05** | vision 失败 / 离线仍可 `succeeded` 成稿；有一次人话降级说明 | `_vision_downgrade_notice` → clusterNotice toast + 手测 | ✅ | ⏳ |

### W0 非回归

| ID | 标准 | 方法 | 工程 |
|----|------|------|------|
| **AC-SFC-NR-01** | Ambiguous 意图卡三选一仍可用 | 手测 / 既有 recipe e2e | ⏳ |
| **AC-SFC-NR-02** | Narrative「按章导出」CTA 仍可用 | 手测大册 | ⏳ |
| **AC-SFC-NR-03** | 不新建第四套进度/成功面栈 | 代码审查：复用 Importing / Dock | ⏳ |

---

## 3. W1 · AC-SFC（少打断 + 人话）

| ID | 标准 | 方法 | 工程 | 产品手测 |
|----|------|------|------|----------|
| **AC-SFC-06** | 用户面主词仅「分享图需更新」；无「长图可更新 / 待更新 / 已过期」作主词 | 全文/DOM 扫描 + 手测 F4 | ⏳ | ⏳ |
| **AC-SFC-07** | demo-album（及新 stub 成片）无「×日续」章名 | 单测 + 手测 F2 | ⏳ | ⏳ |
| **AC-SFC-08** | `kept_n≤9` 快速分享默认设置：无 G1 阻断横幅 | e2e + 手测 F5 | ⏳ | ⏳ |
| **AC-SFC-09** | 设置开启「导入后先确认章节」后，Sparse 仍可出现 G1 | 手测 F5 | ⏳ | ⏳ |
| **AC-SFC-11** | FirstSuccess 无 Key 无「杂志文案已完成」类承诺 | 文案断言 + 手测 | ⏳ | ⏳ |

---

## 4. W2 · AC-SFC（精修词表）

| ID | 标准 | 方法 | 工程 | 产品手测 |
|----|------|------|------|----------|
| **AC-SFC-10** | 精修态可见标签无「媒资」；为「照片类型」或等价人话 | DOM 契约 + 手测 | ⏳ | ⏳ |

---

## 5. 主题完成门

| ID | 标准 | 方法 | 通过 |
|----|------|------|------|
| **AC-SFC-15** | 真人 N≥5（建议 U1 分享者 · U3 空态首访 · U7 家庭组织者）主链通过 | [dogfood CHECKLIST](./acceptance-records/share-face-closeout-v1-dogfood-CHECKLIST.md) 非实现者签字 | ⏳ |

---

## 6. 禁词 / 脏名 fixture（W0 必锁）

| Fixture ID | 输入 / 场景 | 期望 |
|------------|-------------|------|
| **FX-SFC-01** | stub 句「示例游记的竖幅。」 | 不进分享面（空或替换） |
| **FX-SFC-02** | 「抬头看见示例游记。」 | 不进分享面 |
| **FX-SFC-03** | 「夜景，白天」/「白天，傍晚」 | 不进分享面 |
| **FX-SFC-04** | 文件夹 `武大--米娜` | 展示 `武大 米娜`（或更优用户标题） |
| **FX-SFC-05** | 文件夹 `2025东澳岛9` | 无裸尾数字目录腔上封面 |
| **FX-SFC-06** | 章名候选 `5月27日续` | 渲染为时段或 `5月27日（2）` |

---

## 7. 手测入口

完整勾选表见：**[share-face-closeout-v1-dogfood-CHECKLIST.md](./acceptance-records/share-face-closeout-v1-dogfood-CHECKLIST.md)**。

```powershell
cd C:\Users\xiafe\Projects\travelogue
$empty = Join-Path $env:TEMP "travelogue-sfc-accept"
New-Item -ItemType Directory -Force -Path $empty | Out-Null
$env:TRAVELOGUE_STUDIO_TRUST_LOCAL_ALBUM = "1"
python -m travelogue studio --no-open --host 127.0.0.1 --port 8780 --trips-dir $empty
```

浏览器：`http://127.0.0.1:8780/`。

---

## 8. 签字

| 角色 | 姓名 | 日期 | W0 | W1 | W2 | 备注 |
|------|------|------|----|----|----|------|
| 工程 | | | ☐ | ☐ | ☐ | |
| 产品（非实现者） | | | ☐ | ☐ | ☐ | |
| 设计 / UX | | | ☐ | ☐ | ☐ | 线框对照 |
