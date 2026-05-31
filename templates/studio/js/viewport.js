/**
 * Travelogue Studio · viewport layout tier (P10-Layout).
 * Sets html[data-studio-layout=wide|tablet|compact] — not UA sniffing.
 */
"use strict";

import { trackStudioEvent } from "./analytics.js";

export const LAYOUT_BREAKPOINTS = {
  compactMax: 768,
  tabletMax: 980,
};

export function layoutTierForWidth(width) {
  var w = width || 0;
  if (w <= LAYOUT_BREAKPOINTS.compactMax) return "compact";
  if (w <= LAYOUT_BREAKPOINTS.tabletMax) return "tablet";
  return "wide";
}

export function getStudioLayout() {
  return (
    document.documentElement.getAttribute("data-studio-layout") ||
    layoutTierForWidth(window.innerWidth || document.documentElement.clientWidth)
  );
}

export function syncStudioLayout() {
  var tier = layoutTierForWidth(
    window.innerWidth || document.documentElement.clientWidth
  );
  document.documentElement.setAttribute("data-studio-layout", tier);
  return tier;
}

export function initViewport() {
  syncStudioLayout();
  function onLayoutChange() {
    var prev = document.documentElement.getAttribute("data-studio-layout");
    var tier = syncStudioLayout();
    if (tier !== prev) {
      trackStudioEvent("layout_tier", { tier: tier, from: prev || null });
    }
    try {
      window.dispatchEvent(new CustomEvent("travelogue:studio-layout"));
    } catch (e) { /* ignore */ }
  }
  if (typeof window.matchMedia === "function") {
    var mqTablet = window.matchMedia(
      "(max-width: " + LAYOUT_BREAKPOINTS.tabletMax + "px)"
    );
    if (mqTablet.addEventListener) {
      mqTablet.addEventListener("change", onLayoutChange);
    } else if (mqTablet.addListener) {
      mqTablet.addListener(onLayoutChange);
    }
  }
  window.addEventListener("resize", onLayoutChange);
}
