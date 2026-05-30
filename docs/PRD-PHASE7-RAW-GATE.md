# Travelogue · Phase 7 子专项 PRD（RAW 格式拦截与用户引导）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue |
| **文档版本** | v0.7.0-RAW-GATE |
| **状态** | Draft · 开发准入 |
| **所属阶段** | Phase 7（极速管线） |
| **专项代号** | P7-RAW-GATE · RAW 前置拦截 |
| **目标** | 不支持 RAW 解码；检测到 RAW 时即时提示用户先转 JPG 再重试，避免长等待和不确定失败 |
| **关联主文档** | [PRD-PHASE7.md](./PRD-PHASE7.md) |
| **关联验收** | [ACCEPTANCE-PHASE7.md](./ACCEPTANCE-PHASE7.md) |
| **更新日期** | 2026-05-30 |

---

## 1. 背景与问题

当前用户会将单反原片文件夹直接导入（常见为 `.cr2/.cr3/.nef/.arw/.dng`）。项目当前 ingest 只接受常见位图格式与 HEIC/HEIF。  
当文件夹中主要是 RAW 时，用户会出现两类体验问题：

1. 不知道为何“可识别照片数很少/为 0”；
2. 等待后才失败，感知为“算法不稳定”。

Phase 7 聚焦提速与稳定，RAW 直接拦截属于“低成本高收益”的确定性改进：
- 及时失败（fail-fast）；
- 明确下一步操作（转 JPG）；
- 降低支持成本与误判为算法故障。

---

## 2. 目标与非目标

### 2.1 目标

| ID | 目标 | 衡量方式 |
|----|------|----------|
| **G-RAW-01** | 识别并拦截常见 RAW 文件 | 预置后缀清单命中率 100%（测试样本） |
| **G-RAW-02** | 用户收到明确可执行提示 | Studio/CLI 提示包含“先转 JPG 再重试” |
| **G-RAW-03** | 快速失败，减少无效等待 | RAW-only 文件夹在扫描阶段即返回，不进入后续 ingest 编码 |
| **G-RAW-04** | 不影响非 RAW 主路径 | JPG/HEIC 正常流程不退化 |

### 2.2 非目标

- 本专项 **不支持** RAW 解码、色彩管理、去马赛克、镜头校正。
- 不引入 RAW 第三方解码依赖（如 `rawpy`）到默认主链路。
- 不做 RAW 到 JPG 的内置转码器（仅提示用户外部转换）。

---

## 3. 已拍板决策（D-RAW）

| ID | 决策 | 结论 |
|----|------|------|
| **D-RAW-01** | RAW 支持策略 | 默认不支持，明确拦截 |
| **D-RAW-02** | 拦截时机 | 在 `scan_image_paths` 阶段前置检测 |
| **D-RAW-03** | 用户反馈 | Studio 弹窗 + CLI 错误码与文本 |
| **D-RAW-04** | 文案策略 | 指令式文案：先转 JPG，再重试；附常见 RAW 后缀 |
| **D-RAW-05** | 兼容策略 | HEIC/HEIF 保持现状（已支持路径） |

---

## 4. 范围与规格

### 4.1 RAW 后缀识别范围（首版）

建议首版清单（全部小写比较）：

` .cr2 .cr3 .nef .nrw .arw .srf .sr2 .dng .rw2 .orf .raf .pef .x3f .kdc .erf .3fr .iiq `

> 后缀清单可配置扩展：`ingest.raw_blocklist_suffixes`

### 4.2 输入行为定义

| 场景 | 行为 |
|------|------|
| 文件夹仅 RAW | 立即失败并提示转 JPG |
| RAW + JPG 混合 | 默认失败并提示（避免“导入不全”的隐形风险） |
| 无 RAW，仅支持格式 | 正常进入现有扫描/ingest |

> 说明：混合场景默认也拦截，保证用户对“输入全集”的预期一致；如后续需要，可在 P7.1 引入“忽略 RAW 继续”高级开关。

### 4.3 错误码与提示文案

- 新增错误码：`E_INGEST_RAW_UNSUPPORTED`
- 推荐文案（Studio/CLI 统一语义）：
  - `检测到 RAW 原片格式（如 .CR3/.NEF/.ARW）。当前版本不支持 RAW，请先转换为 JPG 后重试。`
- 详情字段建议：
  - `rawCount`
  - `sampleRawFiles`（最多 5 个文件名）
  - `detectedSuffixes`

