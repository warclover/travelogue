# 模型 API 接入 · 狗粮清单（DeepSeek / 通义百炼）

发版或改动 `llm/settings|ping|ready` 后，本机各跑一遍。**勿把真实 Key 写入仓库或聊天。**

## 前置

- [ ] Studio 已启动；预览打开任一 trip
- [ ] `studio.ai_surface_enabled: true` 或 `TRAVELOGUE_AI_SURFACE=1`（测叙述时）
- [ ] 准备 DeepSeek Key 与/或百炼 Key（可只用一家）

## 必测路径

| # | 步骤 | 期望 |
|---|------|------|
| 1 | AI → API配置 → 选 DeepSeek → 粘贴 Key → 保存并测试 | 成功文案「已连通 · DeepSeek…」；徽章「已就绪」；Sheet 沉底「API配置 · 已就绪」 |
| 2 | 故意改错 Key 再保存并测试 | 失败中文（鉴权类）；徽章「连接失败」；Sheet **不**显示「已就绪」 |
| 3 | 切通义千问 + 中国站 + 有效 Key → 保存并测试 | 成功；overlay 无 deepseek 残留 model/URL |
| 4 | 高级里填 `http://…` 或 `https://127.0.0.1/v1` | 拒绝保存（公网 https 校验） |
| 5 | 清除配置 | 回到未配置；叙述入口引导「配置写作引擎」 |
| 6 | 关闸（`ai_surface_enabled: false`）仍打开 API配置并保存测通 | 可保存/ping；叙述等动作仍诚实不可用 |
| 7 | 开闸后对已测通 Key 点「生成杂志感文案」 | 可启动 Job（非「当前版本不可用」） |

## 回归命令（无外呼）

```powershell
python -m pytest tests/unit/web/test_ai_surface_gate.py tests/unit/web/test_llm_ping_provider_isolation.py tests/unit/web/test_cqa_llm_ping_isolation.py tests/unit/web/test_user_llm_settings.py tests/unit/llm/test_provider_endpoint_coerce.py tests/unit/llm/test_llm_client.py tests/unit/web/test_alg3_llm_ready.py tests/unit/web/test_sas_ai_sheet_wiring.py -q
```
