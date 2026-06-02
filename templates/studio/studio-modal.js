/**
 * StudioModal — CMP-HP-07
 * Replaces window.confirm with accessible modal dialog.
 * IIFE, no framework. <script src="studio-modal.js" defer>
 * Styles: studio-modal.css
 */
(function () {
  "use strict";

  var FOCUSABLE = 'a[href],button:not([disabled]),input:not([disabled]),[tabindex="0"]';
  var _openCount = 0;

  function focusNoScroll(el) {
    if (!el || !el.focus) return;
    try {
      el.focus({ preventScroll: true });
    } catch (e) {
      el.focus();
    }
  }

  function lockBodyScroll() {
    _openCount += 1;
    if (_openCount === 1) {
      document.body.classList.add("studio-modal-open");
    }
  }

  function unlockBodyScroll() {
    _openCount = Math.max(0, _openCount - 1);
    if (_openCount === 0) {
      document.body.classList.remove("studio-modal-open");
    }
  }

  function trapFocus(modal) {
    function onKeydown(e) {
      if (e.key !== "Tab") return;
      var items = modal.querySelectorAll(FOCUSABLE);
      if (!items.length) return;
      var first = items[0];
      var last = items[items.length - 1];
      if (e.shiftKey) {
        if (document.activeElement === first) {
          e.preventDefault();
          focusNoScroll(last);
        }
      } else if (document.activeElement === last) {
        e.preventDefault();
        focusNoScroll(first);
      }
    }
    modal.addEventListener("keydown", onKeydown);
    return function () { modal.removeEventListener("keydown", onKeydown); };
  }

  /**
   * Open a modal dialog.
   * @param {Object} opts
   * @param {string} opts.title
   * @param {string} opts.body
   * @param {string} [opts.confirmText='确定']
   * @param {string} [opts.cancelText='取消']
   * @param {boolean} [opts.danger=false] - red confirm button
   * @param {boolean} [opts.focusCancel=false] - default focus on cancel (destructive flows)
   * @returns {Promise<boolean>} true=confirm, false=cancel
   */
  window.studioModal = function (opts) {
    return new Promise(function (resolve) {
      opts = opts || {};
      var isDanger = !!opts.danger;

      var backdrop = document.createElement("div");
      backdrop.className = "studio__modal-backdrop";

      var modal = document.createElement("div");
      modal.className = "studio__modal";
      modal.setAttribute("role", isDanger ? "alertdialog" : "dialog");
      modal.setAttribute("aria-modal", "true");

      var h = document.createElement("h3");
      h.id = "studio-modal-title-" + Date.now();
      h.textContent = opts.title || "";
      modal.setAttribute("aria-labelledby", h.id);

      var p = document.createElement("p");
      p.className = "studio__modal-body";
      p.id = "studio-modal-body-" + Date.now();
      p.textContent = opts.body || "";
      modal.setAttribute("aria-describedby", p.id);

      var actions = document.createElement("div");
      actions.className = "studio__modal-actions";

      var cancelBtn = document.createElement("button");
      cancelBtn.type = "button";
      cancelBtn.className = "studio__btn studio__btn--ghost studio__btn--sm";
      cancelBtn.textContent = opts.cancelText || "取消";

      var confirmBtn = document.createElement("button");
      confirmBtn.type = "button";
      confirmBtn.className = "studio__btn studio__btn--sm "
        + (isDanger ? "studio__btn--danger" : "studio__btn--primary");
      confirmBtn.textContent = opts.confirmText || "确定";

      actions.appendChild(cancelBtn);
      actions.appendChild(confirmBtn);
      modal.appendChild(h);
      modal.appendChild(p);
      modal.appendChild(actions);
      backdrop.appendChild(modal);
      document.body.appendChild(backdrop);

      lockBodyScroll();

      var previousFocus = document.activeElement;
      var escHandler = function (e) {
        if (e.key === "Escape") {
          document.removeEventListener("keydown", escHandler);
          cleanup(false);
        }
      };

      var releaseTrap = trapFocus(modal);

      function cleanup(result) {
        document.removeEventListener("keydown", escHandler);
        if (releaseTrap) releaseTrap();
        backdrop.remove();
        unlockBodyScroll();
        if (previousFocus && previousFocus.focus) focusNoScroll(previousFocus);
        resolve(result);
      }

      cancelBtn.addEventListener("click", function () { cleanup(false); });
      confirmBtn.addEventListener("click", function () { cleanup(true); });
      backdrop.addEventListener("click", function (e) {
        if (e.target === backdrop) cleanup(false);
      });
      document.addEventListener("keydown", escHandler);

      focusNoScroll(opts.focusCancel ? cancelBtn : confirmBtn);
    });
  };
})();
