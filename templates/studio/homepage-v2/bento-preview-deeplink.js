/**
 * 首页 v2 · 预览画册 URL deep link（D-14 Phase 3 · ?preview=）。
 */
import { trackStudioEvent } from "../js/analytics.js";
import { persistBentoPreviewTripId } from "./store.js";

function urlParams() {
  try {
    return new URLSearchParams(window.location.search);
  } catch (e) {
    return new URLSearchParams("");
  }
}

/** @returns {string|null|undefined} undefined = 无参数；null = 示例作品 */
export function readPreviewDeepLinkTripId() {
  if (!urlParams().has("preview")) return undefined;
  var raw = urlParams().get("preview");
  if (raw === null || raw === "" || raw === "demo") return null;
  var id = String(raw).trim();
  return id || null;
}

export function stripPreviewDeepLinkParam() {
  try {
    var url = new URL(window.location.href);
    if (!url.searchParams.has("preview")) return;
    url.searchParams.delete("preview");
    var next = url.pathname + url.search + url.hash;
    window.history.replaceState(null, "", next);
  } catch (e) { /* ignore */ }
}

/**
 * 将 ?preview= 写入 localStorage preference（在 bootstrap 最早阶段调用）。
 * @returns {boolean} 是否处理了 preview 参数
 */
export function applyPreviewDeepLink() {
  var tripId = readPreviewDeepLinkTripId();
  if (tripId === undefined) return false;
  persistBentoPreviewTripId(tripId);
  stripPreviewDeepLinkParam();
  trackStudioEvent("bento_preview_select", {
    trip_id: tripId,
    source: "deeplink",
  });
  return true;
}
