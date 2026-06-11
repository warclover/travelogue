/**
 * Preview toolbar · shared UI + trip path helpers (M-P2b).
 */
"use strict";

import { postJson } from "../js/http.js";

var _toastTimer = null;

export function tripIdFromPath() {
  var parts = window.location.pathname.replace(/^\/+|\/+$/g, "").split("/");
  return parts[0] || "";
}

export function tripApiBase(tripId) {
  return "/" + encodeURIComponent(tripId) + "/__travelogue";
}

export function revealTripPath(tripId, relPath) {
  return postJson("/__travelogue/reveal", { tripId: tripId, relPath: relPath });
}

export function toolbarConfirm(opts) {
  if (typeof studioModal === "function") {
    return studioModal(opts);
  }
  var msg = (opts.title ? opts.title + "\n\n" : "") + (opts.body || "");
  return Promise.resolve(window.confirm(msg));
}

export function toolbarAlert(message, opts) {
  opts = opts || {};
  if (message) showToolbarToast(message, { error: !!opts.error });
}

export function showToolbarToast(message, opts) {
  opts = opts || {};
  var el = document.getElementById("preview-toolbar-toast");
  if (!el) {
    el = document.createElement("p");
    el.id = "preview-toolbar-toast";
    el.className = "preview-toolbar__toast";
    el.setAttribute("role", "status");
    el.hidden = true;
    document.body.appendChild(el);
  }
  el.textContent = message;
  el.classList.toggle("preview-toolbar__toast--error", !!opts.error);
  el.hidden = false;
  clearTimeout(_toastTimer);
  _toastTimer = setTimeout(function () {
    el.hidden = true;
  }, opts.duration || (opts.error ? 5000 : 2800));
}

export function setSlowHint(root, text, visible) {
  var el = root.querySelector(".preview-toolbar__slow-hint");
  if (!el) {
    el = document.createElement("span");
    el.className = "preview-toolbar__slow-hint";
    el.hidden = true;
    var actions = root.querySelector(".preview-toolbar__actions");
    if (actions) actions.appendChild(el);
  }
  el.hidden = !visible;
  el.textContent = text || "";
}
