/**
 * Travelogue · screens Web 页 → index-longshot.html 长图桥接
 */
(function (global) {
  "use strict";

  function isFileProtocol() {
    return global.location && global.location.protocol === "file:";
  }

  function serveHint() {
    return "python -m travelogue serve trips/<tripId>";
  }

  function ensureFileBanner() {
    if (!isFileProtocol()) return;
    if (document.querySelector(".longshot-file-banner")) return;
    var el = document.createElement("div");
    el.className = "longshot-file-banner";
    el.setAttribute("role", "alert");
    el.innerHTML =
      '<p class="longshot-file-banner__text"><strong>保存长图需 HTTP 打开</strong>：请运行 ' +
      serveHint() +
      "，用 http://127.0.0.1:8766 访问（不要双击 HTML）。</p>";
    document.body.appendChild(el);
  }

  function init() {
    var root = document.documentElement;
    if (root.getAttribute("data-longshot-bridge") !== "on") return;

    var btn = document.getElementById("longshot-bridge");
    if (!btn || btn.dataset.longshotBridgeBound === "1") return;
    btn.dataset.longshotBridgeBound = "1";

    if (isFileProtocol()) {
      ensureFileBanner();
      btn.disabled = true;
      btn.title = "需 HTTP 打开，见顶部说明";
      return;
    }

    var mobileUrl =
      root.getAttribute("data-longshot-mobile-url") || "index-longshot.html";

    btn.addEventListener("click", function () {
      if (btn.disabled) return;
      if (isFileProtocol()) {
        ensureFileBanner();
        return;
      }
      btn.disabled = true;
      var prev = btn.textContent;
      btn.textContent = "跳转中…";
      global.location.href = mobileUrl;
      setTimeout(function () {
        btn.disabled = false;
        btn.textContent = prev;
      }, 4000);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})(typeof window !== "undefined" ? window : this);
