/**
 * 首页 v2 · Carousel 纯逻辑（无 DOM，可被浏览器与 node --test 导入）。
 *
 * 契约：docs/studio-homepage-v2/DATA-CONTRACT.md §1.3
 *  - viewport 一次显示 2 半页（spread）；横滑每次移动 1 半页
 *  - D-10：到头 clamp，**不 wrap**
 *  - dot 数量 = pageCount；索引 i ∈ [0, pageCount-1]
 *  - scrollLeft = i × (viewportWidth / 2)
 *  - spread：左 = pages[i]，右 = pages[i+1] 或留白（奇数尾页）
 */

/** clamp 请求索引到 [0, pageCount-1]（不 wrap）。非整数四舍五入。 */
export function clampIndex(requested, pageCount) {
  if (!pageCount || pageCount <= 0) return 0;
  var i = Math.round(Number(requested) || 0);
  if (i < 0) return 0;
  if (i > pageCount - 1) return pageCount - 1;
  return i;
}

/** 索引 i 的 spread 内容：{ left, right }。右半越界则为 null（留白）。 */
export function spreadFor(pages, i) {
  var list = pages || [];
  var idx = clampIndex(i, list.length);
  return {
    left: list[idx] != null ? list[idx] : null,
    right: list[idx + 1] != null ? list[idx + 1] : null,
  };
}

/** 索引 i 对应的 scrollLeft（每半页 = viewportWidth/2）。 */
export function scrollLeftFor(i, viewportWidth) {
  var w = Number(viewportWidth) || 0;
  return Math.round((Number(i) || 0) * (w / 2));
}

/** 由 scrollLeft 反推当前左缘对齐的索引（用于原生滚动同步）。 */
export function indexFromScrollLeft(scrollLeft, viewportWidth, pageCount) {
  var half = (Number(viewportWidth) || 0) / 2;
  if (half <= 0) return 0;
  return clampIndex(Math.round((Number(scrollLeft) || 0) / half), pageCount);
}

/** 是否可向前（左）翻——首页禁用。 */
export function canPrev(i) {
  return (Number(i) || 0) > 0;
}

/** 是否可向后（右）翻——末页禁用（D-10 clamp，禁止尾→封面拼版）。 */
export function canNext(i, pageCount) {
  return (Number(i) || 0) < (pageCount || 0) - 1;
}

/** 末页且为奇数页序列时，右半留白（杂志 bleed）。 */
export function isOddTail(pages, i) {
  var list = pages || [];
  var idx = clampIndex(i, list.length);
  return idx === list.length - 1;
}
