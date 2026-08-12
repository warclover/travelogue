/**
 * Preview toolbar · entry bootstrap (v4 shell mount + DOM ready).
 */
"use strict";

import { dockIconSvg } from "./dock.js";
import {
  isSharePreview,
  initShareMinimal,
  ensureCoverMobileFootnote,
} from "./share.js";
import { tripIdFromPath } from "./shell.js";
import { initPreviewNarrowGate } from "./narrow-gate.js";

var _initToolbarV3 = function (_root, _tripId) {};

export function registerBootstrapBridge(api) {
  if (typeof api.initToolbarV3 === "function") _initToolbarV3 = api.initToolbarV3;
}

export function initPreviewToolbar() {
  if (isSharePreview()) {
    initShareMinimal();
    return;
  }

  document.documentElement.setAttribute("data-preview-toolbar", "on");

  var root = document.createElement("div");
  root.className = "preview-toolbar preview-toolbar--v4";
  root.innerHTML =
    '<nav class="preview-toolbar__dock preview-toolbar__dock--ink-glass" aria-label="预览快捷操作">' +
    '<a class="preview-toolbar__dock-btn preview-toolbar__dock-btn--back preview-toolbar__dock-btn--labeled preview-toolbar__ctl" href="/" aria-label="返回">' +
    dockIconSvg("back") +
    '<span class="preview-toolbar__dock-label">返回</span>' +
    "</a>" +
    '<span class="preview-toolbar__dock-divider" aria-hidden="true"></span>' +
    '<div class="preview-toolbar__menu-wrap">' +
    '<button type="button" class="preview-toolbar__menu-btn preview-toolbar__dock-btn preview-toolbar__dock-btn--menu preview-toolbar__dock-btn--folio preview-toolbar__dock-btn--labeled" aria-haspopup="dialog" aria-expanded="false" aria-label="精修">' +
    dockIconSvg("refine") +
    '<span class="preview-toolbar__dock-label">精修</span>' +
    "</button>" +
    "</div>" +
    "</nav>";

  document.body.insertBefore(root, document.body.firstChild);
  ensureCoverMobileFootnote();
  // PMX FE-PMX-20 · Studio 预览窄屏诚实门面（Share 模式已提前 return）
  initPreviewNarrowGate();
  var tripId = tripIdFromPath();
  if (!tripId) return;
  _initToolbarV3(root, tripId);
}

export function bootstrapPreviewToolbarWhenReady() {
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initPreviewToolbar);
  } else {
    initPreviewToolbar();
  }
}
