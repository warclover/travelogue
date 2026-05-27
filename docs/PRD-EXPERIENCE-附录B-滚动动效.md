# PRD-EXPERIENCE · 附录 B · 滚动动效（呼吸感）

| 属性 | 内容 |
|------|------|
| **主文档** | [PRD-EXPERIENCE.md](./PRD-EXPERIENCE.md) |
| **域** | L2b 滚动动效 · **仅 scroll 模式** · Agent 3 |
| **Epic** | E2（soft）· E6（flow）· E8（cinematic/gallery） |
| **参考** | [Chicago Current](https://chicago-current.vercel.app/) · [Lenis](https://github.com/darkroomengineering/lenis) |
| **更新** | 2026-05-27 |

> 配置字段：`export.reading.scroll.breath`（profile 展开）。longshot / present **强制 off**。

---

## 1. 定义

**呼吸感**：滚动时内容 **稍后到位**、停滚 **略有拖尾**；章内 **逐屏渐显**，非 1:1 跟手跳变。

| 维度 | 期望 |
|------|------|
| 节奏 | 滚一下 → 稍后到位 |
| 空间 | 封面/章首轻视差或渐显 |
| 控制 | 可反向滚；无 trapped scroll |

---

## 2. 档位

| ID | 用户文案 | 技术 | Epic |
|----|----------|------|------|
| `off` | 经典 | 无 | — |
| `soft` | 呼吸·轻 | CSS reveal + IO | **E2** |
| `flow` | 呼吸·标准 | + Lenis lerp≈0.1 | E6 |
| `cinematic` | 呼吸·电影 | + ScrollTrigger scrub | E8 |
| `gallery` | 图库横滑 | gallery pin + scrub:1 | E8 |

**默认**（`default_hybrid`）：`soft`。  
**share / longshot / mobile / inline-edit**：`off`。

---

## 3. 技术分层

| 层 | 组件 | 阶段 |
|----|------|------|
| L2 | `IntersectionObserver` + `.breath-reveal` | E2 · 无外链 |
| L0 滚动 | Lenis · 与 ST 同步 | E6 |
| L1 驱动 | GSAP ScrollTrigger scrub | E8 |

### 3.1 P0 · soft（E2）

```css
.breath-reveal {
  opacity: 0;
  transform: translateY(1.5rem);
  transition: opacity 0.7s cubic-bezier(0.22, 1, 0.36, 1),
              transform 0.7s cubic-bezier(0.22, 1, 0.36, 1);
}
.breath-reveal.is-visible { opacity: 1; transform: none; }
```

- 触发：`threshold 0.12` · `rootMargin: 0 0 -8% 0`  
- 单位：每 `layout-screen` 一次 reveal（非每 slot）  
- `userTier: featured` → duration ×1.15（与附录 A 协同）

### 3.2 Lenis · flow（E6）

```javascript
{ lerp: 0.1, smoothWheel: true, wheelMultiplier: 0.85, syncTouch: false }
lenis.on('scroll', ScrollTrigger.update); // 若 ST 已加载
```

**present 激活时暂停 Lenis。**

### 3.3 ScrollTrigger · cinematic（E8）

| 目标 | scrub | pin |
|------|-------|-----|
| cover 视差 | true | ❌ |
| chapter-header | true | ❌ |
| gallery 横滑 | 1 | ✅ 仅 gallery 章 |

**禁止** 全站 78 屏 pin。

---

## 4. scroll-snap（E2 · 属 Hybrid 非 breath 专属）

```css
main { scroll-snap-type: y proximity; }
.layout-screen { scroll-snap-align: start; }
```

字段：`reading.scroll.snap` · `off | proximity | mandatory`  
longshot 捕获前移除 snap 类。

---

## 5. DOM 绑定

| data-block | soft+ | cinematic |
|------------|-------|-----------|
| cover-hero | reveal | + 视差 |
| hook-line | reveal | scrub |
| chapter-header | reveal | scrub |
| layout-screen | reveal | 首屏 scrub 0.6 |
| media-scroll | — | pin（gallery 档） |

不新增 manifest 块类型。

---

## 6. Teardown API（E4）

```javascript
// 规划 · longshot / 模式切换前调用
window.__TRAVELOGUE_BREATH__.teardown()
// → 移除 transform/opacity 中间态 · kill ST · destroy Lenis · 还原 snap
```

**AC-EXP-03** 门禁。

---

## 7. 边界

| 场景 | 行为 |
|------|------|
| prefers-reduced-motion | 等同 off |
| inline-edit | off |
| screenplay 播放 | 不加载 breath |
| 无 JS | 内容可见（`.no-js` / `@media (scripting: none)`） |
| E2 | **禁止** GSAP 硬依赖 |

---

## 8. 文件（规划）

| 文件 | 内容 |
|------|------|
| `breath.css` | reveal · snap 辅助 |
| `breath.js` | IO · profile 路由 · teardown |
| `breath-lenis.js` | E6 动态加载 |
| `breath-gsap.js` | E8 动态加载 |

---

## 9. 验收（附录 B）

| ID | 通过条件 |
|----|----------|
| AC-BR-01 | soft · 林芝 · 逐屏渐显 |
| AC-BR-02 | flow · 停滚拖尾 ≤300ms |
| AC-BR-03 | cinematic · 封面视差 |
| AC-BR-04 | reduced-motion → off |
| AC-BR-05 | inline-edit → off |
| AC-BR-06 | longshot smoke PASS |
| AC-BR-07 | 无 JS 可读 |
| AC-BR-08 | mobile 无 breath 脚本 |

→ **AC-EXP-02、AC-EXP-03、AC-EXP-10**

---

## 10. 开放问题

1. E2 满意度够是否推迟 Lenis → **E6 可选**  
2. GSAP 商业许可 → E8 前法务确认  
3. mobile web 弱启用 flow → **12 个月内否**（ADR-003）
