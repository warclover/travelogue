/**
 * Travelogue · 保存长图
 * 将 <main> 按朋友圈 9:16 版式（390px 宽）导出为 PNG。
 * 依赖 html2canvas（优先本地 vendor/，失败则 CDN）。
 */
(function (global) {
  "use strict";

  var HTML2CANVAS_CDN =
    "https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js";
  var CAPTURE_WIDTH = 390;
  var DESKTOP_CAPTURE_SCALE = 3;
  var MOBILE_CAPTURE_SCALE = 2;
  var MAX_CAPTURE_SCALE = 3;
  var MIN_CAPTURE_SCALE = 1;
  var LARGE_TRIP_IMAGES = 45;
  var SINGLE_PAGE_MAX_IMAGES = 30;
  var MODE_KEY = "travelogue:longshotMode";
  var MODE_FULL = "full";
  var MODE_CHAPTER = "chapter";
  var JPEG_QUALITY = 0.96;
  var CAPTURING_CLASS = "longshot-capturing";
  var ROOT_CLASS = "longshot-capturing-root";
  var DISCLAIMER_KEY = "travelogue:longshotDisclaimer";
  var FORMAT_KEY = "travelogue:longshotFormat";
  var SCALE_KEY = "travelogue:longshotScale";
  var CAPTION_DISPLAY_KEY = "travelogue:captionDisplay";
  var CAPTION_EDIT_KEY = "travelogue:captionEdit";
  var CAPTION_ON = "on";
  var CAPTION_OFF = "off";

  function readingConfig() {
    return global.__TRAVELOGUE_READING__ || {};
  }

  /** Tear down scroll motion before longshot capture (E4). */
  function teardownReadingMotion() {
    if (global.TravelogueBreath && typeof global.TravelogueBreath.destroy === "function") {
      global.TravelogueBreath.destroy();
    }
    document.querySelectorAll(".breath-reveal").forEach(function (el) {
      el.classList.add("is-visible");
      el.style.opacity = "1";
      el.style.transform = "none";
    });
  }

  function restoreReadingMotion() {
    var scroll = (readingConfig().scroll || {});
    var breath = scroll.breath || "off";
    if (breath === "off") return;
    if (global.TravelogueBreath && typeof global.TravelogueBreath.init === "function") {
      global.TravelogueBreath.init();
    }
  }

  global.TravelogueReading = global.TravelogueReading || {};
  global.TravelogueReading.teardown = teardownReadingMotion;
  global.TravelogueReading.restore = restoreReadingMotion;
  global.TravelogueReading.config = readingConfig;

  var html2canvasPromise = null;
  var toastEl = null;
  var progressEl = null;
  var selectedScaleCache = null;

  function scriptDir() {
    var scripts = document.getElementsByTagName("script");
    for (var i = scripts.length - 1; i >= 0; i--) {
      var src = scripts[i].src;
      if (src && /longshot\.js(?:\?|$)/.test(src)) {
        return src.replace(/[^/]+$/, "");
      }
    }
    return "";
  }

  function loadScript(url) {
    return new Promise(function (resolve, reject) {
      var s = document.createElement("script");
      s.src = url;
      s.async = true;
      s.onload = function () {
        resolve();
      };
      s.onerror = function () {
        reject(new Error("script load failed: " + url));
      };
      document.head.appendChild(s);
    });
  }

  function loadHtml2Canvas() {
    if (global.html2canvas) return Promise.resolve(global.html2canvas);
    if (html2canvasPromise) return html2canvasPromise;

    html2canvasPromise = (async function () {
      var local = scriptDir() + "vendor/html2canvas.min.js";
      if (local.indexOf("vendor/") > 0) {
        try {
          await loadScript(local);
          if (global.html2canvas) return global.html2canvas;
        } catch (_e) {
          /* try CDN */
        }
      }
      await loadScript(HTML2CANVAS_CDN);
      if (global.html2canvas) return global.html2canvas;
      throw new Error("无法加载 html2canvas，请检查网络或使用本地 http 服务打开页面");
    })();

    return html2canvasPromise;
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

  function slugPart(text, maxLen) {
    var t = (text || "").trim().slice(0, maxLen || 24);
    t = t.replace(/[<>:"/\\|?*\x00-\x1f]/g, "").replace(/\s+/g, "-");
    return t || "chapter";
  }

  function slugFilename(title, format, suffix) {
    var base = slugPart(title, 24) || "travelogue";
    var now = new Date();
    var pad = function (n) {
      return n < 10 ? "0" + n : String(n);
    };
    var stamp =
      now.getFullYear() +
      pad(now.getMonth() + 1) +
      pad(now.getDate()) +
      "-" +
      pad(now.getHours()) +
      pad(now.getMinutes());
    var ext = format === "jpeg" ? "jpg" : "png";
    var mid = suffix ? "-" + suffix : "-长图";
    return base + mid + "-" + stamp + "." + ext;
  }

  function chapterFilename(tripTitle, chapterIndex, chapterTitle, format) {
    var idx = chapterIndex < 10 ? "0" + chapterIndex : String(chapterIndex);
    return slugFilename(tripTitle, format, idx + "-" + slugPart(chapterTitle, 18));
  }

  function isWeChatBrowser() {
    return /MicroMessenger/i.test(global.navigator && global.navigator.userAgent ? global.navigator.userAgent : "");
  }

  function isFileProtocol() {
    return global.location && global.location.protocol === "file:";
  }

  function parseLongshotQuery() {
    var params = new URLSearchParams(global.location.search || "");
    var format = params.get("format");
    if (format !== "jpeg" && format !== "jpg") {
      format = null;
    } else {
      format = "jpeg";
    }
    return {
      auto: params.get("longshot") === "auto",
      format: format,
      scale: params.get("scale"),
      mode: params.get("mode"),
    };
  }

  function getMainImageCount() {
    var main = document.querySelector("main");
    return main ? main.querySelectorAll("img").length : 0;
  }

  function getDefaultCaptureMode(imgTotal) {
    if (imgTotal > SINGLE_PAGE_MAX_IMAGES) return MODE_CHAPTER;
    return MODE_FULL;
  }

  function getUserSelectedMode() {
    try {
      var stored = global.localStorage.getItem(MODE_KEY);
      if (stored === MODE_FULL || stored === MODE_CHAPTER) return stored;
    } catch (_e) {
      /* ignore */
    }
    return getDefaultCaptureMode(getMainImageCount());
  }

  function setUserSelectedMode(mode) {
    if (mode !== MODE_FULL && mode !== MODE_CHAPTER) return;
    try {
      global.localStorage.setItem(MODE_KEY, mode);
    } catch (_e) {
      /* ignore */
    }
    syncModeToggleUI(mode);
    refreshExportPanelIfOpen();
  }

  function syncModeToggleUI(mode) {
    document.querySelectorAll("[data-longshot-mode]").forEach(function (btn) {
      var val = btn.getAttribute("data-longshot-mode");
      var on = val === mode;
      btn.setAttribute("aria-pressed", on ? "true" : "false");
      btn.classList.toggle("longshot-segment__btn--active", on);
    });
  }

  function bindModeToggle(root) {
    (root || document).querySelectorAll("[data-longshot-mode]").forEach(function (btn) {
      if (btn.dataset.longshotModeBound === "1") return;
      btn.dataset.longshotModeBound = "1";
      btn.addEventListener("click", function () {
        if (btn.disabled) return;
        setUserSelectedMode(btn.getAttribute("data-longshot-mode"));
      });
    });
  }

  function getChapterCount() {
    var main = document.querySelector("main");
    return main ? listChapterSections(main).length : 0;
  }

  function shouldDisableFullExport(imgTotal) {
    return imgTotal > LARGE_TRIP_IMAGES;
  }

  function shouldWarnFullExport(imgTotal) {
    return imgTotal > SINGLE_PAGE_MAX_IMAGES && imgTotal <= LARGE_TRIP_IMAGES;
  }

  function buildExportSummary(mode, scale, imgTotal, chapterCount, includeCaptions) {
    var scaleLabel = scale + "×";
    var capNote = includeCaptions === false ? " · 无图注" : "";
    if (mode === MODE_CHAPTER) {
      var n = Math.max(1, chapterCount || 1);
      return n + " 章 · " + n + " 张 PNG · " + scaleLabel + " · 适合微信群" + capNote;
    }
    if (imgTotal > LARGE_TRIP_IMAGES) {
      return "单张长图 · 约 " + imgTotal + " 张 · " + scaleLabel + " · 不推荐" + capNote;
    }
    if (imgTotal > SINGLE_PAGE_MAX_IMAGES) {
      return "单张长图 · 约 " + imgTotal + " 张 · " + scaleLabel + " · 可能较慢" + capNote;
    }
    return "单张长图 · 约 " + imgTotal + " 张 · " + scaleLabel + capNote;
  }

  function isDraftPreview() {
    return document.documentElement.getAttribute("data-export") === "draft";
  }

  function areCaptionsVisible() {
    return document.documentElement.getAttribute("data-caption-display") !== CAPTION_OFF;
  }

  function syncCaptionToggleUI() {
    var btn = document.getElementById("longshot-caption-toggle");
    if (!btn) return;
    var visible = areCaptionsVisible();
    btn.setAttribute("aria-pressed", visible ? "false" : "true");
    btn.textContent = visible
      ? btn.getAttribute("data-label-on") || "图注：开"
      : btn.getAttribute("data-label-off") || "图注：关";
  }

  function syncCaptionEditUI() {
    var btn = document.getElementById("longshot-caption-edit");
    if (!btn) return;
    var on = document.documentElement.getAttribute("data-caption-edit") === "on";
    btn.setAttribute("aria-pressed", on ? "true" : "false");
    btn.classList.toggle("longshot-toolbar__btn--active", on);
    btn.textContent = on ? "完成编辑" : "编辑图注";
  }

  function syncExportCaptionCheckbox() {
    if (!exportSheetEl) return;
    var cb = exportSheetEl.querySelector("[data-longshot-include-captions]");
    if (cb) cb.checked = areCaptionsVisible();
  }

  function applyCaptionDisplay(visible) {
    var root = document.documentElement;
    if (visible) {
      root.removeAttribute("data-caption-display");
    } else {
      root.setAttribute("data-caption-display", CAPTION_OFF);
    }
    syncCaptionToggleUI();
    syncExportCaptionCheckbox();
    try {
      global.sessionStorage.setItem(CAPTION_DISPLAY_KEY, visible ? CAPTION_ON : CAPTION_OFF);
    } catch (_eCap) {
      /* private mode */
    }
  }

  function readCaptionDisplayPref() {
    try {
      var v = global.sessionStorage.getItem(CAPTION_DISPLAY_KEY);
      if (v === CAPTION_ON) return true;
      if (v === CAPTION_OFF) return false;
    } catch (_eRead) {
      /* ignore */
    }
    return true;
  }

  function applyCaptionEditMode(on) {
    var root = document.documentElement;
    if (on && isDraftPreview()) {
      root.setAttribute("data-caption-edit", "on");
    } else {
      root.removeAttribute("data-caption-edit");
    }
    syncCaptionEditUI();
    try {
      if (on) global.sessionStorage.setItem(CAPTION_EDIT_KEY, "1");
      else global.sessionStorage.removeItem(CAPTION_EDIT_KEY);
    } catch (_eEdit) {
      /* ignore */
    }
  }

  function readCaptionEditPref() {
    try {
      return global.sessionStorage.getItem(CAPTION_EDIT_KEY) === "1";
    } catch (_ePref) {
      return false;
    }
  }

  function bindCaptionControls() {
    var toggleBtn = document.getElementById("longshot-caption-toggle");
    if (toggleBtn && toggleBtn.dataset.captionBound !== "1") {
      toggleBtn.dataset.captionBound = "1";
      toggleBtn.addEventListener("click", function () {
        applyCaptionDisplay(!areCaptionsVisible());
      });
    }
    var editBtn = document.getElementById("longshot-caption-edit");
    if (editBtn && editBtn.dataset.captionBound !== "1") {
      editBtn.dataset.captionBound = "1";
      editBtn.addEventListener("click", function () {
        var next = document.documentElement.getAttribute("data-caption-edit") !== "on";
        applyCaptionEditMode(next);
        if (next) toast("点击图注文字可直接修改（需 travelogue serve）");
      });
    }
  }

  function initCaptionDisplay() {
    if (document.documentElement.getAttribute("data-photos-only") === "on") {
      applyCaptionDisplay(false);
    } else {
      applyCaptionDisplay(readCaptionDisplayPref());
    }
    if (isDraftPreview() && readCaptionEditPref()) {
      applyCaptionEditMode(true);
    }
    bindCaptionControls();
  }

  function updateSaveButtonLabel() {
    var btn = document.getElementById("longshot-save");
    if (!btn) return;
    var mode = getUserSelectedMode();
    var scale = getUserSelectedScale();
    var modeLabel = mode === MODE_CHAPTER ? "按章" : "完整";
    btn.setAttribute("title", "当前偏好：" + modeLabel + " · " + scale + "×（点击可修改）");
  }

  var exportSheetEl = null;

  function refreshExportPanelIfOpen() {
    if (exportSheetEl && !exportSheetEl.hidden) {
      updateExportPanelUI(exportSheetEl);
    }
    updateSaveButtonLabel();
  }

  function updateExportPanelUI(sheet) {
    var imgTotal = getMainImageCount();
    var chapterCount = getChapterCount();
    var fullBtn = sheet.querySelector('[data-longshot-mode="' + MODE_FULL + '"]');
    var warnEl = sheet.querySelector("[data-longshot-full-warn]");
    var recommendChapter = sheet.querySelector("[data-longshot-chapter-badge]");

    if (shouldDisableFullExport(imgTotal)) {
      if (getUserSelectedMode() === MODE_FULL) {
        setUserSelectedMode(MODE_CHAPTER);
      }
      if (fullBtn) {
        fullBtn.disabled = true;
        fullBtn.title = "图片过多，建议按章导出";
      }
      if (warnEl) {
        warnEl.textContent =
          "共 " + imgTotal + " 张图，完整长图可能失败或占用大量内存，已推荐按章导出。";
      }
    } else if (shouldWarnFullExport(imgTotal)) {
      if (fullBtn) {
        fullBtn.disabled = false;
        fullBtn.removeAttribute("title");
      }
      if (warnEl) {
        warnEl.textContent = "共 " + imgTotal + " 张图，完整长图生成可能较慢。";
      }
    } else {
      if (fullBtn) {
        fullBtn.disabled = false;
        fullBtn.removeAttribute("title");
      }
      if (warnEl) warnEl.textContent = "";
    }

    if (recommendChapter) {
      recommendChapter.hidden = imgTotal <= SINGLE_PAGE_MAX_IMAGES;
    }

    syncModeToggleUI(getUserSelectedMode());
    syncScaleToggleUI(getUserSelectedScale());

    var summary = sheet.querySelector("[data-longshot-export-summary]");
    if (summary) {
      summary.textContent = buildExportSummary(
        getUserSelectedMode(),
        getUserSelectedScale(),
        imgTotal,
        chapterCount,
        areCaptionsVisible()
      );
    }
  }

  function getExportSheet() {
    if (exportSheetEl) return exportSheetEl;
    exportSheetEl = document.createElement("div");
    exportSheetEl.className = "longshot-export-sheet";
    exportSheetEl.hidden = true;
    exportSheetEl.innerHTML =
      '<div class="longshot-export-sheet__panel" role="dialog" aria-modal="true" aria-labelledby="longshot-export-title">' +
      '<p id="longshot-export-title" class="longshot-export-sheet__title">保存长图</p>' +
      '<p class="longshot-export-sheet__body">将保存竖版图片到本机。发送到哪里、谁可以看到，由你决定。</p>' +
      '<div class="longshot-export-sheet__field">' +
      '<span class="longshot-export-sheet__label">导出范围</span>' +
      '<div class="longshot-segment" role="group" aria-label="导出范围">' +
      '<button type="button" class="longshot-segment__btn" data-longshot-mode="full" aria-pressed="false">完整长图</button>' +
      '<button type="button" class="longshot-segment__btn" data-longshot-mode="chapter" aria-pressed="true">' +
      '按章导出 <span class="longshot-export-sheet__badge" data-longshot-chapter-badge hidden>推荐</span></button>' +
      "</div>" +
      '<p class="longshot-export-sheet__warn" data-longshot-full-warn"></p>' +
      "</div>" +
      '<div class="longshot-export-sheet__field">' +
      '<span class="longshot-export-sheet__label">清晰度</span>' +
      '<div class="longshot-segment" role="group" aria-label="清晰度">' +
      '<button type="button" class="longshot-segment__btn longshot-segment__btn--active" data-longshot-scale-option="2" aria-pressed="true">标准 2×</button>' +
      '<button type="button" class="longshot-segment__btn" data-longshot-scale-option="3" aria-pressed="false">高清 3×</button>' +
      "</div>" +
      '<p class="longshot-export-sheet__field-note">高清适合放大看细节，文件更大、耗时更长。</p>' +
      "</div>" +
      '<div class="longshot-export-sheet__field">' +
      '<label class="longshot-export-sheet__check">' +
      '<input type="checkbox" data-longshot-include-captions checked />' +
      "<span>包含图注（章导语仍保留）</span></label>" +
      "</div>" +
      '<p class="longshot-export-sheet__summary" data-longshot-export-summary></p>' +
      '<p class="longshot-export-sheet__note longshot-export-sheet__note--wechat">微信内若无法下载，生成后会弹出预览，长按图片保存。</p>' +
      '<p class="longshot-export-sheet__note longshot-export-sheet__note--bridge">排版与 Web 浏览可能略有不同。</p>' +
      '<div class="longshot-export-sheet__actions">' +
      '<button type="button" class="longshot-export-sheet__btn longshot-export-sheet__btn--primary" data-action="ok">开始生成</button>' +
      '<button type="button" class="longshot-export-sheet__btn" data-action="cancel">取消</button>' +
      "</div></div>";
    document.body.appendChild(exportSheetEl);
    bindModeToggle(exportSheetEl);
    bindScaleToggle(exportSheetEl);
    var captionCb = exportSheetEl.querySelector("[data-longshot-include-captions]");
    if (captionCb && captionCb.dataset.bound !== "1") {
      captionCb.dataset.bound = "1";
      captionCb.addEventListener("change", function () {
        applyCaptionDisplay(!!captionCb.checked);
        updateExportPanelUI(exportSheetEl);
      });
    }
    return exportSheetEl;
  }

  function openExportPanel() {
    return new Promise(function (resolve, reject) {
      var sheet = getExportSheet();
      updateExportPanelUI(sheet);
      syncExportCaptionCheckbox();

      var bodyNote = sheet.querySelector(".longshot-export-sheet__body");
      var seenDisclaimer = false;
      try {
        seenDisclaimer = global.sessionStorage.getItem(DISCLAIMER_KEY) === "1";
      } catch (_eDisc) {
        seenDisclaimer = false;
      }
      if (bodyNote) bodyNote.hidden = seenDisclaimer;

      var bridgeNote = sheet.querySelector(".longshot-export-sheet__note--bridge");
      if (bridgeNote) {
        var fromBridge = false;
        try {
          fromBridge = /index\.html(?:\?|#|$)/.test(document.referrer || "");
        } catch (_eRef) {
          fromBridge = false;
        }
        bridgeNote.hidden = !fromBridge;
      }
      var wechatNote = sheet.querySelector(".longshot-export-sheet__note--wechat");
      if (wechatNote) wechatNote.hidden = !isWeChatBrowser();

      sheet.hidden = false;
      var okBtn = sheet.querySelector('[data-action="ok"]');
      var cancelBtn = sheet.querySelector('[data-action="cancel"]');

      function cleanup() {
        sheet.hidden = true;
        okBtn.removeEventListener("click", onOk);
        cancelBtn.removeEventListener("click", onCancel);
      }

      function onOk() {
        try {
          global.sessionStorage.setItem(DISCLAIMER_KEY, "1");
        } catch (_e2) {
          /* ignore */
        }
        cleanup();
        resolve({
          mode: getUserSelectedMode(),
          scale: getUserSelectedScale(),
          includeCaptions: areCaptionsVisible(),
        });
      }

      function onCancel() {
        cleanup();
        reject(new Error("已取消"));
      }

      okBtn.addEventListener("click", onOk);
      cancelBtn.addEventListener("click", onCancel);
    });
  }

  function applyQueryPrefs() {
    var q = parseLongshotQuery();
    if (q.scale) setUserSelectedScale(q.scale);
    else syncScaleToggleUI(getUserSelectedScale());
    if (q.mode === MODE_FULL || q.mode === MODE_CHAPTER) setUserSelectedMode(q.mode);
    else syncModeToggleUI(getUserSelectedMode());
    updateSaveButtonLabel();
  }

  function listChapterSections(main) {
    return Array.prototype.slice.call(main.querySelectorAll("section.chapter"));
  }

  function applyChapterVisibility(main, chapters, chapterIndex) {
    var saved = [];
    var page = main.querySelector(".page");
    var cover = main.querySelector(".cover-hero");
    var hook = page && page.querySelector(".hook-line");
    var epilogue = page && page.querySelector(".epilogue");
    var tripMeta = page && page.querySelector(".trip-meta");
    var isFirst = chapterIndex === 0;
    var isLast = chapterIndex === chapters.length - 1;

    function stash(el, show) {
      if (!el) return;
      saved.push({
        el: el,
        hidden: el.hidden,
        display: el.style.display,
        ariaHidden: el.getAttribute("aria-hidden"),
      });
      if (show) {
        el.hidden = false;
        el.style.display = "";
        el.removeAttribute("aria-hidden");
      } else {
        el.hidden = true;
        el.style.display = "none";
        el.setAttribute("aria-hidden", "true");
      }
    }

    chapters.forEach(function (ch, i) {
      stash(ch, i === chapterIndex);
    });
    stash(cover, isFirst);
    stash(tripMeta, isFirst);
    stash(hook, isFirst);
    stash(epilogue, isLast);
    return saved;
  }

  function restoreChapterVisibility(saved) {
    (saved || []).forEach(function (entry) {
      if (!entry.el) return;
      entry.el.hidden = entry.hidden;
      entry.el.style.display = entry.display || "";
      if (entry.ariaHidden == null) entry.el.removeAttribute("aria-hidden");
      else entry.el.setAttribute("aria-hidden", entry.ariaHidden);
    });
  }

  var previewEl = null;
  var wechatBannerEl = null;
  var fileProtocolBannerEl = null;

  function serveHint() {
    return "请运行：python -m travelogue serve trips/<tripId>  后用 http://127.0.0.1:8766 打开（不可用 file:// 双击 HTML）";
  }

  function ensureFileProtocolBanner() {
    if (!isFileProtocol()) return;
    if (fileProtocolBannerEl) return;
    fileProtocolBannerEl = document.createElement("div");
    fileProtocolBannerEl.className = "longshot-file-banner";
    fileProtocolBannerEl.setAttribute("role", "alert");
    fileProtocolBannerEl.innerHTML =
      '<p class="longshot-file-banner__text"><strong>无法在此环境保存长图</strong>：浏览器禁止 file:// 页面截图。' +
      serveHint() +
      "</p>";
    document.body.appendChild(fileProtocolBannerEl);
  }

  function disableLongshotControls() {
    document.querySelectorAll("[data-longshot-trigger], #longshot-save").forEach(function (el) {
      if (el.tagName === "BUTTON") {
        el.disabled = true;
        el.setAttribute("aria-disabled", "true");
      }
      el.classList.add("longshot-toolbar__btn--blocked");
    });
  }

  function guardFileProtocol() {
    if (!isFileProtocol()) return false;
    ensureFileProtocolBanner();
    disableLongshotControls();
    return true;
  }

  function showPreviewModal(blob, filename, meta) {
    meta = meta || {};
    if (!previewEl) {
      previewEl = document.createElement("div");
      previewEl.className = "longshot-preview";
      previewEl.hidden = true;
      previewEl.innerHTML =
        '<div class="longshot-preview__panel" role="dialog" aria-modal="true" aria-labelledby="longshot-preview-title">' +
        '<p id="longshot-preview-title" class="longshot-preview__title">长图预览</p>' +
        '<p class="longshot-preview__hint"></p>' +
        '<div class="longshot-preview__frame"><img class="longshot-preview__img" alt="长图预览" /></div>' +
        '<p class="longshot-preview__filename"></p>' +
        '<div class="longshot-preview__actions">' +
        '<button type="button" class="longshot-preview__btn longshot-preview__btn--primary" data-action="next">下一张</button>' +
        '<button type="button" class="longshot-preview__btn" data-action="close">关闭</button>' +
        "</div></div>";
      document.body.appendChild(previewEl);
      previewEl._previewState = { onNext: null };
      previewEl.querySelector('[data-action="next"]').addEventListener("click", function () {
        var st = previewEl._previewState;
        closePreviewModal();
        if (st && st.onNext) st.onNext();
      });
      previewEl.querySelector('[data-action="close"]').addEventListener("click", closePreviewModal);
    }

    var url = URL.createObjectURL(blob);
    var img = previewEl.querySelector(".longshot-preview__img");
    var hint = previewEl.querySelector(".longshot-preview__hint");
    var nameEl = previewEl.querySelector(".longshot-preview__filename");
    var nextBtn = previewEl.querySelector('[data-action="next"]');
    var titleEl = previewEl.querySelector(".longshot-preview__title");

    previewEl._previewState.onNext = meta.onNext || null;

    if (img) {
      if (img._prevUrl) URL.revokeObjectURL(img._prevUrl);
      img._prevUrl = url;
      img.src = url;
    }
    if (nameEl) nameEl.textContent = filename || "";
    if (titleEl) {
      titleEl.textContent = meta.title
        ? "第 " + meta.index + "/" + meta.total + " 章 · " + meta.title
        : "长图预览";
    }
    if (hint) {
      hint.textContent = isWeChatBrowser()
        ? "长按图片保存到相册。若无法保存，请点右上角 ⋯ → 在浏览器打开。"
        : "可右键另存，或使用上方下载。";
    }
    if (nextBtn) {
      nextBtn.hidden = !(meta.batch && meta.index < meta.total);
      nextBtn.textContent =
        meta.index < meta.total ? "下一张（" + (meta.index + 1) + "/" + meta.total + "）" : "下一张";
    }

    previewEl.hidden = false;
  }

  function closePreviewModal() {
    if (!previewEl) return;
    previewEl.hidden = true;
    if (previewEl._previewState) previewEl._previewState.onNext = null;
    var img = previewEl.querySelector(".longshot-preview__img");
    if (img && img._prevUrl) {
      URL.revokeObjectURL(img._prevUrl);
      img._prevUrl = null;
      img.removeAttribute("src");
    }
  }

  function deliverCaptureResult(blob, filename, options) {
    options = options || {};
    var wechat = isWeChatBrowser();
    if (!options.previewOnly && !wechat) {
      downloadBlob(blob, filename);
    } else if (!options.previewOnly && wechat) {
      try {
        downloadBlob(blob, filename);
      } catch (_eDl) {
        /* WeChat may block programmatic download */
      }
    }
    if (wechat || options.forcePreview) {
      showPreviewModal(blob, filename, options.previewMeta || {});
    }
  }

  function ensureWeChatBanner() {
    if (!isWeChatBrowser()) return;
    if (wechatBannerEl) return;
    wechatBannerEl = document.createElement("div");
    wechatBannerEl.className = "longshot-wechat-banner";
    wechatBannerEl.setAttribute("role", "note");
    wechatBannerEl.innerHTML =
      '<p class="longshot-wechat-banner__text">微信内保存可能受限，建议点右上角 <strong>⋯</strong> → <strong>在浏览器打开</strong> 后再导出。</p>' +
      '<button type="button" class="longshot-wechat-banner__close" aria-label="关闭提示">×</button>';
    document.body.appendChild(wechatBannerEl);
    wechatBannerEl.querySelector(".longshot-wechat-banner__close").addEventListener("click", function () {
      wechatBannerEl.hidden = true;
    });
  }

  function clampCaptureScale(value) {
    var n = parseInt(value, 10);
    if (!n || n < MIN_CAPTURE_SCALE) return MOBILE_CAPTURE_SCALE;
    return Math.min(MAX_CAPTURE_SCALE, Math.max(MIN_CAPTURE_SCALE, n));
  }

  function getUserSelectedScale() {
    if (selectedScaleCache != null) {
      return clampCaptureScale(selectedScaleCache);
    }
    try {
      var stored = global.localStorage.getItem(SCALE_KEY);
      if (stored) return clampCaptureScale(stored);
    } catch (_e) {
      /* ignore */
    }
    return MOBILE_CAPTURE_SCALE;
  }

  function setUserSelectedScale(scale) {
    selectedScaleCache = clampCaptureScale(scale);
    try {
      global.localStorage.setItem(SCALE_KEY, String(selectedScaleCache));
    } catch (_e) {
      /* ignore */
    }
    syncScaleToggleUI(selectedScaleCache);
    refreshExportPanelIfOpen();
  }

  function syncScaleToggleUI(scale) {
    document.querySelectorAll("[data-longshot-scale-option]").forEach(function (btn) {
      var val = btn.getAttribute("data-longshot-scale-option");
      var on = String(val) === String(scale);
      btn.setAttribute("aria-pressed", on ? "true" : "false");
      btn.classList.toggle("longshot-segment__btn--active", on);
    });
  }

  function bindScaleToggle(root) {
    (root || document).querySelectorAll("[data-longshot-scale-option]").forEach(function (btn) {
      if (btn.dataset.longshotScaleBound === "1") return;
      btn.dataset.longshotScaleBound = "1";
      btn.addEventListener("click", function () {
        if (btn.disabled) return;
        setUserSelectedScale(btn.getAttribute("data-longshot-scale-option"));
      });
    });
  }

  function resolveCaptureScale(explicit) {
    if (explicit != null && explicit !== "") {
      return clampCaptureScale(explicit);
    }
    var q = parseLongshotQuery();
    if (q.scale) return clampCaptureScale(q.scale);
    return getUserSelectedScale();
  }

  function parseSrcsetEntries(srcset) {
    var entries = [];
    srcset.split(",").forEach(function (part) {
      var chunk = part.trim();
      if (!chunk) return;
      var match = chunk.match(/^(\S+)\s+(\d+)w$/);
      if (match) {
        entries.push({ url: match[1], w: parseInt(match[2], 10) });
        return;
      }
      entries.push({ url: chunk.split(/\s+/)[0], w: 0 });
    });
    entries.sort(function (a, b) {
      return a.w - b.w;
    });
    return entries;
  }

  function pickBestSrcForCapture(img, requiredWidth) {
    var srcset = img.getAttribute("srcset");
    if (!srcset) return null;
    var entries = parseSrcsetEntries(srcset);
    if (!entries.length) return null;
    var need = Math.max(1, requiredWidth || CAPTURE_WIDTH);
    for (var i = 0; i < entries.length; i++) {
      if (entries[i].w >= need) return entries[i].url;
    }
    return entries[entries.length - 1].url;
  }

  function pickHighestSrcFromSrcset(img) {
    return pickBestSrcForCapture(img, 99999);
  }

  function upgradeImagesToMaxSrc(root, requiredWidth) {
    var saved = [];
    root.querySelectorAll("img").forEach(function (img) {
      var best = pickBestSrcForCapture(img, requiredWidth);
      if (!best) return;
      var current = img.currentSrc || img.src || "";
      if (srcKey(best) === srcKey(current)) return;
      saved.push({
        img: img,
        src: img.getAttribute("src"),
        srcset: img.getAttribute("srcset"),
        sizes: img.getAttribute("sizes"),
      });
      img.removeAttribute("sizes");
      img.src = best;
    });
    return saved;
  }

  function restoreUpgradedImages(saved) {
    (saved || []).forEach(function (entry) {
      if (!entry.img) return;
      if (entry.sizes == null) entry.img.removeAttribute("sizes");
      else entry.img.setAttribute("sizes", entry.sizes);
      if (entry.srcset == null) entry.img.removeAttribute("srcset");
      else entry.img.setAttribute("srcset", entry.srcset);
      if (entry.src == null) entry.img.removeAttribute("src");
      else entry.img.setAttribute("src", entry.src);
    });
  }

  function formatBytes(bytes) {
    if (bytes >= 1048576) return (bytes / 1048576).toFixed(1) + " MB";
    if (bytes >= 1024) return Math.round(bytes / 1024) + " KB";
    return bytes + " B";
  }

  function resolveOutputFormat(explicit) {
    if (explicit === "jpeg" || explicit === "png") return explicit;
    var q = parseLongshotQuery();
    if (q.format) return q.format;
    try {
      var stored = global.localStorage.getItem(FORMAT_KEY);
      if (stored === "jpeg" || stored === "png") return stored;
    } catch (_e) {
      /* ignore */
    }
    return "png";
  }

  function mapCaptureError(err) {
    var msg = (err && err.message) || String(err || "未知错误");
    if (isFileProtocol()) {
      return "无法从 file:// 生成长图。" + serveHint();
    }
    if (/html2canvas|script load failed|无法加载 html2canvas/i.test(msg)) {
      return "无法加载截图组件，请用本地 http 服务打开页面并检查网络";
    }
    if (/memory|allocation|canvas/i.test(msg)) {
      return "图片过多或过大，内存不足。可尝试 ?scale=2 降低清晰度，或 ?format=jpeg 减小体积";
    }
    if (/图片导出失败/i.test(msg)) {
      return "图片导出失败，请刷新后重试；微信内请用浏览器打开再保存";
    }
    if (isWeChatBrowser()) {
      return msg + "（微信内若无法下载，请点右上角 → 在浏览器打开）";
    }
    return msg;
  }

  function getProgress() {
    if (!progressEl) {
      progressEl = document.getElementById("longshot-progress");
      if (!progressEl) {
        progressEl = document.createElement("div");
        progressEl.id = "longshot-progress";
        progressEl.className = "longshot-progress";
        progressEl.hidden = true;
        progressEl.innerHTML =
          '<div class="longshot-progress__panel" role="status" aria-live="polite">' +
          '<p class="longshot-progress__title">正在生成长图</p>' +
          '<div class="longshot-progress__bar-wrap"><div class="longshot-progress__bar"></div></div>' +
          '<p class="longshot-progress__detail"></p>' +
          "</div>";
        document.body.appendChild(progressEl);
      }
    }
    return progressEl;
  }

  function showProgress(pct, detail) {
    var el = getProgress();
    el.hidden = false;
    var bar = el.querySelector(".longshot-progress__bar");
    var detailEl = el.querySelector(".longshot-progress__detail");
    if (bar) bar.style.width = Math.max(0, Math.min(100, pct)) + "%";
    if (detailEl) detailEl.textContent = detail || "";
  }

  function hideProgress() {
    if (progressEl) progressEl.hidden = true;
  }

  function preloadImages(root, onProgress) {
    var imgs = root.querySelectorAll("img");
    var total = imgs.length;
    var done = 0;
    function tick() {
      done += 1;
      if (onProgress) onProgress(done, total);
    }
    if (total === 0) return Promise.resolve();
    return Promise.all(
      Array.prototype.map.call(imgs, function (img) {
        img.loading = "eager";
        img.decoding = "sync";
        return new Promise(function (resolve) {
          function finish() {
            tick();
            resolve();
          }
          if (img.complete && img.naturalWidth > 0) {
            finish();
            return;
          }
          img.addEventListener("load", finish, { once: true });
          img.addEventListener("error", finish, { once: true });
          var url = img.currentSrc || img.src;
          if (url) {
            var probe = new Image();
            probe.crossOrigin = "anonymous";
            probe.onload = finish;
            probe.onerror = finish;
            probe.src = url;
          } else {
            finish();
          }
        });
      })
    );
  }

  function downloadBlob(blob, filename) {
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.rel = "noopener";
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(function () {
      URL.revokeObjectURL(url);
    }, 3000);
  }

  function srcKey(url) {
    return (url || "").split("#")[0].split("?")[0];
  }

  function buildOriginalImageMap() {
    var map = { byAsset: {}, bySrc: {} };
    document.querySelectorAll("main img").forEach(function (img) {
      var key = srcKey(img.currentSrc || img.src);
      if (key) map.bySrc[key] = img;
      var host = img.closest("[data-asset-id]");
      if (host) {
        map.byAsset[host.getAttribute("data-asset-id")] = img;
      }
    });
    map.cover = document.querySelector("main .cover-hero__media img");
    return map;
  }

  function findOriginalImage(cloneImg, imageMap) {
    var host = cloneImg.closest("[data-asset-id]");
    if (host) {
      var byAsset = imageMap.byAsset[host.getAttribute("data-asset-id")];
      if (byAsset) return byAsset;
    }
    if (cloneImg.closest(".cover-hero")) {
      return imageMap.cover || null;
    }
    var key = srcKey(cloneImg.getAttribute("src") || "");
    if (key && imageMap.bySrc[key]) {
      return imageMap.bySrc[key];
    }
    return null;
  }

  function resetImageContainers(img) {
    [
      ".media-card__visual",
      ".media-card__frame",
      ".cover-hero__media",
      ".media-scroll__item",
      ".media-scroll__track",
      ".media-row",
      ".media-card",
      ".cover-hero",
      "figure",
    ].forEach(function (sel) {
      var el = img.closest(sel);
      if (!el) return;
      el.style.width = "100%";
      el.style.maxWidth = "100%";
      el.style.height = "auto";
      el.style.maxHeight = "none";
      el.style.minHeight = "0";
      el.style.aspectRatio = "auto";
      el.style.marginLeft = "0";
      el.style.marginRight = "0";
      el.style.flex = "none";
      el.style.float = "none";
      if (
        el.classList.contains("media-card__frame") ||
        el.classList.contains("cover-hero__media") ||
        el.classList.contains("media-card__visual")
      ) {
        el.style.position = "relative";
        el.style.display = "block";
        el.style.overflow = "visible";
      }
      if (el.classList.contains("cover-hero")) {
        el.style.display = "block";
        el.style.overflow = "visible";
        el.style.alignItems = "stretch";
      }
      if (el.classList.contains("media-scroll__track")) {
        el.style.display = "flex";
        el.style.flexDirection = "column";
        el.style.overflow = "visible";
        el.style.gap = "4px";
      }
      if (el.classList.contains("media-row")) {
        el.style.display = "flex";
        el.style.flexDirection = "column";
        el.style.gap = "4px";
      }
    });
  }

  function pinImageLayout(img, w, h) {
    img.style.width = w + "px";
    img.style.height = h + "px";
    img.style.minWidth = w + "px";
    img.style.minHeight = h + "px";
    img.style.maxWidth = w + "px";
    img.style.maxHeight = h + "px";
    if (img.tagName === "CANVAS") {
      // 重设 canvas 像素尺寸会清空位图；仅改 CSS，位图尺寸由 rasterizeForCapture 决定
    } else {
      img.setAttribute("width", String(w));
      img.setAttribute("height", String(h));
    }

    var frame =
      img.closest(".media-card__frame") ||
      img.closest(".cover-hero__media") ||
      img.closest(".media-scroll__item") ||
      img.closest(".media-row");
    if (frame) {
      frame.style.height = h + "px";
      frame.style.minHeight = h + "px";
      frame.style.maxHeight = h + "px";
      frame.style.display = "block";
      frame.style.overflow = "visible";
    }

    var card = img.closest(".media-card");
    if (card) {
      card.style.display = "block";
      card.style.height = "auto";
      card.style.overflow = "visible";
    }

    var hero = img.closest(".cover-hero");
    if (hero) {
      hero.style.height = h + "px";
      hero.style.minHeight = h + "px";
      hero.style.maxHeight = "none";
      hero.style.display = "block";
      hero.style.overflow = "visible";
      var text = hero.querySelector(".cover-hero__text");
      if (text) {
        text.style.position = "relative";
        text.style.display = "block";
      }
    }
  }

  function shouldUseDisplaySizes(_layout) {
    // 截图前一律优先屏上绘制盒（含 object-fit: contain 的真实绘制区），与手机版修复一致
    return true;
  }

  function getContainBoxSize(img) {
    var frame =
      img.closest(".media-card__frame") ||
      img.closest(".cover-hero__media") ||
      img.closest(".media-scroll__item") ||
      img.closest(".media-row");
    if (frame) {
      var rect = frame.getBoundingClientRect();
      if (rect.width > 0 && rect.height > 0) {
        return { w: rect.width, h: rect.height };
      }
    }
    var rect = img.getBoundingClientRect();
    if (rect.width > 0 && rect.height > 0) {
      return { w: rect.width, h: rect.height };
    }
    return null;
  }

  function getPaintedImageSize(img) {
    var nw = img.naturalWidth;
    var nh = img.naturalHeight;
    if (!nw || !nh) {
      var rect = img.getBoundingClientRect();
      if (rect.width <= 0 || rect.height <= 0) return null;
      return { w: rect.width, h: rect.height };
    }

    var box = getContainBoxSize(img);
    if (!box) return null;

    var fit = getComputedStyle(img).objectFit || "fill";
    if (fit === "contain" || fit === "scale-down") {
      var scale = Math.min(box.w / nw, box.h / nh);
      if (scale <= 0) return { w: box.w, h: box.h };
      return { w: nw * scale, h: nh * scale };
    }
    if (fit === "cover") {
      return { w: box.w, h: box.h };
    }
    return { w: box.w, h: box.h };
  }

  function buildDisplaySizeMap(root) {
    var map = new WeakMap();
    root.querySelectorAll("img").forEach(function (img) {
      var size = getPaintedImageSize(img);
      if (size) map.set(img, size);
    });
    return map;
  }

  function captureDimensions(origImg, width, sizeMap, useDisplaySizes) {
    var w = width;
    if (useDisplaySizes && origImg && sizeMap && sizeMap.has(origImg)) {
      var rec = sizeMap.get(origImg);
      return { w: w, h: Math.max(1, Math.round((rec.h / rec.w) * w)) };
    }
    if (origImg && origImg.naturalWidth && origImg.naturalHeight) {
      return {
        w: w,
        h: Math.max(1, Math.round((origImg.naturalHeight / origImg.naturalWidth) * w)),
      };
    }
    if (origImg && sizeMap && sizeMap.has(origImg)) {
      var fallback = sizeMap.get(origImg);
      return { w: w, h: Math.max(1, Math.round((fallback.h / fallback.w) * w)) };
    }
    return { w: w, h: w };
  }

  function buildCaptureDimensionMap(root, width, sizeMap, useDisplaySizes) {
    var byImg = new WeakMap();
    var bySrc = {};
    root.querySelectorAll("img").forEach(function (img) {
      var dim = captureDimensions(img, width, sizeMap, useDisplaySizes);
      byImg.set(img, dim);
      var key = srcKey(img.currentSrc || img.src);
      if (key) bySrc[key] = dim;
    });
    return { byImg: byImg, bySrc: bySrc };
  }

  function lookupCaptureDim(origImg, cloneImg, dimStore) {
    if (origImg && dimStore.byImg.has(origImg)) {
      return dimStore.byImg.get(origImg);
    }
    var key = srcKey((cloneImg && cloneImg.getAttribute("src")) || "");
    if (key && dimStore.bySrc[key]) {
      return dimStore.bySrc[key];
    }
    return null;
  }

  function rasterizeForCapture(origImg, w, h, doc, pixelScale) {
    if (!origImg || !origImg.naturalWidth || !origImg.naturalHeight) return null;
    pixelScale = pixelScale || 1;
    var ownerDoc = doc || document;
    var canvas = ownerDoc.createElement("canvas");
    var pxW = Math.max(1, Math.round(w * pixelScale));
    var pxH = Math.max(1, Math.round(h * pixelScale));
    canvas.width = pxW;
    canvas.height = pxH;
    canvas.setAttribute("data-longshot-raster", "1");
    if (origImg.className) canvas.className = origImg.className;
    canvas.style.display = "block";
    canvas.style.width = w + "px";
    canvas.style.height = h + "px";
    canvas.style.maxWidth = "none";
    canvas.style.maxHeight = "none";
    try {
      canvas.getContext("2d").drawImage(origImg, 0, 0, pxW, pxH);
    } catch (_e) {
      return null;
    }
    return canvas;
  }

  function normalizeImageForCapture(
    origImg,
    cloneImg,
    width,
    sizeMap,
    useDisplaySizes,
    dimStore,
    pixelScale
  ) {
    var dim =
      (dimStore && lookupCaptureDim(origImg, cloneImg, dimStore)) ||
      captureDimensions(origImg, width, sizeMap, useDisplaySizes);
    if (!dim || !cloneImg) return;

    if (origImg && origImg.naturalWidth && cloneImg.parentNode) {
      var raster = rasterizeForCapture(origImg, dim.w, dim.h, cloneImg.ownerDocument, pixelScale);
      if (raster) {
        resetImageContainers(cloneImg);
        cloneImg.parentNode.replaceChild(raster, cloneImg);
        return;
      }
    }

    resetImageContainers(cloneImg);
    cloneImg.removeAttribute("sizes");
    cloneImg.removeAttribute("srcset");
    cloneImg.style.display = "block";
    cloneImg.style.position = "static";
    cloneImg.style.objectFit = "fill";
    cloneImg.style.objectPosition = "center";
    cloneImg.style.verticalAlign = "top";
    cloneImg.style.flex = "none";
    cloneImg.style.float = "none";
    pinImageLayout(cloneImg, dim.w, dim.h);
  }

  function normalizeCloneImages(
    clonedRoot,
    imageMap,
    width,
    sizeMap,
    useDisplaySizes,
    dimStore,
    pixelScale
  ) {
    clonedRoot.querySelectorAll("img").forEach(function (cloneImg) {
      normalizeImageForCapture(
        findOriginalImage(cloneImg, imageMap),
        cloneImg,
        width,
        sizeMap,
        useDisplaySizes,
        dimStore,
        pixelScale
      );
    });
  }

  function normalizeLiveImages(root, imageMap, width, sizeMap, useDisplaySizes, dimStore, pixelScale) {
    var saved = [];
    root.querySelectorAll("img").forEach(function (img) {
      saved.push({
        orig: img,
        cssText: img.style.cssText,
        widthAttr: img.getAttribute("width"),
        heightAttr: img.getAttribute("height"),
        sizesAttr: img.getAttribute("sizes"),
        srcsetAttr: img.getAttribute("srcset"),
        containerStyles: [
          ".media-card__visual",
          ".media-card__frame",
          ".cover-hero__media",
          ".cover-hero",
          ".media-card",
          ".media-scroll__item",
          ".media-scroll__track",
          ".media-row",
          "figure",
        ]
          .map(function (sel) {
            var el = img.closest(sel);
            return el ? { el: el, cssText: el.style.cssText } : null;
          })
          .filter(Boolean),
      });
      normalizeImageForCapture(img, img, width, sizeMap, useDisplaySizes, dimStore, pixelScale);
    });
    return saved;
  }

  function restoreLiveImages(saved) {
    saved.forEach(function (entry) {
      if (!entry.orig) return;
      entry.orig.style.cssText = entry.cssText || "";
      if (entry.widthAttr == null) entry.orig.removeAttribute("width");
      else entry.orig.setAttribute("width", entry.widthAttr);
      if (entry.heightAttr == null) entry.orig.removeAttribute("height");
      else entry.orig.setAttribute("height", entry.heightAttr);
      if (entry.sizesAttr == null) entry.orig.removeAttribute("sizes");
      else entry.orig.setAttribute("sizes", entry.sizesAttr);
      if (entry.srcsetAttr == null) entry.orig.removeAttribute("srcset");
      else entry.orig.setAttribute("srcset", entry.srcsetAttr);
      (entry.containerStyles || []).forEach(function (item) {
        item.el.style.cssText = item.cssText;
      });
    });
  }

  function pinLiveCaptureLayout(main) {
    return {
      mainWidth: main.style.width,
      mainMaxWidth: main.style.maxWidth,
      htmlWidth: document.documentElement.style.width,
      htmlMaxWidth: document.documentElement.style.maxWidth,
      bodyWidth: document.body.style.width,
      bodyMaxWidth: document.body.style.maxWidth,
    };
  }

  function applyCaptureLayout(main) {
    main.style.width = CAPTURE_WIDTH + "px";
    main.style.maxWidth = CAPTURE_WIDTH + "px";
    document.documentElement.style.width = CAPTURE_WIDTH + "px";
    document.documentElement.style.maxWidth = CAPTURE_WIDTH + "px";
    document.body.style.width = CAPTURE_WIDTH + "px";
    document.body.style.maxWidth = CAPTURE_WIDTH + "px";
  }

  function restoreCaptureLayout(main, saved) {
    main.style.width = saved.mainWidth;
    main.style.maxWidth = saved.mainMaxWidth;
    document.documentElement.style.width = saved.htmlWidth;
    document.documentElement.style.maxWidth = saved.htmlMaxWidth;
    document.body.style.width = saved.bodyWidth;
    document.body.style.maxWidth = saved.bodyMaxWidth;
  }

  function prepareClone(doc, clonedRoot, imageMap, sizeMap, useDisplaySizes, dimStore, pixelScale) {
    doc.documentElement.setAttribute("data-layout", "mobile");
    doc.documentElement.classList.add(ROOT_CLASS);
    doc.body.classList.add(CAPTURING_CLASS);
    doc.documentElement.style.width = CAPTURE_WIDTH + "px";
    doc.documentElement.style.maxWidth = CAPTURE_WIDTH + "px";
    doc.body.style.width = CAPTURE_WIDTH + "px";
    doc.body.style.maxWidth = CAPTURE_WIDTH + "px";
    if (clonedRoot && clonedRoot.style) {
      clonedRoot.style.width = CAPTURE_WIDTH + "px";
      clonedRoot.style.maxWidth = CAPTURE_WIDTH + "px";
    }

    var removeSelectors = [
      ".golden-banner",
      ".longshot-toolbar",
      ".longshot-wechat-banner",
      ".longshot-preview",
      ".longshot-export-sheet",
      "#longshot-toast",
      ".longshot-toast",
      ".footer-cta",
    ];
    removeSelectors.forEach(function (sel) {
      doc.querySelectorAll(sel).forEach(function (el) {
        el.remove();
      });
    });

    doc.querySelectorAll("details.voice-transcript").forEach(function (d) {
      d.removeAttribute("open");
    });

    doc.querySelectorAll(".cover-hero__overlay").forEach(function (el) {
      el.style.display = "none";
    });

    if (clonedRoot) {
      normalizeCloneImages(
        clonedRoot,
        imageMap,
        CAPTURE_WIDTH,
        sizeMap,
        useDisplaySizes,
        dimStore,
        pixelScale
      );
    }
  }

  async function captureMainToBlob(options) {
    options = options || {};
    teardownReadingMotion();
    var outputFormat = resolveOutputFormat(options.format);

    if (isFileProtocol()) {
      throw new Error("file protocol");
    }

    var main = document.querySelector("main");
    if (!main) throw new Error("未找到游记正文");

    var imgTotal = main.querySelectorAll("img").length;
    var captureScale = resolveCaptureScale(options.scale);
    var outputWidth = CAPTURE_WIDTH * captureScale;
    var requiredSrcWidth = outputWidth;
    var largeTrip = imgTotal > LARGE_TRIP_IMAGES;
    var shared = options.sharedState || null;
    var html2canvas;

    if (!options.quietProgress) {
      showProgress(5, "加载截图组件…");
    }
    if (shared && shared.html2canvas) {
      html2canvas = shared.html2canvas;
    } else {
      html2canvas = await loadHtml2Canvas();
      if (shared) shared.html2canvas = html2canvas;
    }
    if (!options.quietProgress) {
      showProgress(
        10,
        "加载图片（" +
          captureScale +
          "×" +
          (largeTrip && captureScale >= DESKTOP_CAPTURE_SCALE ? " · 图片较多请稍候" : "") +
          "）…"
      );
    }

    var root = document.documentElement;
    var prevLayout = root.getAttribute("data-layout");
    var prevScroll = window.scrollY;
    var imageMap = buildOriginalImageMap();
    var layoutSaved = pinLiveCaptureLayout(main);
    var liveImageSaved = null;
    var upgradedSrcSaved = null;
    var displaySizeMap = null;
    var captureDimStore = null;
    var useDisplaySizes = shouldUseDisplaySizes(prevLayout);

    try {
      if (shared && shared.preloaded) {
        upgradedSrcSaved = shared.upgradedSrcSaved;
      } else {
        upgradedSrcSaved = upgradeImagesToMaxSrc(main, requiredSrcWidth);
        await preloadImages(main, function (done, total) {
          if (options.quietProgress) return;
          var pct = 10 + Math.round((done / Math.max(total, 1)) * 50);
          showProgress(pct, "预加载高清图 " + done + "/" + total);
        });
        if (shared) {
          shared.upgradedSrcSaved = upgradedSrcSaved;
          shared.preloaded = true;
        }
      }
      if (!options.quietProgress) {
        showProgress(62, "调整排版…");
      }
      displaySizeMap = buildDisplaySizeMap(main);
      captureDimStore = buildCaptureDimensionMap(
        main,
        CAPTURE_WIDTH,
        displaySizeMap,
        useDisplaySizes
      );

      document.body.classList.add(CAPTURING_CLASS);
      root.classList.add(ROOT_CLASS);
      root.setAttribute("data-layout", "mobile");
      applyCaptureLayout(main);
      window.scrollTo(0, 0);

      liveImageSaved = normalizeLiveImages(
        main,
        imageMap,
        CAPTURE_WIDTH,
        displaySizeMap,
        useDisplaySizes,
        captureDimStore,
        captureScale
      );
      await new Promise(function (r) {
        requestAnimationFrame(function () {
          requestAnimationFrame(r);
        });
      });

      if (!options.quietProgress) {
        showProgress(72, "合成长图（" + imgTotal + " 张 · " + outputWidth + "px 宽）…");
      }

      var scale = captureScale;
      var pageBg =
        getComputedStyle(document.documentElement).getPropertyValue("--bg-page").trim() ||
        getComputedStyle(document.body).backgroundColor ||
        "#111110";
      if (pageBg && !/^#|rgb|hsl/.test(pageBg)) {
        pageBg = "#111110";
      }

      var captureHeight = Math.max(
        main.scrollHeight,
        main.offsetHeight,
        document.documentElement.scrollHeight
      );

      var canvas = await html2canvas(main, {
        backgroundColor: pageBg,
        scale: scale,
        useCORS: true,
        allowTaint: false,
        logging: false,
        windowWidth: CAPTURE_WIDTH,
        windowHeight: captureHeight,
        scrollX: 0,
        scrollY: 0,
        onclone: function (doc, clonedElement) {
          prepareClone(
            doc,
            clonedElement,
            imageMap,
            displaySizeMap,
            useDisplaySizes,
            captureDimStore,
            captureScale
          );
        },
      });

      if (!options.quietProgress) {
        showProgress(92, "导出文件…");
      }

      var title =
        document.querySelector(".cover-hero__text h1")?.textContent ||
        document.title ||
        "travelogue";
      var mime = outputFormat === "jpeg" ? "image/jpeg" : "image/png";
      var quality = outputFormat === "jpeg" ? JPEG_QUALITY : undefined;
      var blob = await new Promise(function (resolve, reject) {
        canvas.toBlob(
          function (b) {
            if (b) resolve(b);
            else reject(new Error("图片导出失败"));
          },
          mime,
          quality
        );
      });

      return {
        blob: blob,
        title: title,
        outputFormat: outputFormat,
        captureScale: captureScale,
        outputWidth: outputWidth,
        imgTotal: imgTotal,
      };
    } finally {
      if (!options.keepProgress) hideProgress();
      if (liveImageSaved) restoreLiveImages(liveImageSaved);
      if (!shared && upgradedSrcSaved) restoreUpgradedImages(upgradedSrcSaved);
      document.body.classList.remove(CAPTURING_CLASS);
      root.classList.remove(ROOT_CLASS);
      restoreCaptureLayout(main, layoutSaved);
      if (prevLayout) root.setAttribute("data-layout", prevLayout);
      else root.removeAttribute("data-layout");
      window.scrollTo(0, prevScroll);
      restoreReadingMotion();
    }
  }

  async function captureLongShotFull(options) {
    options = options || {};
    var result = await captureMainToBlob(options);
    var filename = options.filename || slugFilename(result.title, result.outputFormat);
    deliverCaptureResult(result.blob, filename, {
      forcePreview: isWeChatBrowser() || options.forcePreview,
      previewMeta: options.previewMeta,
    });
    try {
      global.localStorage.setItem(FORMAT_KEY, result.outputFormat);
      global.localStorage.setItem(SCALE_KEY, String(result.captureScale));
      selectedScaleCache = result.captureScale;
    } catch (_e) {
      /* ignore */
    }
    if (!options.quietProgress) {
      showProgress(100, "完成");
    }
    var fmtLabel = result.outputFormat === "jpeg" ? "JPEG" : "PNG";
    var sizeLabel = formatBytes(result.blob.size);
    toast(
      "长图已保存（" +
        result.captureScale +
        "× · " +
        fmtLabel +
        " · " +
        result.outputWidth +
        "px · " +
        sizeLabel +
        "）"
    );
    if (
      result.blob.size > 35 * 1048576 &&
      result.outputFormat === "png" &&
      result.captureScale >= DESKTOP_CAPTURE_SCALE
    ) {
      setTimeout(function () {
        toast("体积较大：可切换「标准 2×」、按章导出，或加 ?format=jpeg", true);
      }, 2600);
    }
    return result;
  }

  async function captureLongShotByChapter(options) {
    options = options || {};
    var main = document.querySelector("main");
    if (!main) throw new Error("未找到游记正文");
    var chapters = listChapterSections(main);
    if (!chapters.length) throw new Error("未找到章节");

    var outputFormat = resolveOutputFormat(options.format);
    var captureScale = resolveCaptureScale(options.scale);
    var tripTitle =
      document.querySelector(".cover-hero__text h1")?.textContent ||
      document.title ||
      "travelogue";
    var total = chapters.length;
    var sharedState = { html2canvas: null, upgradedSrcSaved: null, preloaded: false };
    var previewQueue = [];

    showProgress(8, "按章导出 0/" + total + "…");
    for (var i = 0; i < total; i++) {
      var ch = chapters[i];
      var chTitle = (ch.querySelector(".chapter-header h2") || {}).textContent || "第" + (i + 1) + "章";
      var visibilitySaved = applyChapterVisibility(main, chapters, i);
      var pct = 8 + Math.round(((i + 0.2) / total) * 88);
      showProgress(pct, "第 " + (i + 1) + "/" + total + " 章 · " + chTitle.trim());
      try {
        var result = await captureMainToBlob({
          format: outputFormat,
          scale: captureScale,
          sharedState: sharedState,
          quietProgress: true,
          keepProgress: true,
        });
        var filename = chapterFilename(tripTitle, i + 1, chTitle, outputFormat);
        previewQueue.push({
          blob: result.blob,
          filename: filename,
          meta: {
            index: i + 1,
            total: total,
            title: chTitle.trim(),
            batch: true,
          },
        });
      } finally {
        restoreChapterVisibility(visibilitySaved);
      }
    }

    if (sharedState.upgradedSrcSaved) restoreUpgradedImages(sharedState.upgradedSrcSaved);

    function showQueuedPreview(index) {
      var item = previewQueue[index];
      if (!item) return;
      var meta = Object.assign({}, item.meta, {
        onNext:
          index + 1 < previewQueue.length
            ? function () {
                showQueuedPreview(index + 1);
              }
            : null,
      });
      deliverCaptureResult(item.blob, item.filename, {
        previewMeta: meta,
        forcePreview: isWeChatBrowser(),
      });
    }

    if (isWeChatBrowser()) {
      showQueuedPreview(0);
    } else {
      previewQueue.forEach(function (item) {
        deliverCaptureResult(item.blob, item.filename, {});
      });
    }

    hideProgress();
    try {
      global.localStorage.setItem(FORMAT_KEY, outputFormat);
      global.localStorage.setItem(SCALE_KEY, String(captureScale));
      selectedScaleCache = captureScale;
    } catch (_eStore) {
      /* ignore */
    }
    toast("已导出 " + total + " 张按章长图（" + captureScale + "×）");
    return previewQueue;
  }

  async function captureLongShot(options) {
    options = options || {};
    var mode = options.mode || getUserSelectedMode();
    if (mode === MODE_CHAPTER) {
      return captureLongShotByChapter(options);
    }
    return captureLongShotFull(options);
  }

  function runCapture(btn, format) {
    if (btn && btn.disabled) return;
    if (isFileProtocol()) {
      ensureFileProtocolBanner();
      toast(mapCaptureError(new Error("file protocol")), true);
      return;
    }
    var label = (btn && btn.getAttribute("data-longshot-label")) || "保存长图";
    var busyText = (btn && btn.getAttribute("data-longshot-busy")) || "生成中…";
    var prevText = btn ? btn.textContent : "";
    if (btn) {
      btn.disabled = true;
      btn.setAttribute("aria-busy", "true");
      btn.textContent = busyText;
    }

    openExportPanel()
      .then(function (choice) {
        return captureLongShot({
          format: format,
          scale: choice.scale,
          mode: choice.mode,
        });
      })
      .catch(function (err) {
        if ((err && err.message) === "已取消") return;
        console.error("[longshot]", err);
        toast(mapCaptureError(err), true);
      })
      .finally(function () {
        if (!btn) return;
        btn.disabled = false;
        btn.removeAttribute("aria-busy");
        btn.textContent = prevText || label;
      });
  }

  function bindButton(btn) {
    if (!btn || btn.dataset.longshotBound === "1") return;
    btn.dataset.longshotBound = "1";

    btn.addEventListener("click", function () {
      var format = btn.getAttribute("data-longshot-format") || null;
      runCapture(btn, format);
    });
  }

  function maybeAutoCapture() {
    if (document.documentElement.getAttribute("data-longshot") !== "on") return;
    if (isFileProtocol()) return;
    var q = parseLongshotQuery();
    if (!q.auto) return;

    function start() {
      runCapture(null, q.format);
    }

    if (document.readyState === "complete") {
      setTimeout(start, 400);
    } else {
      global.addEventListener("load", function () {
        setTimeout(start, 400);
      });
    }
  }

  function init() {
    if (guardFileProtocol()) return;
    applyQueryPrefs();
    initCaptionDisplay();
    ensureWeChatBanner();
    document
      .querySelectorAll("[data-longshot-trigger]")
      .forEach(function (el) {
        bindButton(el);
      });

    var fab = document.getElementById("longshot-save");
    if (fab) bindButton(fab);

    maybeAutoCapture();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  global.TravelogueLongshot = {
    capture: captureLongShot,
    captureFull: captureLongShotFull,
    captureByChapter: captureLongShotByChapter,
    captureMainToBlob: captureMainToBlob,
    captureDimensions: captureDimensions,
    buildDisplaySizeMap: buildDisplaySizeMap,
    getPaintedImageSize: getPaintedImageSize,
    shouldUseDisplaySizes: shouldUseDisplaySizes,
    pinImageLayout: pinImageLayout,
    pickHighestSrcFromSrcset: pickHighestSrcFromSrcset,
    pickBestSrcForCapture: pickBestSrcForCapture,
    resolveCaptureScale: resolveCaptureScale,
    getUserSelectedScale: getUserSelectedScale,
    setUserSelectedScale: setUserSelectedScale,
    getUserSelectedMode: getUserSelectedMode,
    setUserSelectedMode: setUserSelectedMode,
    clampCaptureScale: clampCaptureScale,
    MODE_FULL: MODE_FULL,
    MODE_CHAPTER: MODE_CHAPTER,
    SINGLE_PAGE_MAX_IMAGES: SINGLE_PAGE_MAX_IMAGES,
    LARGE_TRIP_IMAGES: LARGE_TRIP_IMAGES,
    DESKTOP_CAPTURE_SCALE: DESKTOP_CAPTURE_SCALE,
    MOBILE_CAPTURE_SCALE: MOBILE_CAPTURE_SCALE,
    MAX_CAPTURE_SCALE: MAX_CAPTURE_SCALE,
    openExportPanel: openExportPanel,
    buildExportSummary: buildExportSummary,
    areCaptionsVisible: areCaptionsVisible,
    applyCaptionDisplay: applyCaptionDisplay,
    applyCaptionEditMode: applyCaptionEditMode,
  };
})(typeof window !== "undefined" ? window : this);
