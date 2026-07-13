/**
 * Preview toolbar v3 · unified refine sheet（这页 | 这本 | 导出与更多）.
 * Mobile: bottom sheet · Desktop (≥1024px): right side panel.
 */
"use strict";

var TAB_MODES = [
  { id: "page", label: "这页" },
  { id: "book", label: "这本" },
  { id: "more", label: "导出与更多" },
];

var TAB_ALIASES = {
  edit: "book",
  structure: "book",
  layout: "book",
  advanced: "more",
};

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
    return { empty: true, label: "当前屏", detail: "" };
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
    (idx ? "第 " + idx + " 屏" : "正文屏") + (chapterName ? " · " + chapterName : "");
  var kicker = el.querySelector(".kicker, .hook-line, [data-copy-role='kicker']");
  var body = el.querySelector(".caption, .lead, .body-copy, [data-copy-role='caption'], [data-copy-role='lead']");
  return {
    empty: false,
    label: label,
    detail: "body",
    screen: el,
    featured: el.getAttribute("data-featured") === "true",
    hasStar: !!el.querySelector(".preview-toolbar__featured-star"),
    hasMediaCtl: !!el.querySelector(".preview-toolbar__collage-media, .preview-collage-media"),
    copyHint: !!(kicker || body),
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
    }
    if (tabId === activeTab) {
      if (activeTab === "book" && pendingBookendsDeepLink) {
        applyBookendsFocusUi();
      }
      return;
    }
    confirmLeave(function (ok) {
      if (!ok) {
        pendingBookendsDeepLink = null;
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
    if (shell.hidden || activeTab !== "book") return;
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
          if (shell.hidden || activeTab !== "book") return;
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
      if (!shell.hidden && activeTab === "book") applyBookendsFocusUi(side);
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
    var side = resolveBookendsFocusSide(forcedSide);
    var storyZone = bodyEl.querySelector('[data-book-zone="story"]');
    var bookendsZone = bodyEl.querySelector('[data-book-zone="bookends"]');
    var badge = bodyEl.querySelector("[data-bookends-focus-badge]");
    var openingPane = bodyEl.querySelector("[data-bookends-opening]");
    var closingPane = bodyEl.querySelector("[data-bookends-closing]");

    if (side && bookendsZone) {
      bookendsZone.open = true;
      if (storyZone && !storyZone.open) {
        /* keep story as user left it */
      }
    }
    if (badge) {
      if (side === "opening") {
        badge.hidden = false;
        badge.textContent = "正在看封面";
      } else if (side === "closing") {
        badge.hidden = false;
        badge.textContent = "正在看封底";
      } else {
        badge.hidden = true;
        badge.textContent = "";
      }
    }
    if (openingPane && closingPane) {
      openingPane.classList.toggle("is-focus", side === "opening");
      openingPane.classList.toggle("is-dim", side === "closing");
      closingPane.classList.toggle("is-focus", side === "closing");
      closingPane.classList.toggle("is-dim", side === "opening");
      if (!side) {
        openingPane.classList.remove("is-focus", "is-dim");
        closingPane.classList.remove("is-focus", "is-dim");
      }
    }

    if (pendingBookendsDeepLink) {
      var dl = pendingBookendsDeepLink;
      pendingBookendsDeepLink = null;
      if (dl.scroll && bookendsZone) {
        window.requestAnimationFrame(function () {
          bookendsZone.scrollIntoView({ behavior: "smooth", block: "nearest" });
        });
      }
    }
  }

  function renderAdvancedPanel() {
    bodyEl.innerHTML =
      '<div class="preview-sheet__section">' +
      '<p class="preview-sheet__label">快捷</p>' +
      '<button type="button" class="preview-sheet__link preview-sheet__link--block" data-action="focus-export">打开导出设置</button>' +
      '<p class="preview-sheet__hint">也可点 Dock 导出旁的 ▾</p>' +
      "</div>" +
      '<div class="preview-sheet__section">' +
      '<p class="preview-sheet__label">长图文案范围</p>' +
      '<div class="preview-sheet__seg" data-field="copy-preset" role="group">' +
      '<button type="button" data-copy-preset="photos">纯照片</button>' +
      '<button type="button" data-copy-preset="full">完整文案</button>' +
      "</div>" +
      '<div class="preview-sheet__chip-row">' +
      '<button type="button" class="preview-sheet__chip" data-preview-chip="caption">图注</button>' +
      '<button type="button" class="preview-sheet__chip" data-preview-chip="narrative">导语</button>' +
      "</div></div>" +
      '<div class="preview-sheet__section">' +
      '<p class="preview-sheet__label">导出范围</p>' +
      '<div class="preview-sheet__seg" data-field="longshot-mode" role="group">' +
      '<button type="button" data-studio-longshot-mode="chapter">按章导出</button>' +
      '<button type="button" data-studio-longshot-mode="full">完整长图</button>' +
      "</div></div>" +
      '<div class="preview-sheet__section">' +
      '<p class="preview-sheet__label">清晰度</p>' +
      '<div class="preview-sheet__seg" data-field="longshot-scale" role="group">' +
      '<button type="button" data-studio-longshot-scale="2">标准 2×</button>' +
      '<button type="button" data-studio-longshot-scale="3">高清 3×</button>' +
      "</div></div>" +
      '<div class="preview-sheet__section">' +
      '<p class="preview-sheet__label">预览显示</p>' +
      '<div class="preview-sheet__seg" data-field="reader-mode" role="group">' +
      '<button type="button" data-reader-mode="edit">编辑预览</button>' +
      '<button type="button" data-reader-mode="reader">阅读视图</button>' +
      "</div></div>" +
      '<ul class="preview-sheet__list">' +
      '<li><span>在文件夹中显示</span><button type="button" class="preview-sheet__link" data-action="reveal-folder">打开</button></li>' +
      '<li><span>导出 zip（自行托管）</span><button type="button" class="preview-sheet__link" data-action="export-zip">导出</button></li>' +
      '<li class="preview-sheet__list-item--optional" hidden><span>放映精选</span><button type="button" class="preview-sheet__link" data-action="present">开始</button></li>' +
      '<li class="preview-sheet__list-item--optional" hidden><span>生成杂志感文案</span><button type="button" class="preview-sheet__link" data-action="llm">生成</button></li>' +
      "</ul>" +
      '<p class="preview-sheet__footnote">点画面上的字可直接改；改精选或拼图后请点「更新版面」。</p>';

    wireAdvancedPanelActions();
  }

  function wireAdvancedPanelActions() {
    if (typeof hooks.syncCopyDisplayUi === "function") {
      hooks.syncCopyDisplayUi(bodyEl);
    }
    bodyEl.querySelectorAll("[data-copy-preset]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        if (typeof hooks.applyCopyPreset === "function") {
          hooks.applyCopyPreset(btn.getAttribute("data-copy-preset"));
        }
        if (typeof hooks.syncCopyDisplayUi === "function") {
          hooks.syncCopyDisplayUi(bodyEl);
        }
      });
    });
    var captionChip = bodyEl.querySelector('[data-preview-chip="caption"]');
    if (captionChip) {
      captionChip.addEventListener("click", function () {
        if (typeof hooks.toggleCaptions === "function") hooks.toggleCaptions();
        if (typeof hooks.syncCopyDisplayUi === "function") hooks.syncCopyDisplayUi(bodyEl);
      });
    }
    var narrativeChip = bodyEl.querySelector('[data-preview-chip="narrative"]');
    if (narrativeChip) {
      narrativeChip.addEventListener("click", function () {
        if (typeof hooks.toggleNarrative === "function") hooks.toggleNarrative();
        if (typeof hooks.syncCopyDisplayUi === "function") hooks.syncCopyDisplayUi(bodyEl);
      });
    }

    if (typeof hooks.syncLongshotPrefsUi === "function") {
      hooks.syncLongshotPrefsUi(bodyEl);
    }
    if (typeof hooks.syncReaderModeUi === "function") {
      hooks.syncReaderModeUi(bodyEl);
    }

    bodyEl.querySelectorAll("[data-studio-longshot-mode]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        if (typeof hooks.setLongshotMode === "function") {
          hooks.setLongshotMode(btn.getAttribute("data-studio-longshot-mode"));
        }
        if (typeof hooks.syncLongshotPrefsUi === "function") {
          hooks.syncLongshotPrefsUi(bodyEl);
        }
      });
    });
    bodyEl.querySelectorAll("[data-studio-longshot-scale]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        if (typeof hooks.setLongshotScale === "function") {
          hooks.setLongshotScale(parseInt(btn.getAttribute("data-studio-longshot-scale"), 10));
        }
        if (typeof hooks.syncLongshotPrefsUi === "function") {
          hooks.syncLongshotPrefsUi(bodyEl);
        }
      });
    });
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

    var focusExport = bodyEl.querySelector('[data-action="focus-export"]');
    if (focusExport) {
      focusExport.addEventListener("click", function () {
        close();
        if (typeof hooks.onFocusExportSettings === "function") {
          hooks.onFocusExportSettings();
        } else {
          var caret = root.querySelector(".preview-toolbar__longshot-caret");
          if (caret) caret.click();
        }
      });
    }
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
    var llmBtn = bodyEl.querySelector('[data-action="llm"]');
    if (llmBtn) {
      llmBtn.addEventListener("click", function () {
        close();
        if (typeof hooks.onLlmNarrate === "function") hooks.onLlmNarrate(llmBtn);
      });
    }

    if (typeof hooks.refreshAdvancedOptions === "function") {
      hooks.refreshAdvancedOptions(bodyEl);
    }
  }

  function renderPagePanel() {
    var ctx = describeScreenContext(findDominantScreen());
    if (ctx.empty) {
      var isClosing = ctx.detail === "closing";
      var focusSide = isClosing ? "closing" : "opening";
      var watching =
        ctx.detail === "cover"
          ? "你正在看封面"
          : isClosing
            ? "你正在看封底"
            : "当前是封面或封底";
      bodyEl.innerHTML =
        '<p class="preview-sheet__hint preview-sheet__hint--lead">滚动到正文屏可调整本页</p>' +
        '<p class="preview-sheet__empty-label"><strong>' +
        watching +
        "</strong></p>" +
        '<p class="preview-sheet__hint">本页精修用于正文屏。要换第一眼 / 最后一眼，请调首尾装帧。</p>' +
        '<button type="button" class="preview-sheet__primary" data-action="goto-bookends">去调封面与封底</button>';
      var goBookends = bodyEl.querySelector('[data-action="goto-bookends"]');
      if (goBookends) {
        goBookends.addEventListener("click", function () {
          requestTabSwitch("book", { bookendsFocus: focusSide, scrollToBookends: true });
        });
      }
      return;
    }

    bodyEl.innerHTML =
      '<p class="preview-sheet__label">当前屏</p>' +
      '<p class="preview-sheet__context">' +
      ctx.label +
      "</p>" +
      (ctx.copyHint
        ? '<p class="preview-sheet__hint">本屏有文案 · 也可直接点画面修改</p>'
        : '<p class="preview-sheet__hint">也可直接点画面上的字修改</p>') +
      '<div class="preview-sheet__section preview-sheet__page-actions"></div>' +
      '<p class="preview-sheet__footnote">改精选或拼图后，请点「更新版面」。</p>';

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
      mediaBtn.textContent = "改判普通照片 / 拼图";
      mediaBtn.addEventListener("click", function () {
        var ctl =
          ctx.screen &&
          ctx.screen.querySelector(
            ".preview-toolbar__collage-media, .preview-collage-media, button[data-media-class]"
          );
        if (ctl) ctl.click();
      });
      actions.appendChild(mediaBtn);
    }
    if (actions && !actions.childNodes.length) {
      actions.innerHTML =
        '<p class="preview-sheet__hint">本屏可在画面上标精选或改判拼图；改后请更新版面。</p>';
    }
  }

  function renderBookPanel() {
    stopPreviewFocusWatch();
    bodyEl.innerHTML =
      '<p class="preview-sheet__hint preview-sheet__hint--lead">改整本的名字、意图，以及封面与封底。</p>' +
      '<details class="preview-sheet__zone preview-sheet__zone--story" data-book-zone="story">' +
      '<summary>整本故事 <span class="preview-sheet__zone-meta">杂志名 · 意图</span></summary>' +
      '<div class="preview-sheet__zone-body">' +
      '<div class="preview-sheet__embed preview-sheet__embed--edit"></div>' +
      "</div></details>" +
      '<details class="preview-sheet__zone preview-sheet__zone--bookends" data-book-zone="bookends">' +
      '<summary>首尾装帧 <span class="preview-sheet__zone-meta" data-bookends-focus-badge hidden></span></summary>' +
      '<div class="preview-sheet__zone-body">' +
      '<div class="preview-sheet__bookends-slot"></div>' +
      '<div class="preview-sheet__cover-slot" hidden></div>' +
      "</div></details>" +
      '<details class="preview-sheet__zone preview-sheet__zone--advanced" data-book-zone="advanced">' +
      '<summary>进阶 <span class="preview-sheet__zone-meta">模板 · 同框 · 分章</span></summary>' +
      '<div class="preview-sheet__zone-body">' +
      '<div class="preview-sheet__template-slot"></div>' +
      '<div class="preview-sheet__embed preview-sheet__embed--cohort"></div>' +
      '<button type="button" class="preview-sheet__primary preview-sheet__apply-layout" hidden>更新版面</button>' +
      '<p class="preview-sheet__footnote">改精选或拼图后，请点「更新版面」。</p>' +
      '<p class="preview-sheet__hint">结构确认见顶栏横幅（若开启）；「为什么这样分章」见下方。</p>' +
      '<div class="preview-sheet__embed preview-sheet__embed--structure"></div>' +
      "</div></details>";

    var focusSide = resolveBookendsFocusSide(null);
    var focusBookends = !!focusSide || !!pendingBookendsDeepLink;
    var storyZone = bodyEl.querySelector('[data-book-zone="story"]');
    var bookendsZone = bodyEl.querySelector('[data-book-zone="bookends"]');
    var advancedZone = bodyEl.querySelector('[data-book-zone="advanced"]');
    if (storyZone) storyZone.open = !focusBookends;
    if (bookendsZone) bookendsZone.open = focusBookends;
    if (advancedZone) advancedZone.open = false;

    var editSlot = bodyEl.querySelector(".preview-sheet__embed--edit");
    if (editSlot && hooks.drawers && typeof hooks.drawers.openEmbed === "function") {
      hooks.drawers.openEmbed("edit", editSlot, { sheetMode: true });
    }

    var bookendsSlot = bodyEl.querySelector(".preview-sheet__bookends-slot");
    if (bookendsSlot && typeof hooks.mountBookendsPanel === "function") {
      hooks.mountBookendsPanel(bookendsSlot);
      var scrollOpening = bookendsSlot.querySelector("[data-bookends-scroll-opening]");
      var scrollClosing = bookendsSlot.querySelector("[data-bookends-scroll-closing]");
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
    } else {
      var coverSlot = bodyEl.querySelector(".preview-sheet__cover-slot");
      if (coverSlot) {
        coverSlot.hidden = false;
        if (typeof hooks.mountCoverStyleControls === "function") {
          hooks.mountCoverStyleControls(coverSlot);
        }
      }
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

    startPreviewFocusWatch();
  }

  function switchTab(tabId) {
    activeTab = resolveSheetTab(tabId);
    syncTabUi();
    stopPreviewFocusWatch();
    bodyEl.innerHTML = "";
    bodyEl.scrollTop = 0;
    if (typeof hooks.onSheetTabShown === "function") {
      hooks.onSheetTabShown(activeTab);
    }

    if (activeTab === "more") {
      renderAdvancedPanel();
      return;
    }
    if (activeTab === "page") {
      renderPagePanel();
      return;
    }
    renderBookPanel();
  }

  function open(tabId) {
    previousFocus = document.activeElement;
    beginSheetEnter();
    pausePageFlowScroll();
    if (menuBtn) {
      menuBtn.classList.remove("preview-toolbar__menu-btn--pulse");
      menuBtn.setAttribute("aria-expanded", "true");
    }
    if (typeof hooks.onSheetOpened === "function") {
      hooks.onSheetOpened();
    }
    switchTab(resolveSheetTab(tabId || activeTab));
    activateFocusTrap();
    closeBtn.focus();
  }

  function close() {
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
          hooks.onSheetClosed();
        }
        if (previousFocus && typeof previousFocus.focus === "function") {
          previousFocus.focus();
        } else if (menuBtn && typeof menuBtn.focus === "function") {
          menuBtn.focus();
        }
        previousFocus = null;
      });
    });
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

  closeBtn.addEventListener("click", close);
  scrim.addEventListener("click", close);
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && !shell.hidden && !sheetClosing) close();
  });

  if (menuBtn) {
    menuBtn.addEventListener("click", function (e) {
      e.stopPropagation();
      if (sheetClosing) return;
      if (shell.hidden) open("page");
      else close();
    });
  }

  return {
    open: open,
    close: close,
    switchTab: switchTab,
    setPendingDot: setPendingDot,
    setStructureDot: setStructureDot,
    refreshLayoutTab: function () {
      if (!shell.hidden && activeTab === "book") {
        renderBookPanel();
      }
    },
    refreshAdvancedTab: function () {
      if (!shell.hidden && activeTab === "more") {
        renderAdvancedPanel();
      }
    },
  };
}
