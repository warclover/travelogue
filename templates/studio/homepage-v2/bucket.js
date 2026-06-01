/**
 * 首页 v2 · holdback 分桶 ID（对齐 studio_homepage_gate.stable_bucket）。
 */
const BUCKET_SALT = "travelogue-studio-homepage-v2";

function bucketFromHex(hex) {
  return parseInt(hex.slice(0, 8), 16) % 100;
}

/** 与服务端 SHA256(盐:UA) 一致；无 Web Crypto 时用弱回退（仅 dev）。 */
export function resolveBucketId() {
  var ua = navigator.userAgent || "unknown";
  var text = BUCKET_SALT + ":" + ua;
  if (window.crypto && crypto.subtle && TextEncoder) {
    var enc = new TextEncoder().encode(text);
    return crypto.subtle.digest("SHA-256", enc).then(function (buf) {
      var arr = Array.from(new Uint8Array(buf));
      var hex = arr.map(function (b) { return b.toString(16).padStart(2, "0"); }).join("");
      return bucketFromHex(hex);
    });
  }
  return Promise.resolve(fallbackBucket(text));
}

function fallbackBucket(text) {
  var h = 0;
  for (var i = 0; i < text.length; i++) {
    h = ((h << 5) - h + text.charCodeAt(i)) | 0;
  }
  return Math.abs(h) % 100;
}
