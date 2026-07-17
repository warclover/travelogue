# 狗粮记录 · 写作引擎 API 配置加固 V1

| 属性 | 内容 |
|------|------|
| **日期** | YYYY-MM-DD |
| **构建 / commit** | |
| **环境** | Windows · Studio 本机 |
| **对应 ACCEPTANCE** | [ACCEPTANCE-WRITING-ENGINE-API-HARDENING-V1.md](../ACCEPTANCE-WRITING-ENGINE-API-HARDENING-V1.md) |

> 复制本文件为 `writing-engine-api-hardening-v1-dogfood-YYYY-MM-DD.md` 后填写。  
> **禁止**把 API Key、完整 base_url query、截图中的密钥贴进仓库。

---

## 参与人

| 人 | DeepSeek | 通义中国站 | 通义国际站（可选） | 备注 |
|----|----------|------------|-------------------|------|
| | ☐ 通过 / ☐ 失败 | ☐ 通过 / ☐ 失败 | ☐ / 跳过 | |

---

## 清单（每人至少 DeepSeek + 通义中国站）

| AC | 步骤摘要 | 结果 | 备注（错误文案 / 截图路径） |
|----|----------|------|---------------------------|
| AC-WEA-01 | DeepSeek 就绪 → 改通义中国站 Key → 保存并测试 | ☐ | |
| AC-WEA-02 | 通义就绪 → 改回 DeepSeek → 保存并测试 | ☐ | |
| AC-WEA-03 | 非法 Key → 连接失败 ≠ 已就绪；Key 仍可改 | ☐ | |
| AC-WEA-04 | 合法 Key 一点「保存并测试」 | ☐ | |
| AC-WEA-05 | 通义国际站（有 intl Key 时） | ☐ / 跳过 | |
| AC-WEA-06 | 高级填 `http://…` → 拒绝 | ☐ | |
| AC-WEA-07 | 清除 → 未配置；预览恢复配置 CTA | ☐ | |
| AC-WEA-08 | 已有 DeepSeek 时存通义 → 见确认；取消不写 | ☐ | |
| AC-WEA-09 | 脚注含本机 Key + 费用结算 | ☐ | |
| AC-WEA-10 | H7 含国内/国际与保存并测试 | ☐ | |
| AC-WEA-11 | AI zone meta 与徽章同词 | ☐ | |
| AC-WEA-12 | 模型改 qwen-turbo 后保存并测试 | ☐ | |

---

## 观察（可选）

- 切换确认是否好懂：
- 失败文案是否可行动：
- 其他：
