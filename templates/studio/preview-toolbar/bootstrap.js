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
    '<nav class="preview-toolbar__dock" aria-label="预览快捷操作">' +
    '<a class="preview-toolbar__dock-btn preview-toolbar__dock-btn--back preview-toolbar__ctl" href="/" aria-label="返回" title="返回 Studio 首页">' +
    dockIconSvg("back") +
    "</a>" +
    '<span class="preview-toolbar__dock-divider" aria-hidden="true"></span>' +
    '<div class="preview-toolbar__menu-wrap">' +
    '<button type="button" class="preview-toolbar__menu-btn preview-toolbar__dock-btn preview-toolbar__dock-btn--menu preview-toolbar__dock-btn--folio" aria-haspopup="dialog" aria-expanded="false" aria-label="编辑与设置" title="编辑与设置">' +
    dockIconSvg("settings") +
    "</button>" +
    "</div>" +
    "</nav>";

  document.body.insertBefore(root, document.body.firstChild);
  ensureCoverMobileFootnote();
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
