/**
 * Preview toolbar · template, featured, reader mode, cover style UX.
 */
"use strict";

import {
  postJson,
  postJsonConflictRetry,
  patchJsonConflictRetry,
} from "../js/http.js";
import { trackStudioEvent } from "../js/analytics.js";
import { pollJobUntilDone } from "../js/job-poll.js";
import { presentAutoplayHref } from "./dock.js";
import { saveMagazineTitle } from "./inline-edit.js";
import { formatAestheticPurposeLine, isAestheticDebugEnabled } from "./drawers.js";
import {
  revealTripPath,
  refreshStaleHint,
  syncLongshotPreviewRowVisibility,
} from "./longshot.js";
import {
  showToolbarToast,
  toolbarConfirm,
  tripApiBase,
  toolbarBody,
} from "./shell.js";
import { syncInspectChromeVisibility } from "./preview-mode.js";
import {
  activateG1Pending,
  applyLayoutRerender,
  fetchEntry,
  refreshPreviewAfterCopySave,
  refreshTaskDockState,
  setLayoutPending,
  setLayoutPendingMessage,
  syncCoverOpeningStyleInDom,
} from "./core.js";
import { HELP_COPY } from "../js/help-onboarding.js";
import { openHelpDrawer } from "../js/help-drawer.js";

function attachFeaturedHelpLinkOnToast() {
  var el = document.getElementById("preview-toolbar-toast");
  if (!el) return;
  var msg = el.textContent || "";
  el.textContent = "";
  var span = document.createElement("span");
  span.textContent = msg + " · ";
  var btn = document.createElement("button");
  btn.type = "button";
  btn.className = "preview-toolbar__toast-link";
  btn.textContent = HELP_COPY.featuredMoreLink || "了解更多 →";
  btn.addEventListener("click", function (ev) {
    ev.preventDefault();
    ev.stopPropagation();
    openHelpDrawer({ source: "deep_link", itemId: "H2" });
  });
  el.appendChild(span);
  el.appendChild(btn);
}

function showFeaturedRerankDockCue(root) {
  if (!root || !root._taskDock || typeof root._taskDock.showFeaturedRerankCue !== "function") {
    return;
  }
  if (root._exportDockActive) return;
  root._exportResultShowing = true;
  root._taskDock.showFeaturedRerankCue({
    title: HELP_COPY.featuredRerankDockTitle || "已记下精选",
    subtitle: HELP_COPY.featuredRerankDockSub,
    cta: HELP_COPY.featuredRerankCta || "按精选重排",
  });
}

var COVER_OPENING_STYLE_OPTIONS = [];
var READER_VIEW_KEY = "travelogue.studio.readerView";
var _DEFAULT_COVER_STYLE = "veil-footer";


export function toggleAdvancedMenu(root) {
    var menu = root.querySelector(".preview-toolbar__menu");
    if (!menu) return;
    menu.hidden = !menu.hidden;
  }


export function initTitleEdit(root, tripId) {
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


export function initDisplayedAestheticTitles(tripId) {
    if (!isAestheticDebugEnabled()) return;
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


export function initG1V3(root, tripId, drawers, sheet) {
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
        activateG1Pending();
        if (sheet) sheet.setStructureDot(true);
        mountG1Banner(root, drawers);
        refreshTaskDockState(root);
      })
      .catch(function () {});
  }


