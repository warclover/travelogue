/**
 * StudioToast — CMP-HP-09
 * Bottom-center toast: 3s auto-dismiss, slide-up + fade, max 2 stacked.
 * IIFE, no framework. <script src="studio-toast.js" defer>
 */
(function () {
  "use strict";

  var MAX_TOASTS = 2;
  var DEFAULT_DURATION = 3000;
  var container = null;

  function getContainer() {
    if (!container) {
      container = document.getElementById("studio-toast-container")
        || document.getElementById("v2-toast-container");
    }
    return container;
  }

  function removeToast(el) {
    el.classList.add("studio__toast--leaving");
    setTimeout(function () {
      if (el.parentNode) el.parentNode.removeChild(el);
    }, 250);
  }

  /**
   * Show a toast notification.
   * @param {string} message
   * @param {Object} [opts]
   * @param {number} [opts.duration=3000] - ms before auto-dismiss (0=sticky)
   * @param {boolean} [opts.large=false] - slightly larger text for FirstSuccess
   */
  window.studioToast = function (message, opts) {
    opts = opts || {};
    var c = getContainer();
    if (!c) return;

    // Enforce max stack
    while (c.children.length >= MAX_TOASTS) {
      removeToast(c.firstElementChild);
    }

    var el = document.createElement("div");
    el.className = "studio__toast";
    el.setAttribute("role", "status");
    el.setAttribute("aria-live", "polite");
    el.textContent = message;

    if (opts.large) {
      el.style.fontSize = "15px";
      el.style.padding = "16px 24px";
    }

    c.appendChild(el);

    var duration = opts.duration !== undefined ? opts.duration : DEFAULT_DURATION;
    if (duration > 0) {
      setTimeout(function () { removeToast(el); }, duration);
    }

    return el;
  };
})();
