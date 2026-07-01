/**
 * Preview toolbar v3 · unified settings panel (文字 | 结构 | 排版 | 高级).
 * Mobile: bottom sheet · Desktop (≥1024px): right side panel.
 */
"use strict";

var TAB_MODES = [
  { id: "edit", label: "文字" },
  { id: "structure", label: "结构" },
  { id: "layout", label: "排版" },
  { id: "advanced", label: "高级" },
];

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
    '<h2 id="preview-sheet-title" class="preview-sheet__title">编辑与设置</h2>' +
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

  var activeTab = "edit";
  var previousFocus = null;
  var pendingDot = false;
  var structureDot = false;
  var focusRelease = null;
  var lenisPausedBySheet = false;
  var sheetClosing = false;
  var sheetCloseTimer = null;
  var SHEET_ANIM_MS = 540;

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
        id === "structure" && structureDot && !on
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

  function requestTabSwitch(tabId) {
    if (tabId === activeTab) return;
    confirmLeave(function (ok) {
      if (!ok) return;
      switchTab(tabId);
    });
  }

  function renderAdvancedPanel() {
    bodyEl.innerHTML =
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
      "</ul>";

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

  function renderLayoutPanel() {
    bodyEl.innerHTML =
      '<p class="preview-sheet__hint preview-sheet__hint--lead">封面版式与模板策略保存后会自动更新预览。拼图改判、精选与旅行主角设置需点「应用排版」。</p>' +
      '<div class="preview-sheet__cover-slot"></div>' +
      '<div class="preview-sheet__template-slot"></div>' +
      '<div class="preview-sheet__embed"></div>' +
      '<button type="button" class="preview-sheet__primary preview-sheet__apply-layout" hidden>应用排版</button>';

    var coverSlot = bodyEl.querySelector(".preview-sheet__cover-slot");
    if (coverSlot && typeof hooks.mountCoverStyleControls === "function") {
      hooks.mountCoverStyleControls(coverSlot);
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

    var embed = bodyEl.querySelector(".preview-sheet__embed");
    if (embed && hooks.drawers && typeof hooks.drawers.openEmbed === "function") {
      if (hooks.cohortEnabled) {
        hooks.drawers.openEmbed("cohort", embed, { sheetMode: true });
      } else {
        embed.innerHTML =
          '<p class="preview-sheet__hint">旅行主角 · 同框功能未开启。可在结构 Tab 调整分章，或在画面上改判拼图/标精选。</p>';
      }
    }
  }

  function switchTab(tabId) {
    activeTab = tabId;
    syncTabUi();
    bodyEl.innerHTML = "";
    bodyEl.scrollTop = 0;
    if (typeof hooks.onSheetTabShown === "function") {
      hooks.onSheetTabShown(tabId);
    }

    if (tabId === "advanced") {
      renderAdvancedPanel();
      return;
    }
    if (tabId === "layout") {
      renderLayoutPanel();
      return;
    }

    var mode = tabId === "edit" ? "edit" : "structure";
    if (hooks.drawers && typeof hooks.drawers.openEmbed === "function") {
      hooks.drawers.openEmbed(mode, bodyEl, { sheetMode: true });
    }
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
    switchTab(tabId || activeTab);
    activateFocusTrap();
    closeBtn.focus();
  }

  function close() {
    confirmLeave(function (ok) {
      if (!ok) return;
      if (sheetClosing) return;
      releaseFocusTrap();
      if (hooks.drawers && typeof hooks.drawers.close === "function") {
        hooks.drawers.close();
      }
      if (menuBtn) {
        menuBtn.setAttribute("aria-expanded", "false");
      }
      beginSheetExit(function () {
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
      if (shell.hidden) open("edit");
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
      if (!shell.hidden && activeTab === "layout") {
        renderLayoutPanel();
      }
    },
    refreshAdvancedTab: function () {
      if (!shell.hidden && activeTab === "advanced") {
        renderAdvancedPanel();
      }
    },
  };
}
