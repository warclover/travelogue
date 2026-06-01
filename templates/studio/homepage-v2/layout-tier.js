/**
 * 首页 v2 · 性能降级层级（PRD §12.4 / DATA-CONTRACT §4.2）。
 *
 * L0 默认 · L1 reduced-motion · L2 saveData/慢网 · L3 assets 失败
 */

function harnessSlowNetOverride() {
  try {
    var body = document.body;
    if (!body || body.getAttribute("data-studio-dev") !== "1") return false;
    return new URLSearchParams(location.search).get("studioSlowNet") === "1";
  } catch (e) {
    return false;
  }
}

function prefersReducedMotion() {
  try {
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  } catch (e) {
    return false;
  }
}

function slowConnection() {
  try {
    var conn = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
    if (!conn) return false;
    if (conn.saveData === true) return true;
    var et = conn.effectiveType || "";
    return et === "slow-2g" || et === "2g";
  } catch (e) {
    return false;
  }
}

/**
 * @param {{ manifestError?: boolean }} [opts]
 * @returns {"L0"|"L1"|"L2"|"L3"}
 */
export function resolveLayoutTier(opts) {
  opts = opts || {};
  if (opts.manifestError) return "L3";
  if (opts.harnessSlowNet || harnessSlowNetOverride()) return "L2";
  if (prefersReducedMotion()) return "L1";
  if (slowConnection()) return "L2";
  return "L0";
}

/** carousel L2：仅 eager 加载前 2 屏（index 0..1）。 */
export function shouldEagerCarouselPage(index, tier) {
  if (tier !== "L2") return true;
  return index <= 1;
}
