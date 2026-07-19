/**
 * Share-Ready W2 · BE-SR-05 · 文件夹名 → 默认杂志标题（与 travelogue.domain.title_humanize 对齐）。
 * Share-Face Closeout W0 · D-SFC-03 / OQ-SFC-01。
 * 纯函数、无 DOM 依赖，可供 node --test 直接 import。
 */

var DEFAULT_TITLE = "我的旅途";
var KNOWN_SUFFIX =
  /\.(?:zip|jpe?g|png|gif|webp|heic|heif|bmp|tiff?|mov|mp4|avi|mkv|pdf|rar|7z)$/i;
var HASH_OR_TEST_SUFFIX =
  /[-_]?(?:[0-9a-f]{8,}|(?:ux-)?handtest[-_\w]*|demo[-_]?\d+|copy(?:\s*\(\d+\))?)$/i;
var NOISE_PREFIX = /^(新建文件夹|untitled|copy)\s*/i;
var HEXISH = /^[0-9a-f-]{8,}$/i;
var CJK_TRAILING_DIGIT = /[\u4e00-\u9fff]\d{1,3}$/;
var GLUED_ALNUM = /^[\u4e00-\u9fffA-Za-z]{2,}\d{1,3}$/;
var EXPORT_DIRISH = /(导出|download|dcim|camera roll|img_|vid_|screenshot)/i;
var DIRTY_SEP = /--|__|\.\./;
var LEADING_YEAR = /^(?:19|20)\d{2}/;
var TRAILING_SERIAL = /\d{1,3}$/;
var CJK_PLACE = /^[\u4e00-\u9fff]{2,6}$/;

/**
 * @param {string|null|undefined} raw
 * @param {{ limit?: number }} [opts]
 * @returns {string}
 */
export function humanizeFolderTitle(raw, opts) {
  var limit = opts && typeof opts.limit === "number" ? opts.limit : 20;
  var name = String(raw || "").trim();
  if (!name) return DEFAULT_TITLE;
  name = name.replace(KNOWN_SUFFIX, "");
  name = name.replace(HASH_OR_TEST_SUFFIX, "");
  name = name.replace(/[_\-.]+/g, " ").replace(/\s+/g, " ").trim();
  name = name.replace(NOISE_PREFIX, "").trim();
  if (!name || HEXISH.test(name)) return DEFAULT_TITLE;
  return name.length > limit ? name.slice(0, limit) : name;
}

/** BE-FST-06 · 中文启发式：像目录名噪音 */
export function isFolderTitleNoise(title) {
  var t = String(title || "").trim();
  if (!t || t === DEFAULT_TITLE) return false;
  if (DIRTY_SEP.test(t)) return true;
  if (EXPORT_DIRISH.test(t)) return true;
  if (CJK_TRAILING_DIGIT.test(t)) return true;
  if (t.indexOf(" ") < 0 && t.indexOf("·") < 0 && GLUED_ALNUM.test(t)) return true;
  return false;
}

/** OQ-SFC-01 · 抽取 2–6 字中文地名 */
export function extractPlaceLabel(raw) {
  var cleaned = humanizeFolderTitle(raw, { limit: 40 });
  if (!cleaned || cleaned === DEFAULT_TITLE) return null;
  var t = cleaned.replace(/\s+/g, "");
  t = t.replace(TRAILING_SERIAL, "");
  t = t.replace(LEADING_YEAR, "");
  t = t.replace(/^[\s·\-_.]+|[\s·\-_.]+$/g, "");
  if (CJK_PLACE.test(t)) return t;
  return null;
}

function _acceptDisplay(candidate, limit) {
  var t = String(candidate || "").trim();
  if (!t) return null;
  var cleaned = humanizeFolderTitle(t, { limit: limit });
  if (cleaned && cleaned !== DEFAULT_TITLE && !isFolderTitleNoise(cleaned)) {
    return cleaned;
  }
  return null;
}

