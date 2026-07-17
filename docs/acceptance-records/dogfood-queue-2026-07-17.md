# 手测 / 狗粮队列 · 2026-07-17

> 工程已合入、**挡主题完成**的真人验收清单。  
> 建议由**非实现者**勾选「产品手测」列。勿把 API Key 写入仓库。

---

## P0 · 本周必跑

| 优先级 | 主题 | 清单 | 最少覆盖 |
|--------|------|------|----------|
| 1 | **写作引擎 WEA** | [writing-engine-api-hardening-v1-dogfood-TEMPLATE.md](./writing-engine-api-hardening-v1-dogfood-TEMPLATE.md) | DeepSeek + 通义中国站各 1 次「保存并测试」（AC-WEA-01/02/04） |
| 2 | **Wait Tips** | [wait-tips-v1-dogfood-CHECKLIST.md](./wait-tips-v1-dogfood-CHECKLIST.md) | 出现 · 暂停 · × 关闭 · 成功后消失；帮助「重播等待提示」后再导应再出现 |
| 3 | **首访可信 FST** | [first-session-trust-v1-dogfood-CHECKLIST.md](./first-session-trust-v1-dogfood-CHECKLIST.md) | AC-FST-15 完成宣布前至少 F1–F2 |
| 4 | **敢发闭环 Share-Ready** | [ACCEPTANCE-SHARE-READY-OPTIMIZATION-V1.md](../ACCEPTANCE-SHARE-READY-OPTIMIZATION-V1.md) §5 | 意图卡 / 成功面「换种分享」/ 书架可读标题抽检 |

---

## 建议跑法（约 60–90 分钟）

1. 清 `travelogue.waitTips.dismissed`（或帮助 → 重播等待提示）。  
2. 示例导入 → 观察 Wait Tips → 完成 → 确认 FirstSuccess 无 Tips。  
3. 设置 → AI 文案 → 真 Key「保存并测试」DeepSeek / 通义。  
4. 预览长图：意图卡（若触发）→ 导出成功面主句与「换种分享方式」。  

---

## 工程侧已绿（不必重复编码）

| 主题 | 状态 |
|------|------|
| WEA W0–W2 | 编码 ✅ · 自动化 ✅ |
| Wait Tips W0–W2 | 编码 ✅ · 契约 ✅ |
| FST W0–W2 | 工程 ✅ |
| Share-Ready W0–W2 | 工程 ✅（可选补 QA-SR-02 扫描） |

---

| 填写人 | 日期 | 备注 |
|--------|------|------|
| | | |
