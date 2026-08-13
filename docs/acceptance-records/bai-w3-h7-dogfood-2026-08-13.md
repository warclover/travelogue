# BAI W3 合入后本机核对（AC-BAI-14）

| 属性 | 内容 |
|------|------|
| **日期** | 2026-08-13 |
| **代码** | `master` `71f40403`（PR #65 squash） |
| **环境** | `TRAVELOGUE_AI_SURFACE=1` · `python -m travelogue studio --no-open --port 8766` · `http://127.0.0.1:8766/` |
| **密钥** | 本记录不含 Key。status：`provider=dashscope` `region=cn` `connectionOk=true` |

截图：[attachments/bai-w3-h7-dogfood-2026-08-13](./attachments/bai-w3-h7-dogfood-2026-08-13)

---

## 结论

| 项 | 结果 |
|----|------|
| **AC-BAI-14 / H7** | **过**。设置 →「模型API 配置」→「了解更多（帮助）」打开帮助抽屉，当前条标题「模型API 配置」，正文为 COPY-BAI-12（一把通义百炼 Key，无需选择模型）。 |
| **设置摘要** | 分区标题「模型API 配置」，meta「已连接通义百炼」，说明「一把通义百炼 Key，用于文案和封面字体」。 |
| **万相现网** | **`wanx2.1-t2i-plus` 提交+轮询 SUCCEEDED**（1 张结果）。今早 W1b 狗粮时路线 C 失败，本次同把 Key 已通。 |
| **Studio 图像灯** | 仍 `imageReady=false`（磁盘 `last_image_ok=false` 未刷新）。协议通了，点一次「生成字体」才会改灯。 |
| **W2** | **不开**。通了只说明额度/鉴权恢复，不是字形盲评，生产 t2i 仍 `wanx2.1-t2i-plus`。 |

截图：`01-help-h7.png`

---

## 不做

- 不切 `wan2.2` / `wan2.7` / `qwen-image`
- 不改审美默认
- 不对真实用户册跑 `--regenerate` / 封面字重算
