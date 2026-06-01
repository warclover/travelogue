/**
 * 首页 v2 · 视口分类纯逻辑（无 DOM，可被浏览器与 node --test 导入）。
 *
 * 契约：PRD §10.1 支持矩阵
 *  - ≥1024px          → wide（Bento 双列）
 *  - 768–1023 横屏    → tablet_landscape（iPad 横屏 · 同 Bento 双列）
 *  - 768–1023 竖屏    → unsupported_rotate（旋转提示）
 *  - <768 触屏(phone) → unsupported_phone（去电脑/小程序）
 *  - <768 桌面窄窗    → unsupported_narrow（拉宽窗口）
 * 拒绝 768 三行堆叠。
 */

export const WIDE_MIN_WIDTH = 1024;
export const TABLET_MIN_WIDTH = 768;

/** @returns {'wide'|'tablet_landscape'|'unsupported_rotate'|'unsupported_phone'|'unsupported_narrow'} */
export function classifyViewport(width, height, coarsePointer) {
  var w = Number(width) || 0;
  var h = Number(height) || 0;
  if (w >= WIDE_MIN_WIDTH) return "wide";
  if (w >= TABLET_MIN_WIDTH) {
    return w >= h ? "tablet_landscape" : "unsupported_rotate";
  }
  // 窄视口
  return coarsePointer ? "unsupported_phone" : "unsupported_narrow";
}

export function isSupported(layout) {
  return layout === "wide" || layout === "tablet_landscape";
}

/** Unsupported 文案（§10.3）。 */
export function unsupportedCopy(layout) {
  if (layout === "unsupported_rotate") {
    return {
      title: "请旋转至横屏使用 Studio",
      lead: "Studio 工作台为横屏双列设计，请将设备旋转至横屏。",
    };
  }
  if (layout === "unsupported_phone") {
    return {
      title: "请在电脑浏览器打开 Studio",
      lead: "手机端的阅读与分享请使用微信小程序；工作台导入请在电脑浏览器打开。",
    };
  }
  return {
    title: "请拉宽窗口至 1024px 以上",
    lead: "当前窗口过窄，拉宽窗口即可进入 Studio 工作台。",
  };
}