/** PRD §6.2 · G1 顶栏横幅（M4）；可见时为栈顶主待办，滚出可视区后由 Task Dock 镜像。 */
export function mountG1Banner(root, drawers) {
    if (document.querySelector(".preview-toolbar__g1-banner")) return null;

    var banner = document.createElement("div");
    banner.className = "preview-toolbar__g1-banner";
    if (root && root.classList.contains("preview-toolbar--v4")) {
      banner.classList.add("preview-toolbar__g1-banner--v4");
    }
    banner.setAttribute("role", "status");
    banner.innerHTML =
      '<p class="preview-toolbar__g1-banner-text">章节结构待确认 · 请浏览各章顺序后确认</p>' +
      '<div class="preview-toolbar__g1-banner-actions">' +
      '<button type="button" class="preview-toolbar__g1-banner-confirm">章节顺序 OK</button>' +
      '<button type="button" class="preview-toolbar__g1-banner-regen">重新生成结构</button>' +
      "</div>";

    // v4：挂到 body，固定在 Dock 下方；旧壳：插在 toolbar body 内
    if (banner.classList.contains("preview-toolbar__g1-banner--v4")) {
      document.body.appendChild(banner);
    } else {
      var body = toolbarBody(root);
      if (!body) {
        document.body.appendChild(banner);
      } else {
        var bar = body.querySelector(".preview-toolbar__bar");
        if (bar && bar.nextSibling) {
          body.insertBefore(banner, bar.nextSibling);
        } else {
          body.appendChild(banner);
        }
      }
    }

    var confirmBtn = banner.querySelector(".preview-toolbar__g1-banner-confirm");
    var regenBtn = banner.querySelector(".preview-toolbar__g1-banner-regen");
    if (confirmBtn) {
      confirmBtn.addEventListener("click", function () {
        if (drawers && typeof drawers.confirmStructure === "function") {
          drawers.confirmStructure();
        }
      });
    }
    if (regenBtn) {
      regenBtn.addEventListener("click", function () {
        if (drawers && typeof drawers.regenerateStructure === "function") {
          drawers.regenerateStructure();
        }
      });
    }

    // 横幅在视口内时不抢 Task Dock；滚出后恢复 G1 镜像
    if (typeof IntersectionObserver !== "undefined" && root) {
      var io = new IntersectionObserver(
        function (entries) {
          var visible = entries[0] && entries[0].isIntersecting;
          root._g1BannerVisible = !!visible;
          refreshTaskDockState(root);
        },
        { threshold: 0.2 }
      );
      io.observe(banner);
      root._g1BannerObs = io;
      root._g1BannerVisible = true;
    } else if (root) {
      root._g1BannerVisible = true;
    }

    return banner;
  }


/** @deprecated 使用 mountG1Banner；保留别名以免外部引用断裂 */
export function initG1Banner(root, tripId, drawers) {
    mountG1Banner(root, drawers);
  }


