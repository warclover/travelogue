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
  var CAPTURING_CLASS = "longshot-capturing";
  var ROOT_CLASS = "longshot-capturing-root";

  var html2canvasPromise = null;
  var toastEl = null;

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

  function slugFilename(title) {
    var t = (title || "travelogue").trim().slice(0, 24);
    t = t.replace(/[<>:"/\\|?*\x00-\x1f]/g, "").replace(/\s+/g, "-");
    return (t || "travelogue") + "-长图.png";
  }

  function preloadImages(root) {
    var imgs = root.querySelectorAll("img");
    return Promise.all(
      Array.prototype.map.call(imgs, function (img) {
        img.loading = "eager";
        img.decoding = "sync";
        if (img.complete && img.naturalWidth > 0) return Promise.resolve();
        return new Promise(function (resolve) {
          function done() {
            resolve();
          }
          img.addEventListener("load", done, { once: true });
          img.addEventListener("error", done, { once: true });
          var url = img.currentSrc || img.src;
          if (url) {
            var probe = new Image();
            probe.crossOrigin = "anonymous";
            probe.onload = done;
            probe.onerror = done;
            probe.src = url;
          } else {
            resolve();
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

  function rasterizeForCapture(origImg, w, h, doc) {
    if (!origImg || !origImg.naturalWidth || !origImg.naturalHeight) return null;
    var ownerDoc = doc || document;
    var canvas = ownerDoc.createElement("canvas");
    canvas.width = w;
    canvas.height = h;
    canvas.setAttribute("data-longshot-raster", "1");
    if (origImg.className) canvas.className = origImg.className;
    canvas.style.display = "block";
    canvas.style.width = w + "px";
    canvas.style.height = h + "px";
    canvas.style.maxWidth = "none";
    canvas.style.maxHeight = "none";
    try {
      canvas.getContext("2d").drawImage(origImg, 0, 0, w, h);
    } catch (_e) {
      return null;
    }
    return canvas;
  }

  function normalizeImageForCapture(origImg, cloneImg, width, sizeMap, useDisplaySizes, dimStore) {
    var dim =
      (dimStore && lookupCaptureDim(origImg, cloneImg, dimStore)) ||
      captureDimensions(origImg, width, sizeMap, useDisplaySizes);
    if (!dim || !cloneImg) return;

    if (origImg && origImg.naturalWidth && cloneImg.parentNode) {
      var raster = rasterizeForCapture(origImg, dim.w, dim.h, cloneImg.ownerDocument);
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

  function normalizeCloneImages(clonedRoot, imageMap, width, sizeMap, useDisplaySizes, dimStore) {
    clonedRoot.querySelectorAll("img").forEach(function (cloneImg) {
      normalizeImageForCapture(
        findOriginalImage(cloneImg, imageMap),
        cloneImg,
        width,
        sizeMap,
        useDisplaySizes,
        dimStore
      );
    });
  }

  function normalizeLiveImages(root, imageMap, width, sizeMap, useDisplaySizes, dimStore) {
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
      normalizeImageForCapture(img, img, width, sizeMap, useDisplaySizes, dimStore);
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

  function prepareClone(doc, clonedRoot, imageMap, sizeMap, useDisplaySizes, dimStore) {
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
        dimStore
      );
    }
  }

  async function captureLongShot() {
    var main = document.querySelector("main");
    if (!main) throw new Error("未找到游记正文");

    var html2canvas = await loadHtml2Canvas();
    var root = document.documentElement;
    var prevLayout = root.getAttribute("data-layout");
    var prevScroll = window.scrollY;
    var imageMap = buildOriginalImageMap();
    var layoutSaved = pinLiveCaptureLayout(main);
    var liveImageSaved = null;
    var displaySizeMap = null;
    var captureDimStore = null;
    var useDisplaySizes = shouldUseDisplaySizes(prevLayout);

    try {
      await preloadImages(main);
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
        captureDimStore
      );
      await new Promise(function (r) {
        requestAnimationFrame(function () {
          requestAnimationFrame(r);
        });
      });

      var scale = Math.min(2, global.devicePixelRatio || 2);
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
            captureDimStore
          );
        },
      });

      var title =
        document.querySelector(".cover-hero__text h1")?.textContent ||
        document.title ||
        "travelogue";
      var blob = await new Promise(function (resolve, reject) {
        canvas.toBlob(function (b) {
          if (b) resolve(b);
          else reject(new Error("图片导出失败"));
        }, "image/png");
      });

      downloadBlob(blob, slugFilename(title));
      toast("长图已保存（9:16 竖版，可发朋友圈）");
    } finally {
      if (liveImageSaved) restoreLiveImages(liveImageSaved);
      document.body.classList.remove(CAPTURING_CLASS);
      root.classList.remove(ROOT_CLASS);
      restoreCaptureLayout(main, layoutSaved);
      if (prevLayout) root.setAttribute("data-layout", prevLayout);
      else root.removeAttribute("data-layout");
      window.scrollTo(0, prevScroll);
    }
  }

  function bindButton(btn) {
    if (!btn || btn.dataset.longshotBound === "1") return;
    btn.dataset.longshotBound = "1";

    btn.addEventListener("click", function () {
      if (btn.disabled) return;
      var label = btn.getAttribute("data-longshot-label") || "保存长图";
      btn.disabled = true;
      btn.setAttribute("aria-busy", "true");
      var busyText = btn.getAttribute("data-longshot-busy") || "生成中…";
      var prevText = btn.textContent;
      btn.textContent = busyText;

      captureLongShot()
        .catch(function (err) {
          console.error("[longshot]", err);
          toast(err.message || String(err), true);
        })
        .finally(function () {
          btn.disabled = false;
          btn.removeAttribute("aria-busy");
          btn.textContent = prevText || label;
        });
    });
  }

  function init() {
    document
      .querySelectorAll("[data-longshot-trigger]")
      .forEach(function (el) {
        bindButton(el);
      });

    var fab = document.getElementById("longshot-save");
    if (fab) bindButton(fab);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  global.TravelogueLongshot = {
    capture: captureLongShot,
    captureDimensions: captureDimensions,
    buildDisplaySizeMap: buildDisplaySizeMap,
    getPaintedImageSize: getPaintedImageSize,
    shouldUseDisplaySizes: shouldUseDisplaySizes,
    pinImageLayout: pinImageLayout,
  };
})(typeof window !== "undefined" ? window : this);
