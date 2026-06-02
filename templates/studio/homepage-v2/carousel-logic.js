/**
 * 首页 v2 · Carousel 纯逻辑（无 DOM，可被 browser 与 node --test 导入）。
 *
 * 契约：docs/studio-homepage-v2/DATA-CONTRACT.md §1.3
 *  - viewport 一次显示 1 整页；横滑每次移动 1 页
 *  - D-10：到头 clamp，**不 wrap**
 *  - dot 数量 = pageCount；索引 i ∈ [0, pageCount-1]
 *  - scrollLeft = i × viewportWidth
 */

/** clamp 请求索引到 [0, pageCount-1]（不 wrap）。非整数四舍五入。 */
export function clampIndex(requested, pageCount) {
  if (!pageCount || pageCount <= 0) return 0;
  var i = Math.round(Number(requested) || 0);
  if (i < 0) return 0;
  if (i > pageCount - 1) return pageCount - 1;
  return i;
}

/** 索引 i 的当前页（保留 left/right 形状以兼容调用方；单页模式下 right 恒为 null）。 */
export function spreadFor(pages, i) {
  var list = pages || [];
  var idx = clampIndex(i, list.length);
  return {
    left: list[idx] != null ? list[idx] : null,
    right: null,
  };
}

/** 索引 i 对应的 scrollLeft（每页 = viewportWidth）。 */
export function maxScrollLeft(viewportWidth, pageCount) {
  var w = Number(viewportWidth) || 0;
  var n = Number(pageCount) || 0;
  if (w <= 0 || n <= 0) return 0;
  return Math.max(0, Math.round((n - 1) * w));
}

export function scrollLeftFor(i, viewportWidth, pageCount) {
  var w = Number(viewportWidth) || 0;
  var idx = clampIndex(i, pageCount);
  return Math.round(idx * w);
}

/** 由 scrollLeft 反推当前页索引（用于原生滚动同步）。 */
export function indexFromScrollLeft(scrollLeft, viewportWidth, pageCount) {
  var w = Number(viewportWidth) || 0;
  if (w <= 0) return 0;
  var n = Number(pageCount) || 0;
  var sl = Number(scrollLeft) || 0;
  if (n > 0 && sl >= maxScrollLeft(w, n) - 2) {
    return n - 1;
  }
  return clampIndex(Math.round(sl / w), pageCount);
}

/** 是否可向前（左）翻——首页禁用。 */
export function canPrev(i) {
  return (Number(i) || 0) > 0;
}

/** 是否可向后（右）翻——末页禁用（D-10 clamp，禁止尾→封面拼版）。 */
export function canNext(i, pageCount) {
  return (Number(i) || 0) < (pageCount || 0) - 1;
}

/** 是否为末页（单页模式下无 spread 留白，仅用于边界判断）。 */
export function isOddTail(pages, i) {
  var list = pages || [];
  var idx = clampIndex(i, list.length);
  return idx === list.length - 1;
}
