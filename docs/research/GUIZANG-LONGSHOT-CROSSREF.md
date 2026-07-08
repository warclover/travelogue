# Guizang Social Card × Travelogue Longshot 2.0 · 对照参考

| 属性 | 内容 |
|------|------|
| **外部来源** | `guizang-social-card-skill` · `references/content-planning.md` · `references/platform-specs.md` |
| **关联 PRD** | [PRD-LONGSHOT-2.0.md](../PRD-LONGSHOT-2.0.md) v0.3.3 |
| **状态** | Reference · 非实现规范 |
| **更新日期** | 2026-07-08 |

> 本文档说明 Guizang 社交卡片 skill 与 Travelogue 长图导出 2.0 的 **关系、可采纳项与明确不采纳项**。  
> 已写回主 PRD 的条目见 **§4 写回索引**；未写回者仅作 Phase P3 研究储备。

---

## 1. 范式对比

| 维度 | Guizang Social Card | Travelogue Longshot 2.0 |
|------|---------------------|-------------------------|
| **输入** | 文章、脚本、截图、产品说明 | 已渲染 **杂志风游记**（trip） |
| **输出** | 逐页 **新设计** 的 3:4 / 公众号封面 HTML→PNG | 对现有 scroll **切分/裁切** |
| **内容** | Compression Ladder · Hook · Page Roles | 保留 trip 既有叙事与排版 |
| **平台** | 小红书轮播、公众号 21:9+1:1 | 朋友圈 9 竖切、小红书 letterbox 切片 |
| **引擎** | HTML/CSS 多 frame + 渲染脚本 | Playwright capture + Python split |

**结论**：Guizang 是 **创作型** skill；Longshot 2.0 是 **导出型** 管线。不应在 Phase A/B 合并为同一 Job。

---

## 2. content-planning.md · 条目对照

| Guizang 章节 | 要点 | Longshot 采纳 | PRD 位置 |
|--------------|------|---------------|----------|
| **Compression Ladder** | 长文压成 4–8 屏视觉提纲 | ❌ v2.0 · ✅ Phase P3 | §16 P3-LNG2-04 |
| **Rednote Page Plan** | 逐页 Hook/Visual/Layout | ❌ v2.0 | Phase P3 |
| **Good Page Roles** | Hook、清单、对比、总结页 | ❌ v2.0 · ✅ Phase P3 | §16 P3-LNG2-02 |
| **Copy Rules** | 标题锋利、动词、禁「背景介绍」 | ❌ 不重写 trip 文案 | — |
| **Cover Hook Patterns** | 「终于有 Mac 版了」等 | ❌ | — |
| **WeChat Square Title** | 21:9 标题压到 4–10 字 | ❌ 非朋友圈 9 切 | — |
| **Image-Led Sequence** | 旅行最强图 P1；禁止连续 M16 | ✅ **切点权重** | §6.3.7 · D-LNG2-29 |
| **Page Count Guidance** | 600–1800 字 → 5–9 图 | ✅ **校准 auto 张数** | §6.4.3 · D-LNG2-31 |
| **Matching Visuals** | 截图/照片/生成图角色 | ⚠️ 仅研究 | Phase P3 |
| **Captions / Metadata** | `03 / 08` 页码 orientation | ✅ footer `{i}/{n}` | D-LNG2-32 · §7.3 |

---

## 3. platform-specs.md · 条目对照

| Guizang 规格 | 值 | Longshot 采纳 | PRD 位置 |
|--------------|-----|---------------|----------|
| 小红书尺寸 | 1080×1440 · 3:4 | ✅ 已一致 | §6.4 |
| Safe area | 左右 72–96 · 上 72–112 · 下 80–120 | ✅ Phase B 参考 | §6.4.2 · D-LNG2-30 |
| 推荐集 | 1 cover + 4–8 content | ✅ 校准 auto N | §6.4.3 |
| 命名 | `xhs-01-cover.png` … | ⚠️ 沿用 `{title}-xhs-{nn}` | §6.4.4 |
| 公众号 21:9 + 1:1 | 2100×900 · 1080×1080 | ❌ 非 Moments 9 切 | — |
| Live Photo | .pvt · 5s | ❌ Out of scope | — |

---

## 4. 写回 PRD 索引（v0.3.3）

| 决策 ID | 内容 |
|---------|------|
| **D-LNG2-29** | 切点优先级权重（cover / 章 / photo） |
| **D-LNG2-30** | 小红书 safe area（Phase B 参考，非 MVP 硬 AC） |
| **D-LNG2-31** | xhs auto 张数 5–9 为主，超长 ≤10 |
| **D-LNG2-32** | 页码 footer 为 orientation · publishGuide 文案 |
| **OQ-LNG2-05** | Phase P3 社交卡片重排模式 |
| **§16** | P3-LNG2-01～04 backlog |

---

## 5. 实现提示（开发）

### Phase A · `content_splitter.py`

```python
BOUNDARY_WEIGHT = {
    "cover": 1.5,
    "chapter_separator": 1.4,
    "chapter_start": 1.2,
    "photo": 1.0,
    "card": 0.9,
}

def boundary_cost(distance: float, kind: str) -> float:
    return distance / BOUNDARY_WEIGHT.get(kind, 1.0)
```

`boundary_metrics` 须输出 `boundaryKinds[]` 与 `boundariesCss[]` 对齐。

### Phase B · `slide_postprocess.py`

- letterbox 后 log warn 若主体 bbox 超出 safe area（不 fail Job）
- `resolve_slide_count(photo_count)` 实现 §6.4.3 公式

### 明确不做

- 按 Guizang 模板生成新 HTML frame
- 在 export Job 内调用 LLM 重写 Hook
- 公众号 1:1 方形标题压缩

---

## 6. 与 Guizang 产品的关系（战略）

| 路径 | 用户场景 |
|------|----------|
| **Longshot 2.0** | 已有 Travelogue 游记 · 一键导出可发 |
| **Guizang skill** | 从文章/脚本 **做** 小红书图文（非 trip） |
| **未来** | Studio「导出为社交卡片组」可链 Guizang 或内置 P3 重排 |

---

## 7. 版本记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1.0 | 2026-07-08 | 初稿 · 写回 PRD v0.3.3 |
