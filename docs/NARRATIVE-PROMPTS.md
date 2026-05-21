# Travelogue · 叙事提示与填槽规范（Agent 2）

| 属性 | 内容 |
|------|------|
| **Agent** | Storyteller（Agent 2） |
| **文档版本** | v0.1 |
| **关联** | `VALIDATION-RULES.md`、`DATA-MODEL.md`、`config.yaml.example` |
| **更新日期** | 2026-05-19 |
| **ADR** | [adr/001-delivery-and-media.md](./adr/001-delivery-and-media.md) |

---

## 1. 目标

- **只填槽**：输出 JSON Patch 或完整字段子树，不写 HTML。  
- **短文案**：遵守 manifest limits。  
- **可验证**：失败自动重试 ≤2 次（`config.narrative.max_auto_fix_retries`）。  
- **尊重用户**：`edited: true` 字段跳过。  
- **可见性**：依赖 Agent 0 的 `tags` + G1 的 `memoryAnchors`，**不**发送原图二进制（ADR-001）。

---

## 2. 输入：Brief 结构

每次调用组装一个 brief（**禁止**仅依赖 EXIF/城市；必须包含 tags 与 anchors）：

```json
{
  "task": "fill_trip_copy",
  "trip": {
    "tripId": "kyoto-2025-04",
    "dateStart": "2025-04-02",
    "dateEnd": "2025-04-06",
    "places": ["京都"],
    "tone": "relaxed",
    "userNotes": "别总停下来拍照"
  },
  "limits": {
    "tripTitleMaxChars": 20,
    "hookMaxChars": 56,
    "chapterTitleMaxChars": 12,
    "chapterLeadMaxChars": 80,
    "mediaTitleMaxChars": 14,
    "captionMaxChars": 60,
    "epilogueMaxChars": 80
  },
  "chapters": [
    {
      "id": "ch-02",
      "patternId": "moment",
      "places": ["祇园"],
      "memoryAnchors": ["避雨", "老板推荐的小酒馆"],
      "assets": [
        {
          "id": "asset-010",
          "takenAt": "2025-04-03T20:10:00+09:00",
          "tags": ["雨天", "石板路", "夜景", "纸伞"],
          "tagsSource": "clip",
          "hasVoice": true,
          "voiceExcerpt": "雨太大了我们先回酒店拿伞"
        }
      ],
      "existing": { "title": "", "lead": "" }
    }
  ],
  "fieldsRequested": ["meta.title", "meta.hook", "chapters[].title", "chapters[].items[].caption"]
}
```

`--field meta.hook` 时仅 `fieldsRequested` 含单字段。

---

## 3. System Prompt（模板）

```
你是旅行视觉游记的文案编辑。你只输出合法 JSON，不写 HTML。

规则：
1. 中文、短句、口语可保留；禁止流水账和公文腔。
2. 禁止虚构未在 brief 中出现的城市、人物、事件；tags 与 memoryAnchors 是你的事实来源。
3. 优先把 memoryAnchors 和 voiceExcerpt 融入 hook/caption，避免导游词。
4. 章标题用地点/情绪/事件，禁止 Day1、Day2。
5. 严格遵守 limits 字数；超长你自己先截断。
6. 禁用词：{banned_phrases}
7. caption 优先改写 voiceExcerpt，不得把 ASR 全文原样当作 caption。
8. tone=relaxed：轻松、留白；tone=documentary：克制、少形容词。

输出格式：仅一个 JSON 对象，字段见 user 消息中的 outputSchema。
```

---

## 4. User Prompt（模板）

```
根据以下 brief 填写游记文案。

brief:
{brief_json}

outputSchema:
{
  "meta": {
    "title": "string",
    "subtitle": "string | null",
    "hook": "string | null",
    "epilogue": "string | null"
  },
  "chapters": [
    {
      "id": "ch-02",
      "title": "string",
      "lead": "string",
      "items": [
        { "assetId": "asset-010", "title": "string | null", "caption": "string | null" }
      ]
    }
  ]
}

只返回 JSON，不要 markdown 代码块。
```

---

## 5. Tone 差异

| 字段 | relaxed | documentary |
|------|---------|-------------|
| hook | 感官细节、一句画面 | 时间地点、一句事实 |
| caption | 可含语气词 | 少用感叹号 |
| chapter lead | 可空或很轻 | 可空 |

---

## 6. 输出合并规则

1. 解析 JSON；失败 → `E_NARRATE_PARSE`，重试。  
2. 对每个字段跑 L1 + L2（`VALIDATION-RULES.md`）。  
3. 合并进 `trip.json`；设置 `edited: false`（新生成字段）。  
4. 用户曾编辑的字段：brief 中标记 `skip: true` 则不写入。

---

## 7. 单字段重生成

`travelogue narrate <id> --field chapters[ch-02].items[0].caption`

- brief 仅含该章该 asset。  
- 仍跑禁用词与字数校验。

---

## 8. 失败与重试

| 次数 | 行为 |
|------|------|
| 1 | 将 validator 错误列表附加到 user prompt |
| 2 | 同上 + 要求「仅修正错误字段」 |
| 3 | 中止，`E_NARRATE_RETRY_EXHAUSTED` |

---

## 9. 成本优化

- 先填 `meta` + 章 `title`，再按章 batch `caption`（每章 1 次调用）。  
- 缓存 key：`hash(brief + model + tone)` → 本地 `trips/{id}/.narrative-cache/`（P1）。

---

## 10. Brief 组装清单（实现）

从 `trip.json` 构建 brief 时 **必须**：

| 字段 | 来源 |
|------|------|
| `assets[].tags` | Agent 0 |
| `chapters[].curation.memoryAnchors` | G1 用户 / CLI 编辑 |
| `meta.places` / `takenAt` | EXIF |
| `userNotes` | trip 顶层 |

缺 tags 时：降级用 `place.city` + 时段，并在日志 WARN。

---

## 11. 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1 | 2026-05-19 | 初稿 |
| v0.2 | 2026-05-19 | ADR-001：tags + memoryAnchors |
