/**
 * Travelogue · 分享工具栏
 * 复制链接、下载分享包、系统分享；保存长图委托 TravelogueLongshot。
 */
(function (global) {
  "use strict";

  var toastEl = null;

  function rootEl() {
    return document.querySelector('[data-block="share-toolbar"]');
  }

  function getToast() {
    if (!toastEl) {
      toastEl = document.getElementById("longshot-toast");
      if (!toastEl) {
        toastEl = document.createElement("p");
        toastEl.id = "longshot-toast";
        toastEl.className = "longshot-toast";
        toastEl.setAttribute("role", "status");
        toastEl.hidden = true;
        document.body.appendChild(toastEl);
      }
    }
    return toastEl;
  }

  function toast(msg, isError) {
    var el = getToast();
    el.textContent = msg;
    el.classList.toggle("longshot-toast--error", !!isError);
    el.hidden = false;
    clearTimeout(el._hideTimer);
    el._hideTimer = setTimeout(function () {
      el.hidden = true;
    }, isError ? 7000 : 4000);
  }

  function shareTitle() {
    var root = rootEl();
    if (root && root.getAttribute("data-share-title")) {
      return root.getAttribute("data-share-title");
    }
    return (
      document.querySelector(".cover-hero__text h1")?.textContent?.trim() ||
      document.title ||
      "Travelogue"
    );
  }

  function shareZipFile() {
    var root = rootEl();
    return root ? root.getAttribute("data-share-zip") || "" : "";
  }

  function panelEl() {
    return document.getElementById("share-panel");
  }

  function toggleEl() {
    return document.getElementById("share-toggle");
  }

  function setPanelOpen(open) {
    var panel = panelEl();
    var toggle = toggleEl();
    if (!panel || !toggle) return;
    panel.hidden = !open;
    toggle.setAttribute("aria-expanded", open ? "true" : "false");
  }

  function closePanel() {
    setPanelOpen(false);
  }

  function togglePanel() {
    var panel = panelEl();
    if (!panel) return;
    setPanelOpen(panel.hidden);
  }

  async function copyLink() {
    var url = location.href;
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(url);
      toast("链接已复制，可粘贴到微信或邮件");
      return;
    }
    var input = document.createElement("textarea");
    input.value = url;
    input.setAttribute("readonly", "");
    input.style.position = "fixed";
    input.style.left = "-9999px";
    document.body.appendChild(input);
    input.select();
    var ok = false;
    try {
      ok = document.execCommand("copy");
    } catch (_e) {
      ok = false;
    }
    input.remove();
    if (ok) toast("链接已复制");
    else toast("无法复制，请手动复制地址栏链接", true);
  }

  function downloadZip() {
    var file = shareZipFile();
    if (!file) {
      toast("分享包尚未生成，请运行 publish 导出", true);
      return;
    }
    var a = document.createElement("a");
    a.href = file;
    a.download = file.split("/").pop() || file;
    a.rel = "noopener";
    document.body.appendChild(a);
    a.click();
    a.remove();
    toast("正在下载分享包…");
  }

  async function nativeShare() {
    var title = shareTitle();
    var url = location.href;
    var payload = { title: title, text: title, url: url };
    if (!navigator.share) {
      await copyLink();
      return;
    }
    try {
      await navigator.share(payload);
      toast("已唤起系统分享");
    } catch (err) {
      if (err && err.name === "AbortError") return;
      console.warn("[share]", err);
      await copyLink();
    }
  }

  function bindLongshot(btn) {
    if (!btn || btn.dataset.shareBound === "1") return;
    btn.dataset.shareBound = "1";
    btn.addEventListener("click", function () {
      if (btn.disabled) return;
      closePanel();
      if (global.TravelogueLongshot && global.TravelogueLongshot.capture) {
        global.TravelogueLongshot.capture().catch(function (err) {
          console.error("[share/longshot]", err);
          toast(err.message || String(err), true);
        });
        return;
      }
      var fallback = document.getElementById("longshot-save");
      if (fallback) fallback.click();
      else toast("长图功能未加载", true);
    });
  }

  function bindAction(btn) {
    if (!btn || btn.dataset.shareBound === "1") return;
    btn.dataset.shareBound = "1";
    var action = btn.getAttribute("data-share-action");
    btn.addEventListener("click", function () {
      closePanel();
      if (action === "copy-link") {
        copyLink().catch(function (err) {
          toast(err.message || "复制失败", true);
        });
      } else if (action === "download-zip") {
        downloadZip();
      } else if (action === "native") {
        nativeShare().catch(function (err) {
          toast(err.message || "分享失败", true);
        });
      }
    });
  }

  function init() {
    var root = rootEl();
    if (!root) return;

    var toggle = toggleEl();
    if (toggle && toggle.dataset.shareBound !== "1") {
      toggle.dataset.shareBound = "1";
      toggle.addEventListener("click", function (e) {
        e.stopPropagation();
        togglePanel();
      });
    }

    root.querySelectorAll("[data-share-action]").forEach(bindAction);
    root.querySelectorAll("[data-longshot-trigger]").forEach(bindLongshot);

    document.addEventListener("click", function (e) {
      var panel = panelEl();
      if (!panel || panel.hidden) return;
      if (root.contains(e.target)) return;
      closePanel();
    });

    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") closePanel();
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  global.TravelogueShare = {
    copyLink: copyLink,
    downloadZip: downloadZip,
    nativeShare: nativeShare,
  };
})(typeof window !== "undefined" ? window : this);