function _placeFallbackLabel(meta) {
  var places = (meta && meta.places) || [];
  if (Array.isArray(places)) {
    for (var i = 0; i < places.length; i++) {
      var s = String(places[i] || "").trim();
      if (s && s !== "旅途" && s !== "未知" && s !== "这里") return s;
    }
  }
  return "旅行";
}

function _parseIsoYmd(value) {
  var parts = String(value || "")
    .trim()
    .slice(0, 10)
    .split("-");
  if (parts.length !== 3) return null;
  var y = parseInt(parts[0], 10);
  var m = parseInt(parts[1], 10);
  var d = parseInt(parts[2], 10);
  if (isNaN(y) || isNaN(m) || isNaN(d)) return null;
  return { y: y, m: m, d: d };
}

function _isCrossYearSpan(meta) {
  var start = _parseIsoYmd(meta && meta.dateStart);
  var end = _parseIsoYmd(meta && meta.dateEnd);
  return !!(start && end && start.y !== end.y);
}

/** Detect yearless spans like ``1月20–1月16日`` (cross-year smell). */
function _looksLikeYearlessDateSpan(label) {
  var t = String(label || "").trim();
  if (!t || t.indexOf("年") >= 0 || /(?:19|20)\d{2}/.test(t)) return false;
  return /\d{1,2}月\d{1,2}.+\d{1,2}月\d{1,2}/.test(t);
}

/** 与 BE ``_date_fallback_label`` 同源：同月日区间 / 跨年紧凑形，无日期回 "游记"。 */
function _dateFallbackLabel(meta) {
  var start = _parseIsoYmd(meta && meta.dateStart);
  if (!start) return "游记";
  var label = start.m + "月" + start.d + "日";
  var end = _parseIsoYmd(meta && meta.dateEnd);
  if (end && !(end.y === start.y && end.m === start.m && end.d === start.d)) {
    if (start.y !== end.y) {
      label =
        (start.y % 100) +
        "." +
        start.m +
        "." +
        start.d +
        "–" +
        (end.y % 100) +
        "." +
        end.m +
        "." +
        end.d;
    } else {
      label = start.m + "月" + start.d + "–" + end.m + "月" + end.d + "日";
    }
  }
  return label;
}

/** 与 BE ``_fallback_display`` 同源：``{地} · {日期}``（无地点→旅行，无日期→游记）。 */
function _fallbackDisplay(meta, limit) {
  var place = _placeFallbackLabel(meta);
  var datePart = _dateFallbackLabel(meta);
  var fallback = place + " · " + datePart;
  return fallback.length > limit ? fallback.slice(0, limit) : fallback;
}

/**
 * 与 BE ``resolve_display_title`` 同源（D-SFC-03）。
 * @param {{ displayTitle?: string, title?: string, places?: string[] }|null} meta
 * @param {{ limit?: number, rawTitle?: string }} [opts]
 */
export function resolveDisplayTitle(meta, opts) {
  opts = opts || {};
  var limit = typeof opts.limit === "number" ? opts.limit : 20;
  meta = meta || {};
  var stored = String(meta.displayTitle || "").trim();
  var accepted = _acceptDisplay(stored, limit);
  // Cross-year trips must not keep yearless spans like「1月20–1月16日」
  if (accepted && _isCrossYearSpan(meta) && _looksLikeYearlessDateSpan(accepted)) {
    accepted = null;
  }
  if (accepted) return accepted;

  var raw =
    opts.rawTitle != null
      ? String(opts.rawTitle || "").trim()
      : String(meta.title || "").trim();
  accepted = _acceptDisplay(raw, limit);
  if (accepted) return accepted;

  // 清洗后仍噪音：优先 meta 地点 → {地} · {日期}；否则文件夹地名抽取 → {地} · 旅行。
  var metaPlace = _placeFallbackLabel(meta);
  if (metaPlace !== "旅行") {
    return _fallbackDisplay(meta, limit);
  }

  var extracted = extractPlaceLabel(raw || stored);
  if (extracted) {
    var out = extracted + " · 旅行";
    return out.length > limit ? out.slice(0, limit) : out;
  }

  return _fallbackDisplay(meta, limit);
}
