# Travelogue · 敢发叙事就绪 V1 验收合同（ACCEPTANCE）

| 属性 | 内容 |
|------|------|
| **DOC-STATUS** | **active** |
| **PRD 源** | [PRD-SHARE-NARRATIVE-READINESS-V1.md](./PRD-SHARE-NARRATIVE-READINESS-V1.md) §11 |
| **主题代号** | **SNR** |
| **更新日期** | 2026-08-10 |

> AC 以本文件为源；PRD 仅索引。未注明处 Fail-open：叙事增强失败不得阻断导出。

---

## AC 清单

| ID | 断言 | 里程碑 | 证据类型 |
|----|------|--------|----------|
| **AC-SNR-01** | 任意成册打开预览后可判定 `narrativePosture`；`photo_led` / `upgrade_ready` 时用户可见对应 COPY-SNR-P01/P02（`narrative_ready` 可无主条） | W1 | 手测 + API/fixture |
| **AC-SNR-02** | `upgrade_ready` 时点击姿态 CTA → 打开 AI Sheet 且聚焦杂志文案区（或等价 scrollIntoView） | W1 | Playwright |
| **AC-SNR-03** | 长图文字层与卷轴可见 caption **零**「旅行照片」；全库扫描闸可重复跑 | W1 | 扫描脚本 + 单测 |
| **AC-SNR-04** | 无 AI、同册 ≥3 章样片：章主标题「仅裸日期且无时段/地点/场景区分」占比 ≤30%，或全部含时段/地点短标；**零**序号腔 | W2 | 扫描 + fixture |
| **AC-SNR-05** | 含离群年样片（如武大高光）：自动角标/图注不展示无解释的四位离群年；可为「往年 · …」或省略年 | W1 | 手测 + fixture |
| **AC-SNR-06** | AI Sheet 打开时，真实鼠标点击 × **一次成功关闭**（禁止仅测 Esc）；Dock caret 不得拦截 | W0 | Playwright |
| **AC-SNR-07** | 打开导出设置 ⇒ AI Sheet 关闭；打开 AI ⇒ 导出设置关闭；与分章/精修互斥不回退 | W0 | Playwright |
| **AC-SNR-08** | 杂志文案生成成功后出现 diff 条，摘要含至少一个槽位类型；可关闭；状态变为「已是杂志文案」 | W2 | Playwright / 手测 |
| **AC-SNR-09** | `可生成` 状态下预览/姿态**不得**出现「杂志文案已完成」类文案 | W2 | 文案契约单测 |
| **AC-SNR-10** | `narrative_ready` 下小红书文案包 body 非空（规则拼装）或明示 L1；L0 仍显示 COPY-SNR-X01 | W2 | 单测 + 手测 |
| **AC-SNR-11** | 单选小红书时金色主 CTA 为人话「导出小红书」（或 COPY-SNR-C02 等价）；主文案**不是**孤立「N 个模式」 | W0 | Playwright |
| **AC-SNR-12** | 喜欢项零回退：六平台选项仍在；窄屏 gate 文案仍在；脏题名扫描保持 0（对照库） | W3 | 回归清单 |

---

## 门禁建议

| 门 | 必须绿 |
|----|--------|
| Kickoff W0 | 线框 F5/F6/F8 认可 · AC-SNR-06/07/11 测试骨架 |
| W1 Done | AC-SNR-01～03/05 |
| W2 Done | AC-SNR-04/08～10 |
| 主题 Done | AC-SNR-12 + Persona 复测 C1–C8 关闭或书面降级 |
