# ACCEPTANCE · Studio AI Surface V1（SAS）

| 属性 | 内容 |
|------|------|
| **对应 PRD** | [PRD-STUDIO-AI-SURFACE-V1.md](./PRD-STUDIO-AI-SURFACE-V1.md) **v0.2.1** |
| **实施** | [IMPLEMENTATION-STUDIO-AI-SURFACE-V1.md](./IMPLEMENTATION-STUDIO-AI-SURFACE-V1.md) |
| **评审** | [acceptance-records/sas-studio-ai-surface-v1-review-2026-08-10.md](./acceptance-records/sas-studio-ai-surface-v1-review-2026-08-10.md) |
| **狗粮** | [acceptance-records/sas-studio-ai-surface-v1-w3-dogfood-2026-08-10.md](./acceptance-records/sas-studio-ai-surface-v1-w3-dogfood-2026-08-10.md) |
| **更新日期** | 2026-08-10 |

> **Done 口径**：AC-SAS-01～17（**不含** AC-SAS-08b）。三语气归 AIR。正式发版默认开闸仍受 OQ-AIR-01。

## 自动化门禁

```powershell
python -m pytest tests/unit/web/test_sas_ai_sheet_wiring.py -q
```

## W1 · 壳 + 杂志现网解冻 + 装帧主入口

| ID | 步骤 | 期望 | 结果 |
|----|------|------|------|
| AC-SAS-01 | 预览 Dock | 「AI」在精修后、导出前（D-SAS-02） | ☑ 接线单测 + 狗粮 |
| AC-SAS-02 | 点 AI / × / 再点 | Sheet 开合 | ☑ |
| AC-SAS-03 | 开 AI ↔ 开精修 | 互斥；Dock「精修」「AI」在对方开时仍可点 | ☑ |
| AC-SAS-04 | 开闸 Sheet | 本册动作 / 本机连接 / 高级（localhost） | ☑ |
| AC-SAS-05 | 勾「优先 AI 手写体」 | **零** `title-art`/`narrate` 请求 | ☑ 狗粮 |
| AC-SAS-06 | 点「生成装帧标题」 | 成功或 fail-open toast；不挡预览 | ☑ 路径存在（可选手跑烧 API） |
| AC-SAS-07 | 无 Key → 配置；有 Key → 确认后 narrate | 不触发 curate；失败不挡导出 | ☑ 确认取消零 narrate；配置引导 ☑ |
| AC-SAS-08 | 杂志卡 | **无**语气选择器；确认含覆盖提示 | ☑ |
| AC-SAS-12 | `aiSurfaceEnabled=false` | Dock 仍见 AI；诚实态；杂志零外呼 | ☑ |
| AC-SAS-13 | 本机连接 | 打开既有 LLM Modal；无第二套密钥 API | ☑ |
| AC-SAS-14 | 无 Key 导入主链 | 仍可出长图（NAS 回归） | ☑ 既有 NAS 合同 |
| AC-SAS-17 | allowlist | `ai_sheet_*` 在 analytics + domain events | ☑ 单测 |

## W2 · 意图 / 建议 / 徽标 / 旧入口

| ID | 步骤 | 期望 | 结果 |
|----|------|------|------|
| AC-SAS-09 | 有未处理 `layoutSuggestions` | Dock「AI」橙点；打开/处理后熄灭 | ☑ 接线 + 逻辑 |
| AC-SAS-10 | 采纳 / 忽略 | 采纳写 `accepted`；忽略本地 dismiss；不改 `structure_locked` 章结构 | ☑ |
| AC-SAS-11 | 「重新解析」 | 显式 `POST .../ai/intent-brief`；UI 无 Agent 工程名 | ☑ |
| AC-SAS-15 | 窄屏（≤720） | AI 图标可用；Sheet 可开；文件夹隐藏保挤度 | ☑ CSS + smoke |
| AC-SAS-16 | 精修「杂志文案」 | 「在 AI 中打开」深链；无直接 `data-action=llm` | ☑ 单测 |

## W3 · 收口

| ID | 步骤 | 期望 | 结果 |
|----|------|------|------|
| COPY-SAS-08 | AI Sheet 顶 | 「版式与书衣请用「精修」；智能生成请用「AI」。」 | ☑ |
| 狗粮 N≥5 | 见狗粮记录 | 会话勾选 | ☑ 见狗粮纪要 |
| 埋点核对 | 打开/动作/narrate `source=ai_sheet` | allowlist 绿 + 狗粮抽检 | ☑ |

## 不挡 Done（依赖）

| ID | 说明 | 状态 |
|----|------|------|
| AC-SAS-08b | AIR `voice` 落地后再验 | ☐ 归 AIR |

## 入口收敛对照表（AC-SAS-16）

| 现网入口 | V1 策略 | 勾选 |
|----------|---------|------|
| 精修 → 画册 → 杂志文案 | 「在 AI 中打开」深链 | ☑ |
| 精修 → 装帧标题次入口 | **保留**（OQ-SAS-03 · W2 评估：仍保留） | ☑ |
| 首页写作引擎设置 | 保留；Sheet「本机连接」复用 | ☑ |
| dark 工具行 narrate | 开闸后非默认发现路径；权威在 AI Sheet | ☑ |
