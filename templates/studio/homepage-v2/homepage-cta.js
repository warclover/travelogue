/**
 * UX-01 · 首页状态主按钮接线。
 */
import { V2, $ } from "./store.js";
import { trackStudioEvent } from "../js/analytics.js";
import { openImportSheet } from "./import-entry.js";
import { previewHref, resolveHomepageCta } from "./homepage-cta-logic.js";
import { runTripRecipeReexport } from "./shelf-outputs.js";

var _wired = false;

export function syncHomepageCta() {
  var resolved = resolveHomepageCta(V2.trips);
  var cta = $("v2-cta");
  var label = $("v2-cta-label");
  var chip = $("v2-cta-chip");
  var secondary = $("v2-cta-secondary");
  if (!cta) return resolved;
  if (label) label.textContent = resolved.primaryLabel;
  else cta.textContent = resolved.primaryLabel;
  cta.setAttribute("aria-label", resolved.primaryAria);
  cta.dataset.action = resolved.primaryAction;
  cta.dataset.tripId = (resolved.trip && resolved.trip.tripId) || "";
  if (chip) {
    chip.hidden = !resolved.chip;
    chip.textContent = resolved.chip || "";
  }
  if (secondary) {
    secondary.hidden = !resolved.secondaryLabel;
    secondary.textContent = resolved.secondaryLabel || "";
    secondary.dataset.action = resolved.secondaryAction || "";
    secondary.dataset.tripId = (resolved.trip && resolved.trip.tripId) || "";
  }
  return resolved;
}

function runCtaAction(action, tripId, surface) {
  var trip = (V2.trips || []).find(function (row) {
    return row && row.tripId === tripId;
  });
  if (action === "import") {
    trackStudioEvent("cta_click", { surface: surface, action: "import" });
    openImportSheet();
    return;
  }
  if (action === "demo") {
    trackStudioEvent("cta_click", { surface: surface, action: "demo" });
    import("./import-wizard.js").then(function (mod) {
      if (mod && typeof mod.startDemoAlbumImport === "function") {
        mod.startDemoAlbumImport({ source: "homepage_cta" });
      }
    });
    return;
  }
  if (action === "reexport_recipe" && trip) {
    trackStudioEvent("cta_click", {
      surface: surface,
      action: action,
      trip_id: trip.tripId,
      stale: true,
    });
    runTripRecipeReexport(trip, "homepage_cta");
    return;
  }
  if ((action === "preview" || action === "preview_export") && trip) {
    trackStudioEvent("cta_click", {
      surface: surface,
      action: action,
      trip_id: trip.tripId,
      stale: !!trip.longshotStale,
    });
    window.location.href = previewHref(trip, action === "preview_export");
  }
}

export function initHomepageCta() {
  if (_wired) return;
  _wired = true;
  var cta = $("v2-cta");
  if (cta) {
    cta.addEventListener("click", function () {
      var surface = cta.classList.contains("is-headline") ? "headline" : "bench";
      runCtaAction(cta.dataset.action || "import", cta.dataset.tripId, surface);
    });
  }
  var secondary = $("v2-cta-secondary");
  if (secondary) {
    secondary.addEventListener("click", function (ev) {
      ev.preventDefault();
      var surface = cta && cta.classList.contains("is-headline") ? "headline" : "bench";
      runCtaAction(
        secondary.dataset.action || "demo",
        secondary.dataset.tripId,
        surface
      );
    });
  }
}
