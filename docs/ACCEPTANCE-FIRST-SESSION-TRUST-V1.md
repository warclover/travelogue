# 首访可信体验优化 V1 · 验收清单

| 属性 | 内容 |
|------|------|
| **对应 PRD** | [PRD-FIRST-SESSION-TRUST-V1.md](./PRD-FIRST-SESSION-TRUST-V1.md) **v1.0.2** |
| **评审纪要** | [跨职能](./acceptance-records/first-session-trust-v1-review-2026-07-17.md) · [用户联席](./acceptance-records/first-session-trust-v1-user-panel-2026-07-17.md) · Conditional Go |
| **实施清单** | [IMPLEMENTATION-FIRST-SESSION-TRUST-V1.md](./IMPLEMENTATION-FIRST-SESSION-TRUST-V1.md) |
| **手测狗粮** | [first-session-trust-v1-dogfood-CHECKLIST.md](./acceptance-records/first-session-trust-v1-dogfood-CHECKLIST.md) · F1–F5 |
| **线框** | [wireframes/first-session-trust-v1-wireframe.html](./wireframes/first-session-trust-v1-wireframe.html) · F1–F5 |
| **状态** | **W0–W2 工程已合入** · 产品手测 / AC-FST-15 待签 · **不得对外宣布主题完成** |
| **日期** | 2026-07-17 |

> **验收原则**
>
> 1. 环境：Windows · Studio · Chrome/Edge；空态建议 `--trips-dir <空目录>`。  
> 2. W0 / W1 / W2 分门挡；**W0 ≠ 主题完成**。  
> 3. 默认成功面合同以本主题为准（**不教微信 · 不自动弹文件夹**）；Help H4 仅按需。  
> 4. 手测「产品」列须 **非实现者** 勾选。  
> 5. 主题对外宣布完成前：真人 N≥5（AC-FST-15 · USR-06）。

---

## 1. 里程碑完成度

| 里程碑 | 文档 | 编码 | 说明 |
|--------|------|------|------|
| **评审 + 线框 + AC/IMPL + 相邻脚注** | ✅ | — | 2026-07-17 |
| **W0** | ✅ 合同 | ✅ 工程 | 进度 · 终端 · 成功面（手测仍待） |
| **W1** | ✅ 合同 | ✅ 工程 | 敢秀底线（手测仍待） |
| **W2** | ✅ 合同 | ✅ 工程 | 封底「辑封」+ 张数同源（手测仍待） |
| **完成宣布** | ✅ 合同 | ⏳ | 真人 N≥5 · [dogfood](./acceptance-records/first-session-trust-v1-dogfood-CHECKLIST.md) |

---

## 2. W0 · AC-FST（自动化 + 手测）

| ID | 标准 | 方法 | 工程 | 产品手测 |
|----|------|------|------|----------|
| **AC-FST-01** | 离开 ingest 后主句不再仅为「已处理 N/N」 | 单测 `resolveImportStageCopy` + 手测 F1 | ✅ | ⏳ |
| **AC-FST-02** | 慢安抚出现时阶段主句仍可见 | 手测 F1（次行 DOM） | ✅ | ⏳ |
| **AC-FST-03** | 任一 stage 文案无变化 >8s → 狗粮失败 | 手测 + `import_stage_stall` 埋点 | ✅ | ⏳ |
| **AC-FST-04** | `succeeded` 后 ≤1s FirstSuccess；忙碌壳关闭 | **e2e 必锁** + 手测 F2 | ✅ | ⏳ |
| **AC-FST-05** | `refreshTrips` 失败不阻止 FirstSuccess | e2e 拖慢 trips + 代码审查 | ✅ | ⏳ |
| **AC-FST-06** | 长图开始后 >3s 不得仍以「0%」为唯一进度 | FE indeterminate + 手测 F3 | ✅ | ⏳ |
| **AC-FST-07** | 长图主句人话；无 Playwright/浏览器等工程词 | DOM 契约 + 手测 | ✅ | ⏳ |
| **AC-FST-08** | 长图 succeeded → 成功面可见 ≥3s 或至用户关闭 | Playwright + 手测 F4 | ✅ | ⏳ |
| **AC-FST-08b** | 成功时**不**自动 reveal；仅点击主钮后打开文件夹 | e2e/单测 + 手测 | ✅ | ⏳ |
| **AC-FST-08c** | 主操作可见文案「在文件夹中显示」且为实心主钮 | e2e + 手测 F4 | ✅ | ⏳ |
| **AC-FST-13** | 默认成功面无发群步骤教学句 | 文案断言 + 手测 | ✅ | ⏳ |

