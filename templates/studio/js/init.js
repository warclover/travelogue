/**
 * Travelogue Studio · small standalone init helpers.
 */
import { $, show } from "./dom.js";
import { loadTrips } from "./api.js";

// ── Footer toggle ──
export function initFooter() {
  var toggle = $("studio-footer-toggle");
  var checklist = $("studio-footer-checklist");
  if (toggle && checklist) {
    toggle.addEventListener("click", function (e) {
      e.preventDefault();
      var visible = !checklist.hidden;
      show(checklist, !visible);
      toggle.textContent = visible ? "如何发到微信 ▸" : "如何发到微信 ▾";
    });
  }
}

// ── Copy address ──
export function initCopyAddr() {
  var addr = $("studio-copy-addr");
  if (!addr) return;
  addr.addEventListener("click", function () {
    var text = addr.textContent;
    if (navigator.clipboard) {
      navigator.clipboard.writeText(text).then(function () {
        if (typeof studioToast === "function") studioToast("已复制", { duration: 1500 });
      });
    }
  });
}

// ── Path form toggle ──
export function initPathToggle() {
  /* studio-path-toggle → openImportSheet (initImportSheet) */
}

// ── Scroll hint ──
export function initScrollHint() {
  var hint = $("studio-scroll-hint");
  var below = $("studio-below");
  if (hint && below) {
    hint.addEventListener("click", function () {
      below.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  }
}

// ── Trips "more" button ──
export function initTripsMore() {
  var moreBtn = $("studio-trips-more");
  if (!moreBtn) return;
  moreBtn.addEventListener("click", function () { loadTrips({ more: true }); });
}
