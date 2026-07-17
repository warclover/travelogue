/**
 * Share-Ready W2 · BE-SR-05 · 文件夹名 → 默认杂志标题（与 travelogue.domain.title_humanize 对齐）。
 * 纯函数、无 DOM 依赖，可供 node --test 直接 import。
 */

var DEFAULT_TITLE = "我的旅途";
var KNOWN_SUFFIX =
  /\.(?:zip|jpe?g|png|gif|webp|heic|heif|bmp|tiff?|mov|mp4|avi|mkv|pdf|rar|7z)$/i;
var HASH_OR_TEST_SUFFIX =
  /[-_]?(?:[0-9a-f]{8,}|(?:ux-)?handtest[-_\w]*|demo[-_]?\d+|copy(?:\s*\(\d+\))?)$/i;
var NOISE_PREFIX = /^(新建文件夹|untitled|copy)\s*/i;
var HEXISH = /^[0-9a-f-]{8,}$/i;

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

var CJK_TRAILING_DIGIT = /[\u4e00-\u9fff]\d{1,3}$/;
var GLUED_ALNUM = /^[\u4e00-\u9fffA-Za-z]{2,}\d{1,3}$/;
var EXPORT_DIRISH = /(导出|download|dcim|camera roll|img_|vid_|screenshot)/i;

/** BE-FST-06 · 中文启发式：像目录名噪音 */
export function isFolderTitleNoise(title) {
  var t = String(title || "").trim();
  if (!t || t === DEFAULT_TITLE) return false;
  if (EXPORT_DIRISH.test(t)) return true;
  if (CJK_TRAILING_DIGIT.test(t)) return true;
  if (t.indexOf(" ") < 0 && t.indexOf("·") < 0 && GLUED_ALNUM.test(t)) return true;
  return false;
}
