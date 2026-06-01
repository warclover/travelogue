/**
 * 首页 v2 · Lightbox 触发手势纯逻辑（无 DOM，可被浏览器与 node --test 导入）。
 *
 * 契约：PRD §6.4
 *  - 轻点（位移 ≤ 阈值）→ 开 Lightbox
 *  - 横拖 >10px（pointer/mouse）/ >8px（touch）→ 仅翻页
 *  - 9:16 内滚超阈值 → 仅滚动
 */

/** 拖拽阈值（px）：mouse 10 / touch 8（单测覆盖）。 */
export const LIGHTBOX_DRAG_THRESHOLD_PX = { mouse: 10, touch: 8 };

export function thresholdFor(isTouch) {
  return isTouch ? LIGHTBOX_DRAG_THRESHOLD_PX.touch : LIGHTBOX_DRAG_THRESHOLD_PX.mouse;
}

/** 位移在阈值内即视为轻点（dx/dy 均不超阈值）。 */
export function isTap(dx, dy, isTouch) {
  var t = thresholdFor(isTouch);
  return Math.abs(Number(dx) || 0) <= t && Math.abs(Number(dy) || 0) <= t;
}

/**
 * 手势分类：'tap' | 'horizontal-drag' | 'vertical-scroll'。
 * 超阈值后按主导轴判定：横向 → 翻页；纵向 → 内滚。
 */
export function classifyGesture(dx, dy, isTouch) {
  if (isTap(dx, dy, isTouch)) return "tap";
  var ax = Math.abs(Number(dx) || 0);
  var ay = Math.abs(Number(dy) || 0);
  return ax >= ay ? "horizontal-drag" : "vertical-scroll";
}
