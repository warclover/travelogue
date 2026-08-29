// @ts-nocheck
/**
 * LIVE · Preview toolbar refine sheet (cover | page | book).
 * Loaded by: init-v3.js. Filename v3 ≠ frozen.
 * Export decisions stay in Dock. Not a reader-facing module.
 */
"use strict";

import { trackStudioEvent } from "./js/analytics.js";
import { postJsonConflictRetry } from "./js/http.js";
import { isAiSurfaceEnabled } from "./js/ai-surface.js";
import { DARK_COPY } from "./js/ai-surface-dark-copy.js";
import { showToolbarToast, tripApiBase, tripIdFromPath } from "./preview-toolbar/shell.js";

var TAB_MODES = [
  { id: "cover", label: "封面" },
  { id: "page", label: "页面" },
  { id: "book", label: "画册" },
];

var COVER_SEGS = [
  { id: "photo", label: "照片", hint: "封面/封底" },
  { id: "style", label: "版式", hint: "样式" },
  { id: "name", label: "杂志名", hint: "改名·字体" },
];

var TAB_ALIASES = {
  edit: "book",
  structure: "book",
  layout: "book",
  advanced: "book",
  more: "book",
  bookends: "cover",
};

function resolveCoverSeg(segId) {
  if (segId === "style" || segId === "name" || segId === "photo") return segId;
  if (segId === "title" || segId === "font") return "name";
  return "photo";
}

function resolveSheetTab(tabId) {
  if (!tabId) return "page";
  return TAB_ALIASES[tabId] || tabId;
}

function findDominantScreen() {
  var nodes = document.querySelectorAll(
    ".cover-opening[data-block='cover-opening'], .cover-closing[data-block='cover-closing'], .layout-screen, .screen-spread[data-block='screen-spread'], section.chapter .layout-screen, [data-role='moment'], [data-role='peak']"
  );
  var best = null;
  var bestVis = 0;
  nodes.forEach(function (el) {
    var rect = el.getBoundingClientRect();
    var vis = Math.min(rect.bottom, window.innerHeight) - Math.max(rect.top, 0);
    if (vis > bestVis) {
      bestVis = vis;
      best = el;
    }
  });
  return best;
}

function describeScreenContext(el) {
  if (!el) {
    return { empty: true, label: "当前页", detail: "" };
  }
  var block = el.getAttribute("data-block") || "";
  if (block === "cover-opening" || el.classList.contains("cover-opening")) {
    return { empty: true, label: "封面", detail: "cover" };
  }
  if (block === "cover-closing" || el.classList.contains("cover-closing")) {
    return { empty: true, label: "封底", detail: "closing" };
  }
  var chapter = el.closest("section.chapter[data-chapter-id]");
  var chapterName =
    (chapter &&
      (chapter.getAttribute("data-chapter-title") ||
        (chapter.querySelector(".chapter-header__title, .chapter-title") || {}).textContent)) ||
    "";
  chapterName = String(chapterName || "").trim();
  var screens = chapter
    ? chapter.querySelectorAll(".layout-screen, .screen-spread, [data-role='moment'], [data-role='peak']")
    : [];
  var idx = 0;
  for (var i = 0; i < screens.length; i++) {
    if (screens[i] === el) {
      idx = i + 1;
      break;
    }
  }
  var label =
    (idx ? "第 " + idx + " 页" : "画册正文") + (chapterName ? " · " + chapterName : "");
  var kicker = el.querySelector(".kicker, .hook-line, [data-copy-role='kicker']");
  var body = el.querySelector(".caption, .lead, .body-copy, [data-copy-role='caption'], [data-copy-role='lead']");
  var rawIds = el.getAttribute("data-asset-ids") || "";
  var primaryAssetId = (rawIds.split(",")[0] || "").trim();
  var isAppendix =
    !!(chapter && chapter.getAttribute("data-appendix") === "1");
  return {
    empty: false,
    label: label,
    detail: "body",
    screen: el,
    featured: el.getAttribute("data-featured") === "true",
    hasStar: !!el.querySelector(".preview-toolbar__featured-star"),
    hasMediaCtl: !!el.querySelector(
      ".preview-toolbar__collage-ctrl, .preview-toolbar__collage-select"
    ),
    copyHint: !!(kicker || body),
    isAppendix: isAppendix,
    primaryAssetId: primaryAssetId,
  };
}

