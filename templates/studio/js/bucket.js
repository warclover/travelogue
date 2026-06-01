/**
 * Studio holdback 分桶 ID（v2/v3 共享 · 对齐 studio_homepage_gate.stable_bucket）。
 * 优先读服务端注入的 data-bucket-id；无则 UA SHA256。
 */
const BUCKET_SALT = "travelogue-studio-homepage-v2";

function bucketFromHex(hex) {
  return parseInt(hex.slice(0, 8), 16) % 100;
}

/** 服务端 HTML 注入的分桶（holdback 权威值）。 */
export function readServerBucketId() {
  try {
    var body = document.body;
    if (!body) return null;
    var raw = body.getAttribute("data-bucket-id");
    if (raw === null || raw === "" || raw.indexOf("__") === 0) return null;
    var n = parseInt(raw, 10);
    if (!Number.isNaN(n) && n >= 0 && n <= 99) return n;
  } catch (e) { /* ignore */ }
  return null;
}

/** → bucket 0–99 或 null（无 Web Crypto 时不猜测）。 */
export function resolveBucketId() {
  var fromServer = readServerBucketId();
  if (fromServer !== null) return Promise.resolve(fromServer);

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
  return Promise.resolve(null);
}
