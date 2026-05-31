/**
 * Travelogue Studio · server-reported capabilities (P10-L08).
 * Separate from data-studio-layout (viewport).
 */
"use strict";

import { trackStudioEvent } from "./analytics.js";

export function applyStudioCapabilities(data) {
  if (!data || !data.capabilities) return;
  var pick = !!data.capabilities.pickFolder;
  document.documentElement.setAttribute("data-cap-pick-folder", pick ? "on" : "off");
  if (!pick) {
    var alt = document.getElementById("studio-sheet-alt-import");
    if (alt) alt.open = true;
  }
  try {
    if (!sessionStorage.getItem("travelogue.studio.capLogged")) {
      sessionStorage.setItem("travelogue.studio.capLogged", "1");
      trackStudioEvent("studio_capabilities", { pickFolder: pick });
    }
  } catch (e) { /* ignore */ }
}

export function initStudioCapabilities() {
  return fetch("/__travelogue/config")
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (data) {
      applyStudioCapabilities(data);
      return data;
    })
    .catch(function () {});
}
