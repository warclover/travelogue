# BAI W0 实机狗粮（AC-BAI-16）

| 属性 | 内容 |
|------|------|
| **日期** | 2026-08-13 |
| **对应** | [PRD-BAILIAN-AI-INTEGRATION-V1.md](../PRD-BAILIAN-AI-INTEGRATION-V1.md) · [IMPLEMENTATION-BAILIAN-AI-INTEGRATION-V1.md](../IMPLEMENTATION-BAILIAN-AI-INTEGRATION-V1.md) |
| **环境** | 源码开发 · `secrets.json` `provider=dashscope` `region=cn` `last_ping_ok=true` · 兼容端点 `dashscope.aliyuncs.com/compatible-mode/v1` |
| **脚本** | `python scripts/bai_w0_probe.py`；字形补跑用现网 `generate_raw` + `ocr_verify` |
| **密钥** | 本记录不含 Key / 请求体 / 图片 URL |

> 结论可指导 W1b 默认型号；**不可**据此把生产 t2i 默认改离 `wanx2.1-t2i-plus`（AC-BAI-11 仍要字形盲评）。

---

## 1. 关闭的问题

| ID | 结论 | 依据 |
|----|------|------|
| **OQ-BAI-02** | **Pro 可在现网兼容端点调用**，无需 Workspace MaaS URL | ping 2.6s · narrate JSON 5.4s |
| **OQ-BAI-01 / D-BAI-14** | **非流式 + `enable_thinking` + 杂志 JSON 可解析**；V1 **保持思考默认开**，不必为此做流式 client | Pro / Flash 均 HTTP 200，`reasoning_content` 有值，JSON 可解析 |
| **D-BAI-16 合同** | `qwen3.5-ocr` **吃**现网 `image_url` + JSON | 白底印刷体「拾光」合同通过 |
| **OQ-BAI-04** | 书法贴纸上 **不要把 OCR 默认设成 `qwen3.5-ocr`**；改 **`qwen3.7-flash`**，旧 `qwen-vl-plus` 仅链尾 | 飞白风格贴纸：3.5-ocr 两次均 false；3.7-flash 两次均 true |
| **D-BAI-15 协议** | `wan2.2-t2i-plus` **与 `route_c` 同构**；`wan2.7-image-pro` / `qwen-image-3.0-pro` **不同构**（400 url error） | 现网 `image-synthesis` 异步 URL |

**OQ-BAI-03 生图冠军：未关。** 同构候选只有 `wan2.2-t2i-plus`；本轮各 1 张「拾光」+ `qwen3.7-flash` 回读都过，**不够**当冠军门。生产默认仍 `wanx2.1-t2i-plus`。

---

## 2. 文案槽

| 模型 | ping（关思考） | narrate JSON（关思考） | 非流式思考 + JSON |
|------|----------------|------------------------|-------------------|
| `qwen3.7-flash` | 3.2s ✅ | 26.3s ✅ | （未测，非 V4） |
| `deepseek-v4-flash-0731` | 1.7s ✅ | 2.6s ✅ | 2.7s ✅ |
| `deepseek-v4-pro` | 2.6s ✅ | 5.4s ✅ | 3.1s ✅ |

W1b 文案默认：**`deepseek-v4-pro`**；链：Pro → Flash-0731 → `qwen3.7-flash` → …  
Ping **继续关思考**（D-BAI-06）。  
本轮 narrate 是精简 hook/lead schema，不是 AIR 全书；语气抽检见 [W1b Studio 走通](./bai-w1b-studio-dogfood-2026-08-13.md)（SHD-BAI-04）。

---

## 3. OCR / vision

| 模型 | 白底印刷体「拾光」`image_url` | 路线 C `flowing-brush` 贴纸「拾光」 |
|------|------------------------------|-------------------------------------|
| `qwen3.5-ocr` | 合同 ✅ · match ✅ | match ❌（2.1 与 2.2 各一张） |
| `qwen3.7-flash` | 合同 ✅ · match ✅ | match ✅ |
| `qwen-vl-plus` | 合同 ✅ · match ✅ | （本轮未对贴纸再打） |

W1 OCR 默认：**`qwen3.7-flash`**（满足 AC-BAI-10：不再是 `qwen-vl-plus`）。  
`qwen3.5-ocr` 可留作文档 OCR 实验，**不进**封面字形门默认。

---

## 4. 生图协议

提交 URL 均为现网 `https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis`。

| 模型 | HTTP | 同构 | 轮询 |
|------|------|------|------|
| `wanx2.1-t2i-plus` | 200 | ✅ | SUCCEEDED · 有图 |
| `wan2.2-t2i-plus` | 200 | ✅ | SUCCEEDED · 有图 |
| `wan2.7-image-pro` | 400 `InvalidParameter` url error | ❌ | — |
| `qwen-image-3.0-pro` | 400 `InvalidParameter` url error | ❌ | — |

字形补跑（`generate_raw` · `flowing-brush` · 「拾光」· 各 1 张）：

| 生图模型 | `qwen3.5-ocr` | `qwen3.7-flash` |
|----------|---------------|-----------------|
| `wanx2.1-t2i-plus` | false | true |
| `wan2.2-t2i-plus` | false | true |

W2 若要换默认：只允许在 `wan2.2-t2i-plus` 上做盲评；2.7 / 千问生图须单独立项改 `route_c.py`，禁止当 drop-in。

---

## 5. 给 W1b 的默认表（本记录冻结）

| 槽 | W1b 默认 | 不得做 |
|----|----------|--------|
| copy | `deepseek-v4-pro` + 思考开（ping 关） | 假绿流式；用户面出现型号 |
| vision · OCR | `qwen3.7-flash` | 把 `qwen3.5-ocr` 设成封面 OCR 默认 |
| t2i | **仍** `wanx2.1-t2i-plus` | 未盲评就切 2.2；把 2.7 / qwen-image 塞进现网 URL |