### W0 非回归

| ID | 标准 | 方法 | 工程 |
|----|------|------|------|
| **AC-FST-NR-01** | 空态/示例入口（FTUE）不回归 | 手测向导（dogfood NR-01） | ⏳ 手测 |
| **AC-FST-NR-02** | 无 Key 仍可示例成稿（L0） | 手测（dogfood NR-02） | ⏳ 手测 |
| **AC-FST-NR-03** | 不新建第四套成功面 Modal | 代码审查：复用 Task Dock / FirstSuccess | ✅ |

---

## 3. W1 · AC-FST

| ID | 标准 | 方法 | 工程 | 产品手测 |
|----|------|------|------|----------|
| **AC-FST-09** | 示例成片封面/开篇不含说明书腔（§4.5） | 单测 + 手测 F5 | ✅ | ⏳ |
| **AC-FST-10** | 读者面可见文案不含相机 Make/Model | 单测 + 手测 | ✅ | ⏳ |
| **AC-FST-11** | 无「*续」章名；符合时段/（n）一字面 | 单测 + 手测 | ✅ | ⏳ |
| **AC-FST-12** | 目录名噪音触发回退；封面 + FirstSuccess + 书架一致 | 单测 + 手测（噪音文件夹名） | ✅ | ⏳ |

---

## 4. W2 · AC-FST

| ID | 标准 | 方法 | 工程 | 产品手测 |
|----|------|------|------|----------|
| **AC-FST-14** | 封底不以「Colophon」为唯一眉题；张数与版面精选同源 | 契约单测 + 手测 | ✅ | ⏳ |

---

## 5. 主题完成门

| ID | 标准 | 方法 | 通过 |
|----|------|------|------|
| **AC-FST-15** | 真人 N≥5（建议含分享者 · 空态首访 · 家庭组织者）手测主链通过 | [dogfood CHECKLIST](./acceptance-records/first-session-trust-v1-dogfood-CHECKLIST.md) 非实现者签字 | ⏳ |

---

## 6. 手测入口

完整勾选表见：**[first-session-trust-v1-dogfood-CHECKLIST.md](./acceptance-records/first-session-trust-v1-dogfood-CHECKLIST.md)**（F1–F5 · W2 · 埋点抽查 · 签字栏）。

快速环境：

```powershell
cd C:\Users\xiafe\Projects\travelogue
$empty = Join-Path $env:TEMP "travelogue-fst-accept"
New-Item -ItemType Directory -Force -Path $empty | Out-Null
$env:TRAVELOGUE_STUDIO_TRUST_LOCAL_ALBUM = "1"
python -m travelogue studio --no-open --host 127.0.0.1 --port 8778 --trips-dir $empty
```

---

## 7. 与相邻验收的关系

| 主题 | 关系 |
|------|------|
| FTUE AC-FTUE-08～10 | **默认成功面 COPY** 以本清单 AC-FST-08/08b/08c/13 为准；FTUE 空态/示例 AC 不变 |
| Help AC-HELP-06a | 发群三要素改为 **Help 抽屉按需**；不再作为默认成功面拒收条件（见 Help PRD 脚注） |
| Share-Ready AC-SR-09 | 「第一可读行=发群三要素」**修订**为稳定成功确认；「换种分享方式」仍归 Share-Ready |

---

## 8. 签字

| 项 | 日期 | 结论 |
|----|------|------|
| 验收清单初稿 | 2026-07-17 | ✅ 文档 |
| W0 工程验收 | 2026-07-17 | ✅ 自动化 + 契约绿；产品手测待签 |
| W1 工程验收 | 2026-07-17 | ✅ 自动化 + 契约绿；产品手测待签 |
| W2 工程验收 | 2026-07-17 | ✅ 契约绿；产品手测待签 |
| 真人完成门 AC-15 | — | ⏳ |
