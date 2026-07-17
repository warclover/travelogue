/**
 * Preview Toolbar · 长图纯逻辑（无 DOM / 无 fetch · node --test）
 * SFH W1 · 壳层见 longshot.js。
 */
"use strict";

/**
 * Trust V1 附录 D · 可读性启发式
 * @returns {null|{level:"soft"|"severe", reason:string}}
 */
export function assessMagazineTitleRisk(title) {
  var t = String(title || "").trim();
  if (!t) return { level: "severe", reason: "empty" };
  if (/[\uFFFD\u0000-\u0008]/.test(t) || /�/.test(t)) {
    return { level: "severe", reason: "garbled" };
  }
  if (t.length < 2) return { level: "severe", reason: "too_short" };
  if (t.length > 40) {
    var half = Math.floor(t.length / 2);
    if (t.slice(0, half) === t.slice(half, half * 2)) {
      return { level: "soft", reason: "repeat_long" };
    }
  }
  if (/\S\+\S/.test(t) && !/^[A-Za-z0-9]+\+[A-Za-z0-9]+/.test(t)) {
    return { level: "soft", reason: "plus_join" };
  }
  if (/\+\s|\s\+/.test(t) || /^\+|\+$/.test(t)) {
    return { level: "soft", reason: "plus_join" };
  }
  return null;
}

/** Trust V1 · F-TRU-EXP-04 / 附录 C.2 · 断服反馈文案 */
export function disconnectExportFeedback(tripId, pathname) {
  var href =
    tripId
      ? "/" + encodeURIComponent(String(tripId)) + "/"
      : pathname || "/";
  return {
    title: "服务已停止，长图还没有导出",
    subtitle: "请重新启动 Studio 后打开本游记，再点「长图」",
    linkText: "回到预览",
    linkHref: href,
  };
}

/**
 * @param {{ ts?: number }|null|undefined} data
 * @param {number} nowMs
 * @param {number} ttlMs
 */
export function isFlagExpired(data, nowMs, ttlMs) {
  if (!data || !data.ts) return true;
  return Number(nowMs) - Number(data.ts) > Number(ttlMs);
}

/**
 * 导出成功静音窗：同 trip 且 until 未过期 → active（壳层负责清存储）
 * @param {{ tripId?: string, until?: number }|null|undefined} data
 */
export function isExportSideEffectActiveFor(data, tripId, nowMs) {
  if (!data || String(data.tripId || "") !== String(tripId || "")) return false;
  var until = Number(data.until || 0);
  if (!until || Number(nowMs) > until) return false;
  return true;
}

/**
 * 是否应展示 longshot stale 主警告（D-REF-18 / Trust 静音窗）。
 * @param {{
 *   layoutPending?: boolean,
 *   sourceMissing?: boolean,
 *   sideEffectActive?: boolean,
 *   exportResultShowing?: boolean,
 *   longshotStale?: boolean
 * }} ctx
 */
export function shouldShowLongshotStale(ctx) {
  var c = ctx || {};
  if (c.layoutPending) return false;
  if (c.sourceMissing) return false;
  if (c.sideEffectActive) return false;
  if (c.exportResultShowing) return false;
  return !!c.longshotStale;
}

/**
 * revision / token 不一致 → stale（供本地对照；服务端 longshotStale 仍为权威信号源之一）
 * @param {{ contentRevision?: string|number|null, exportToken?: string|null }} current
 * @param {{ contentRevision?: string|number|null, exportToken?: string|null }} exported
 * 缺字段 fail-open：无法比较时视为非 stale（避免误升主警告）
 */
export function isLongshotContentStale(current, exported) {
  if (!current || !exported) return false;
  var curRev = current.contentRevision;
  var expRev = exported.contentRevision;
  if (curRev == null || expRev == null) return false;
  if (String(curRev) !== String(expRev)) return true;
  var curTok = current.exportToken;
  var expTok = exported.exportToken;
  if (curTok == null || expTok == null) return false;
  return String(curTok) !== String(expTok);
}
