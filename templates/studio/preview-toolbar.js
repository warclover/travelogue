/**
 * Travelogue Studio · preview page toolbar (ESM).
 */
"use strict";

import {
  postJson,
  patchJson,
  postJsonBusyRetry,
  postJsonConflictRetry,
  patchJsonConflictRetry,
  isJobBusyResponse,
} from "./js/http.js";
import { trackStudioEvent } from "./js/analytics.js";
import { mountPreviewTaskDock } from "./preview-toolbar-v3-task-dock.js";
import { mountPreviewUnifiedSheet } from "./preview-toolbar-v3-sheet.js";
import {
  dockIconSvg,
  insertScreenplayControl,
  isPreviewToolbarV4,
  isPreviewToolbarV3,
  dockLongshotIconHtml,
  ensureDockTooltip,
  syncDockScreenplayTip,
  initDockTooltips,
  initDockScrollFade,
} from "./preview-toolbar/dock.js";
import {
  isSharePreview,
  initShareMinimal,
  ensureCoverMobileFootnote,
} from "./preview-toolbar/share.js";
import {
  registerInlineEditBridge,
  initCoverTitleEdit,
  resolveSplitMatTitleLayoutClass,
  syncCoverTitleLayoutClass,
  saveMagazineTitle,
} from "./preview-toolbar/inline-edit.js";
import {
  registerLongshotBridge,
  cancelPreviewLongshotExport,
  startLongshot,
  setLongshotExportState,
  readLongshotExportPrefs,
  writeStoredLongshotPrefs,
  buildLongshotRequestFromPage,
  refreshLongshotExportMeta,
  openLongshotExportOptions,
  pollJob,
  exportZip,
  revealTripPath,
  isReaderSurfaceMode,
  syncLongshotPreviewRowVisibility,
  syncLongshotPreviewChips,
  refreshStaleHint,
  showStaleHint,
} from "./preview-toolbar/longshot.js";
import {
  tripIdFromPath,
  tripApiBase,
  toolbarConfirm,
  toolbarAlert,
  showToolbarToast,
  maybeShowCoverOpeningStyleToast,
  reloadPreviewAfterLayout,
  setSlowHint,
  toolbarBody,
  syncToolbarHeight,
  setToolbarCollapsed,
  toggleToolbarCollapsed,
  bindToolbarCollapse,
} from "./preview-toolbar/shell.js";
import {
  registerDrawersBridge,
  initPreviewDrawers,
  trapDrawerFocus,
  formatAestheticPurposeLine,
} from "./preview-toolbar/drawers.js";

