/**
 * SNR · 成册叙事姿态条（D-SNR-01/02 · chrome，不进 screen copy region）。
 */
"use strict";

import { fetchEntry } from "./core.js";
import { trackStudioEvent } from "../js/analytics.js";

var COPY = {
  photoLed: "纯照片成册",
  upgradeReady: "纯照片成册 · 可生成杂志感文案",
  upgradeCta: "生成杂志感文案",
  helpLink: "如何升级文案",
};

/**
 * @param {HTMLElement} root
 * @param {string} tripId
 */
export function mountNarrativePostureBar(root, tripId) {
  if (!root || !tripId) return null;
  if (root._narrativePostureBar) return root._narrativePostureBar;

  var el = null;

  function removeBar() {
    if (el && el.parentNode) el.parentNode.removeChild(el);
    el = null;
    root._narrativePostureEl = null;
  }

  function openUpgrade() {
    trackStudioEvent("snr_upgrade_cta_click", {
      source: "banner",
      tripId: tripId || null,
      posture: "upgrade_ready",
    });
    var sheet = root._aiSheet;
    if (sheet && typeof sheet.open === "function") {
      sheet.open({ source: "snr_posture", focus: "narrate" });
      return;
    }
    import("/__studio/js/help-drawer.js")
      .then(function (mod) {
        if (mod && typeof mod.openHelpDrawer === "function") {
          mod.openHelpDrawer({ source: "snr_posture", itemId: "H7" });
        }
      })
      .catch(function () {});
  }

  function openHelp() {
    trackStudioEvent("snr_posture_help_click", {
      tripId: tripId || null,
      posture: "photo_led",
    });
    import("/__studio/js/help-drawer.js")
      .then(function (mod) {
        if (mod && typeof mod.openHelpDrawer === "function") {
          mod.openHelpDrawer({ source: "snr_posture", itemId: "H7" });
        }
      })
      .catch(function () {});
  }

  function render(posture) {
    removeBar();
    if (!posture || posture === "narrative_ready") return null;

    el = document.createElement("div");
    el.className = "preview-toolbar__posture-bar preview-toolbar__posture-bar--v4";
    el.setAttribute("role", "status");
    el.setAttribute("data-narrative-posture", posture);

    var text = document.createElement("span");
    text.className = "preview-toolbar__posture-bar-text";
    text.textContent =
      posture === "upgrade_ready" ? COPY.upgradeReady : COPY.photoLed;
    el.appendChild(text);

    if (posture === "upgrade_ready") {
      var cta = document.createElement("button");
      cta.type = "button";
      cta.className = "preview-toolbar__posture-bar-cta";
      cta.textContent = COPY.upgradeCta;
      cta.addEventListener("click", function (e) {
        e.stopPropagation();
        openUpgrade();
      });
      el.appendChild(cta);
    } else {
      var help = document.createElement("button");
      help.type = "button";
      help.className = "preview-toolbar__posture-bar-help";
      help.textContent = COPY.helpLink;
      help.addEventListener("click", function (e) {
        e.stopPropagation();
        openHelp();
      });
      el.appendChild(help);
    }

    document.body.appendChild(el);
    root._narrativePostureEl = el;
    trackStudioEvent("snr_posture_impression", {
      tripId: tripId || null,
      posture: posture,
    });
    return el;
  }

  function refresh() {
    return fetchEntry(tripId)
      .then(function (entry) {
        var posture = (entry && entry.narrativePosture) || "photo_led";
        render(posture);
        return posture;
      })
      .catch(function () {
        render("photo_led");
        return "photo_led";
      });
  }

  var api = {
    refresh: refresh,
    remove: removeBar,
  };
  root._narrativePostureBar = api;
  refresh();
  return api;
}