---

## 5. 用户体验设计（Studio / CLI）

### 5.1 Studio

- 在导入动作触发后、进入长流程前进行 RAW 检测。
- 命中后显示阻断型弹窗：
  - 标题：`暂不支持 RAW 原片`
  - 正文：`检测到 N 张 RAW 文件。请先转换为 JPG，再重新选择文件夹导入。`
  - 操作：`我知道了`（关闭）
- 不进入 ingest/curate/narrate/render 阶段，不创建半成品 trip。

### 5.2 CLI

- 返回非 0 退出码。
- 输出 `E_INGEST_RAW_UNSUPPORTED` 及简要修复建议。
- 支持 `--verbose` 时打印后缀统计与样例文件名。

---

## 6. 配置与数据模型

### 6.1 配置项新增

| 配置键 | 默认值 | 说明 |
|--------|--------|------|
| `ingest.reject_raw` | `true` | 是否启用 RAW 拦截 |
| `ingest.raw_blocklist_suffixes` | 见 §4.1 | RAW 后缀清单 |
| `ingest.raw_detect_sample_limit` | `5` | 错误消息中展示样例数量 |

### 6.2 telemetry 建议字段

- `ingestStats.rawRejectedCount`
- `ingestStats.rawRejectedSuffixes`
- `ingestStats.rawRejectedSampleFiles`

---

## 7. 实施任务（可拆）

| ID | 模块 | 动作 | 优先级 |
|----|------|------|--------|
| **RAW-T1** | `media/ingest.py` | 增加 RAW 后缀检测与错误抛出 | P0 |
| **RAW-T2** | `config.py` + `config.yaml.example` | 增加 `reject_raw` 与后缀清单配置 | P0 |
| **RAW-T3** | Studio pipeline | 捕获并映射 `E_INGEST_RAW_UNSUPPORTED` 到弹窗 | P0 |
| **RAW-T4** | CLI | 输出统一错误文案与建议 | P0 |
| **RAW-T5** | tests | 增加 RAW-only / RAW+JPG / JPG-only 三类测试 | P0 |
| **RAW-T6** | docs | 更新 FAQ 与导入指引 | P1 |

---

## 8. 验收标准（AC-RAW）

| ID | 通过条件 |
|----|----------|
| **AC-RAW-01** | RAW-only 文件夹导入时返回 `E_INGEST_RAW_UNSUPPORTED` |
| **AC-RAW-02** | RAW+JPG 混合文件夹默认同样阻断并提示 |
| **AC-RAW-03** | 提示文案明确包含“先转 JPG 后重试” |
| **AC-RAW-04** | 非 RAW 文件夹行为不变（回归通过） |
| **AC-RAW-05** | ingestStats 正确记录 RAW 命中信息 |

---

## 9. 测试用例（最小集）

### TC-RAW-01 RAW-only
- 输入：20 张 `.cr3`
- 期望：阻断；错误码命中；不产生 trip 半成品

### TC-RAW-02 RAW+JPG 混合
- 输入：10 张 `.cr3` + 20 张 `.jpg`
- 期望：阻断；提示包含 RAW 数量与后缀

### TC-RAW-03 常规 JPG
- 输入：50 张 `.jpg`
- 期望：流程完全正常

### TC-RAW-04 HEIC
- 输入：20 张 `.heic`（环境具备 pillow-heif）
- 期望：不被 RAW 规则误伤

---

## 10. 风险与回滚

| 风险 | 缓解 |
|------|------|
| 用户误解为“系统坏了” | 统一文案 + FAQ + 示例后缀 |
| 误拦截非 RAW 文件 | 后缀白名单回归测试 + 可配置清单 |
| 混合目录用户希望“先导入 JPG” | 当前版本明确阻断；后续可评估高级开关 |

回滚策略：
- 将 `ingest.reject_raw=false` 即可关闭拦截（仅限紧急回滚，不建议长期开启）。

---

## 11. 发布与灰度建议

- G0：离线测试通过 AC-RAW-01~05
- G1：10% 内测用户开启（默认）
- G2：50%
- G3：全量

监控项：
- `rawRejectedCount / 导入请求数`
- RAW 拦截后重试成功率（转 JPG 后）

---

## 12. 变更记录

| 版本 | 日期 | 说明 |
|------|------|------|
| **v0.7.0-RAW-GATE** | 2026-05-30 | 初稿：RAW 拦截策略、提示文案、任务拆分、验收标准 |