var isJobBusy409 = isJobBusyResponse;
var HINT_KEY = "travelogue.studio.editHint.dismissed";
var READER_VIEW_KEY = "travelogue.studio.readerView";
var SHEET_HINT_KEY = "travelogue.studio.previewSheet.hintSeen";
var COVER_OPENING_STYLE_OPTIONS = [
  { id: "card-br", label: "书名卡" },
  { id: "split-mat", label: "分屏衬纸" },
  { id: "magazine-head", label: "杂志顶题" },
];

  var _layoutPending = false;
  var _pendingDockDismissed = false;
  var _layoutPendingMessage = "";
  var _g1Pending = false;
  var _g1DockDismissed = false;
  var _sheetEditDirty = false;
  var _sheetEditBaseline = "";

  function snapshotEditPanel(el) {
    if (!el) return "";
    var title = el.querySelector(".preview-drawer__title-input");
    var notes = el.querySelector(".preview-drawer__notes");
    var anchors = [];
    el.querySelectorAll(".preview-drawer__anchor").forEach(function (inp) {
      anchors.push((inp.value || "").trim());
    });
    var mood = el.querySelector(".preview-drawer__chip-mood.is-selected");
    var focus = el.querySelector(".preview-drawer__chip-focus.is-selected");
    var note = el.querySelector(".preview-drawer__copy-intent-note");
    var sub = el.querySelector(".preview-drawer__copy-intent-subsequent");
    return JSON.stringify({
      title: title ? title.value : "",
      notes: notes ? notes.value : "",
      anchors: anchors,
      mood: mood ? mood.getAttribute("data-value") : "",
      focus: focus ? focus.getAttribute("data-value") : "",
      intentNote: note ? note.value : "",
      subsequent: sub ? sub.checked : false,
    });
  }

  function markSheetEditBaseline(root, panel) {
    _sheetEditBaseline = snapshotEditPanel(panel);
    _sheetEditDirty = false;
    if (root) root._sheetEditDirty = false;
  }

  function wireSheetEditDirty(root, panel) {
    if (!panel || panel.dataset.sheetDirtyBound === "1") return;
    panel.dataset.sheetDirtyBound = "1";
    function syncDirty() {
      _sheetEditDirty = snapshotEditPanel(panel) !== _sheetEditBaseline;
      if (root) root._sheetEditDirty = _sheetEditDirty;
    }
    panel.addEventListener("input", syncDirty);
    panel.addEventListener("change", syncDirty);
    panel.querySelectorAll(".preview-drawer__chip-mood, .preview-drawer__chip-focus").forEach(
      function (btn) {
        btn.addEventListener("click", function () {
          window.setTimeout(syncDirty, 0);
        });
      }
    );
  }

  function refreshTaskDockState(root) {
    if (!root || !isPreviewToolbarV3(root) || !root._taskDock) return;
    if (root._exportDockActive || root._exportResultShowing) return;
    if (_g1Pending && !_g1DockDismissed) {
      root._taskDock.showG1({});
      return;
    }
    if (_layoutPending && !_pendingDockDismissed) {
      root._taskDock.showPending({
        title: _layoutPendingMessage || "有编辑尚未应用排版",
      });
      return;
    }
    root._taskDock.hide();
  }

  function layoutApplyButtons(root) {
    var scope = root && root.nodeType === 1 ? root : document;
    var toolbar =
      (scope.closest && scope.closest(".preview-toolbar")) ||
      (scope.classList && scope.classList.contains("preview-toolbar") ? scope : null) ||
      document.querySelector(".preview-toolbar");
    var searchRoot = toolbar || scope;
    return searchRoot.querySelectorAll(
      ".preview-toolbar__apply-layout, .preview-sheet__apply-layout, .preview-drawer__apply-layout"
    );
  }

  function syncCoverOpeningStyleInDom(style) {
    var section = document.querySelector('.cover-opening[data-block="cover-opening"]');
    if (!section || !style) return;
    section.setAttribute("data-cover-opening", style);
    var titleEl = section.querySelector(".cover-opening__title");
    if (style === "split-mat") {
      syncCoverTitleLayoutClass(titleEl);
    } else if (titleEl) {
      titleEl.classList.remove(
        "cover-opening__title--vertical",
        "cover-opening__title--vertical-compact",
        "cover-opening__title--horizontal"
      );
    }
  }

  function refreshPreviewAfterCopySave(res, tripId, root) {
    var rendered = res.body && res.body.rendered;
    if (rendered && rendered.length) {
      return Promise.resolve(true);
    }
    return applyLayoutRerender(tripId, root);
  }

  function setLayoutPending(on) {
    _layoutPending = !!on;
    if (on) _pendingDockDismissed = false;
    document
      .querySelectorAll(
        ".preview-toolbar__apply-layout, .preview-sheet__apply-layout, .preview-drawer__apply-layout"
      )
      .forEach(function (btn) {
        btn.hidden = !_layoutPending;
      });
    document.querySelectorAll(".preview-toolbar__pending-row").forEach(function (row) {
      row.hidden = !_layoutPending;
    });
    var toolbar = document.querySelector(".preview-toolbar");
    if (toolbar && isPreviewToolbarV3(toolbar)) {
      if (toolbar._sheet) toolbar._sheet.setPendingDot(_layoutPending);
      refreshTaskDockState(toolbar);
      if (toolbar._sheet && typeof toolbar._sheet.refreshLayoutTab === "function") {
        toolbar._sheet.refreshLayoutTab();
      }
      return;
    }
    if (toolbar) {
      syncLongshotPreviewRowVisibility(toolbar);
      requestAnimationFrame(function () {
        syncToolbarHeight(toolbar);
      });
    }
  }

  function toggleAdvancedMenu(root) {
    var menu = root.querySelector(".preview-toolbar__menu");
    if (!menu) return;
    menu.hidden = !menu.hidden;
  }

  function startLlmNarrate(root, tripId, btn) {
    if (!btn || btn.disabled) return;
    toolbarConfirm({
      title: "生成杂志感文案",
      body: "将调用 LLM 重写 hook、导语与图注，可能覆盖未锁定的文案。继续？",
      confirmText: "继续",
    }).then(function (ok) {
      if (!ok) return;
      setToolbarCollapsed(root, false, false);
      btn.disabled = true;
      setSlowHint(root, "", false);
      setSlowHint(root, "正在生成杂志感文案…", true);
      return postJson("/__travelogue/narrate", { tripId: tripId });
    }).then(function (res) {
      if (!res) return;
      if (res.status === 409 || res.status === 400) {
        setSlowHint(root, (res.body && res.body.message) || "无法开始", true);
        btn.disabled = false;
        return;
      }
      if (res.status !== 202 || !res.body.jobId) {
        setSlowHint(root, "无法开始文案生成", true);
        btn.disabled = false;
        return;
      }
      narrateJobId = res.body.jobId;
      pollJob(
        res.body.jobId,
        root,
        function (job) {
          btn.disabled = false;
          narrateJobId = null;
          setSlowHint(root, "", false);
          if (job.status === "succeeded") {
            window.location.reload();
            return;
          }
          var err = (job.error && (job.error.message || job.error.code)) || "文案生成失败";
          toolbarAlert(err, { error: true });
        },
        function () {
          setSlowHint(root, "比预期久一些，请耐心等待…", true);
        },
        "narrate"
      );
    }).catch(function () {
      btn.disabled = false;
      setSlowHint(root, "网络错误", true);
    });
  }

  function refreshPreviewCover(root) {
    var body = toolbarBody(root);
    var card = body.querySelector(".preview-toolbar__preview-card");
    if (card) card.remove();
  }

  function applyLayoutRerender(tripId, root) {
    var applyBtns = layoutApplyButtons(
      root || document.querySelector(".preview-toolbar") || document.body
    );
    var pendingBtn =
      (root && root.querySelector && root.querySelector(".preview-toolbar__pending-apply")) ||
      document.querySelector(".preview-toolbar__pending-apply");
    applyBtns.forEach(function (btn) {
      btn.disabled = true;
    });
    if (pendingBtn) pendingBtn.disabled = true;
    showToolbarToast("正在应用排版…", { duration: 3000 });
    return postJson(tripApiBase(tripId) + "/rerender", {})
      .then(function (res) {
        applyBtns.forEach(function (btn) {
          btn.disabled = false;
        });
        if (pendingBtn) pendingBtn.disabled = false;
        if (res.status !== 200 || !res.body.ok) {
          showToolbarToast((res.body && res.body.error) || "排版失败", { error: true });
          setLayoutPending(true);
          return false;
        }
        setLayoutPending(false);
        reloadPreviewAfterLayout();
        return true;
      })
      .catch(function () {
        applyBtns.forEach(function (btn) {
          btn.disabled = false;
        });
        if (pendingBtn) pendingBtn.disabled = false;
        showToolbarToast("排版失败", { error: true });
        setLayoutPending(true);
        return false;
      });
  }


  function initTitleEdit(root, tripId) {
    var wrap = root.querySelector(".preview-toolbar__title-wrap");
    if (!wrap) return;

    var display = document.createElement("button");
    display.type = "button";
    display.className = "preview-toolbar__title";
    display.title = "点击编辑杂志名";
    display.textContent = "我的旅途";
    wrap.appendChild(display);

    function setTitle(text) {
      var t = (text || "我的旅途").trim() || "我的旅途";
      display.textContent = t.length > 20 ? t.slice(0, 20) : t;
      display.dataset.title = t;
    }

    fetch("/__travelogue/trips/" + encodeURIComponent(tripId) + "/entry")
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (data) {
        if (data && data.intentSummary && data.intentSummary.title) {
          setTitle(data.intentSummary.title);
        }
      })
      .catch(function () {});

    display.addEventListener("click", function () {
      if (wrap.querySelector(".preview-toolbar__title-input")) return;
      var input = document.createElement("input");
      input.type = "text";
      input.className = "preview-toolbar__title-input";
      input.maxLength = 20;
      input.value = display.dataset.title || display.textContent || "";
      display.hidden = true;
      wrap.appendChild(input);
      input.focus();
      input.select();

      function finish(save) {
        var next = (input.value || "").trim();
        input.remove();
        display.hidden = false;
        if (!save) {
          setTitle(display.dataset.title || display.textContent);
          return;
        }
        if (next.length > 20) {
          showToolbarToast("杂志名最多 20 个字", { error: true });
          return;
        }
        if (!next) {
          showToolbarToast("杂志名不能为空", { error: true });
          return;
        }
        var prev = (display.dataset.title || "").trim();
        if (next === prev) {
          setTitle(next);
          return;
        }
        display.classList.add("preview-toolbar__title--saving");
        saveMagazineTitle(tripId, next, display, function () {
          display.classList.remove("preview-toolbar__title--saving");
          setTitle(next);
        });
      }

      input.addEventListener("keydown", function (e) {
        if (e.key === "Enter") {
          e.preventDefault();
          finish(true);
        }
        if (e.key === "Escape") {
          e.preventDefault();
          finish(false);
        }
      });
      input.addEventListener("blur", function () {
        finish(true);
      });
    });
  }

  function initDisplayedAestheticTitles(tripId) {
    fetch("/__travelogue/trips/" + encodeURIComponent(tripId) + "/aesthetic")
      .then(function (resp) { return resp.ok ? resp.json() : null; })
      .then(function (data) {
        if (!data || !data.ok || !data.enabled) return;
        var byId = {};
        (data.assets || []).forEach(function (row) {
          if (row && row.id) byId[row.id] = row;
        });
        document
          .querySelectorAll('.layout-screen[data-block="layout-screen"][data-asset-ids]')
          .forEach(function (screen) {
            var aid = (screen.getAttribute("data-asset-ids") || "").split(",")[0];
            var row = byId[aid];
            if (!row || !row.explain || !row.explain.length) return;
            var img = screen.querySelector("img");
            if (!img) return;
            var tips = row.explain
              .map(function (item) { return item.reason || item.label; })
              .filter(Boolean)
              .join("；");
            var pct = row.overall != null ? Math.round(Number(row.overall) * 100) : null;
            var stratum = row.stratumLabel || row.stratum || "";
            var purposeLine = formatAestheticPurposeLine(row);
            img.setAttribute(
              "title",
              [
                pct != null ? "审美 " + pct : "",
                stratum ? stratum : "",
                purposeLine,
                tips,
              ]
                .filter(Boolean)
                .join(" · ")
            );
          });
      })
      .catch(function () { /* fail-open */ });
  }

  function fetchEntry(tripId) {
    return fetch("/__travelogue/trips/" + encodeURIComponent(tripId) + "/entry")
      .then(function (r) { return r.ok ? r.json() : null; })
      .catch(function () { return null; });
  }

  function currentChapterId() {
    var sections = document.querySelectorAll("section.chapter[data-chapter-id]");
    var best = null;
    var bestVis = 0;
    sections.forEach(function (sec) {
      var rect = sec.getBoundingClientRect();
      var vis = Math.min(rect.bottom, window.innerHeight) - Math.max(rect.top, 0);
      if (vis > bestVis) {
        bestVis = vis;
        best = sec.getAttribute("data-chapter-id");
      }
    });
    return best;
  }

  function initG1V3(root, tripId, drawers, sheet) {
    Promise.all([
      fetch("/__travelogue/config").then(function (r) { return r.ok ? r.json() : null; }),
      fetch("/__travelogue/trips/" + encodeURIComponent(tripId) + "/entry").then(function (r) {
        return r.ok ? r.json() : null;
      }),
    ])
      .then(function (rows) {
        var cfg = rows[0];
        var entry = rows[1];
        if (!cfg || !entry || !entry.g1Pending) return;
        if (!(cfg.studio && cfg.studio.g1ConfirmStructure)) return;
        _g1Pending = true;
        _g1DockDismissed = false;
        if (sheet) sheet.setStructureDot(true);
        refreshTaskDockState(root);
      })
      .catch(function () {});
  }

  function initG1Banner(root, tripId, drawers) {
    var body = toolbarBody(root);
    if (!body) return;
    Promise.all([
      fetch("/__travelogue/config").then(function (r) { return r.ok ? r.json() : null; }),
      fetch("/__travelogue/trips/" + encodeURIComponent(tripId) + "/entry").then(function (r) {
        return r.ok ? r.json() : null;
      }),
    ])
      .then(function (rows) {
        var cfg = rows[0];
        var entry = rows[1];
        if (!cfg || !entry || !entry.g1Pending) return;
        if (!(cfg.studio && cfg.studio.g1ConfirmStructure)) return;
        if (body.querySelector(".preview-toolbar__g1-banner")) return;

        var banner = document.createElement("div");
        banner.className = "preview-toolbar__g1-banner";
        banner.setAttribute("role", "status");
        banner.innerHTML =
          '<p class="preview-toolbar__g1-banner-text">章节结构待确认（G1 已开启）</p>' +
          '<div class="preview-toolbar__g1-banner-actions">' +
          '<button type="button" class="preview-toolbar__g1-banner-open">查看结构</button>' +
          '<button type="button" class="preview-toolbar__g1-banner-confirm">确认并继续</button>' +
          "</div>";
        var bar = body.querySelector(".preview-toolbar__bar");
        if (bar && bar.nextSibling) {
          body.insertBefore(banner, bar.nextSibling);
        } else {
          body.appendChild(banner);
        }
        banner.querySelector(".preview-toolbar__g1-banner-open").addEventListener("click", function () {
          drawers.openStructure();
        });
        banner.querySelector(".preview-toolbar__g1-banner-confirm").addEventListener("click", function () {
          drawers.confirmStructure();
        });
      })
      .catch(function () {});
  }

  function startFeaturedPresent() {
    var featuredHref = presentAutoplayHref({ featured: true });
    if (featuredHref) {
      window.location.href = featuredHref;
      showToolbarToast("精选全屏放映已开始");
      return;
    }
    var toggle = document.getElementById("featured-present-toggle");
    var start = document.getElementById("screenplay-start");
    if (!start) {
      showToolbarToast("当前页面不支持全屏放映", { error: true });
      return;
    }
    if (toggle && toggle.getAttribute("aria-pressed") !== "true") {
      toggle.click();
    }
    start.click();
    showToolbarToast("精选全屏放映已开始");
  }

  function initCollageMediaControls(tripId, assetMediaById) {
    assetMediaById = assetMediaById || {};
    var apiUrl =
      "/__travelogue/trips/" + encodeURIComponent(tripId) + "/asset-media-class";

    function shouldShowControl(screen, assetId) {
      var raw = screen.getAttribute("data-asset-ids") || "";
      var ids = raw.split(",").filter(function (id) { return !!id; });
      if (ids.length === 1) return true;
      var mc = assetMediaById[assetId] || "photo";
      var pattern = screen.getAttribute("data-pattern") || "";
      var hint = screen.getAttribute("data-layout-hint") || "";
      return mc === "collage" || pattern === "screen-full-frame" || hint === "full-frame";
    }

    function applyMediaClass(assetId, mediaClass, selectEl) {
      if (selectEl.disabled) return;
      selectEl.disabled = true;
      patchJsonConflictRetry(apiUrl, { assetId: assetId, mediaClass: mediaClass })
        .then(function (res) {
          selectEl.disabled = false;
          if (res.status !== 200 || !res.body.ok) {
            showToolbarToast((res.body && res.body.error) || "改判失败", { error: true });
            selectEl.value = assetMediaById[assetId] || "photo";
            return;
          }
          assetMediaById[assetId] = mediaClass;
          selectEl.value = mediaClass;
          setLayoutPending(true);
          showToolbarToast(
            mediaClass === "collage"
              ? "已标记为拼图 · 点应用排版后生效"
              : "已标记为普通照片 · 点应用排版后生效"
          );
        })
        .catch(function () {
          selectEl.disabled = false;
          showToolbarToast("改判失败", { error: true });
        });
    }

    document
      .querySelectorAll('.layout-screen[data-block="layout-screen"][data-asset-ids]')
      .forEach(function (screen) {
        if (screen.querySelector(".preview-toolbar__collage-ctrl")) return;
        var raw = screen.getAttribute("data-asset-ids") || "";
        var assetId = raw.split(",")[0];
        if (!assetId || !shouldShowControl(screen, assetId)) return;

        var wrap = document.createElement("div");
        wrap.className = "preview-toolbar__collage-ctrl";
        var label = document.createElement("span");
        label.className = "preview-toolbar__collage-label";
        label.textContent = "媒资";
        var sel = document.createElement("select");
        sel.className = "preview-toolbar__collage-select";
        sel.setAttribute("aria-label", "拼图改判");
        [["photo", "普通照片"], ["collage", "拼图"]].forEach(function (pair) {
          var opt = document.createElement("option");
          opt.value = pair[0];
          opt.textContent = pair[1];
          sel.appendChild(opt);
        });
        sel.value = assetMediaById[assetId] === "collage" ? "collage" : "photo";
        sel.addEventListener("change", function (e) {
          e.stopPropagation();
          applyMediaClass(assetId, sel.value, sel);
        });
        wrap.appendChild(label);
        wrap.appendChild(sel);
        screen.style.position = screen.style.position || "relative";
        screen.appendChild(wrap);
      });
  }

  function initFeaturedStars(tripId) {
    var screens = document.querySelectorAll('.layout-screen[data-block="layout-screen"][data-asset-ids]');
    screens.forEach(function (screen) {
      if (screen.querySelector(".preview-toolbar__featured-star")) return;
      var raw = screen.getAttribute("data-asset-ids") || "";
      var assetId = raw.split(",")[0];
      if (!assetId) return;

      var star = document.createElement("button");
      star.type = "button";
      star.className = "preview-toolbar__featured-star";
      star.setAttribute("aria-label", "标为精选");
      star.textContent = "★";
      if (screen.getAttribute("data-featured") === "true") {
        star.classList.add("preview-toolbar__featured-star--on");
        star.setAttribute("aria-pressed", "true");
      }
      star.addEventListener("click", function (e) {
        e.preventDefault();
        e.stopPropagation();
        if (star.disabled) return;
        star.disabled = true;
        postJsonConflictRetry(tripApiBase(tripId) + "/promote-tier", {
          assetIds: [assetId],
          rerender: false,
        })
          .then(function (res) {
            star.disabled = false;
            if (res.status !== 200 || !res.body.ok) {
              showToolbarToast((res.body && res.body.error) || "标记失败", { error: true });
              return;
            }
            star.classList.add("preview-toolbar__featured-star--on");
            star.setAttribute("aria-pressed", "true");
            screen.setAttribute("data-featured", "true");
            setLayoutPending(true);
            showToolbarToast("已标为精选 · 点应用排版后生效");
          })
          .catch(function () {
            star.disabled = false;
            showToolbarToast("标记失败", { error: true });
          });
      });
      screen.style.position = screen.style.position || "relative";
      screen.appendChild(star);
    });
  }

  function revealTripFolder(tripId) {
    fetch("/__travelogue/trips")
      .then(function (resp) { return resp.json(); })
      .then(function (data) {
        var trips = data.trips || [];
        var trip = trips.filter(function (t) { return t.tripId === tripId; })[0];
        var rel = (trip && trip.previewRelPath) || "index.html";
        return revealTripPath(tripId, rel);
      })
      .catch(function () {
        showToolbarToast("无法打开文件夹", { error: true });
      });
  }

  function readCoverOpeningStyleFromDom() {
    var section = document.querySelector(".cover-opening[data-cover-opening]");
    return section ? section.getAttribute("data-cover-opening") || "card-br" : "card-br";
  }

  function mountCoverStyleControls(slot, tripId) {
    if (!slot || slot.querySelector(".preview-sheet__cover-styles")) return;
    var section = document.createElement("div");
    section.className = "preview-sheet__section preview-sheet__cover-section";
    section.innerHTML =
      '<span class="preview-sheet__label">封面版式</span>' +
      '<p class="preview-sheet__hint preview-sheet__hint--compact">电脑预览有效；窄屏与手机版式不同。</p>' +
      '<div class="preview-sheet__cover-styles" role="group" aria-label="封面版式"></div>';
    var group = section.querySelector(".preview-sheet__cover-styles");
    var selectedStyle = readCoverOpeningStyleFromDom();

    function syncSelection(style) {
      if (!group) return;
      group.querySelectorAll("[data-cover-style]").forEach(function (btn) {
        var on = btn.getAttribute("data-cover-style") === style;
        btn.classList.toggle("is-on", on);
        btn.setAttribute("aria-pressed", on ? "true" : "false");
      });
    }

    function setBusy(busy) {
      if (!group) return;
      group.querySelectorAll("[data-cover-style]").forEach(function (btn) {
        btn.disabled = !!busy;
      });
    }

    COVER_OPENING_STYLE_OPTIONS.forEach(function (opt) {
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "preview-sheet__cover-style";
      btn.setAttribute("data-cover-style", opt.id);
      btn.setAttribute("aria-label", opt.label);
      btn.innerHTML =
        '<span class="preview-sheet__cover-thumb" data-cover-thumb="' +
        opt.id +
        '" aria-hidden="true"></span>' +
        '<span class="preview-sheet__cover-label">' +
        opt.label +
        "</span>";
      btn.addEventListener("click", function () {
        var next = opt.id;
        if (!next || next === selectedStyle) return;
        setBusy(true);
        postJsonConflictRetry(tripApiBase(tripId) + "/save-copy", {
          patches: [{ path: "meta.coverOpeningStyle", value: next }],
        })
          .then(function (res) {
            setBusy(false);
            if (res.status !== 200 || !res.body.ok) {
              showToolbarToast((res.body && res.body.error) || "保存失败", { error: true });
              return;
            }
            var prev = selectedStyle;
            selectedStyle = next;
            syncSelection(next);
            syncCoverOpeningStyleInDom(next);
            trackStudioEvent("cover_opening_style_change", {
              tripId: tripId,
              coverOpeningStyle: next,
              previousCoverOpeningStyle: prev,
            });
            showToolbarToast("封面版式已更新");
            var toolbar = document.querySelector(".preview-toolbar");
            return refreshPreviewAfterCopySave(
              res,
              tripId,
              toolbar || section
            ).then(function (ok) {
              if (ok && toolbar) refreshStaleHint(toolbar, tripId);
            });
          })
          .catch(function () {
            setBusy(false);
            showToolbarToast("保存失败", { error: true });
          });
      });
      group.appendChild(btn);
    });

    syncSelection(selectedStyle);
    fetchEntry(tripId)
      .then(function (data) {
        if (data && data.coverOpeningStyle) {
          selectedStyle = data.coverOpeningStyle;
          syncSelection(selectedStyle);
        }
      })
      .catch(function () {});

    slot.appendChild(section);
    trackStudioEvent("cover_opening_style_selector_impression", {
      surface: "preview-sheet",
      tripId: tripId,
      coverOpeningStyle: selectedStyle,
    });
  }

  function mountTemplateControls(slot, tripId, opts) {
    opts = opts || {};
    if (!slot || slot.querySelector(".preview-toolbar__template")) return;
    fetchEntry(tripId)
      .then(function (data) {
        var t = data && data.template;
        if (!t) return;
        var pill = document.createElement("span");
        pill.className =
          "preview-toolbar__template" + (opts.inSheet ? " preview-toolbar__template--sheet" : "");
        pill.setAttribute("title", t.feedbackMessage || "");
        var label = t.sourceLabel || "模板";
        if (t.locked) label += " · 已锁定";
        pill.textContent = label + " · " + (t.resolvedTemplateId || "visual-journal");
        slot.appendChild(pill);
        trackStudioEvent("template_selector_impression", {
          surface: opts.inSheet ? "preview-sheet" : "preview",
          tripId: tripId,
        });
        if (t.locked) return;
        var wrap = document.createElement("span");
        wrap.className = "preview-toolbar__template-adjust";
        var sel = document.createElement("select");
        sel.setAttribute("aria-label", "调整模板");
        ["smart", "manual:visual-journal", "manual:event-recap"].forEach(function (v) {
          var o = document.createElement("option");
          o.value = v;
          o.textContent = v === "smart" ? "智能匹配" : v.slice(7);
          sel.appendChild(o);
        });
        if (t.mode === "manual" && t.resolvedTemplateId) {
          sel.value = "manual:" + t.resolvedTemplateId;
        } else {
          sel.value = "smart";
        }
        var btn = document.createElement("button");
        btn.type = "button";
        btn.textContent = "应用";
        btn.addEventListener("click", function () {
          var v = String(sel.value || "smart");
          var body = { mode: v.indexOf("manual:") === 0 ? "manual" : "smart" };
          if (body.mode === "manual") body.templateId = v.slice(7);
          fetch("/__travelogue/trips/" + encodeURIComponent(tripId) + "/template", {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
          })
            .then(function (r) {
              return r.json().then(function (j) {
                return { ok: r.ok, j: j };
              });
            })
            .then(function (res) {
              if (!res.ok) {
                showToolbarToast((res.j && res.j.message) || "模板调整失败", { error: true });
                return;
              }
              pill.textContent =
                ((res.j.template && res.j.template.sourceLabel) || "已更新") +
                " · " +
                ((res.j.template && res.j.template.resolvedTemplateId) ||
                  t.resolvedTemplateId ||
                  "visual-journal");
              showToolbarToast("模板已更新，正在应用排版…", { duration: 2500 });
              return applyLayoutRerender(
                tripId,
                document.querySelector(".preview-toolbar") || slot
              );
            })
            .catch(function () {
              showToolbarToast("模板调整失败", { error: true });
            });
        });
        wrap.appendChild(sel);
        wrap.appendChild(btn);
        slot.appendChild(wrap);
      })
      .catch(function () {});
  }

  function initTemplateBadge(root, tripId) {
    var bar = root.querySelector(".preview-toolbar__bar");
    var cluster = bar && bar.querySelector(".preview-toolbar__cluster");
    if (!cluster) return;
    mountTemplateControls(cluster, tripId, { inSheet: false });
  }

  function snapshotReadingPayload() {
    var reading = window.__TRAVELOGUE_READING__;
    if (!reading || typeof reading !== "object") return null;
    try {
      return JSON.parse(JSON.stringify(reading));
    } catch (e) {
      return null;
    }
  }

  function applyReaderSurfaceMode(readerMode) {
    var html = document.documentElement;
    var reading = window.__TRAVELOGUE_READING__ || {};
    if (readerMode) {
      html.setAttribute("data-reading-profile", "reader_immersive");
      html.setAttribute("data-surface-mode", "reader");
      html.removeAttribute("data-folio");
      reading.profile = "reader_immersive";
      reading.scroll = reading.scroll || {};
      reading.scroll.folio = "off";
    } else {
      html.setAttribute("data-reading-profile", "studio_preview");
      html.removeAttribute("data-surface-mode");
      html.setAttribute("data-folio", "lite");
      reading.profile = "studio_preview";
      reading.scroll = reading.scroll || {};
      reading.scroll.folio = "lite";
    }
    window.__TRAVELOGUE_READING__ = reading;
    if (window.TravelogueBreath && typeof window.TravelogueBreath.destroy === "function") {
      window.TravelogueBreath.destroy();
    }
    if (window.TravelogueBreath && typeof window.TravelogueBreath.init === "function") {
      window.TravelogueBreath.init();
    }
  }

  function initPreviewModeSeg(root, actions) {
    var baseline = snapshotReadingPayload();
    var seg = document.createElement("div");
    seg.className = "preview-toolbar__mode-seg";
    seg.setAttribute("role", "group");
    seg.setAttribute("aria-label", "预览模式");

    var readerBtn = document.createElement("button");
    readerBtn.type = "button";
    readerBtn.textContent = "阅读视图";
    var editBtn = document.createElement("button");
    editBtn.type = "button";
    editBtn.textContent = "编辑预览";
    seg.appendChild(readerBtn);
    seg.appendChild(editBtn);
    actions.insertBefore(seg, actions.firstChild);

    var readerOn = true;
    try {
      var stored = localStorage.getItem(READER_VIEW_KEY);
      if (stored === "0") readerOn = false;
      else if (stored === "1") readerOn = true;
    } catch (e) {}

    function syncSeg() {
      readerBtn.classList.toggle("is-selected", readerOn);
      editBtn.classList.toggle("is-selected", !readerOn);
      readerBtn.setAttribute("aria-pressed", readerOn ? "true" : "false");
      editBtn.setAttribute("aria-pressed", readerOn ? "false" : "true");
    }

    function setReaderMode(on) {
      readerOn = !!on;
      applyReaderSurfaceMode(readerOn);
      syncSeg();
      syncLongshotPreviewRowVisibility(root);
      try {
        localStorage.setItem(READER_VIEW_KEY, readerOn ? "1" : "0");
      } catch (e2) {}
    }

    readerBtn.addEventListener("click", function () {
      setReaderMode(true);
    });
    editBtn.addEventListener("click", function () {
      setReaderMode(false);
    });

    if (baseline && baseline.profile === "reader_immersive") {
      setReaderMode(true);
    } else {
      setReaderMode(readerOn);
    }
    syncSeg();
  }


  function initToolbarV3(root, tripId) {
    registerLongshotBridge({
      showToolbarToast: showToolbarToast,
      toolbarConfirm: toolbarConfirm,
      toolbarAlert: toolbarAlert,
      setSlowHint: setSlowHint,
      setToolbarCollapsed: setToolbarCollapsed,
      syncToolbarHeight: syncToolbarHeight,
      refreshTaskDockState: refreshTaskDockState,
      getLayoutPending: function () { return _layoutPending; },
      tripIdFromPath: tripIdFromPath,
      toolbarBody: toolbarBody,
      setLayoutPending: setLayoutPending,
      setLayoutPendingMessage: function (msg) { _layoutPendingMessage = msg; },
    });
    registerDrawersBridge({
      fetchEntry: fetchEntry,
      currentChapterId: currentChapterId,
      markSheetEditBaseline: markSheetEditBaseline,
      wireSheetEditDirty: wireSheetEditDirty,
      startLlmNarrate: startLlmNarrate,
      applyLayoutRerender: applyLayoutRerender,
      getLayoutPending: function () { return _layoutPending; },
    });
    registerInlineEditBridge({
      tripApiBase: tripApiBase,
      reloadPreviewAfterLayout: reloadPreviewAfterLayout,
      showToolbarToast: showToolbarToast,
      isSharePreview: isSharePreview,
    });
    var dock = root.querySelector(".preview-toolbar__dock");
    var actions = dock || root.querySelector(".preview-toolbar__actions");
    if (!isPreviewToolbarV4(root)) {
      initTitleEdit(root, tripId);
    }
    var drawers = initPreviewDrawers(root, tripId);

    var readerOn = false;
    try {
      var stored = localStorage.getItem(READER_VIEW_KEY);
      if (stored === "1") readerOn = true;
    } catch (e0) {}
    var baseline = snapshotReadingPayload();
    if (baseline && baseline.profile === "reader_immersive") readerOn = true;
    applyReaderSurfaceMode(readerOn);

    function syncLongshotPrefsUi(container) {
      if (!container) return;
      var prefs = readLongshotExportPrefs();
      container.querySelectorAll("[data-studio-longshot-mode]").forEach(function (btn) {
        var on = btn.getAttribute("data-studio-longshot-mode") === prefs.mode;
        btn.classList.toggle("is-on", on);
        btn.setAttribute("aria-pressed", on ? "true" : "false");
      });
      container.querySelectorAll("[data-studio-longshot-scale]").forEach(function (btn) {
        var on = String(btn.getAttribute("data-studio-longshot-scale")) === String(prefs.scale);
        btn.classList.toggle("is-on", on);
        btn.setAttribute("aria-pressed", on ? "true" : "false");
      });
    }

    function syncReaderModeUi(container) {
      if (!container) return;
      var on = isReaderSurfaceMode();
      container.querySelectorAll("[data-reader-mode]").forEach(function (btn) {
        var reader = btn.getAttribute("data-reader-mode") === "reader";
        btn.classList.toggle("is-on", reader === on);
        btn.setAttribute("aria-pressed", reader === on ? "true" : "false");
      });
    }

    var cohortEnabled = false;
    var menuBtn = root.querySelector(".preview-toolbar__menu-btn");
    try {
      if (menuBtn && !sessionStorage.getItem(SHEET_HINT_KEY)) {
        menuBtn.classList.add("preview-toolbar__menu-btn--pulse");
      }
    } catch (eHint) {}

    var sheetHooks = {
      drawers: drawers,
      get cohortEnabled() { return cohortEnabled; },
      isLayoutPending: function () { return _layoutPending; },
      confirmLeaveCurrentTab: function (tabId, done) {
        if (tabId !== "edit" || !_sheetEditDirty) {
          done(true);
          return;
        }
        toolbarConfirm({
          title: "未保存的编辑",
          body: "当前「文字」Tab 有未保存改动，离开将丢弃。",
          confirmText: "离开",
          cancelText: "留下",
        }).then(done);
      },
      onSheetTabShown: function (tabId) {
        if (tabId !== "edit") {
          _sheetEditDirty = false;
          root._sheetEditDirty = false;
        }
      },
      onSheetOpened: function () {
        try {
          sessionStorage.setItem(SHEET_HINT_KEY, "1");
        } catch (eOpen) {}
        if (menuBtn) menuBtn.classList.remove("preview-toolbar__menu-btn--pulse");
      },
      syncLongshotPrefsUi: syncLongshotPrefsUi,
      syncReaderModeUi: syncReaderModeUi,
      setLongshotMode: function (mode) {
        var prefs = readLongshotExportPrefs();
        writeStoredLongshotPrefs(mode, prefs.scale);
      },
      setLongshotScale: function (scale) {
        var prefs = readLongshotExportPrefs();
        writeStoredLongshotPrefs(prefs.mode, scale === 3 ? 3 : 2);
      },
      setReaderMode: function (on) {
        applyReaderSurfaceMode(!!on);
        try {
          localStorage.setItem(READER_VIEW_KEY, on ? "1" : "0");
        } catch (e1) {}
      },
      onRevealFolder: function () {
        revealTripFolder(tripId);
      },
      onExportZip: function () {
        exportZip(tripId);
      },
      onPresentFeatured: function () {
        startFeaturedPresent();
      },
      onLlmNarrate: function (btn) {
        startLlmNarrate(root, tripId, btn);
      },
      onApplyLayout: function () {
        applyLayoutRerender(tripId, root);
      },
      mountTemplateControls: function (slot) {
        mountTemplateControls(slot, tripId, { inSheet: true });
      },
      mountCoverStyleControls: function (slot) {
        mountCoverStyleControls(slot, tripId);
      },
      syncCopyDisplayUi: function (container) {
        if (!container) return;
        var html = document.documentElement;
        var photosOnly = html.getAttribute("data-photos-only") === "on";
        var narrativeHidden = html.getAttribute("data-copy-display") === "photos";
        var captionsOn = html.getAttribute("data-caption-display") !== "off";
        container.querySelectorAll("[data-copy-preset]").forEach(function (btn) {
          var on = photosOnly
            ? btn.getAttribute("data-copy-preset") === "photos"
            : btn.getAttribute("data-copy-preset") === "full";
          btn.classList.toggle("is-on", on);
          btn.setAttribute("aria-pressed", on ? "true" : "false");
        });
        var captionChip = container.querySelector('[data-preview-chip="caption"]');
        if (captionChip) {
          captionChip.classList.toggle("is-on", captionsOn);
          captionChip.setAttribute("aria-pressed", captionsOn ? "true" : "false");
          captionChip.textContent = captionsOn ? "图注：开" : "图注：关";
          captionChip.disabled = photosOnly;
        }
        var narrativeChip = container.querySelector('[data-preview-chip="narrative"]');
        if (narrativeChip) {
          narrativeChip.classList.toggle("is-on", !narrativeHidden);
          narrativeChip.setAttribute("aria-pressed", !narrativeHidden ? "true" : "false");
          narrativeChip.textContent = !narrativeHidden ? "导语：显" : "导语：隐";
          narrativeChip.disabled = photosOnly;
        }
      },
      applyCopyPreset: function (preset) {
        applyToolbarCopyPreset(root, preset);
      },
      toggleCaptions: function () {
        toggleToolbarCaptions(root);
      },
      toggleNarrative: function () {
        toggleToolbarNarrative(root);
      },
      trapFocus: function (el) {
        return trapDrawerFocus(el);
      },
      refreshAdvancedOptions: function (panel) {
        if (!panel) return;
        drawers.refreshEntry().then(function (data) {
          var count = (data && data.intentSummary && data.intentSummary.featuredCount) || 0;
          panel.querySelectorAll(".preview-sheet__list-item--optional").forEach(function (li) {
            var action = li.querySelector("[data-action]");
            if (!action) return;
            if (action.getAttribute("data-action") === "present") {
              li.hidden = count < 1;
            }
          });
        });
        fetch("/__travelogue/config")
          .then(function (r) { return r.ok ? r.json() : null; })
          .then(function (cfg) {
            if (!cfg || !cfg.llmAvailable) return;
            panel.querySelectorAll(".preview-sheet__list-item--optional").forEach(function (li) {
              var action = li.querySelector('[data-action="llm"]');
              if (action) li.hidden = false;
            });
          })
          .catch(function () {});
      },
    };

    fetch("/__travelogue/config")
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (cfg) {
        cohortEnabled = !!(cfg && cfg.cohort && cfg.cohort.enabled);
      })
      .catch(function () {});

    root._taskDock = mountPreviewTaskDock(root, {
onCancelExport: function () {
        cancelPreviewLongshotExport(root);
        root._exportDockActive = false;
        root._taskDock.hide();
      },
      onRevealFolder: function (relPath, tid) {
        revealTripPath(tid || tripId, relPath);
      },
      onCopyPath: function (text) {
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(text).then(function () {
            showToolbarToast("路径已复制");
          }).catch(function () {
            showToolbarToast(text);
          });
        } else {
          showToolbarToast(text);
        }
      },
      onApplyLayout: function () {
        applyLayoutRerender(tripId, root);
      },
      onDismissPending: function () {
        _pendingDockDismissed = true;
        refreshTaskDockState(root);
      },
      onOpenStructure: function () {
        if (root._sheet) root._sheet.open("structure");
      },
      onConfirmStructure: function () {
        drawers.confirmStructure();
      },
      onDismissG1: function () {
        _g1DockDismissed = true;
        refreshTaskDockState(root);
      },
      onResultDismissed: function () {
        root._exportResultShowing = false;
        refreshTaskDockState(root);
      },
    });

    root._sheet = mountPreviewUnifiedSheet(root, sheetHooks);
    initG1V3(root, tripId, drawers, root._sheet);
    initDisplayedAestheticTitles(tripId);

    var exportWrap = document.createElement("div");
    exportWrap.className = "preview-toolbar__export-zone-wrap";

    var exportZone = document.createElement("div");
    exportZone.className = "preview-toolbar__export-zone";

    var longshotBtn = document.createElement("button");
    longshotBtn.type = "button";
    longshotBtn.className =
      "preview-toolbar__longshot preview-toolbar__longshot--v3 preview-toolbar__longshot--idle";
    if (isPreviewToolbarV4(root)) {
      longshotBtn.className +=
        " preview-toolbar__dock-btn preview-toolbar__dock-btn--export";
      longshotBtn.innerHTML = dockLongshotIconHtml("idle");
      longshotBtn.setAttribute("aria-label", "导出长图");
    } else {
      longshotBtn.textContent = "导出长图";
    }

    exportZone.appendChild(longshotBtn);
    exportWrap.appendChild(exportZone);
    var menuWrap = actions.querySelector(".preview-toolbar__menu-wrap");
    if (isPreviewToolbarV4(root)) {
      insertScreenplayControl(actions, menuWrap, { label: "▶", v3: true, dock: true });
      var exportDivider = document.createElement("span");
      exportDivider.className = "preview-toolbar__dock-divider";
      exportDivider.setAttribute("aria-hidden", "true");
      actions.appendChild(exportDivider);
      actions.appendChild(exportWrap);
    } else {
      actions.insertBefore(exportWrap, menuWrap);
      insertScreenplayControl(actions, menuWrap, { label: "放映", v3: true });
    }

    setLongshotExportState(root, "idle");

    longshotBtn.addEventListener("click", function () {
      startLongshot(root, tripId);
    });

    if (window.location.search.indexOf("focus=longshot") >= 0) {
      requestAnimationFrame(function () {
        longshotBtn.focus();
        longshotBtn.classList.add("preview-toolbar__longshot--focus");
      });
    }

    refreshStaleHint(root, tripId);
    refreshPreviewCover(root);
    fetchEntry(tripId).then(function (data) {
      initFeaturedStars(tripId);
      initCollageMediaControls(tripId, (data && data.assetMediaById) || {});
    });

    window.addEventListener("travelogue:copy-saved", function () {
      showStaleHint(root);
    });

    if (isPreviewToolbarV4(root)) {
      initDockTooltips(root);
      initDockScrollFade(root);
      initCoverTitleEdit(tripId);
    }

    maybeShowCoverOpeningStyleToast(tripId);
    syncToolbarHeight(root);
  }


  function init() {
    if (isSharePreview()) {
      initShareMinimal();
      return;
    }

    document.documentElement.setAttribute("data-preview-toolbar", "on");

    var root = document.createElement("div");
    root.className = "preview-toolbar preview-toolbar--v4";
    root.innerHTML =
      '<nav class="preview-toolbar__dock" aria-label="预览快捷操作">' +
      '<a class="preview-toolbar__dock-btn preview-toolbar__dock-btn--back preview-toolbar__ctl" href="/" aria-label="返回" title="返回 Studio 首页">' +
      dockIconSvg("back") +
      "</a>" +
      '<span class="preview-toolbar__dock-divider" aria-hidden="true"></span>' +
      '<div class="preview-toolbar__menu-wrap">' +
      '<button type="button" class="preview-toolbar__menu-btn preview-toolbar__dock-btn preview-toolbar__dock-btn--menu preview-toolbar__dock-btn--folio" aria-haspopup="dialog" aria-expanded="false" aria-label="编辑与设置" title="编辑与设置">' +
      dockIconSvg("settings") +
      "</button>" +
      "</div>" +
      "</nav>";

    document.body.insertBefore(root, document.body.firstChild);
    ensureCoverMobileFootnote();
    var tripId = tripIdFromPath();
    if (!tripId) return;
    initToolbarV3(root, tripId);
  }

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}