export function mountPreviewUnifiedSheet(root, hooks) {
  hooks = hooks || {};
  var shell = document.createElement("div");
  shell.className = "preview-sheet-root";
  shell.hidden = true;
  shell.innerHTML =
    '<div class="preview-sheet__scrim"></div>' +
    '<div class="preview-sheet" role="dialog" aria-modal="true" aria-labelledby="preview-sheet-title" hidden>' +
    '<div class="preview-sheet__grab" aria-hidden="true"></div>' +
    '<div class="preview-sheet__head">' +
    '<h2 id="preview-sheet-title" class="preview-sheet__title">精修</h2>' +
    '<button type="button" class="preview-sheet__close" aria-label="关闭">×</button>' +
    "</div>" +
    '<div class="preview-sheet__content">' +
    '<nav class="preview-sheet__tabs" role="tablist"></nav>' +
    '<div class="preview-sheet__body"></div>' +
    "</div>" +
    "</div>";
  document.body.appendChild(shell);

  var sheet = shell.querySelector(".preview-sheet");
  var scrim = shell.querySelector(".preview-sheet__scrim");
  var closeBtn = shell.querySelector(".preview-sheet__close");
  var tabsEl = shell.querySelector(".preview-sheet__tabs");
  var bodyEl = shell.querySelector(".preview-sheet__body");
  var menuBtn = root.querySelector(".preview-toolbar__menu-btn");

  var activeTab = "page";
  /** RCI · 封面二级分段 photo | style | name */
  var activeCoverSeg = "photo";
  var previousFocus = null;
  var pendingDot = false;
  var structureDot = false;
  var focusRelease = null;
  var lenisPausedBySheet = false;
  var sheetClosing = false;
  var sheetCloseTimer = null;
  var SHEET_ANIM_MS = 540;
  /** @type {{ side: "opening"|"closing", scroll?: boolean } | null} */
  var pendingBookendsDeepLink = null;
  /** @type {string | null} */
  var pendingCoverSeg = null;
  var previewFocusObs = null;
  var previewFocusScrollTimer = null;

  function pausePageFlowScroll() {
    if (lenisPausedBySheet) return;
    if (window.TravelogueLenis && typeof window.TravelogueLenis.pause === "function") {
      window.TravelogueLenis.pause();
      lenisPausedBySheet = true;
    }
  }

  function resumePageFlowScroll() {
    if (!lenisPausedBySheet) return;
    if (window.TravelogueLenis && typeof window.TravelogueLenis.resume === "function") {
      window.TravelogueLenis.resume();
    }
    lenisPausedBySheet = false;
  }

  function setExportControlsInert(inert) {
    // PMX D5 · Sheet 打开时禁用导出区命中，避免挡住关闭 ×；保留返回/完成
    var exportWrap = document.querySelector(".preview-toolbar__export-zone-wrap");
    if (!exportWrap) return;
    if (inert) exportWrap.setAttribute("inert", "");
    else exportWrap.removeAttribute("inert");
  }

  function beginSheetEnter() {
    sheetClosing = false;
    if (sheetCloseTimer) {
      clearTimeout(sheetCloseTimer);
      sheetCloseTimer = null;
    }
    shell.hidden = false;
    sheet.hidden = false;
    shell.classList.remove("preview-sheet-root--closing");
    shell.classList.add("preview-sheet-root--visible");
    setExportControlsInert(true);
    requestAnimationFrame(function () {
      requestAnimationFrame(function () {
        shell.classList.add("preview-sheet-root--open");
        document.body.classList.add("preview-sheet-open");
      });
    });
  }

  function finishSheetExit(after) {
    sheetClosing = false;
    shell.classList.remove(
      "preview-sheet-root--closing",
      "preview-sheet-root--visible",
      "preview-sheet-root--open"
    );
    shell.hidden = true;
    sheet.hidden = true;
    bodyEl.innerHTML = "";
    setExportControlsInert(false);
    if (after) after();
  }

  function beginSheetExit(after) {
    if (shell.hidden || sheetClosing) {
      if (after) after();
      return;
    }
    sheetClosing = true;
    shell.classList.remove("preview-sheet-root--open");
    shell.classList.add("preview-sheet-root--closing");
    document.body.classList.remove("preview-sheet-open");
    setExportControlsInert(false);
    resumePageFlowScroll();

    function onTransitionEnd(e) {
      if (e.target !== sheet || e.propertyName !== "transform") return;
      sheet.removeEventListener("transitionend", onTransitionEnd);
      if (sheetCloseTimer) {
        clearTimeout(sheetCloseTimer);
        sheetCloseTimer = null;
      }
      finishSheetExit(after);
    }

    sheet.addEventListener("transitionend", onTransitionEnd);
    sheetCloseTimer = setTimeout(function () {
      sheet.removeEventListener("transitionend", onTransitionEnd);
      sheetCloseTimer = null;
      finishSheetExit(after);
    }, SHEET_ANIM_MS + 80);
  }

  function releaseFocusTrap() {
    if (focusRelease) {
      focusRelease();
      focusRelease = null;
    }
  }

  function activateFocusTrap() {
    releaseFocusTrap();
    if (typeof hooks.trapFocus === "function") {
      focusRelease = hooks.trapFocus(sheet);
    }
  }

  TAB_MODES.forEach(function (tab) {
    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "preview-sheet__tab";
    btn.setAttribute("role", "tab");
    btn.setAttribute("data-sheet-tab", tab.id);
    btn.textContent = tab.label;
    btn.addEventListener("click", function () {
      requestTabSwitch(tab.id);
    });
    tabsEl.appendChild(btn);
  });

  function syncTabUi() {
    tabsEl.querySelectorAll(".preview-sheet__tab").forEach(function (btn) {
      var id = btn.getAttribute("data-sheet-tab");
      var on = id === activeTab;
      btn.classList.toggle("is-active", on);
      btn.setAttribute("aria-selected", on ? "true" : "false");
      btn.classList.toggle(
        "preview-sheet__tab--dot",
        id === "book" && structureDot && !on
      );
    });
  }

  function confirmLeave(next) {
    if (typeof hooks.confirmLeaveCurrentTab !== "function") {
      next();
      return;
    }
    hooks.confirmLeaveCurrentTab(activeTab, next);
  }

  function requestTabSwitch(tabId, opts) {
    opts = opts || {};
    if (opts.bookendsFocus) {
      pendingBookendsDeepLink = {
        side: opts.bookendsFocus === "closing" ? "closing" : "opening",
        scroll: opts.scrollToBookends !== false,
      };
      if (!opts.coverSeg) opts.coverSeg = "photo";
    }
    if (opts.coverSeg) {
      pendingCoverSeg = resolveCoverSeg(opts.coverSeg);
    }
    if (tabId === activeTab) {
      if (activeTab === "cover") {
        if (pendingCoverSeg) {
          activeCoverSeg = pendingCoverSeg;
          pendingCoverSeg = null;
          renderCoverPanel();
          return;
        }
        if (pendingBookendsDeepLink) {
          applyBookendsFocusUi();
        }
      }
      return;
    }
    confirmLeave(function (ok) {
      if (!ok) {
        pendingBookendsDeepLink = null;
        pendingCoverSeg = null;
        return;
      }
      switchTab(tabId);
    });
  }

  function stopPreviewFocusWatch() {
    if (previewFocusObs) {
      previewFocusObs.disconnect();
      previewFocusObs = null;
    }
    if (previewFocusScrollTimer) {
      window.clearTimeout(previewFocusScrollTimer);
      previewFocusScrollTimer = null;
    }
    window.removeEventListener("scroll", onPreviewScrollForBookends, true);
  }

  function onPreviewScrollForBookends() {
    if (shell.hidden || activeTab !== "cover") return;
    if (previewFocusScrollTimer) window.clearTimeout(previewFocusScrollTimer);
    previewFocusScrollTimer = window.setTimeout(function () {
      previewFocusScrollTimer = null;
      applyBookendsFocusUi();
    }, 120);
  }

  function startPreviewFocusWatch() {
    stopPreviewFocusWatch();
    applyBookendsFocusUi();
    var targets = document.querySelectorAll(
      ".cover-opening[data-block='cover-opening'], .cover-closing[data-block='cover-closing'], .cover-opening, .cover-closing"
    );
    if (targets.length && typeof IntersectionObserver !== "undefined") {
      previewFocusObs = new IntersectionObserver(
        function () {
          if (shell.hidden || activeTab !== "cover") return;
          applyBookendsFocusUi();
        },
        { threshold: [0, 0.2, 0.45, 0.7] }
      );
      targets.forEach(function (el) {
        previewFocusObs.observe(el);
      });
    }
    window.addEventListener("scroll", onPreviewScrollForBookends, true);
  }

  function scrollPreviewToBookend(side) {
    var sel =
      side === "closing"
        ? ".cover-closing[data-block='cover-closing'], .cover-closing"
        : ".cover-opening[data-block='cover-opening'], .cover-opening";
    var el = document.querySelector(sel);
    if (!el) return;
    resumePageFlowScroll();
    if (
      window.TravelogueLenis &&
      typeof window.TravelogueLenis.scrollTo === "function"
    ) {
      try {
        window.TravelogueLenis.scrollTo(el, { offset: 0 });
      } catch (_err) {
        el.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    } else {
      el.scrollIntoView({ behavior: "smooth", block: "start" });
    }
    pausePageFlowScroll();
    window.setTimeout(function () {
      if (!shell.hidden && activeTab === "cover") applyBookendsFocusUi(side);
    }, 380);
  }

  function resolveBookendsFocusSide(forcedSide) {
    if (forcedSide === "opening" || forcedSide === "closing") return forcedSide;
    if (pendingBookendsDeepLink && pendingBookendsDeepLink.side) {
      return pendingBookendsDeepLink.side;
    }
    var ctx = describeScreenContext(findDominantScreen());
    if (ctx.detail === "cover") return "opening";
    if (ctx.detail === "closing") return "closing";
    return null;
  }

  function applyBookendsFocusUi(forcedSide) {
    var side = resolveBookendsFocusSide(forcedSide) || "opening";
    var openingPane = bodyEl.querySelector("[data-bookends-opening]");
    var closingPane = bodyEl.querySelector("[data-bookends-closing]");
    var titleEl = bodyEl.querySelector("[data-cover-panel-title]");
    var bookendsRoot = bodyEl.querySelector(".preview-sheet__bookends");

    bodyEl.setAttribute("data-cover-side", side);
    bodyEl.querySelectorAll("button[data-cover-side]").forEach(function (btn) {
      var on = btn.getAttribute("data-cover-side") === side;
      btn.classList.toggle("is-on", on);
      btn.classList.toggle("is-selected", on);
      btn.setAttribute("aria-selected", on ? "true" : "false");
    });
    if (titleEl) {
      titleEl.textContent = side === "closing" ? "换一张封底图" : "换一张封面图";
    }
    if (openingPane && closingPane) {
      openingPane.hidden = side !== "opening";
      closingPane.hidden = side !== "closing";
      openingPane.classList.toggle("is-focus", side === "opening");
      closingPane.classList.toggle("is-focus", side === "closing");
      openingPane.classList.remove("is-dim");
      closingPane.classList.remove("is-dim");
    }
    if (bookendsRoot) {
      bookendsRoot.setAttribute("data-cover-side", side);
    }

    if (pendingBookendsDeepLink) {
      var dl = pendingBookendsDeepLink;
      pendingBookendsDeepLink = null;
      if (dl.scroll) {
        scrollPreviewToBookend(side);
      }
    }
  }

  function bookAdvancedToolsHtml() {
    return (
      '<div class="preview-sheet__section">' +
      '<p class="preview-sheet__label">预览显示</p>' +
      '<div class="preview-sheet__seg" data-field="reader-mode" role="group">' +
      '<button type="button" data-reader-mode="edit">编辑预览</button>' +
      '<button type="button" data-reader-mode="reader">阅读视图</button>' +
      "</div></div>" +
      '<ul class="preview-sheet__list">' +
      '<li data-tool="present"><span>放映精选</span><button type="button" class="preview-sheet__link" data-action="present">开始</button><small class="preview-sheet__present-empty" hidden>先在正文点 ★</small></li>' +
      '<li><span>导出 zip（自行托管）</span><button type="button" class="preview-sheet__link" data-action="export-zip">导出</button></li>' +
      '<li><span>在文件夹中显示</span><button type="button" class="preview-sheet__link" data-action="reveal-folder">打开</button></li>' +
      "</ul>" +
      '<p class="preview-sheet__hint preview-sheet__hint--compact">长图要不要字、导出模式 → 顶栏灰色按钮旁 ▾</p>'
    );
  }

  function bookCopyRefreshHtml() {
    // NAS · FE-NAS-08：默认不渲染 llm 行（dark 再开）
    // SAS W2 · F-SAS-08：权威入口收敛到 AI Sheet，精修仅深链
    if (!isAiSurfaceEnabled()) return "";
    return (
      '<ul class="preview-sheet__list preview-sheet__list--copy-refresh">' +
      '<li data-tool="llm"><span>杂志文案</span>' +
      '<button type="button" class="preview-sheet__link" data-action="open-ai-narrate">在 AI 中打开</button></li>' +
      "</ul>" +
      '<p class="preview-sheet__hint">智能生成请用顶栏「AI」；版式与书衣仍在本精修面板。</p>'
    );
  }

  function wireBookAdvancedTools() {
    if (typeof hooks.syncReaderModeUi === "function") {
      hooks.syncReaderModeUi(bodyEl);
    }
    bodyEl.querySelectorAll("[data-reader-mode]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        if (typeof hooks.setReaderMode === "function") {
          hooks.setReaderMode(btn.getAttribute("data-reader-mode") === "reader");
        }
        if (typeof hooks.syncReaderModeUi === "function") {
          hooks.syncReaderModeUi(bodyEl);
        }
      });
    });
    var revealBtn = bodyEl.querySelector('[data-action="reveal-folder"]');
    if (revealBtn) {
      revealBtn.addEventListener("click", function () {
        if (typeof hooks.onRevealFolder === "function") hooks.onRevealFolder();
      });
    }
    var zipBtn = bodyEl.querySelector('[data-action="export-zip"]');
    if (zipBtn) {
      zipBtn.addEventListener("click", function () {
        if (typeof hooks.onExportZip === "function") hooks.onExportZip();
      });
    }
    var presentBtn = bodyEl.querySelector('[data-action="present"]');
    if (presentBtn) {
      presentBtn.addEventListener("click", function () {
        close();
        if (typeof hooks.onPresentFeatured === "function") hooks.onPresentFeatured();
      });
    }
    var openAiNarrate = bodyEl.querySelector('[data-action="open-ai-narrate"]');
    if (openAiNarrate) {
      openAiNarrate.addEventListener("click", function () {
        close();
        if (root && root._aiSheet && typeof root._aiSheet.open === "function") {
          root._aiSheet.open({ source: "deep_link", focus: "narrate" });
        } else if (typeof hooks.onLlmNarrate === "function") {
          hooks.onLlmNarrate(openAiNarrate);
        }
      });
    }
    if (typeof hooks.refreshAdvancedOptions === "function") {
      hooks.refreshAdvancedOptions(bodyEl);
    }
  }

  function scrollPreviewToBodyScreen() {
    var el = document.querySelector(
      '.layout-screen[data-block="layout-screen"][data-asset-ids], section.chapter .layout-screen'
    );
    if (!el) return false;
    resumePageFlowScroll();
    if (
      window.TravelogueLenis &&
      typeof window.TravelogueLenis.scrollTo === "function"
    ) {
      try {
        window.TravelogueLenis.scrollTo(el, { offset: 0 });
      } catch (_err) {
        el.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    } else {
      el.scrollIntoView({ behavior: "smooth", block: "start" });
    }
    pausePageFlowScroll();
    return true;
  }

  function renderPagePanel() {
    var ctx = describeScreenContext(findDominantScreen());
    if (ctx.empty) {
      var isClosing = ctx.detail === "closing";
      var focusSide = isClosing ? "closing" : "opening";
      var emptyTitle = isClosing
        ? "封底在「封面」里换"
        : ctx.detail === "cover"
          ? "封面在「封面」里换"
          : "封面与封底在「封面」里换";
      var primaryLabel = isClosing ? "去换封底" : "去换封面";
      bodyEl.innerHTML =
        '<p class="preview-sheet__context"><span class="preview-sheet__ctx-pill">' +
        (isClosing ? "封底" : ctx.detail === "cover" ? "封面" : "封面/封底") +
        "</span></p>" +
        '<p class="preview-sheet__empty-label"><strong>' +
        emptyTitle +
        "</strong></p>" +
        '<p class="preview-sheet__hint">点精选、改拼图要在有照片的画册页。</p>' +
        '<div class="preview-sheet__empty-actions">' +
        '<button type="button" class="preview-sheet__primary" data-action="goto-bookends">' +
        primaryLabel +
        "</button>" +
        '<button type="button" class="preview-sheet__ghost" data-action="goto-body">去画册正文</button>' +
        '<button type="button" class="preview-sheet__ghost" data-action="collapse-panel">先收起面板</button>' +
        "</div>";
      var collapsePanel = bodyEl.querySelector('[data-action="collapse-panel"]');
      if (collapsePanel) {
        collapsePanel.addEventListener("click", function () {
          close();
        });
      }
      var goBody = bodyEl.querySelector('[data-action="goto-body"]');
      if (goBody) {
        goBody.addEventListener("click", function () {
          if (!scrollPreviewToBodyScreen()) return;
          window.setTimeout(function () {
            renderPagePanel();
          }, 420);
        });
      }
      var goBookends = bodyEl.querySelector('[data-action="goto-bookends"]');
      if (goBookends) {
        goBookends.addEventListener("click", function () {
          requestTabSwitch("cover", {
            bookendsFocus: focusSide,
            scrollToBookends: true,
          });
        });
      }
      return;
    }

    bodyEl.innerHTML =
      '<p class="preview-sheet__label">当前页</p>' +
      '<p class="preview-sheet__context">' +
      ctx.label +
      "</p>" +
      '<p class="preview-sheet__hint preview-sheet__hint--compact">也可直接在照片上点 ★。这里改文字与标记。</p>' +
      '<div class="preview-sheet__section preview-sheet__page-actions"></div>' +
      '<div class="preview-sheet__embed preview-sheet__embed--edit-page"></div>' +
      '<p class="preview-sheet__hint preview-sheet__hint--compact" data-featured-semantic>精选只是记下「这张更重要」，不会马上打乱整本顺序。</p>' +
      '<button type="button" class="preview-sheet__ghost" data-action="featured-rerank" style="margin-top:8px">按精选重排整本</button>' +
      '<button type="button" class="preview-sheet__ghost" data-action="collapse-panel" style="margin-top:4px">收起面板，回到画面</button>';

    var pageEditSlot = bodyEl.querySelector(".preview-sheet__embed--edit-page");
    if (pageEditSlot && hooks.drawers && typeof hooks.drawers.openEmbed === "function") {
      hooks.drawers.openEmbed("edit-page", pageEditSlot);
    }

    var collapseOnBody = bodyEl.querySelector('[data-action="collapse-panel"]');
    if (collapseOnBody) {
      collapseOnBody.addEventListener("click", function () {
        close();
      });
    }

    var rerankBtn = bodyEl.querySelector('[data-action="featured-rerank"]');
    if (rerankBtn) {
      rerankBtn.addEventListener("click", function () {
        if (typeof hooks.onFeaturedRerank === "function") {
          hooks.onFeaturedRerank();
        }
      });
    }

    var actions = bodyEl.querySelector(".preview-sheet__page-actions");
    if (ctx.hasStar && actions) {
      var featBtn = document.createElement("button");
      featBtn.type = "button";
      featBtn.className = "preview-sheet__chip" + (ctx.featured ? " is-on" : "");
      featBtn.textContent = ctx.featured ? "★ 已标精选" : "☆ 标为精选";
      featBtn.addEventListener("click", function () {
        var star = ctx.screen && ctx.screen.querySelector(".preview-toolbar__featured-star");
        if (star) star.click();
        window.setTimeout(function () {
          renderPagePanel();
        }, 200);
      });
      actions.appendChild(featBtn);
    }
    if (ctx.hasMediaCtl && actions) {
      var mediaBtn = document.createElement("button");
      mediaBtn.type = "button";
      mediaBtn.className = "preview-sheet__chip";
      var sel0 =
        ctx.screen && ctx.screen.querySelector(".preview-toolbar__collage-select");
      var isCollage = sel0 && sel0.value === "collage";
      mediaBtn.textContent = isCollage ? "改回单张" : "改成拼图";
      mediaBtn.addEventListener("click", function () {
        var sel =
          ctx.screen &&
          ctx.screen.querySelector(".preview-toolbar__collage-select");
        if (sel) {
          sel.focus();
          sel.value = sel.value === "collage" ? "photo" : "collage";
          sel.dispatchEvent(new Event("change", { bubbles: true }));
          window.setTimeout(function () {
            renderPagePanel();
          }, 200);
          return;
        }
        var ctl =
          ctx.screen && ctx.screen.querySelector(".preview-toolbar__collage-ctrl");
        if (ctl) ctl.click();
      });
      actions.appendChild(mediaBtn);
    }
    // FE-SFI-07 · 精修单张「移回原章」（附录章）
    if (ctx.isAppendix && ctx.primaryAssetId && actions) {
      var restoreBtn = document.createElement("button");
      restoreBtn.type = "button";
      restoreBtn.className = "preview-sheet__chip";
      restoreBtn.textContent = "移回原章";
      restoreBtn.addEventListener("click", function () {
        var tid =
          (hooks && hooks.tripId) ||
          (typeof tripIdFromPath === "function" && tripIdFromPath()) ||
          "";
        if (!tid) {
          showToolbarToast("移回未完成");
          return;
        }
        restoreBtn.disabled = true;
        postJsonConflictRetry(tripApiBase(tid) + "/promote-tier", {
          action: "restoreTimeOutlier",
          assetIds: [ctx.primaryAssetId],
          rerender: false,
        })
          .then(function (res) {
            restoreBtn.disabled = false;
            if (!res || res.status < 200 || res.status >= 300) {
              showToolbarToast(
                (res && res.body && res.body.message) || "移回未完成，请稍后重试"
              );
              return;
            }
            showToolbarToast("已移回，正在重新分章…");
            if (
              hooks.drawers &&
              typeof hooks.drawers.regenerateStructure === "function"
            ) {
              return hooks.drawers.regenerateStructure();
            }
          })
          .catch(function () {
            restoreBtn.disabled = false;
            showToolbarToast("移回未完成");
          });
      });
      actions.appendChild(restoreBtn);
    }
  }

  function mountBookendsInto(slot) {
    if (!slot) return;
    if (typeof hooks.mountBookendsPanel === "function") {
      var api = hooks.mountBookendsPanel(slot);
      if (api) root._bookendsApi = api;
    } else if (typeof hooks.mountCoverStyleControls === "function") {
      var coverSlot = document.createElement("div");
      coverSlot.className = "preview-sheet__cover-slot";
      slot.appendChild(coverSlot);
      hooks.mountCoverStyleControls(coverSlot, { mode: "style", omitTitleArt: true });
    }
    var scrollOpening = slot.querySelector("[data-bookends-scroll-opening]");
    var scrollClosing = slot.querySelector("[data-bookends-scroll-closing]");
    if (scrollOpening) {
      scrollOpening.addEventListener("click", function () {
        scrollPreviewToBookend("opening");
      });
    }
    if (scrollClosing) {
      scrollClosing.addEventListener("click", function () {
        scrollPreviewToBookend("closing");
      });
    }
  }

  function coverSubsegHtml() {
    var isPf = typeof hooks.isPortfolio === "function" && hooks.isPortfolio();
    var segs = COVER_SEGS.map(function (seg) {
      if (seg.id !== "name") return seg;
      return { id: "name", label: isPf ? "书名" : "杂志名", hint: seg.hint };
    });
    return (
      '<div class="preview-sheet__cover-subseg" role="tablist" aria-label="封面子段">' +
      segs.map(function (seg) {
        var on = seg.id === activeCoverSeg;
        return (
          '<button type="button" class="preview-sheet__cover-subseg-btn' +
          (on ? " is-on" : "") +
          '" data-cover-seg="' +
          seg.id +
          '" aria-selected="' +
          (on ? "true" : "false") +
          '">' +
          seg.label +
          '<span class="preview-sheet__cover-subseg-hint">' +
          seg.hint +
          "</span></button>"
        );
      }).join("") +
      "</div>"
    );
  }

  function wireCoverSubseg() {
    bodyEl.querySelectorAll("[data-cover-seg]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var next = resolveCoverSeg(btn.getAttribute("data-cover-seg"));
        if (next === activeCoverSeg) return;
        var from = activeCoverSeg;
        activeCoverSeg = next;
        try {
          trackStudioEvent("cover_seg_switch", {
            from: from,
            to: next,
            source: "subseg",
          });
        } catch (_eTrack) {}
        renderCoverPanel();
      });
    });
  }

  function ensureBookendsApiForStyle() {
    // 版式段需要 viaBookends 回调；若尚未挂过照片段，先挂隐藏 Bookends
    if (root._bookendsApi && typeof root._bookendsApi.applyStyleViaBookends === "function") {
      return;
    }
    var host = bodyEl.querySelector("[data-bookends-hidden-host]");
    if (!host) return;
    mountBookendsInto(host);
  }

  function renderCoverPanel() {
    stopPreviewFocusWatch();
    if (pendingCoverSeg) {
      activeCoverSeg = resolveCoverSeg(pendingCoverSeg);
      pendingCoverSeg = null;
    }
    activeCoverSeg = resolveCoverSeg(activeCoverSeg);

    if (activeCoverSeg === "style") {
      bodyEl.innerHTML =
        coverSubsegHtml() +
        '<div class="preview-sheet__bookends-slot" data-bookends-hidden-host hidden aria-hidden="true"></div>' +
        '<div class="preview-sheet__cover-style-host" data-cover-style-host></div>';
      wireCoverSubseg();
      ensureBookendsApiForStyle();
      var styleHost = bodyEl.querySelector("[data-cover-style-host]");
      if (styleHost && typeof hooks.mountCoverStyleControls === "function") {
        var styleOpts = {
          mode: "style",
          omitTitleArt: true,
          viaBookends: true,
          applyStyleViaBookends: function (styleId, keepCover) {
            if (root._bookendsApi && root._bookendsApi.applyStyleViaBookends) {
              return root._bookendsApi.applyStyleViaBookends(styleId, keepCover);
            }
            return false;
          },
        };
        hooks.mountCoverStyleControls(styleHost, styleOpts);
      }
      return;
    }

    if (activeCoverSeg === "name") {
      bodyEl.innerHTML =
        coverSubsegHtml() +
        '<div class="preview-sheet__cover-name-host" data-cover-name-host></div>';
      wireCoverSubseg();
      var nameHost = bodyEl.querySelector("[data-cover-name-host]");
      if (nameHost && typeof hooks.mountCoverNameFontControls === "function") {
        hooks.mountCoverNameFontControls(nameHost);
      } else if (nameHost && typeof hooks.mountCoverStyleControls === "function") {
        hooks.mountCoverStyleControls(nameHost, { mode: "name" });
      }
      return;
    }

    // photo（默认）
    var side = resolveBookendsFocusSide(null) || "opening";
    if (!pendingBookendsDeepLink) {
      pendingBookendsDeepLink = { side: side, scroll: false };
    }
    bodyEl.innerHTML =
      coverSubsegHtml() +
      '<div class="preview-sheet__seg preview-sheet__cover-side-seg" data-field="cover-side" role="tablist" aria-label="封面或封底">' +
      '<button type="button" data-cover-side="opening">封面</button>' +
      '<button type="button" data-cover-side="closing">封底</button>' +
      "</div>" +
      '<p class="preview-sheet__empty-label"><strong data-cover-panel-title>换一张封面图</strong></p>' +
      '<p class="preview-sheet__hint">点缩略图即可更换。版式与' +
      (typeof hooks.isPortfolio === "function" && hooks.isPortfolio() ? "书名" : "杂志名") +
      "见上方分段。</p>" +
      '<div class="preview-sheet__bookends-slot" data-book-zone="bookends"></div>' +
      '<button type="button" class="preview-sheet__ghost" data-action="goto-cover-style">去换版式</button>';

    wireCoverSubseg();
    bodyEl.querySelectorAll("button[data-cover-side]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var next = btn.getAttribute("data-cover-side") === "closing" ? "closing" : "opening";
        pendingBookendsDeepLink = { side: next, scroll: true };
        applyBookendsFocusUi(next);
      });
    });
    var gotoStyle = bodyEl.querySelector('[data-action="goto-cover-style"]');
    if (gotoStyle) {
      gotoStyle.addEventListener("click", function () {
        requestTabSwitch("cover", { coverSeg: "style" });
      });
    }

    var bookendsSlot = bodyEl.querySelector(".preview-sheet__bookends-slot");
    mountBookendsInto(bookendsSlot);
    applyBookendsFocusUi(side);
    startPreviewFocusWatch();
  }

  function renderBookPanel() {
    stopPreviewFocusWatch();
    var isPortfolio = typeof hooks.isPortfolio === "function" && hooks.isPortfolio();
    var vibeZone = isPortfolio
      ? ""
      : '<details class="preview-sheet__zone preview-sheet__zone--layout-vibe" data-book-zone="layout-vibe" open>' +
        '<summary>成册风格 <span class="preview-sheet__zone-meta">推荐 · 实验</span></summary>' +
        '<div class="preview-sheet__zone-body">' +
        '<p class="preview-sheet__hint preview-sheet__hint--compact">影响整本页面气质，不是封面第一眼样式。要换封面样式 → 「封面 · 版式」。</p>' +
        '<div class="preview-sheet__layout-vibe-slot"></div>' +
        "</div></details>";
    var editionZone = isPortfolio
      ? '<details class="preview-sheet__zone preview-sheet__zone--edition-type" data-book-zone="edition-type" open>' +
        '<summary>改这本作品集 <span class="preview-sheet__zone-meta">作品集</span></summary>' +
        '<div class="preview-sheet__zone-body">' +
        '<div class="preview-sheet__edition-slot"></div>' +
        "</div></details>"
      : '<details class="preview-sheet__zone preview-sheet__zone--edition-type" data-book-zone="edition-type" open>' +
        '<summary>成册类型 <span class="preview-sheet__zone-meta">游记 · 作品集</span></summary>' +
        '<div class="preview-sheet__zone-body">' +
        '<p class="preview-sheet__hint preview-sheet__hint--compact">换类型会重排页面，精选和分组会保留。</p>' +
        '<div class="preview-sheet__edition-slot"></div>' +
        "</div></details>";
    bodyEl.innerHTML =
      '<p class="preview-sheet__hint preview-sheet__hint--lead">' +
      (isPortfolio
        ? "改这本作品集。书名与封面字体在「封面」。"
        : "改一句话与成册风格。杂志名与封面字体在「封面」。") +
      "</p>" +
      '<details class="preview-sheet__zone preview-sheet__zone--story" data-book-zone="story" open>' +
      '<summary>给这本画册的一句话 <span class="preview-sheet__zone-meta">封面副标 · 辑封</span></summary>' +
      '<div class="preview-sheet__zone-body">' +
      '<div class="preview-sheet__embed preview-sheet__embed--edit"></div>' +
      bookCopyRefreshHtml() +
      "</div></details>" +
      editionZone +
      vibeZone +
      '<details class="preview-sheet__zone preview-sheet__zone--brand" data-book-zone="brand" open>' +
      "<summary>作品署名</summary>" +
      '<div class="preview-sheet__zone-body">' +
      '<div class="preview-sheet__brand" data-works-brand>' +
      '<p class="preview-sheet__hint preview-sheet__hint--compact">个人署名 · 同时出现在辑封与长图尾</p>' +
      '<label class="preview-sheet__radio"><input type="radio" name="works-brand" value="default" /> 默认 · Travelogue</label>' +
      '<label class="preview-sheet__radio"><input type="radio" name="works-brand" value="custom" /> 自定义（≤14 字）</label>' +
      '<input type="text" class="preview-sheet__brand-input" maxlength="14" placeholder="你的署名" hidden />' +
      '<label class="preview-sheet__radio"><input type="radio" name="works-brand" value="hidden" /> 不显示</label>' +
      "</div>" +
      "</div></details>" +
      '<details class="preview-sheet__zone preview-sheet__zone--advanced" data-book-zone="advanced">' +
      '<summary>进阶 <span class="preview-sheet__zone-meta">很少需要</span></summary>' +
      '<div class="preview-sheet__zone-body">' +
      '<p class="preview-sheet__hint preview-sheet__hint--compact">阅读视图、放映、换模板、旅行主角同框、分章说明。</p>' +
      bookAdvancedToolsHtml() +
      '<div class="preview-sheet__template-slot"></div>' +
      '<div class="preview-sheet__embed preview-sheet__embed--cohort"></div>' +
      '<button type="button" class="preview-sheet__primary preview-sheet__apply-layout" hidden>更新版面</button>' +
      '<p class="preview-sheet__hint">结构确认见顶栏横幅（若开启）；「为什么这样分章」见下方。</p>' +
      '<div class="preview-sheet__embed preview-sheet__embed--structure"></div>' +
      "</div></details>" +
      '<div class="preview-sheet__book-foot">' +
      '<button type="button" class="preview-sheet__ghost" data-action="goto-cover-name">' +
      (isPortfolio ? "去改书名 / 字体" : "去改杂志名 / 字体") +
      "</button>" +
      '<p class="preview-sheet__hint preview-sheet__hint--compact" style="text-align:center;margin-top:6px">换封面/封底 → 「封面 · 照片」</p>' +
      "</div>";

    if (typeof hooks.onBookTabRendered === "function") {
      hooks.onBookTabRendered();
    }

    var editionSlot = bodyEl.querySelector(".preview-sheet__edition-slot");
    if (editionSlot && typeof hooks.mountEditionControls === "function") {
      hooks.mountEditionControls(editionSlot);
    }

    var vibeSlot = bodyEl.querySelector(".preview-sheet__layout-vibe-slot");
    if (vibeSlot && typeof hooks.mountLayoutVibeControls === "function") {
      hooks.mountLayoutVibeControls(vibeSlot);
    }

    var editSlot = bodyEl.querySelector(".preview-sheet__embed--edit");
    if (editSlot && hooks.drawers && typeof hooks.drawers.openEmbed === "function") {
      hooks.drawers.openEmbed("edit", editSlot, {
        sheetMode: true,
        omitMagazineTitle: true,
      });
    }

    var gotoName = bodyEl.querySelector('[data-action="goto-cover-name"]');
    if (gotoName) {
      gotoName.addEventListener("click", function () {
        requestTabSwitch("cover", { coverSeg: "name" });
      });
    }

    wireWorksBrandControls();
    wireBookAdvancedTools();
    // SAS W2 · 整本信息区杂志文案 → AI Sheet 深链
    var storyAi = bodyEl.querySelector(
      '.preview-sheet__zone--story [data-action="open-ai-narrate"]'
    );
    if (storyAi && !storyAi._sfiWired) {
      storyAi._sfiWired = true;
      storyAi.addEventListener("click", function () {
        close();
        if (root && root._aiSheet && typeof root._aiSheet.open === "function") {
          root._aiSheet.open({ source: "deep_link", focus: "narrate" });
        } else if (typeof hooks.onLlmNarrate === "function") {
          hooks.onLlmNarrate(storyAi);
        }
      });
    }

    var templateSlot = bodyEl.querySelector(".preview-sheet__template-slot");
    if (templateSlot && typeof hooks.mountTemplateControls === "function") {
      hooks.mountTemplateControls(templateSlot);
    }
    var applyBtn = bodyEl.querySelector(".preview-sheet__apply-layout");
    if (applyBtn) {
      applyBtn.hidden = !(
        typeof hooks.isLayoutPending === "function"
          ? hooks.isLayoutPending()
          : hooks.isLayoutPending
      );
      applyBtn.addEventListener("click", function () {
        close();
        if (typeof hooks.onApplyLayout === "function") hooks.onApplyLayout();
      });
    }
    var cohortEmbed = bodyEl.querySelector(".preview-sheet__embed--cohort");
    if (cohortEmbed && hooks.drawers && typeof hooks.drawers.openEmbed === "function") {
      if (hooks.cohortEnabled) {
        var cohortHost = document.createElement("div");
        cohortEmbed.appendChild(cohortHost);
        hooks.drawers.openEmbed("cohort", cohortHost, { sheetMode: true });
      } else {
        cohortEmbed.hidden = true;
        cohortEmbed.innerHTML = "";
      }
    }
    var structEmbed = bodyEl.querySelector(".preview-sheet__embed--structure");
    if (structEmbed) {
      structEmbed.innerHTML =
        '<details class="preview-sheet__details">' +
        "<summary>为什么这样分章 / 结构说明</summary>" +
        '<div class="preview-sheet__struct-host"></div>' +
        "</details>";
      var details = structEmbed.querySelector("details");
      var structHost = structEmbed.querySelector(".preview-sheet__struct-host");
      if (details && structHost && hooks.drawers) {
        details.addEventListener("toggle", function () {
          if (!details.open || structHost.dataset.loaded === "1") return;
          structHost.dataset.loaded = "1";
          hooks.drawers.openEmbed("structure", structHost, { sheetMode: true });
        });
      }
    }
  }

  function wireWorksBrandControls() {
    var host = bodyEl.querySelector("[data-works-brand]");
    if (!host) return;
    var tid =
      (hooks && hooks.tripId) ||
      (typeof tripIdFromPath === "function" && tripIdFromPath()) ||
      "";
    if (!tid) return;
    var input = host.querySelector(".preview-sheet__brand-input");
    var radios = host.querySelectorAll('input[name="works-brand"]');

    function syncCustomVisibility(mode) {
      if (!input) return;
      input.hidden = mode !== "custom";
      if (mode === "custom") {
        try {
          input.focus();
        } catch (_e) {}
      }
    }

    function saveBrand(mode, text) {
      var patches = [{ path: "meta.worksBrandMode", value: mode }];
      if (mode === "custom") {
        patches.push({
          path: "meta.worksBrandText",
          value: String(text || "").trim().slice(0, 14),
        });
      }
      postJsonConflictRetry(tripApiBase(tid) + "/save-copy", { patches: patches })
        .then(function (res) {
          if (!res || res.status < 200 || res.status >= 300) {
            showToolbarToast("署名未保存");
            return;
          }
          showToolbarToast("署名已更新");
        })
        .catch(function () {
          showToolbarToast("署名未保存");
        });
    }

    fetch("/__travelogue/trips/" + encodeURIComponent(tid) + "/entry")
      .then(function (r) {
        return r.ok ? r.json() : null;
      })
      .then(function (entry) {
        var brand = (entry && entry.worksBrand) || {};
        var mode = brand.mode || "default";
        radios.forEach(function (radio) {
          radio.checked = radio.value === mode;
        });
        if (input) input.value = brand.text || "";
        syncCustomVisibility(mode);
      })
      .catch(function () {});

    radios.forEach(function (radio) {
      radio.addEventListener("change", function () {
        if (!radio.checked) return;
        syncCustomVisibility(radio.value);
        if (radio.value === "custom" && input && !String(input.value || "").trim()) {
          return;
        }
        saveBrand(radio.value, input ? input.value : "");
      });
    });
    if (input) {
      input.addEventListener("change", function () {
        var modeEl = host.querySelector('input[name="works-brand"]:checked');
        var mode = (modeEl && modeEl.value) || "custom";
        if (mode !== "custom") return;
        saveBrand("custom", input.value);
      });
    }
  }

  function consumePreferCoverSeg() {
    try {
      var tid = tripIdFromPath();
      if (!tid) return null;
      var key = "travelogue.rci.preferCoverSeg." + tid;
      var raw = sessionStorage.getItem(key);
      if (!raw) return null;
      sessionStorage.removeItem(key);
      return resolveCoverSeg(raw);
    } catch (_ePref) {
      return null;
    }
  }

  function resolveDefaultOpenTab() {
    var ctx = describeScreenContext(findDominantScreen());
    if (ctx.detail === "cover" || ctx.detail === "closing") {
      pendingBookendsDeepLink = {
        side: ctx.detail === "closing" ? "closing" : "opening",
        scroll: false,
      };
      var prefer = consumePreferCoverSeg();
      if (prefer) {
        pendingCoverSeg = prefer;
        return "cover";
      }
      // 书名/字体贴纸在视口中央时默认进「杂志名」
      var titleArt = document.querySelector(
        ".cover-opening__title-art, .cover-opening__title:not(.sr-only)"
      );
      if (ctx.detail === "cover" && titleArt) {
        var tr = titleArt.getBoundingClientRect();
        var mid = window.innerHeight * 0.45;
        if (tr.top < mid && tr.bottom > window.innerHeight * 0.15) {
          pendingCoverSeg = "name";
        } else {
          pendingCoverSeg = "photo";
        }
      } else {
        pendingCoverSeg = "photo";
      }
      return "cover";
    }
    return "page";
  }

  function switchTab(tabId) {
    activeTab = resolveSheetTab(tabId);
    syncTabUi();
    stopPreviewFocusWatch();
    bodyEl.innerHTML = "";
    bodyEl.removeAttribute("data-cover-side");
    bodyEl.scrollTop = 0;
    if (typeof hooks.onSheetTabShown === "function") {
      hooks.onSheetTabShown(activeTab);
    }

    if (activeTab === "cover") {
      renderCoverPanel();
    } else if (activeTab === "page") {
      renderPagePanel();
    } else {
      renderBookPanel();
    }
    if (typeof hooks.maybeInjectRefineSaveHint === "function") {
      hooks.maybeInjectRefineSaveHint(bodyEl);
    }
  }

  function open(tabId, openOpts) {
    // RCI · 兼容 open({ tab, coverSeg, bookendsFocus })
    if (tabId && typeof tabId === "object") {
      openOpts = tabId;
      tabId = openOpts.tab || openOpts.tabId || null;
    }
    openOpts = openOpts || {};
    // AC-HELP-15 · 帮助开着时禁止再开精修 Sheet
    if (typeof hooks.isHelpOpen === "function" && hooks.isHelpOpen()) {
      return;
    }
    previousFocus = document.activeElement;
    beginSheetEnter();
    pausePageFlowScroll();
    if (menuBtn) {
      menuBtn.classList.remove("preview-toolbar__menu-btn--pulse");
      menuBtn.setAttribute("aria-expanded", "true");
    }
    if (typeof hooks.onSheetOpened === "function") {
      hooks.onSheetOpened({ source: openOpts.source || "dock" });
    }
    var nextTab =
      tabId != null && tabId !== ""
        ? resolveSheetTab(tabId)
        : resolveDefaultOpenTab();
    if (openOpts.bookendsFocus) {
      pendingBookendsDeepLink = {
        side: openOpts.bookendsFocus === "closing" ? "closing" : "opening",
        scroll: openOpts.scrollToBookends !== false,
      };
      nextTab = "cover";
      if (!openOpts.coverSeg) openOpts.coverSeg = "photo";
    }
    if (openOpts.coverSeg) {
      pendingCoverSeg = resolveCoverSeg(openOpts.coverSeg);
      nextTab = "cover";
    }
    switchTab(nextTab);
    activateFocusTrap();
    closeBtn.focus();
  }

  /** @param {string} [via] esc | close | dock_toggle | help
   *  @param {() => void} [afterClose]
   */
  function close(via, afterClose) {
    var closeVia = via || "close";
    confirmLeave(function (ok) {
      if (!ok) return;
      if (sheetClosing) return;
      stopPreviewFocusWatch();
      pendingBookendsDeepLink = null;
      releaseFocusTrap();
      if (hooks.drawers && typeof hooks.drawers.close === "function") {
        hooks.drawers.close();
      }
      if (menuBtn) {
        menuBtn.setAttribute("aria-expanded", "false");
      }
      beginSheetExit(function () {
        if (typeof hooks.onSheetClosed === "function") {
          hooks.onSheetClosed({ via: closeVia });
        }
        if (previousFocus && typeof previousFocus.focus === "function") {
          previousFocus.focus();
        } else if (menuBtn && typeof menuBtn.focus === "function") {
          menuBtn.focus();
        }
        previousFocus = null;
        if (typeof afterClose === "function") afterClose();
      });
    });
  }

  function isOpen() {
    return !shell.hidden && !sheetClosing;
  }

  function setPendingDot(on) {
    pendingDot = !!on;
    if (menuBtn) {
      menuBtn.classList.toggle("preview-toolbar__menu-btn--dot", pendingDot);
    }
  }

  function setStructureDot(on) {
    structureDot = !!on;
    syncTabUi();
  }

  closeBtn.addEventListener("click", function () {
    close("close");
  });
  scrim.addEventListener("click", function () {
    close("close");
  });
  document.addEventListener("keydown", function (e) {
    if (e.key !== "Escape" || shell.hidden || sheetClosing) return;
    // 帮助开着时由帮助抽屉优先处理 Esc（AC-HELP-15）
    if (typeof hooks.isHelpOpen === "function" && hooks.isHelpOpen()) return;
    close("esc");
  });

  if (menuBtn) {
    menuBtn.addEventListener("click", function (e) {
      e.stopPropagation();
      if (sheetClosing) return;
      if (typeof hooks.isHelpOpen === "function" && hooks.isHelpOpen()) {
        return;
      }
      // 面板开 → 关面板保模式
      if (!shell.hidden) {
        close("dock_toggle");
        return;
      }
      // 面板关 + 精修中 → 「完成」退出模式（MF-01c）
      if (
        typeof hooks.isRefineModeOn === "function" &&
        hooks.isRefineModeOn()
      ) {
        if (typeof hooks.onExitRefineMode === "function") {
          hooks.onExitRefineMode({ source: "done" });
        }
        return;
      }
      // D-PCU · 分章与精修互斥
      if (root._chapterPanel && root._chapterPanel.isOpen()) {
        root._chapterPanel.close();
      }
      // SAS · D-SAS-04 · 与 AI Sheet 互斥
      if (root._aiSheet && root._aiSheet.isOpen && root._aiSheet.isOpen()) {
        root._aiSheet.close("refine");
      }
      open(null, { source: "dock" });
    });
  }

  return {
    open: open,
    close: close,
    isOpen: isOpen,
    switchTab: switchTab,
    setPendingDot: setPendingDot,
    setStructureDot: setStructureDot,
    refreshLayoutTab: function () {
      if (!shell.hidden && activeTab === "book") {
        renderBookPanel();
        if (typeof hooks.maybeInjectRefineSaveHint === "function") {
          hooks.maybeInjectRefineSaveHint(bodyEl);
        }
      }
    },
    refreshAdvancedTab: function () {
      if (!shell.hidden && activeTab === "book") {
        renderBookPanel();
        if (typeof hooks.maybeInjectRefineSaveHint === "function") {
          hooks.maybeInjectRefineSaveHint(bodyEl);
        }
      }
    },
  };
}
