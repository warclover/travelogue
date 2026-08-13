# BAI W1b Studio 本机走通（AC-BAI-02 / 03 / 06 · SHD-BAI-04）

| 属性 | 内容 |
|------|------|
| **日期** | 2026-08-13 |
| **对应** | [PRD-BAILIAN-AI-INTEGRATION-V1.md](../PRD-BAILIAN-AI-INTEGRATION-V1.md) v0.2.2 · [IMPLEMENTATION-BAILIAN-AI-INTEGRATION-V1.md](../IMPLEMENTATION-BAILIAN-AI-INTEGRATION-V1.md) · [W0 实机](./bai-w0-live-probe-2026-08-13.md) |
| **环境** | 源码 `python -m travelogue studio --no-open` · `TRAVELOGUE_AI_SURFACE=1` · `http://127.0.0.1:8766/` · `provider=dashscope` `region=cn` |
| **册** | 文案：`trips/demo-album`（斯里兰卡见闻录，frame 范围）；封面字补跑：`trips/_bai_w1b_titleart`（标题改为「拾光」，不改视觉验收原册） |
| **密钥** | 本记录不含 Key / 请求体。UI 占位 `sk-***63b0` |

截图：[attachments/bai-w1b-studio-dogfood-2026-08-13](./attachments/bai-w1b-studio-dogfood-2026-08-13)

---

## 结论

| ID | 结果 | 依据 |
|----|------|------|
| **AC-BAI-02** | **过** | 设置「保存并测试」→「已连接通义百炼」；AI Sheet 点「生成杂志感文案」后封面出现 LLM hook，Sheet 变为「已是杂志文案」 |
| **AC-BAI-03** | **过（走字库）** | 万相本次未通 → `last_image_ok=false`、`imageReady=false`；Sheet COPY-BAI-08；点「生成字体」走路线 B；导出入口仍在 |
| **AC-BAI-06** | **过** | CLI ping 落在 `qwen3.7-flash`（关思考链）；文案走 Pro 默认且 JSON 可解析。Ping ~13s，frame 文案 ~10s |
| **SHD-BAI-04** | **抽检过，不改默认** | 4 条 caption：Pro 更贴 `voiceExcerpt`、更短；Flash 更爱复述场面。无禁用套话。思考未把 caption 拖慢 |

文案灯 / 图像灯已分家：走通结束时 `connectionOk=true` `copyReady=true` `imageReady=false`。

**不要**据此切生产 t2i 离 `wanx2.1-t2i-plus`（AC-BAI-11 仍要盲评）。W0 同把 Key 曾通过万相；本次 7s 内路线 C → 路线 B，并灭图像灯，符合鉴权/额度类失败，不是 OCR/超时误灭。

---

## 1. 保存并测试

1. 开闸后首页设置区可见「模型API 配置」，折叠摘要已是「已连接通义百炼」。
2. 「管理连接…」打开 Modal：标题「模型API 配置」；无服务商/模型下拉/国际站/自定义 URL。
3. 点「保存并测试」：`POST /llm/settings` 200 → `POST /llm/ping` 200。
4. 成功文案「已连接通义百炼」；Key 框清空，占位「已保存 sk-***63b0 · 留空则保持原 Key」。

CLI 对照：`python -m travelogue llm ping --provider dashscope` → `OK llm ping · dashscope/qwen3.7-flash`（约 13s）。

截图：`01-save-ping-ok.png`

---

## 2. 生成杂志感文案（Pro + 思考）

册：`demo-album`。Studio narrate 固定 `scope=frame`（hook + epilogue，不写章节 lead / caption）。

1. 预览顶栏「AI」→ Sheet：「杂志文案 · 可生成」，脚「模型API 配置 · 已连接」。
2. 确认框后 `POST /__travelogue/narrate` 202；约 10s 预览重载。
3. Sheet 变为「已是杂志文案 / 再生成一版」。

落地文案（`hookOrigin=llm`）：

| 槽 | 文本 |
|----|------|
| hook | 赤道边的风，混着红茶与肉桂香。雨说来就来，一会儿又天晴。 |
| epilogue | 回程的航班上，我还在回味那些没有解开的谜。锡兰，再见仍是初见。 |
| chapter leads | 空（frame 范围，符合合同） |

延迟短于「思考会拖垮」的担心；JSON 一次过。若日后全书 caption 变慢，再产品判断关思考，而不是先改路由。

截图：`03-demo-album-hook-after-narrate.png`

---

## 3. 封面字体（路线 C 不通 → 字库）

CLI 对「拾光」+ `veil-footer` 强制 `--route-c`：约 7s 落 **路线 B**（`fallback: diffusion-fixed-prompt-v1 → clean-pipeline-v1`），`last_image_ok=false`。

Studio Sheet（分灯后）：

- 文案：可生成 / 已是杂志文案
- 封面字体：**「封面字体暂时改用本机字库，不影响文案和导出」**（COPY-BAI-08）· 状态「本机字库」

点「生成字体」：`POST .../title-art/resolve` 200，`engine=clean-pipeline-v1`，`openingStyleId=folio-overlap`，封面出现字库题签；底部说明「标题为程序化字库合成，非 AI 绘图」。导出「小红书等 2 项」仍在。

截图：`02-ai-sheet-copy-ready-image-fallback.png` · `04-demo-album-title-art-route-b.png` · `05-qiguang-route-b-fallback.png`

---

## 4. Caption 抽检（SHD-BAI-04）

脚本：`python scripts/bai_w1b_caption_bakeoff.py`  
对照：`qwen3.7-flash`（关思考）vs `deepseek-v4-pro`（开思考）。同一 `SYSTEM_PROMPT`。原始 JSON：`caption-bakeoff.json`。

| 场面 | Flash | Pro | 观察 |
|------|-------|-----|------|
| 清水寺雨后 | 雨停后的清水寺石阶，地还湿着。 · 21s | 雨太大，先回酒店拿伞。地还湿着。 · 7s | Pro 吃 voiceExcerpt |
| 海边小孩 | 黄昏青岛海边，孩子追浪又退回来。别追那么深。 · 24s | 别追那么深，浪会咬脚。 · 7s | Flash 复述场面；Pro 更短 |
| 夜市 | 夜市蒸汽裹着灯牌，摊前问：这要排到几点 · 15s | 这摊要排到几点 · 6s | 都过；Pro 只留口语 |
| 垭口风 | 川西高山垭口风急，帽子差点飞了。 · 21s | 帽子差点飞了，垭口风大经幡猎猎。 · 6s | 都过；无套话 |

8/8 JSON 可解析。Pro+思考在 caption 上 **快于** Flash，不支持「一开思考就不可用」。语气上 Pro 更杂志、更听人话；Flash 更说明书。V1 保持 Pro 默认。

Studio 默认 frame **不会**给用户写这些 caption；抽检是算法对照，不是预览回归。

---

## 5. 未改 / 记下

- 生产 t2i 仍 `wanx2.1-t2i-plus`。
- Sheet 副标题已连接走 COPY-BAI-12；确认框标题与主按钮对齐「生成杂志感文案」（W3）。
- 浏览器可能把 Key 填进密码框；截图前已清空。不要把填满的 Modal 存进仓库。

---

## 修订

| 日期 | 说明 |
|------|------|
| 2026-08-13 | 本机开闸走通：ping、frame 文案、字库封面字、caption 抽检 |