export function startFeaturedPresent() {
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


export function initCollageMediaControls(tripId, assetMediaById) {
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
          setLayoutPendingMessage("版面有改动");
          showToolbarToast(
            mediaClass === "collage"
              ? "已标记为拼图 · 点更新版面后生效"
              : "已标记为普通照片 · 点更新版面后生效"
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
    syncInspectChromeVisibility();
  }


export function initFeaturedStars(tripId) {
    var screens = document.querySelectorAll('.layout-screen[data-block="layout-screen"][data-asset-ids]');
    screens.forEach(function (screen) {
      if (screen.querySelector(".preview-toolbar__featured-star")) return;
      var raw = screen.getAttribute("data-asset-ids") || "";
      var assetId = raw.split(",")[0];
      if (!assetId) return;

      var star = document.createElement("button");
      star.type = "button";
      star.className = "preview-toolbar__featured-star";
      star.textContent = "★";
      var initiallyOn = screen.getAttribute("data-featured") === "true";
      if (initiallyOn) {
        star.classList.add("preview-toolbar__featured-star--on");
        star.setAttribute("aria-pressed", "true");
        star.setAttribute("aria-label", "取消精选");
      } else {
        star.setAttribute("aria-pressed", "false");
        star.setAttribute("aria-label", "标为精选");
      }
      star.addEventListener("click", function (e) {
        e.preventDefault();
        e.stopPropagation();
        if (star.disabled) return;
        var isOn = star.classList.contains("preview-toolbar__featured-star--on");
        trackStudioEvent("featured_star_click", {
          panel_open: document.body.classList.contains("preview-sheet-open"),
          action: isOn ? "demote" : "promote",
        });
        star.disabled = true;
        var body = {
          assetIds: [assetId],
          rerender: false,
        };
        if (isOn) body.tier = "material";
        postJsonConflictRetry(tripApiBase(tripId) + "/promote-tier", body)
          .then(function (res) {
            star.disabled = false;
            if (res.status !== 200 || !res.body.ok) {
              showToolbarToast((res.body && res.body.error) || "标记失败", { error: true });
              return;
            }
            if (isOn) {
              star.classList.remove("preview-toolbar__featured-star--on");
              star.setAttribute("aria-pressed", "false");
              star.setAttribute("aria-label", "标为精选");
              screen.removeAttribute("data-featured");
              showToolbarToast(
                HELP_COPY.featuredDemotedToast || "已取消精选"
              );
              return;
            }
            star.classList.add("preview-toolbar__featured-star--on");
            star.setAttribute("aria-pressed", "true");
            star.setAttribute("aria-label", "取消精选");
            screen.setAttribute("data-featured", "true");
            // D-FEED-03 · 3a：纯 ★ 不置导出拦截 pending（意图类，非渲染类）
            showToolbarToast(
              HELP_COPY.featuredPromotedToast ||
                "已标为精选 · 会优先出现在『放映精选』",
              { duration: 5200 }
            );
            attachFeaturedHelpLinkOnToast();
            var toolbar =
              (screen.closest && screen.closest(".preview-toolbar")) ||
              document.querySelector(".preview-toolbar");
            showFeaturedRerankDockCue(toolbar);
          })
          .catch(function () {
            star.disabled = false;
            showToolbarToast("标记失败", { error: true });
          });
      });
      screen.style.position = screen.style.position || "relative";
      screen.appendChild(star);
    });
    syncInspectChromeVisibility();
  }

/**
 * D-FEED-04 · 按精选重排：确认后 POST /curate（与「更新版面」分权）。
 * @returns {Promise<boolean>}
 */
export function runFeaturedRerank(tripId, root) {
  var coverBefore = "";
  return fetchEntry(tripId)
    .then(function (entry) {
      entry = entry || {};
      coverBefore = String(entry.coverAssetId || "");
      var locked = entry.pipelineStatus === "structure_locked";
      trackStudioEvent("help_funnel_tier_rerank_open", {
        structure_locked: locked,
      });
      var body =
        (HELP_COPY.featuredRerankBody ||
          "将按你标过的精选重新选片排版，封面、章首或部分屏构图可能变化。") +
        (locked
          ? "\n\n" +
            (HELP_COPY.featuredRerankLockedNote ||
              "当前结构已锁定，继续将解锁并可能改动章序相关结果。")
          : "");
      return toolbarConfirm({
        title: HELP_COPY.featuredRerankTitle || "按精选重新排版？",
        body: body,
        confirmText: HELP_COPY.featuredRerankConfirm || "重新排版",
        cancelText: "取消",
        danger: true,
      }).then(function (ok) {
        return { ok: !!ok, locked: locked };
      });
    })
    .then(function (gate) {
      if (!gate || !gate.ok) {
        trackStudioEvent("help_funnel_tier_rerank_cancel", {
          structure_locked: !!(gate && gate.locked),
        });
        return false;
      }
      trackStudioEvent("help_funnel_tier_rerank_confirm", {
        structure_locked: gate.locked,
      });
      if (root) root._exportResultShowing = false;
      showToolbarToast(HELP_COPY.featuredRerankBusy || "正在按精选重新排版…", {
        duration: 4000,
      });
      if (root && root._taskDock && typeof root._taskDock.updateExporting === "function") {
        root._taskDock.updateExporting({
          title: "正在按精选重新排版…",
          subtitle: "完成后将刷新预览",
          pct: 8,
        });
        root._exportDockActive = true;
      }
      return postJson("/__travelogue/trips/" + encodeURIComponent(tripId) + "/curate", {
        force: true,
        reason: "tier_rerank",
      }).then(function (res) {
        if (!(res.status === 202 && res.body && res.body.jobId)) {
          if (root && root._taskDock) root._taskDock.hide();
          root && (root._exportDockActive = false);
          showToolbarToast(
            (res.body && (res.body.message || res.body.error)) || "无法开始重新排版",
            { error: true }
          );
          trackStudioEvent("help_funnel_tier_rerank_fail", { stage: "start" });
          return false;
        }
        return pollJobUntilDone(res.body.jobId, {
          intervalMs: 800,
          onTick: function (job) {
            if (
              root &&
              root._taskDock &&
              typeof root._taskDock.updateExporting === "function" &&
              job &&
              job.stageHint
            ) {
              root._taskDock.updateExporting({
                title: "正在按精选重新排版…",
                subtitle: String(job.stageHint),
                pct: Math.min(90, 10 + (job.progress || 0) * 0.8),
              });
            }
          },
        }).then(function (job) {
          if (root && root._taskDock) root._taskDock.hide();
          root && (root._exportDockActive = false);
          if (!job || job.status !== "succeeded") {
            showToolbarToast("重新排版失败", { error: true });
            trackStudioEvent("help_funnel_tier_rerank_fail", { stage: "job" });
            return false;
          }
          return fetchEntry(tripId)
            .then(function (after) {
              var coverAfter = String((after && after.coverAssetId) || "");
              var coverChanged = !!(
                coverBefore &&
                coverAfter &&
                coverBefore !== coverAfter
              );
              trackStudioEvent("help_funnel_tier_rerank_success", {
                cover_changed: coverChanged,
              });
              showToolbarToast(
                coverChanged
                  ? HELP_COPY.featuredRerankDoneCover || "排版已更新 · 封面已更换"
                  : HELP_COPY.featuredRerankDone || "排版已更新",
                { duration: 2200 }
              );
              window.setTimeout(function () {
                window.location.reload();
              }, 600);
              return true;
            })
            .catch(function () {
              trackStudioEvent("help_funnel_tier_rerank_success", {
                cover_changed: false,
              });
              showToolbarToast(HELP_COPY.featuredRerankDone || "排版已更新");
              window.location.reload();
              return true;
            });
        });
      });
    })
    .catch(function () {
      if (root && root._taskDock) root._taskDock.hide();
      root && (root._exportDockActive = false);
      showToolbarToast("无法开始重新排版", { error: true });
      trackStudioEvent("help_funnel_tier_rerank_fail", { stage: "network" });
      return false;
    });
}


export function revealTripFolder(tripId) {
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


export function readCoverOpeningStyleFromDom() {
    var section = document.querySelector(".cover-opening[data-cover-opening]");
    return section ? section.getAttribute("data-cover-opening") || _DEFAULT_COVER_STYLE : _DEFAULT_COVER_STYLE;
  }


export function mountCoverStyleControls(slot, tripId, opts) {
    opts = opts || {};
    if (!slot || slot.querySelector(".preview-sheet__cover-styles")) return;
    var section = document.createElement("div");
    section.className = "preview-sheet__section preview-sheet__cover-section";
    section.innerHTML =
      '<span class="preview-sheet__label">封面版式</span>' +
      '<p class="preview-sheet__hint preview-sheet__hint--compact">电脑预览有效；窄屏与手机版式不同。更换版式默认会重荐封面图。</p>' +
      '<div class="preview-sheet__cover-styles" role="group" aria-label="封面版式"></div>' +
      '<p class="preview-sheet__cover-blurb" hidden></p>' +
      '<label class="preview-sheet__cover-keep-label">' +
      '<input type="checkbox" class="preview-sheet__cover-keep-check" />' +
      ' 更换时保留当前封面图</label>' +
      '<p class="preview-sheet__cover-fit-hint" hidden></p>';
    var group = section.querySelector(".preview-sheet__cover-styles");
    var blurbEl = section.querySelector(".preview-sheet__cover-blurb");
    var fitHintEl = section.querySelector(".preview-sheet__cover-fit-hint");
    var keepCheck = section.querySelector(".preview-sheet__cover-keep-check");
    var selectedStyle = readCoverOpeningStyleFromDom();
    var options = COVER_OPENING_STYLE_OPTIONS.slice();

    function syncSelection(style) {
      if (!group) return;
      group.querySelectorAll("[data-cover-style]").forEach(function (btn) {
        var on = btn.getAttribute("data-cover-style") === style;
        btn.classList.toggle("is-on", on);
        btn.setAttribute("aria-pressed", on ? "true" : "false");
      });
      if (blurbEl) {
        var hit = options.filter(function (o) { return o.id === style; })[0];
        if (hit && hit.blurb) {
          blurbEl.hidden = false;
          blurbEl.textContent = hit.blurb;
        } else {
          blurbEl.hidden = true;
          blurbEl.textContent = "";
        }
      }
    }

    function setBusy(busy) {
      if (!group) return;
      group.querySelectorAll("[data-cover-style]").forEach(function (btn) {
        btn.disabled = !!busy;
      });
      if (keepCheck) keepCheck.disabled = !!busy;
    }

    function applyStyleChange(next, keepCover) {
      setBusy(true);
      if (fitHintEl) {
        fitHintEl.hidden = true;
        fitHintEl.textContent = "";
      }
      // Nested under Bookends: route through repick-opening for closing cascade (R-BE-14)
      if (opts.viaBookends && typeof opts.applyStyleViaBookends === "function") {
        return Promise.resolve(opts.applyStyleViaBookends(next, keepCover))
          .then(function (ok) {
            setBusy(false);
            if (ok === false) return;
            selectedStyle = next;
            syncSelection(next);
            syncCoverOpeningStyleInDom(next);
            trackStudioEvent("cover_opening_style_change", {
              tripId: tripId,
              coverOpeningStyle: next,
              viaBookends: true,
              repickCover: !keepCover,
            });
          })
          .catch(function () {
            setBusy(false);
            showToolbarToast("保存失败", { error: true });
          });
      }
      postJsonConflictRetry(tripApiBase(tripId) + "/save-copy", {
        patches: [{ path: "meta.coverOpeningStyle", value: next }],
        repickCover: !keepCover,
        keepCover: !!keepCover,
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
            repickCover: !keepCover,
          });
          showToolbarToast(
            keepCover ? "封面版式已更新（保留当前封面图）" : "封面版式已更新，并重荐了封面图"
          );
          if (keepCover && fitHintEl && res.body.fitBelowThreshold) {
            fitHintEl.hidden = false;
            fitHintEl.textContent = "当前封面图可能不太适合此版式";
          }
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
    }

    function renderOptions(list) {
      if (!group) return;
      group.innerHTML = "";
      options = list && list.length ? list : options;
      options.forEach(function (opt) {
        var btn = document.createElement("button");
        btn.type = "button";
        btn.className = "preview-sheet__cover-style";
        btn.setAttribute("data-cover-style", opt.id);
        btn.setAttribute("aria-label", opt.label);
        if (opt.blurb) btn.title = opt.blurb;
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
          var keep = !!(keepCheck && keepCheck.checked);
          applyStyleChange(next, keep);
        });
        group.appendChild(btn);
      });
      syncSelection(selectedStyle);
    }

    renderOptions(options);
    slot.appendChild(section);

    fetchEntry(tripId)
      .then(function (data) {
        if (data && Array.isArray(data.coverStyleOptions) && data.coverStyleOptions.length) {
          renderOptions(data.coverStyleOptions);
        }
        if (data && data.coverOpeningStyle) {
          selectedStyle = data.coverOpeningStyle;
          syncSelection(selectedStyle);
        }
      })
      .catch(function () {});

    trackStudioEvent("cover_opening_style_selector_impression", {
      surface: "preview-sheet",
      tripId: tripId,
      coverOpeningStyle: selectedStyle,
    });
  }


export function mountTemplateControls(slot, tripId, opts) {
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
              showToolbarToast("模板已更新，正在更新版面…", { duration: 2500 });
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


export function initTemplateBadge(root, tripId) {
    var bar = root.querySelector(".preview-toolbar__bar");
    var cluster = bar && bar.querySelector(".preview-toolbar__cluster");
    if (!cluster) return;
    mountTemplateControls(cluster, tripId, { inSheet: false });
  }


export function snapshotReadingPayload() {
    var reading = window.__TRAVELOGUE_READING__;
    if (!reading || typeof reading !== "object") return null;
    try {
      return JSON.parse(JSON.stringify(reading));
    } catch (e) {
      return null;
    }
  }


export function applyReaderSurfaceMode(readerMode) {
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


export function initPreviewModeSeg(root, actions) {
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
