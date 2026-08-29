/**
 * 书架票根装饰编号（非安全用途）。
 * 纯函数抽出，便于单测：避免弱混合导致不同 tripId 撞码。
 */

/** FNV-1a 32-bit. */
export function stubFingerprint(text) {
  var s = String(text || "");
  var h = 2166136261;
  for (var i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}

/**
 * 票根脚「NO.YYYY####」装饰序号。
 * @param {{ tripId?: string, title?: string, updatedAt?: number, photoCount?: number }|null} trip
 */
export function stubSerial(trip) {
  var yearBit = stubYearMonth(trip && trip.updatedAt);
  var year = yearBit ? yearBit.slice(0, 4) : String(new Date().getFullYear());
  var seed =
    String((trip && trip.tripId) || "") +
    "\0" +
    String((trip && trip.title) || "") +
    "\0" +
    String((trip && trip.photoCount) || 0);
  var n = stubFingerprint(seed) % 10000;
  var suffix = ("0000" + n).slice(-4);
  return "NO." + year + suffix;
}

/**
 * 票根右侧 8 位花体码。
 * 前 4 位吃 tripId 哈希、后 4 位吃 title+张数 哈希，逐次右移 5 bit，
 * 避免「只读低 5 位 + LCG」导致不同种子锁死同码。
 * @param {{ tripId?: string, title?: string, photoCount?: number }|string|null} tripOrId
 */
export function stubCode(tripOrId) {
  var alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
  var tripId = "";
  var title = "";
  var photoCount = 0;
  if (tripOrId && typeof tripOrId === "object") {
    tripId = String(tripOrId.tripId || "");
    title = String(tripOrId.title || "");
    photoCount = Number(tripOrId.photoCount) || 0;
  } else {
    tripId = String(tripOrId || "");
  }
  var h1 = stubFingerprint(tripId);
  var h2 = stubFingerprint(title + "\0" + photoCount + "\0" + tripId);
  var out = "";
  var i;
  for (i = 0; i < 4; i++) {
    out += alphabet[h1 & 31];
    h1 >>>= 5;
  }
  for (i = 0; i < 4; i++) {
    out += alphabet[h2 & 31];
    h2 >>>= 5;
  }
  return out;
}

export function stubYearMonth(ts) {
  if (!ts) return "";
  var d = new Date(ts * 1000);
  if (isNaN(d.getTime())) return "";
  var m = d.getMonth() + 1;
  return d.getFullYear() + " · " + (m < 10 ? "0" + m : String(m));
}

/** 票根副行：年月 · 张数。形态不进这一行（C15 单独露）。 */
export function stubFactsLine(trip) {
  var bits = [];
  var ym = stubYearMonth(trip && trip.updatedAt);
  if (ym) bits.push(ym);
  if (trip && trip.photoCount) bits.push(trip.photoCount + " 张");
  return bits.join(" · ");
}
