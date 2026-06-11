/**
 * 首页 v2 · 书架 resume 区 CTA 纯逻辑（无 DOM · node --test）。
 *
 * @typedef {object} ShelfResumeAction
 * @property {"longshot"|"algorithm"|"open"} kind
 * @property {string} label
 * @property {boolean} primary
 * @property {boolean} [focusLongshot]
 * @property {boolean} [triggerCurate]
 */

/**
 * @param {{ longshotStale?: boolean, algorithmStale?: boolean, layoutCssStale?: boolean }} trip
 * @returns {ShelfResumeAction[]}
 */
export function shelfResumeActions(trip) {
  trip = trip || {};
  var actions = [];
  if (trip.longshotStale) {
    actions.push({
      kind: "longshot",
      label: "更新长图",
      primary: true,
      focusLongshot: true,
    });
  }
  if (trip.algorithmStale) {
    actions.push({
      kind: "algorithm",
      label: "重新排版",
      primary: !trip.longshotStale,
      triggerCurate: true,
    });
  }
  if (trip.layoutCssStale) {
    actions.push({
      kind: "layout",
      label: "更新布局",
      primary: !trip.longshotStale && !trip.algorithmStale,
    });
  }
  actions.push({
    kind: "open",
    label: "打开预览",
    primary: !trip.longshotStale && !trip.algorithmStale && !trip.layoutCssStale,
  });
  return actions;
}

/**
 * Bento「最近一本」是否应展示 stale 提示条（算法或布局 CSS 过期）。
 * @param {{ algorithmStale?: boolean, layoutCssStale?: boolean }} trip
 * @returns {boolean}
 */
export function shouldShowBentoStaleBar(trip) {
  return !!(trip && (trip.algorithmStale || trip.layoutCssStale));
}

/**
 * Bento stale 条主操作：recurate 重新排版 | preview 打开预览应用排版。
 * @param {{ algorithmStale?: boolean, layoutCssStale?: boolean }} trip
 * @returns {"recurate"|"preview"|null}
 */
export function bentoStaleActionKind(trip) {
  trip = trip || {};
  if (trip.algorithmStale) return "recurate";
  if (trip.layoutCssStale) return "preview";
  return null;
}

/**
 * @param {{ staleHint?: string, staleHints?: string[], algorithmStale?: boolean, layoutCssStale?: boolean }} trip
 * @returns {string}
 */
export function bentoStaleMessage(trip) {
  trip = trip || {};
  if (trip.staleHint) return String(trip.staleHint);
  var hints = trip.staleHints;
  if (Array.isArray(hints) && hints.length) return String(hints[0]);
  if (trip.algorithmStale) {
    return "排版算法已更新，建议重新排版以刷新预览";
  }
  if (trip.layoutCssStale) {
    return "布局待更新，请在预览中应用排版";
  }
  return "排版算法已更新，建议重新排版以刷新预览";
}
