/**
 * StudioModal — CMP-HP-07
 * Replaces window.confirm with accessible modal dialog.
 * IIFE, no framework. <script src="studio-modal.js" defer>
 */
(function () {
  "use strict";

  var FOCUSABLE = 'a[href],button:not([disabled]),input:not([disabled]),[tabindex="0"]';

  function trapFocus(modal) {
    var items = modal.querySelectorAll(FOCUSABLE);
    if (!items.length) return;
    var first = items[0];
    var last = items[items.length - 1];
    modal.addEventListener("keydown", function (e) {
      if (e.key !== "Tab") return;
      if (e.shiftKey) {
        if (document.activeElement === first) {
          e.preventDefault();
          last.focus();
        }
      } else {
        if (document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    });
  }

  /**
   * Open a modal dialog.
   * @param {Object} opts
   * @param {string} opts.title
   * @param {string} opts.body
   * @param {string} [opts.confirmText='确定']
   * @param {string} [opts.cancelText='取消']
   * @param {boolean} [opts.danger=false] - red confirm button
   * @returns {Promise<boolean>} true=confirm, false=cancel
   */
  window.studioModal = function (opts) {
    return new Promise(function (resolve) {
      var backdrop = document.createElement("div");
      backdrop.className = "studio__modal-backdrop";

      var modal = document.createElement("div");
      modal.className = "studio__modal";
      modal.setAttribute("role", "dialog");
      modal.setAttribute("aria-modal", "true");

      var h = document.createElement("h3");
      h.textContent = opts.title || "";
      var p = document.createElement("p");
      p.textContent = opts.body || "";

      var actions = document.createElement("div");
      actions.className = "studio__modal-actions";

      var cancelBtn = document.createElement("button");
      cancelBtn.type = "button";
      cancelBtn.className = "studio__btn studio__btn--ghost studio__btn--sm";
      cancelBtn.textContent = opts.cancelText || "取消";

      var confirmBtn = document.createElement("button");
      confirmBtn.type = "button";
      confirmBtn.className = "studio__btn studio__btn--primary studio__btn--sm";
      if (opts.danger) {
        confirmBtn.style.background = "var(--color-danger)";
      }
      confirmBtn.textContent = opts.confirmText || "确定";

      actions.appendChild(cancelBtn);
      actions.appendChild(confirmBtn);
      modal.appendChild(h);
      modal.appendChild(p);
      modal.appendChild(actions);
      backdrop.appendChild(modal);
      document.body.appendChild(backdrop);

      var previousFocus = document.activeElement;
      confirmBtn.focus();
      trapFocus(modal);

      function cleanup(result) {
        backdrop.remove();
        if (previousFocus && previousFocus.focus) previousFocus.focus();
        resolve(result);
      }

      cancelBtn.addEventListener("click", function () { cleanup(false); });
      confirmBtn.addEventListener("click", function () { cleanup(true); });
      backdrop.addEventListener("click", function (e) {
        if (e.target === backdrop) cleanup(false);
      });
      document.addEventListener("keydown", function escHandler(e) {
        if (e.key === "Escape") {
          document.removeEventListener("keydown", escHandler);
          cleanup(false);
        }
      });
    });
  };
})();
