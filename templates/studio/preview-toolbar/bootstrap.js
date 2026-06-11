/**
 * Travelogue Studio · preview page toolbar bootstrap (M-P2a).
 */
"use strict";

import { TOOLBAR_HTML } from "./templates.js";
import {
  bindToolbarCollapse,
  readStartCollapsed,
  setToolbarCollapsed,
} from "./shell.js";
import { initShareMinimal, isSharePreview } from "./share-mode.js";
import { tripIdFromPath } from "./toolbar-ui.js";
import { initPendingBar } from "./pending.js";
import { mountExportZone } from "./export-run.js";
import { showStaleHint, refreshPreviewCover } from "./export-state.js";
import { refreshStaleHint } from "./stale-sync.js";
import { exportZip } from "./menu.js";
import { startLlmNarrate } from "./narrate.js";
import { initPreviewDrawers } from "./drawers.js";
import { fetchEntry } from "./drawer-support.js";
import {
  applyLayoutRerender,
  initDisplayedAestheticTitles,
  initEditToolsMenu,
  initFeaturedStars,
  initCollageMediaControls,
  initPendingUndo,
  initTemplateBadge,
  revealTripFolder,
} from "./mode-edit.js";
import {
  initG1Banner,
  initG1ReaderPill,
  initPreviewModeSeg,
} from "./mode-reader.js";

function initTripIdentity(root, tripId) {
  var titleEl = root.querySelector(".preview-toolbar__trip-title");
  var metaEl = root.querySelector(".preview-toolbar__trip-meta");
  if (titleEl) {
    var title = (document.title || "").trim();
    if (title) titleEl.textContent = title;
  }
  if (metaEl) {
    fetchEntry(tripId)
      .then(function (data) {
        var parts = [];
        if (data && data.photoCount) parts.push(data.photoCount + " 张");
        if (data && data.template && data.template.sourceLabel) {
          parts.push(data.template.sourceLabel);
        }
        if (parts.length) metaEl.textContent = parts.join(" · ");
      })
      .catch(function () {});
  }
}

function initToolbar(root) {
  var tripId = tripIdFromPath();
  if (!tripId) return;

  initTripIdentity(root, tripId);

  var bar = root.querySelector(".preview-toolbar__bar");
  var centerActions =
    root.querySelector(".preview-toolbar__center .preview-toolbar__actions") ||
    root.querySelector(".preview-toolbar__actions") ||
    bar;
  var menuBtn = root.querySelector(".preview-toolbar__menu-btn");
  var menu = root.querySelector(".preview-toolbar__more-menu");

  initTemplateBadge(root, tripId);
  var drawers = initPreviewDrawers(root, tripId);
  initPreviewModeSeg(root, centerActions, drawers);
  initEditToolsMenu(root, tripId, drawers);
  initG1Banner(root, tripId, drawers);
  initG1ReaderPill(root, tripId);
  initPendingBar(root);
  initPendingUndo(tripId);
  initDisplayedAestheticTitles(tripId);

  var exportWrap = mountExportZone(root, tripId);

  var pendingApply = root.querySelector(".preview-toolbar__pending-apply");
  if (pendingApply) {
    pendingApply.addEventListener("click", function () {
      applyLayoutRerender(tripId, root);
    });
  }

  root.querySelectorAll(".preview-toolbar__reveal-folder").forEach(function (btn) {
    btn.addEventListener("click", function () {
      if (menu) {
        menu.hidden = true;
        menuBtn.setAttribute("aria-expanded", "false");
      }
      revealTripFolder(tripId);
    });
  });

  if (window.location.search.indexOf("focus=longshot") >= 0) {
    setToolbarCollapsed(root, false, false);
    requestAnimationFrame(function () {
      if (exportWrap) exportWrap.scrollIntoView({ behavior: "smooth", block: "center" });
      var longshotBtn = root.querySelector(".preview-toolbar__longshot--main");
      if (longshotBtn) {
        longshotBtn.focus();
        longshotBtn.classList.add("preview-toolbar__longshot--focus");
      }
    });
  }

  if (menu && menuBtn) {
    var applyBtn = menu.querySelector(".preview-toolbar__apply-layout");
    var presentBtn = menu.querySelector(".preview-toolbar__present-featured");
    var llmSlot = menu.querySelector(".preview-toolbar__llm-slot");
    var zipBtn = menu.querySelector(".preview-toolbar__export-zip");

    function closeMenu() {
      menu.hidden = true;
      menuBtn.setAttribute("aria-expanded", "false");
    }

    menuBtn.addEventListener("click", function (e) {
      e.stopPropagation();
      var willOpen = menu.hidden;
      menu.hidden = !willOpen;
      menuBtn.setAttribute("aria-expanded", willOpen ? "true" : "false");
    });

    if (applyBtn) {
      applyBtn.hidden = true;
      applyBtn.addEventListener("click", function () {
        closeMenu();
        applyLayoutRerender(tripId, root);
      });
    }
    if (presentBtn) {
      presentBtn.hidden = true;
    }
    if (zipBtn) {
      zipBtn.addEventListener("click", function () {
        closeMenu();
        exportZip(tripId);
      });
    }

    var collapseMenuBtn = menu.querySelector(".preview-toolbar__more-collapse");
    if (collapseMenuBtn) {
      collapseMenuBtn.addEventListener("click", function () {
        closeMenu();
        setToolbarCollapsed(root, true);
      });
    }

    fetch("/__travelogue/config")
      .then(function (resp) { return resp.json(); })
      .then(function (cfg) {
        if (!cfg.llmAvailable || !llmSlot) return;
        var llmBtn = document.createElement("button");
        llmBtn.type = "button";
        llmBtn.className = "preview-toolbar__llm";
        llmBtn.textContent = "生成杂志感文案";
        llmBtn.addEventListener("click", function () {
          closeMenu();
          startLlmNarrate(root, tripId, llmBtn);
        });
        llmSlot.appendChild(llmBtn);
      })
      .catch(function () {});

    document.addEventListener("click", function (ev) {
      if (!menu.contains(ev.target) && !menuBtn.contains(ev.target)) {
        closeMenu();
      }
    });
  }

  refreshStaleHint(root, tripId);
  refreshPreviewCover(root);
  fetchEntry(tripId).then(function (data) {
    initFeaturedStars(tripId);
    initCollageMediaControls(tripId, (data && data.assetMediaById) || {});
  });

  window.addEventListener("travelogue:copy-saved", function () {
    showStaleHint(root);
  });
}

export function initPreviewToolbar() {
  if (isSharePreview()) {
    initShareMinimal();
    return;
  }

  document.documentElement.setAttribute("data-preview-toolbar", "on");

  var root = document.createElement("div");
  root.className = "preview-toolbar";
  root.innerHTML = TOOLBAR_HTML;

  document.body.insertBefore(root, document.body.firstChild);
  bindToolbarCollapse(root);
  initToolbar(root);

  var focusLongshot = window.location.search.indexOf("focus=longshot") >= 0;
  setToolbarCollapsed(root, readStartCollapsed(focusLongshot), false);
}

