/**
 * Preview toolbar · shell / collapse (M-P2b).
 */
"use strict";

import { loadCollapsed, persistCollapsed, setPreviewStore } from "./store.js";

export var TOOLBAR_BAR_HEIGHT_PX = 56;

export function toolbarBody(root) {
  return root.querySelector(".preview-toolbar__body") || root;
}

/** 顶栏主行恒 56px；pending 行不计入 scroll-padding（§6.4 B-10）。 */
export function syncToolbarHeight(root) {
  var collapsed = root.classList.contains("preview-toolbar--collapsed");
  if (collapsed) {
    var strip = root.querySelector(".preview-toolbar__collapsed-strip");
    var sh = (strip && strip.offsetHeight) || 32;
    root.style.height = sh + "px";
    document.documentElement.style.setProperty("--preview-toolbar-h", sh + "px");
    return;
  }
  root.style.height = "";
  document.documentElement.style.setProperty(
    "--preview-toolbar-h",
    TOOLBAR_BAR_HEIGHT_PX + "px"
  );
}

export function setToolbarCollapsed(root, collapsed, persist) {
  root.classList.toggle("preview-toolbar--collapsed", collapsed);
  document.documentElement.setAttribute(
    "data-preview-toolbar-collapsed",
    collapsed ? "on" : "off"
  );
  var handle = root.querySelector(".preview-toolbar__handle");
  var collapseBtn = root.querySelector(".preview-toolbar__collapse");
  if (handle) handle.setAttribute("aria-expanded", collapsed ? "false" : "true");
  if (collapseBtn) collapseBtn.setAttribute("aria-expanded", collapsed ? "false" : "true");
  setPreviewStore({ collapsed: collapsed });
  if (persist !== false) persistCollapsed(collapsed);
  requestAnimationFrame(function () {
    syncToolbarHeight(root);
  });
}

export function bindToolbarCollapse(root) {
  var handle = root.querySelector(".preview-toolbar__handle");
  var collapseBtn = root.querySelector(".preview-toolbar__collapse");
  if (handle) {
    handle.addEventListener("click", function () {
      setToolbarCollapsed(root, false);
    });
  }
  if (collapseBtn) {
    collapseBtn.addEventListener("click", function () {
      setToolbarCollapsed(root, true);
    });
  }
  if (typeof ResizeObserver !== "undefined") {
    var ro = new ResizeObserver(function () {
      syncToolbarHeight(root);
    });
    ro.observe(root);
  }
  window.addEventListener("resize", function () {
    syncToolbarHeight(root);
  });
}

export function readStartCollapsed(focusLongshot) {
  if (focusLongshot) return false;
  return loadCollapsed();
}
