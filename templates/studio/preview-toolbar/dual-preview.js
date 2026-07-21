/**
 * LTN R-B3 · dual preview: scroll (index.html) vs longshot (index-longshot.html)
 * at capture width 428px. Opened from export settings (AC-B-03).
 */
"use strict";

var CAPTURE_WIDTH = 428;

function _tripIdFromPath() {
  var parts = (location.pathname || "").split("/").filter(Boolean);
  return parts.length ? parts[0] : "";
}

function _ensureOverlay() {
  var el = document.getElementById("ltn-dual-preview");
  if (el) return el;
  el = document.createElement("div");
  el.id = "ltn-dual-preview";
  el.className = "ltn-dual-preview";
  el.hidden = true;
  el.setAttribute("role", "dialog");
  el.setAttribute("aria-modal", "true");
  el.setAttribute("aria-label", "对比网页与长图");
  el.innerHTML =
    '<div class="ltn-dual-preview__scrim" data-dual-close></div>' +
    '<div class="ltn-dual-preview__panel">' +
    '<header class="ltn-dual-preview__head">' +
    "<h2>对比网页与长图</h2>" +
    '<p class="ltn-dual-preview__note">同宽 ' +
    CAPTURE_WIDTH +
    "px，差异诚实可见（不改排版）</p>" +
    '<div class="ltn-dual-preview__toggle" role="tablist">' +
    '<button type="button" class="is-active" data-dual-tab="both">并排</button>' +
    '<button type="button" data-dual-tab="web">网页</button>' +
    '<button type="button" data-dual-tab="longshot">长图</button>' +
    "</div>" +
    '<button type="button" class="ltn-dual-preview__close" data-dual-close aria-label="关闭">×</button>' +
    "</header>" +
    '<div class="ltn-dual-preview__frames" data-dual-mode="both">' +
    '<figure class="ltn-dual-preview__frame" data-frame="web">' +
    "<figcaption>网页预览</figcaption>" +
    '<div class="ltn-dual-preview__phone">' +
    '<iframe title="网页预览" data-dual-iframe="web" sandbox="allow-same-origin allow-scripts"></iframe>' +
    "</div></figure>" +
    '<figure class="ltn-dual-preview__frame" data-frame="longshot">' +
    "<figcaption>微信长图</figcaption>" +
    '<div class="ltn-dual-preview__phone">' +
    '<iframe title="长图预览" data-dual-iframe="longshot" sandbox="allow-same-origin allow-scripts"></iframe>' +
    "</div></figure>" +
    "</div>" +
    '<p class="ltn-dual-preview__hint" data-dual-hint hidden></p>' +
    "</div>";
  document.body.appendChild(el);

  el.addEventListener("click", function (e) {
    var t = e.target;
    if (t && t.getAttribute && t.getAttribute("data-dual-close") != null) {
      closeDualPreview();
      return;
    }
    var tab = t && t.closest ? t.closest("[data-dual-tab]") : null;
    if (tab) {
      var mode = tab.getAttribute("data-dual-tab") || "both";
      el.querySelectorAll("[data-dual-tab]").forEach(function (btn) {
        var on = btn === tab;
        btn.classList.toggle("is-active", on);
        btn.setAttribute("aria-selected", on ? "true" : "false");
      });
      var frames = el.querySelector(".ltn-dual-preview__frames");
      if (frames) frames.setAttribute("data-dual-mode", mode);
    }
  });

  document.addEventListener("keydown", function onKey(e) {
    if (e.key === "Escape" && !el.hidden) {
      closeDualPreview();
    }
  });

  return el;
}

/**
 * @param {string} [tripId]
 */
export function openDualPreview(tripId) {
  var tid = String(tripId || _tripIdFromPath() || "").trim();
  if (!tid) return;
  var el = _ensureOverlay();
  var web = el.querySelector('[data-dual-iframe="web"]');
  var ls = el.querySelector('[data-dual-iframe="longshot"]');
  var hint = el.querySelector("[data-dual-hint]");
  var webUrl = "/" + encodeURIComponent(tid) + "/index.html?share=1";
  var lsUrl = "/" + encodeURIComponent(tid) + "/index-longshot.html";
  if (web) web.src = webUrl;
  if (ls) {
    ls.src = lsUrl;
    ls.onload = function () {
      // SFI · 尽量套上 capturing 根，使长图侧更接近导出态（紧凑 CSS 已绑 density）
      try {
        var doc = ls.contentDocument;
        if (doc && doc.documentElement && doc.body) {
          doc.documentElement.classList.add("longshot-capturing-root");
          doc.body.classList.add("longshot-capturing");
        }
      } catch (_e) {}
    };
    ls.onerror = function () {
      if (hint) {
        hint.hidden = false;
        hint.textContent =
          "长图页尚未生成。可先导出一次长图，或确认本辑已渲染 index-longshot.html。";
      }
    };
  }
  if (hint) {
    hint.hidden = true;
    hint.textContent = "";
  }
  // Probe longshot existence (iframe onerror is unreliable cross-browser).
  fetch(lsUrl, { method: "HEAD", credentials: "same-origin" })
    .then(function (resp) {
      if (!resp.ok && hint) {
        hint.hidden = false;
        hint.textContent =
          "长图页尚未生成（" +
          resp.status +
          "）。可先点金色按钮导出长图后再对比。";
      }
    })
    .catch(function () {});
  el.hidden = false;
  try {
    document.documentElement.classList.add("ltn-dual-preview-open");
  } catch (e) {}
  try {
    if (window.travelogueTelemetry && typeof window.travelogueTelemetry.track === "function") {
      window.travelogueTelemetry.track("dual_preview_open", { tripId: tid });
    }
  } catch (eTel) {}
}

export function closeDualPreview() {
  var el = document.getElementById("ltn-dual-preview");
  if (!el) return;
  el.hidden = true;
  el.querySelectorAll("iframe").forEach(function (f) {
    f.removeAttribute("src");
  });
  try {
    document.documentElement.classList.remove("ltn-dual-preview-open");
  } catch (e) {}
}
