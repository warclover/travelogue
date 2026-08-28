/**
 * Preview toolbar · template, featured, reader mode, cover style UX.
 */
"use strict";

import {
  postJson,
  patchJson,
  postJsonConflictRetry,
  patchJsonConflictRetry,
} from "../js/http.js";
import { trackStudioEvent } from "../js/analytics.js";
import { pollJobUntilDone } from "../js/job-poll.js";
import { presentAutoplayHref } from "./dock.js";
import { saveMagazineTitle, saveMagazineTitleValue } from "./inline-edit.js";
import { formatAestheticPurposeLine, isAestheticDebugEnabled } from "./drawers.js";
import {
  revealTripFolder,
  refreshStaleHint,
  syncLongshotPreviewRowVisibility,
} from "./longshot.js";
import {
  showToolbarToast,
  toolbarConfirm,
  tripApiBase,
  toolbarBody,
  reloadPreviewAfterLayout,
} from "./shell.js";
import { syncInspectChromeVisibility, setOpeningUpdateBusy } from "./preview-mode.js";
import {
  activateG1Pending,
  applyLayoutRerender,
  fetchEntry,
  refreshPreviewAfterCopySave,
  refreshTaskDockState,
  setLayoutPending,
  setLayoutPendingMessage,
} from "./core.js";
import { HELP_COPY } from "../js/help-onboarding.js";
import { openHelpDrawer } from "../js/help-drawer.js";
import {
  coverNameEmptyToast,
  coverNameLabel,
  coverNameTooLongToast,
  coverTitleEditLabel,
  isPortfolioEdition,
  readEditionFromDom,
} from "../js/portfolio-export-logic.js";
import {
  editionCardOptionsForPipeline,
  editionSwitchConfirm,
  isRadioNavKey,
  nextRadioId,
  normalizeEdition,
  pageCountChipOptions,
  radioTabIndex,
  recommendPageCount,
  renderPortfolioPageCountChips,
  selectedPageCountChip,
  shouldConfirmThinTier,
  thinTierConfirm,
  shouldMountEditionType,
  portfolioRefineIdentitySpec,
} from "../js/portfolio-edition-logic.js";

export { revealTripFolder };

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
/** 路线 C 勾选偏好：缺省优先 AI；用户取消后记 "0"，再勾回记 "1"。 */
var TITLE_ART_ROUTE_C_PREF_KEY = "travelogue.studio.titleArtRouteC";
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
    display.title = coverTitleEditLabel(readEditionFromDom(document));
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
        var summary = data && data.intentSummary;
        var shown = summary
          ? String(summary.displayTitle || "").trim()
          : "";
        if (shown) setTitle(shown);
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

      var imeComposing = false;
      var finished = false;
      function finish(save) {
        if (finished) return;
        if (save && (imeComposing || input.isComposing)) return;
        finished = true;
        var next = (input.value || "").trim();
        input.remove();
        display.hidden = false;
        if (!save) {
          setTitle(display.dataset.title || display.textContent);
          return;
        }
        if (next.length > 20) {
          showToolbarToast(coverNameTooLongToast(readEditionFromDom(document)), {
            error: true,
          });
          return;
        }
        if (!next) {
          showToolbarToast(coverNameEmptyToast(readEditionFromDom(document)), {
            error: true,
          });
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

      input.addEventListener("compositionstart", function () {
        imeComposing = true;
      });
      input.addEventListener("compositionend", function () {
        imeComposing = false;
      });
      input.addEventListener("keydown", function (e) {
        if (e.key === "Enter") {
          if (e.isComposing || imeComposing) {
            e.preventDefault();
            return;
          }
          e.preventDefault();
          finish(true);
        }
        if (e.key === "Escape") {
          e.preventDefault();
          finish(false);
        }
      });
      input.addEventListener("blur", function () {
        if (imeComposing || input.isComposing) return;
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


/**
 * Preview Chrome Unify · D-PCU-07～11
 * - 默认：无黄条/底舱；旧 pending 静默 auto-confirm
 * - 实验 ON：自动开分章面板，维持 pending，禁止黄条
 */
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
        if (!cfg || !entry) return;
        var experimentOn = !!(cfg.studio && cfg.studio.g1ConfirmStructure);

        if (entry.g1Pending && !experimentOn) {
          // D-PCU-11 · 旧 trip 静默锁定，禁止幽灵 pending
          return patchJson(
            "/__travelogue/trips/" + encodeURIComponent(tripId) + "/pipeline",
            { status: "structure_locked", continuePipeline: true }
          ).then(function (res) {
            trackStudioEvent("pcu_legacy_g1_autoconfirm", {
              tripId: tripId,
              ok: !!(res && res.status >= 200 && res.status < 300),
            });
            if (typeof root._maybeShowChapterHint === "function") {
              root._maybeShowChapterHint();
            }
          });
        }

        if (entry.g1Pending && experimentOn) {
          activateG1Pending();
          // 禁止 Task Dock 镜像黄条
          root._g1BannerVisible = true;
          if (sheet) sheet.setStructureDot(true);
          if (typeof root._openChapterPanel === "function") {
            root._openChapterPanel({ auto: true, pending: true });
          } else if (drawers && typeof drawers.openStructure === "function") {
            drawers.openStructure();
          }
          return;
        }

        if (typeof root._maybeShowChapterHint === "function") {
          root._maybeShowChapterHint();
        }
      })
      .catch(function () {});
  }


/** @deprecated D-PCU：默认路径不再挂黄条；保留函数供测试/实验逃生。 */
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
        label.textContent = "照片类型";
        var sel = document.createElement("select");
        sel.className = "preview-toolbar__collage-select";
        sel.setAttribute("aria-label", "改成拼图或改回单张");
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
        scope: "tier",
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
        scope: "tier",
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


export function readCoverOpeningStyleFromDom() {
    var section = document.querySelector(".cover-opening[data-cover-opening]");
    return section ? section.getAttribute("data-cover-opening") || _DEFAULT_COVER_STYLE : _DEFAULT_COVER_STYLE;
  }

/** LVP M2 · 成册风格两卡（精修 · 画册） */
var _LVP_DEFAULT_OPTIONS = [
  {
    id: "magazine_default",
    label: "杂志成册（推荐）",
    consequence: "宽画幅节奏稳，单反 3:2 少进扁四宫",
    badge: "推荐",
  },
  {
    id: "fit_photo_experimental",
    label: "更贴照片比例（实验）",
    consequence: "加权拼图轨道更贴原图，章节页数可能变",
    badge: "实验",
  },
];

var LVP_HINT_KEY = "travelogue.layoutVibeHint.";
var LVP_HINT_OFF_KEY = "travelogue.layoutVibeHint.off";
var LVP_HINT_PENDING_KEY = "travelogue.layoutVibeHintPending.";

export function markLayoutVibeHintPending(tripId) {
  if (!tripId) return;
  try {
    sessionStorage.setItem(LVP_HINT_PENDING_KEY + tripId, "1");
  } catch (_e) {}
}

export function mountLayoutVibeControls(slot, tripId, opts) {
  opts = opts || {};
  var rootEarly = opts.root || document.querySelector(".preview-toolbar") || document.body;
  if (rootEarly && rootEarly._layoutVibeVisible === false) return;
  if (!slot || slot.querySelector(".preview-sheet__layout-vibes")) return;
  var section = document.createElement("div");
  section.className = "preview-sheet__section preview-sheet__layout-vibe-section";
  section.innerHTML =
    '<span class="preview-sheet__label">成册风格</span>' +
    '<p class="preview-sheet__hint preview-sheet__hint--compact">整本排版气质。推荐更稳；实验更贴照片比例，页数可能变。' +
    '<button type="button" class="preview-sheet__text-link" data-lvp-help>了解更多</button></p>' +
    '<div class="preview-sheet__layout-vibes" role="group" aria-label="成册风格"></div>' +
    '<p class="preview-sheet__hint preview-sheet__hint--compact">' +
    '<button type="button" class="preview-sheet__text-link" data-lvp-dismiss-hint>不再提示成册风格引导</button></p>';
  var group = section.querySelector(".preview-sheet__layout-vibes");
  var selected = "magazine_default";
  var options = _LVP_DEFAULT_OPTIONS.slice();
  var root = opts.root || document.querySelector(".preview-toolbar") || document.body;
  var helpBtn = section.querySelector("[data-lvp-help]");
  var dismissHintBtn = section.querySelector("[data-lvp-dismiss-hint]");
  if (helpBtn) {
    helpBtn.addEventListener("click", function (ev) {
      ev.preventDefault();
      openHelpDrawer({ source: "layout_vibe", itemId: "H8" });
    });
  }
  if (dismissHintBtn) {
    dismissHintBtn.addEventListener("click", function () {
      try {
        localStorage.setItem(LVP_HINT_OFF_KEY, "1");
      } catch (_eOff) {}
      showToolbarToast("已关闭成册风格引导");
      trackStudioEvent("layout_vibe_hint_dismiss", { tripId: tripId });
    });
  }

  function syncSelection(vibeId) {
    if (!group) return;
    group.querySelectorAll("[data-layout-vibe]").forEach(function (btn) {
      var on = btn.getAttribute("data-layout-vibe") === vibeId;
      btn.classList.toggle("is-on", on);
      btn.setAttribute("aria-pressed", on ? "true" : "false");
    });
  }

  function setBusy(busy) {
    if (!group) return;
    group.querySelectorAll("[data-layout-vibe]").forEach(function (btn) {
      btn.disabled = !!busy;
    });
  }

  function applyVibe(next, confirmedExperimental) {
    setBusy(true);
    showToolbarToast("正在按成册风格更新版面…", { duration: 3500 });
    if (root && root._taskDock && typeof root._taskDock.updateExporting === "function") {
      root._taskDock.updateExporting({
        title: "正在按成册风格更新版面…",
        subtitle: "完成后将刷新预览",
        pct: 8,
      });
      root._exportDockActive = true;
    }
    function clearDock() {
      if (root && root._taskDock && typeof root._taskDock.hide === "function") {
        root._taskDock.hide();
      }
      if (root) root._exportDockActive = false;
    }
    return postJson("/__travelogue/trips/" + encodeURIComponent(tripId) + "/layout-vibe", {
      layoutVibe: next,
      confirmedExperimental: !!confirmedExperimental,
    })
      .then(function (res) {
        if (res.status === 400 && res.body && res.body.error === "E_LVP_CONFIRM_REQUIRED") {
          setBusy(false);
          clearDock();
          return false;
        }
        if (!(res.status === 202 && res.body && res.body.jobId)) {
          setBusy(false);
          clearDock();
          showToolbarToast(
            (res.body && (res.body.message || res.body.error)) || "无法更新成册风格",
            { error: true }
          );
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
                title: "正在按成册风格更新版面…",
                subtitle: String(job.stageHint),
                pct: Math.min(90, 10 + (job.progress || 0) * 0.8),
              });
            }
          },
        }).then(function (job) {
          setBusy(false);
          clearDock();
          if (!job || job.status !== "succeeded") {
            showToolbarToast("成册风格更新失败", { error: true });
            return false;
          }
          selected = next;
          syncSelection(selected);
          trackStudioEvent("layout_vibe_change", {
            tripId: tripId,
            layoutVibe: next,
          });
          showToolbarToast("成册风格已更新");
          reloadPreviewAfterLayout();
          return true;
        });
      })
      .catch(function () {
        setBusy(false);
        clearDock();
        showToolbarToast("成册风格更新失败", { error: true });
        return false;
      });
  }

  function requestVibe(next) {
    if (!next || next === selected) return;
    if (next === "fit_photo_experimental") {
      // AC-LVP-05 · 实验无二次确认不可保存
      toolbarConfirm({
        title: "改用「更贴照片比例」？",
        body:
          "拼图会更贴原图比例，章节页数或篇幅可能变化。随时可在「成册风格」改回「杂志成册（推荐）」。",
        confirmText: "使用实验风格",
        cancelText: "取消",
      }).then(function (ok) {
        if (!ok) {
          trackStudioEvent("layout_vibe_experimental_cancel", { tripId: tripId });
          return;
        }
        applyVibe(next, true);
      });
      return;
    }
    applyVibe(next, false);
  }

  function renderOptions(list) {
    if (!group) return;
    group.innerHTML = "";
    options = list && list.length ? list : options;
    options.forEach(function (opt) {
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "preview-sheet__layout-vibe";
      btn.setAttribute("data-layout-vibe", opt.id);
      btn.setAttribute("aria-label", opt.label);
      var badge = opt.badge
        ? '<span class="preview-sheet__layout-vibe-badge">' + opt.badge + "</span>"
        : "";
      btn.innerHTML =
        '<span class="preview-sheet__layout-vibe-title">' +
        opt.label +
        badge +
        "</span>" +
        '<span class="preview-sheet__layout-vibe-consequence">' +
        (opt.consequence || "") +
        "</span>";
      btn.addEventListener("click", function () {
        requestVibe(opt.id);
      });
      group.appendChild(btn);
    });
    syncSelection(selected);
  }

  renderOptions(options);
  slot.appendChild(section);

  fetchEntry(tripId)
    .then(function (data) {
      if (data && Array.isArray(data.layoutVibeOptions) && data.layoutVibeOptions.length) {
        renderOptions(data.layoutVibeOptions);
      }
      if (data && data.layoutVibe) {
        selected = data.layoutVibe;
        syncSelection(selected);
      }
    })
    .catch(function () {});

  trackStudioEvent("layout_vibe_selector_impression", {
    surface: "preview-sheet-book",
    tripId: tripId,
    layoutVibe: selected,
  });
}

export function mountEditionControls(slot, tripId, opts) {
  opts = opts || {};
  if (!slot || slot.querySelector(".preview-sheet__editions")) return;
  var section = document.createElement("div");
  section.className = "preview-sheet__section preview-sheet__edition-section";
  section.innerHTML =
    '<span class="preview-sheet__label">成册类型</span>' +
    '<p class="preview-sheet__hint preview-sheet__hint--compact">游记发群长图；作品集出可翻的一本。</p>' +
    '<div class="preview-sheet__editions" role="radiogroup" aria-label="成册类型"></div>' +
    '<div class="preview-sheet__page-count" hidden>' +
    '<span class="preview-sheet__label">页数</span>' +
    '<p class="preview-sheet__hint preview-sheet__hint--compact">生成前系统会按文件夹给一个厚度；多数情况打开看看就能导出。精修改封面和成册类型。</p>' +
    '<div class="preview-sheet__chip-row" role="group" aria-label="页数"></div>' +
    '<p class="preview-sheet__hint preview-sheet__hint--compact" data-page-count-hint hidden></p>' +
    "</div>";
  var group = section.querySelector(".preview-sheet__editions");
  /** @type {HTMLElement | null} */
  var pageHost = section.querySelector(".preview-sheet__page-count");
  /** @type {HTMLElement | null} */
  var pageRow = section.querySelector(".preview-sheet__chip-row");
  /** @type {HTMLElement | null} */
  var pageHint = section.querySelector("[data-page-count-hint]");
  var selected = "journal";
  var selectedPages = "auto";
  var portfolioState = null;
  var pipelineEnabled = false;
  var root = opts.root || document.querySelector(".preview-toolbar") || document.body;

  function syncSelection(editionId) {
    if (!group) return;
    group.querySelectorAll("[data-edition-card]").forEach(function (btn) {
      var id = btn.getAttribute("data-edition-card");
      var on = id === editionId;
      btn.classList.toggle("is-on", on);
      btn.setAttribute("aria-checked", on ? "true" : "false");
      btn.tabIndex = radioTabIndex(editionId, id);
    });
  }

  function focusSelectedEdition() {
    if (!group) return;
    var on = group.querySelector('[data-edition-card="' + selected + '"]');
    if (on && typeof on.focus === "function") on.focus();
  }

  function setBusy(busy) {
    if (group) {
      group.querySelectorAll("[data-edition-card]").forEach(function (btn) {
        btn.disabled = !!busy;
      });
    }
    if (pageRow) {
      pageRow.querySelectorAll("[data-page-count]").forEach(function (btn) {
        btn.disabled = !!busy;
      });
    }
  }

  function syncPageCount(chipId) {
    selectedPages = chipId || "auto";
    if (!pageRow) return;
    pageRow.querySelectorAll("[data-page-count]").forEach(function (btn) {
      var on = btn.getAttribute("data-page-count") === selectedPages;
      btn.classList.toggle("is-on", on);
      btn.setAttribute("aria-pressed", on ? "true" : "false");
    });
  }

  function renderPageCount(portfolio) {
    portfolioState = portfolio || null;
    if (!pageHost || !pageRow) return;
    if (selected !== "portfolio") {
      pageHost.hidden = true;
      return;
    }
    selectedPages = renderPortfolioPageCountChips(
      pageHost instanceof HTMLElement ? pageHost : null,
      pageRow instanceof HTMLElement ? pageRow : null,
      pageHint instanceof HTMLElement ? pageHint : null,
      portfolio,
      { onRequest: requestPageCount }
    );
  }

  function applyEdition(next) {
    setBusy(true);
    showToolbarToast("正在按成册类型重排页面…", { duration: 3500 });
    if (root && root._taskDock && typeof root._taskDock.updateExporting === "function") {
      root._taskDock.updateExporting({
        title: "正在按成册类型重排页面…",
        subtitle: "精选和分组会保留",
        pct: 8,
      });
      root._exportDockActive = true;
    }
    function clearDock() {
      if (root && root._taskDock && typeof root._taskDock.hide === "function") {
        root._taskDock.hide();
      }
      if (root) root._exportDockActive = false;
    }
    return postJson("/__travelogue/trips/" + encodeURIComponent(tripId) + "/edition", {
      edition: next,
      confirmed: true,
    })
      .then(function (res) {
        if (res.status === 200 && res.body && res.body.unchanged) {
          setBusy(false);
          clearDock();
          selected = next;
          syncSelection(selected);
          focusSelectedEdition();
          return true;
        }
        if (!(res.status === 202 && res.body && res.body.jobId)) {
          setBusy(false);
          clearDock();
          showToolbarToast(
            (res.body && (res.body.message || res.body.error)) || "无法切换成册类型",
            { error: true }
          );
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
                title: "正在按成册类型重排页面…",
                subtitle: String(job.stageHint),
                pct: Math.min(90, 10 + (job.progress || 0) * 0.8),
              });
            }
          },
        }).then(function (job) {
          setBusy(false);
          clearDock();
          if (!job || job.status !== "succeeded") {
            showToolbarToast(
              (job && job.error && job.error.message) || "成册类型更新失败",
              { error: true }
            );
            return false;
          }
          selected = next;
          syncSelection(selected);
          focusSelectedEdition();
          renderPageCount(next === "portfolio" ? portfolioState || {} : null);
          if (root) root._edition = next;
          trackStudioEvent("edition_change", { tripId: tripId, edition: next });
          showToolbarToast("页面已按新的成册类型重排");
          reloadPreviewAfterLayout();
          return true;
        });
      })
      .catch(function () {
        setBusy(false);
        clearDock();
        showToolbarToast("成册类型更新失败", { error: true });
        return false;
      });
  }

  function requestEdition(next) {
    next = normalizeEdition(next);
    if (!next || next === selected) return;
    var copy = editionSwitchConfirm(selected, next);
    toolbarConfirm({
      title: copy.title,
      body: copy.body,
      confirmText: copy.confirmText,
      cancelText: copy.cancelText,
    }).then(function (ok) {
      if (!ok) {
        trackStudioEvent("edition_switch_cancel", {
          tripId: tripId,
          from: selected,
          to: next,
        });
        return;
      }
      applyEdition(next);
    });
  }

  function applyPageCount(chipId) {
    var pageCount = chipId === "auto" ? "auto" : Number(chipId);
    setBusy(true);
    showToolbarToast("正在按页数重排页面…", { duration: 3500 });
    if (root && root._taskDock && typeof root._taskDock.updateExporting === "function") {
      root._taskDock.updateExporting({
        title: "正在按页数重排页面…",
        subtitle: "精选和分组会保留",
        pct: 8,
      });
      root._exportDockActive = true;
    }
    function clearDock() {
      if (root && root._taskDock && typeof root._taskDock.hide === "function") {
        root._taskDock.hide();
      }
      if (root) root._exportDockActive = false;
    }
    return postJson("/__travelogue/trips/" + encodeURIComponent(tripId) + "/edition", {
      edition: "portfolio",
      pageCount: pageCount,
    })
      .then(function (res) {
        if (res.status === 200 && res.body && res.body.unchanged) {
          setBusy(false);
          clearDock();
          syncPageCount(chipId);
          return true;
        }
        if (!(res.status === 202 && res.body && res.body.jobId)) {
          setBusy(false);
          clearDock();
          showToolbarToast(
            (res.body && (res.body.message || res.body.error)) || "无法更新页数",
            { error: true }
          );
          return false;
        }
        return pollJobUntilDone(res.body.jobId, { intervalMs: 800 }).then(function (job) {
          setBusy(false);
          clearDock();
          if (!job || job.status !== "succeeded") {
            showToolbarToast("页数更新失败", { error: true });
            return false;
          }
          syncPageCount(chipId);
          trackStudioEvent("page_count_change", { tripId: tripId, pageCount: chipId });
          showToolbarToast("页面已按新的页数重排");
          reloadPreviewAfterLayout();
          return true;
        });
      })
      .catch(function () {
        setBusy(false);
        clearDock();
        showToolbarToast("页数更新失败", { error: true });
        return false;
      });
  }

  function requestPageCount(chipId, opt) {
    if (!chipId || chipId === selectedPages) return;
    if (chipId === "auto") {
      applyPageCount(chipId);
      return;
    }
    var kept = Number(portfolioState && portfolioState.photosKept);
    var cap = Number(opt && opt.capacity);
    var chips =
      (portfolioState &&
        (portfolioState.pageCountChipDetails || portfolioState.pageCountChips)) ||
      [];
    if (!shouldConfirmThinTier(cap, kept)) {
      applyPageCount(chipId);
      return;
    }
    var rec = recommendPageCount(chips, kept);
    var folder = Number(portfolioState && portfolioState.folderCount);
    var copy = thinTierConfirm(
      cap,
      kept,
      rec !== Number(chipId) ? rec : 0,
      folder
    );
    toolbarConfirm({
      title: copy.title,
      body: copy.body,
      confirmText: copy.confirmText,
      cancelText: copy.cancelText,
    }).then(function (ok) {
      if (ok && copy.recommendPages) {
        applyPageCount(String(copy.recommendPages));
        return;
      }
      if (ok && !copy.recommendPages) {
        applyPageCount(chipId);
        return;
      }
      if (!ok && copy.recommendPages) {
        applyPageCount(chipId);
      }
    });
  }

  function renderOptions() {
    if (!group) return;
    group.innerHTML = "";
    editionCardOptionsForPipeline(pipelineEnabled).forEach(function (opt) {
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "preview-sheet__edition";
      btn.setAttribute("data-edition-card", opt.id);
      btn.setAttribute("role", "radio");
      btn.setAttribute("aria-label", opt.label);
      btn.innerHTML =
        '<span class="preview-sheet__edition-title">' +
        opt.label +
        "</span>" +
        '<span class="preview-sheet__edition-consequence">' +
        (opt.consequence || "") +
        "</span>";
      btn.addEventListener("click", function () {
        requestEdition(opt.id);
      });
      btn.addEventListener("keydown", function (e) {
        if (!isRadioNavKey(e.key)) return;
        e.preventDefault();
        var ids = editionCardOptionsForPipeline(pipelineEnabled).map(function (o) {
          return o.id;
        });
        var next = nextRadioId(ids, selected, e.key);
        if (next && next !== selected) requestEdition(next);
      });
      group.appendChild(btn);
    });
    syncSelection(selected);
  }

  section.hidden = true;
  renderOptions();
  slot.appendChild(section);

  fetchEntry(tripId)
    .then(function (data) {
      pipelineEnabled = !!(data && data.portfolioPipelineEnabled === true);
      if (data && data.edition) {
        selected = normalizeEdition(data.edition);
      }
      section.hidden = !shouldMountEditionType(selected, pipelineEnabled);
      renderOptions();
      renderPageCount(data && data.portfolio);
    })
    .catch(function () {});

  bindPortfolioJournalExit(root, tripId);
}

/** F3 · 作品集精修面。禁止走 mountEditionControls 成册类型表。 */
export function mountPortfolioRefineControls(slot, tripId, opts) {
  opts = opts || {};
  if (!slot || slot.querySelector("[data-fxi-refine]")) return;
  var spec = portfolioRefineIdentitySpec(0);
  var section = document.createElement("div");
  section.className = "preview-sheet__section preview-sheet__fxi-refine";
  section.setAttribute("data-fxi-refine", "1");
  section.innerHTML =
    '<span class="preview-sheet__label">' +
    spec.title +
    "</span>" +
    '<p class="preview-sheet__hint preview-sheet__hint--compact">' +
    spec.lead +
    "</p>" +
    '<div class="preview-sheet__page-count">' +
    '<span class="preview-sheet__label">' +
    spec.thicknessLabel +
    ' <span data-fxi-thickness></span></span>' +
    '<div class="preview-sheet__chip-row" role="group" aria-label="' +
    spec.thicknessLabel +
    '"></div>' +
    '<p class="preview-sheet__hint preview-sheet__hint--compact" data-page-count-hint hidden></p>' +
    "</div>" +
    '<p class="preview-sheet__fxi-action">' +
    '<button type="button" class="preview-sheet__fxi-link" data-fxi-to-journal>' +
    spec.action.label +
    "</button></p>";
  var pageHost = section.querySelector(".preview-sheet__page-count");
  var pageRow = section.querySelector(".preview-sheet__chip-row");
  var pageHint = section.querySelector("[data-page-count-hint]");
  var thicknessEl = section.querySelector("[data-fxi-thickness]");
  var selectedPages = "auto";
  var portfolioState = null;
  var root = opts.root || document.querySelector(".preview-toolbar") || document.body;

  function setBusy(busy) {
    if (pageRow) {
      pageRow.querySelectorAll("[data-page-count]").forEach(function (btn) {
        btn.disabled = !!busy;
      });
    }
    var toJ = section.querySelector("[data-fxi-to-journal]");
    if (toJ) toJ.disabled = !!busy;
  }

  function syncPageCount(chipId) {
    selectedPages = chipId || "auto";
    if (!pageRow) return;
    pageRow.querySelectorAll("[data-page-count]").forEach(function (btn) {
      var on = btn.getAttribute("data-page-count") === selectedPages;
      btn.classList.toggle("is-on", on);
      btn.setAttribute("aria-pressed", on ? "true" : "false");
    });
  }

  function applyPageCount(chipId) {
    var pageCount = chipId === "auto" ? "auto" : Number(chipId);
    setBusy(true);
    showToolbarToast("正在按页数重排页面…", { duration: 3500 });
    if (root && root._taskDock && typeof root._taskDock.updateExporting === "function") {
      root._taskDock.updateExporting({
        title: "正在按页数重排页面…",
        subtitle: "精选和分组会保留",
        pct: 8,
      });
      root._exportDockActive = true;
    }
    function clearDock() {
      if (root && root._taskDock && typeof root._taskDock.hide === "function") {
        root._taskDock.hide();
      }
      if (root) root._exportDockActive = false;
    }
    return postJson("/__travelogue/trips/" + encodeURIComponent(tripId) + "/edition", {
      edition: "portfolio",
      pageCount: pageCount,
    })
      .then(function (res) {
        if (res.status === 200 && res.body && res.body.unchanged) {
          setBusy(false);
          clearDock();
          syncPageCount(chipId);
          return true;
        }
        if (!(res.status === 202 && res.body && res.body.jobId)) {
          setBusy(false);
          clearDock();
          showToolbarToast(
            (res.body && (res.body.message || res.body.error)) || "无法更新页数",
            { error: true }
          );
          return false;
        }
        return pollJobUntilDone(res.body.jobId, { intervalMs: 800 }).then(function (job) {
          setBusy(false);
          clearDock();
          if (!job || job.status !== "succeeded") {
            showToolbarToast("页数更新失败", { error: true });
            return false;
          }
          syncPageCount(chipId);
          trackStudioEvent("page_count_change", { tripId: tripId, pageCount: chipId });
          showToolbarToast("页面已按新的页数重排");
          reloadPreviewAfterLayout();
          return true;
        });
      })
      .catch(function () {
        setBusy(false);
        clearDock();
        showToolbarToast("页数更新失败", { error: true });
        return false;
      });
  }

  function requestPageCount(chipId, opt) {
    if (!chipId || chipId === selectedPages) return;
    if (chipId === "auto") {
      applyPageCount(chipId);
      return;
    }
    var kept = Number(portfolioState && portfolioState.photosKept);
    var cap = Number(opt && opt.capacity);
    var chips =
      (portfolioState &&
        (portfolioState.pageCountChipDetails || portfolioState.pageCountChips)) ||
      [];
    if (!shouldConfirmThinTier(cap, kept)) {
      applyPageCount(chipId);
      return;
    }
    var rec = recommendPageCount(chips, kept);
    var folder = Number(portfolioState && portfolioState.folderCount);
    var copy = thinTierConfirm(
      cap,
      kept,
      rec !== Number(chipId) ? rec : 0,
      folder
    );
    toolbarConfirm({
      title: copy.title,
      body: copy.body,
      confirmText: copy.confirmText,
      cancelText: copy.cancelText,
    }).then(function (ok) {
      if (ok && copy.recommendPages) {
        applyPageCount(String(copy.recommendPages));
        return;
      }
      if (ok && !copy.recommendPages) {
        applyPageCount(chipId);
        return;
      }
      if (!ok && copy.recommendPages) {
        applyPageCount(chipId);
      }
    });
  }

  slot.appendChild(section);
  bindPortfolioJournalExit(root, tripId);
  var toJournal = section.querySelector("[data-fxi-to-journal]");
  if (toJournal) {
    toJournal.addEventListener("click", function () {
      if (root && typeof root._onPortfolioToJournal === "function") {
        root._onPortfolioToJournal();
      }
    });
  }

  fetchEntry(tripId)
    .then(function (data) {
      portfolioState = (data && data.portfolio) || null;
      var pages = Number(portfolioState && portfolioState.pageCount) || 0;
      var nextSpec = portfolioRefineIdentitySpec(pages);
      if (thicknessEl) {
        thicknessEl.textContent = nextSpec.thicknessLead
          ? " · " + nextSpec.thicknessLead
          : "";
      }
      selectedPages = renderPortfolioPageCountChips(
        pageHost instanceof HTMLElement ? pageHost : null,
        pageRow instanceof HTMLElement ? pageRow : null,
        pageHint instanceof HTMLElement ? pageHint : null,
        portfolioState,
        { onRequest: requestPageCount }
      );
    })
    .catch(function () {});
}

export function bindPortfolioJournalExit(root, tripId) {
  if (!root || root._onPortfolioToJournal) return;
  root._onPortfolioToJournal = function () {
    var copy = editionSwitchConfirm("portfolio", "journal");
    toolbarConfirm({
      title: copy.title,
      body: copy.body,
      confirmText: copy.confirmText,
      cancelText: copy.cancelText,
    }).then(function (ok) {
      if (!ok) return;
      showToolbarToast("正在改回游记并重排…", { duration: 3500 });
      return postJson("/__travelogue/trips/" + encodeURIComponent(tripId) + "/edition", {
        edition: "journal",
        confirmed: true,
      }).then(function (res) {
        if (res.status === 200 && res.body && res.body.unchanged) {
          return;
        }
        if (!(res.status === 202 && res.body && res.body.jobId)) {
          showToolbarToast(
            (res.body && (res.body.message || res.body.error)) || "无法改回游记",
            { error: true }
          );
          return;
        }
        return pollJobUntilDone(res.body.jobId, { intervalMs: 800 }).then(function (job) {
          if (!job || job.status !== "succeeded") {
            showToolbarToast("改回游记失败", { error: true });
            return;
          }
          showToolbarToast("已改回游记并重排页面");
          reloadPreviewAfterLayout();
        });
      });
    });
  };
}

export function maybeShowLayoutVibeImportHint(tripId, openSheetFn) {
  if (!tripId) return;
  try {
    if (localStorage.getItem(LVP_HINT_OFF_KEY) === "1") return;
    if (localStorage.getItem(LVP_HINT_KEY + tripId) === "1") return;
    // D-LVP-06 · 仅导入完成后打开预览时提示一次
    if (sessionStorage.getItem(LVP_HINT_PENDING_KEY + tripId) !== "1") return;
    sessionStorage.removeItem(LVP_HINT_PENDING_KEY + tripId);
    localStorage.setItem(LVP_HINT_KEY + tripId, "1");
  } catch (_e) {
    return;
  }
  showToolbarToast("可在精修 · 画册选择成册风格（推荐或实验）", {
    duration: 5200,
  });
  trackStudioEvent("layout_vibe_import_hint", { tripId: tripId });
  if (typeof openSheetFn === "function") {
    // soft: toast only; user opens Sheet themselves
  }
}

export function mountCoverStyleControls(slot, tripId, opts) {
    opts = opts || {};
    // RCI · mode=style 仅版式；mode=name 杂志名+生成字体
    var mode = opts.mode === "name" ? "name" : "style";
    if (!slot) return;
    if (mode === "style" && slot.querySelector(".preview-sheet__cover-styles")) return;
    if (mode === "name" && slot.querySelector("[data-cover-name-font]")) return;
    var section = document.createElement("div");
    section.className = "preview-sheet__section preview-sheet__cover-section";
    var nameNoun = coverNameLabel(readEditionFromDom(document));
    var titleArtHtml =
      '<div class="preview-sheet__title-art" data-title-art hidden>' +
      '<p class="preview-sheet__hint preview-sheet__hint--compact">' +
      (isPortfolioEdition(readEditionFromDom(document))
        ? "用书名生成封面字体（此版式支持时生效）。"
        : "用杂志名生成封面字体（此版式支持时生效）。") +
      "</p>" +
      '<p class="preview-sheet__title-art-attr" data-title-art-attr>' +
      (isPortfolioEdition(readEditionFromDom(document))
        ? "用你的书名生成封面字体 · 不生成风景图"
        : "用你的杂志名生成封面字体 · 不生成风景图") +
      "</p>" +
      '<label class="preview-sheet__title-art-routec" data-title-art-routec-label hidden>' +
      '<input type="checkbox" class="preview-sheet__title-art-routec-check" data-title-art-routec-check />' +
      '<span class="preview-sheet__title-art-routec-copy">' +
      '<span class="preview-sheet__title-art-routec-title">优先 AI 手写体</span>' +
      '<span class="preview-sheet__title-art-routec-hint">未通过自动用字库 · 约十几秒</span>' +
      "</span></label>" +
      '<button type="button" class="preview-sheet__ghost preview-sheet__title-art-btn" data-title-art-btn>生成字体</button>' +
      '<p class="preview-sheet__title-art-status" data-title-art-status hidden></p>' +
      "</div>";
    if (mode === "name") {
      section.setAttribute("data-cover-name-font", "1");
      section.innerHTML =
        '<span class="preview-sheet__label">' +
        nameNoun +
        "</span>" +
        '<p class="preview-sheet__hint preview-sheet__hint--compact">先改成你喜欢的名字，再生成封面字体。</p>' +
        '<p class="preview-sheet__cover-name-stale" data-cover-name-stale hidden role="status">' +
        nameNoun +
        "已改 · 旧字体已过期，请重新生成</p>" +
        '<label class="preview-sheet__label" for="preview-cover-magazine-name">' +
        nameNoun +
        "</label>" +
        '<input id="preview-cover-magazine-name" class="preview-sheet__cover-name-input" type="text" maxlength="20" autocomplete="off" placeholder="我的旅途" />' +
        '<p class="preview-sheet__hint preview-sheet__hint--compact preview-sheet__cover-name-meta">' +
        '<span>最多 20 字 · 字体效果宜用更短名字</span>' +
        '<span data-cover-name-count>0/20</span></p>' +
        '<button type="button" class="preview-sheet__ghost" data-cover-name-save hidden>保存名称</button>' +
        '<p class="preview-sheet__hint preview-sheet__hint--compact" data-cover-name-synced hidden>已保存</p>' +
        titleArtHtml;
    } else {
      section.innerHTML =
        '<span class="preview-sheet__label">封面版式</span>' +
        '<p class="preview-sheet__hint preview-sheet__hint--compact">只改封面第一眼样式，不是整本「成册风格」。电脑宽屏（≥1024px）生效；窄屏回落雾底呈现。</p>' +
        '<div class="preview-sheet__cover-styles" role="group" aria-label="封面版式" aria-describedby="preview-cover-legacy-hint"></div>' +
        '<p class="preview-sheet__hint preview-sheet__cover-legacy" id="preview-cover-legacy-hint" hidden></p>' +
        '<p class="preview-sheet__cover-blurb" hidden></p>' +
        '<label class="preview-sheet__cover-keep-label">' +
        '<input type="checkbox" class="preview-sheet__cover-keep-check" />' +
        " 更换时保留当前封面图</label>" +
        '<p class="preview-sheet__cover-fit-hint" hidden></p>' +
        '<p class="preview-sheet__hint preview-sheet__hint--compact">要改整本页面气质 → 「画册 · 成册风格」</p>' +
        (opts.omitTitleArt === false ? titleArtHtml : "");
    }
    var group = section.querySelector(".preview-sheet__cover-styles");
    var legacyEl = section.querySelector(".preview-sheet__cover-legacy");
    var blurbEl = section.querySelector(".preview-sheet__cover-blurb");
    var fitHintEl = section.querySelector(".preview-sheet__cover-fit-hint");
    var keepCheck = section.querySelector(".preview-sheet__cover-keep-check");
    var titleArtBlock = section.querySelector("[data-title-art]");
    var titleArtAttr = section.querySelector("[data-title-art-attr]");
    var titleArtRouteCLabel = section.querySelector("[data-title-art-routec-label]");
    var titleArtRouteCCheck = section.querySelector("[data-title-art-routec-check]");
    var titleArtBtn = section.querySelector("[data-title-art-btn]");
    var titleArtStatus = section.querySelector("[data-title-art-status]");
    var nameInput = section.querySelector(".preview-sheet__cover-name-input");
    var nameSaveBtn = section.querySelector("[data-cover-name-save]");
    var nameSynced = section.querySelector("[data-cover-name-synced]");
    var nameStaleEl = section.querySelector("[data-cover-name-stale]");
    var nameCountEl = section.querySelector("[data-cover-name-count]");
    var savedMagazineName = "";
    var selectedStyle = readCoverOpeningStyleFromDom();
    var options = COVER_OPENING_STYLE_OPTIONS.slice();
    var coverCraft = null;

    function setTitleArtAttribution(engine) {
      if (!titleArtAttr) return;
      var base = isPortfolioEdition(readEditionFromDom(document))
        ? "用你的书名生成封面字体 · 不生成风景图"
        : "用你的杂志名生成封面字体 · 不生成风景图";
      var detail =
        engine === "diffusion-fixed-prompt-v1"
          ? "字迹由 AI 手写体生成"
          : "字库合成，非 AI 绘图";
      titleArtAttr.textContent = engine ? base + "。" + detail : base;
    }

    function setTitleArtStatus(text, isError) {
      if (!titleArtStatus) return;
      if (!text) {
        titleArtStatus.hidden = true;
        titleArtStatus.textContent = "";
        return;
      }
      titleArtStatus.hidden = false;
      titleArtStatus.textContent = text;
      titleArtStatus.classList.toggle("is-error", !!isError);
    }

    function emitTitleArtResolve(meta) {
      // D-CAL-27：漏斗事件；meta.outcome 区分 success/disabled/error/network，
      // 配合 engine + routeCRequested + fallback 可算出 B/C 使用率与失败率。
      trackStudioEvent(
        "title_art_resolve",
        Object.assign(
          {
            tripId: tripId,
            coverOpeningStyle: selectedStyle || "",
          },
          meta || {}
        )
      );
    }

    function requestTitleArt() {
      if (!titleArtBtn) return;
      titleArtBtn.disabled = true;
      var wantRouteC = !!(titleArtRouteCCheck && titleArtRouteCCheck.checked);
      setTitleArtStatus(
        wantRouteC ? "生成中（AI 手写体；未通过会回退默认样式）…" : "生成中…"
      );
      var body = { force: true };
      if (wantRouteC) body.routeC = true;
      postJson(
        "/__travelogue/trips/" + encodeURIComponent(tripId) + "/title-art/resolve",
        body
      )
        .then(function (res) {
          titleArtBtn.disabled = false;
          var failMsg =
            (res.body && res.body.message) ||
            "封面字体暂时不可用，请稍后重试";
          if (res.status !== 200 || !res.body || !res.body.ok) {
            setTitleArtStatus(failMsg, true);
            showToolbarToast(failMsg, { error: true });
            emitTitleArtResolve({
              outcome: "error",
              enabled: false,
              engine: "",
              routeCRequested: wantRouteC,
              fallback: false,
              error: (res.body && res.body.error) || "",
            });
            return;
          }
          if (!res.body.enabled) {
            setTitleArtStatus("此版式或标题暂不支持艺术字，已保持默认样式");
            emitTitleArtResolve({
              outcome: "disabled",
              enabled: false,
              engine: res.body.engine || "",
              routeCRequested: !!res.body.routeCRequested,
              routeCAllowedByConfig: !!res.body.routeCAllowedByConfig,
              fallback: !!res.body.fallbackFrom,
            });
            return;
          }
          var engineLabel =
            res.body.engine === "diffusion-fixed-prompt-v1" ? "AI 手写体" : "字库合成";
          var msg = "已生成 · " + engineLabel;
          if (res.body.fallbackFrom) {
            msg += "（AI 手写体未通过校验，已自动退回默认样式）";
          }
          setTitleArtStatus(msg);
          setTitleArtAttribution(res.body.engine || "clean-pipeline-v1");
          if (nameStaleEl) nameStaleEl.hidden = true;
          if (titleArtBtn) {
            titleArtBtn.textContent = "重新生成字体";
          }
          if (res.body.rendered === false) {
            showToolbarToast(
              (res.body && res.body.message) ||
                "封面字体已生成，预览未刷新，请手动刷新页面",
              { error: true, duration: 5200 }
            );
          } else {
            showToolbarToast("封面字体已更新", { duration: 2200 });
            reloadPreviewAfterLayout();
          }
          emitTitleArtResolve({
            outcome: "success",
            enabled: true,
            engine: res.body.engine || "",
            routeCRequested: !!res.body.routeCRequested,
            routeCAllowedByConfig: !!res.body.routeCAllowedByConfig,
            fallback: !!res.body.fallbackFrom,
            rendered: res.body.rendered !== false,
            ocrVerified:
              typeof res.body.ocrVerified === "boolean" ? res.body.ocrVerified : null,
          });
        })
        .catch(function () {
          titleArtBtn.disabled = false;
          setTitleArtStatus("生成失败，请稍后重试", true);
          showToolbarToast("封面字体请求失败，请稍后重试", { error: true });
          emitTitleArtResolve({
            outcome: "network",
            enabled: false,
            engine: "",
            routeCRequested: wantRouteC,
            fallback: false,
          });
        });
    }

    function syncNameMeta() {
      if (!nameInput) return;
      var v = String(nameInput.value || "");
      if (nameCountEl) {
        nameCountEl.textContent = Array.from(v).length + "/20";
      }
      var dirty = v.trim() !== savedMagazineName;
      if (nameSaveBtn) nameSaveBtn.hidden = !dirty;
      if (nameSynced) nameSynced.hidden = dirty || !savedMagazineName;
    }

    function persistMagazineName() {
      if (!nameInput) return Promise.resolve(false);
      var next = String(nameInput.value || "").trim();
      if (!next) {
        showToolbarToast(
          isPortfolioEdition(readEditionFromDom(document))
            ? "请填写书名"
            : "请填写杂志名",
          { error: true }
        );
        return Promise.resolve(false);
      }
      if (next.length > 20) {
        showToolbarToast(coverNameTooLongToast(readEditionFromDom(document)), {
          error: true,
        });
        return Promise.resolve(false);
      }
      if (next === savedMagazineName) {
        syncNameMeta();
        return Promise.resolve(true);
      }
      if (nameSaveBtn) nameSaveBtn.disabled = true;
      return saveMagazineTitleValue(tripId, next, { skipReload: true }).then(function (ok) {
        if (nameSaveBtn) nameSaveBtn.disabled = false;
        if (!ok) return false;
        savedMagazineName = next;
        if (nameStaleEl) nameStaleEl.hidden = false;
        if (titleArtBtn && !titleArtBtn.disabled) {
          titleArtBtn.textContent = "生成字体";
        }
        syncNameMeta();
        return true;
      });
    }

    if (nameInput) {
      nameInput.addEventListener("input", syncNameMeta);
      if (nameSaveBtn) {
        nameSaveBtn.addEventListener("click", function () {
          // 仅保存：允许整页刷新以看到新杂志名
          if (!nameInput) return;
          var next = String(nameInput.value || "").trim();
          if (!next || next === savedMagazineName) {
            persistMagazineName();
            return;
          }
          if (nameSaveBtn) nameSaveBtn.disabled = true;
          saveMagazineTitleValue(tripId, next).then(function (ok) {
            if (nameSaveBtn) nameSaveBtn.disabled = false;
            if (!ok) return;
            savedMagazineName = next;
            if (nameStaleEl) nameStaleEl.hidden = false;
            if (titleArtBtn && !titleArtBtn.disabled) {
              titleArtBtn.textContent = "生成字体";
            }
            syncNameMeta();
          });
        });
      }
    }

    if (titleArtBtn) {
      titleArtBtn.addEventListener("click", function () {
        var run = function () {
          requestTitleArt();
        };
        if (nameInput && String(nameInput.value || "").trim() !== savedMagazineName) {
          // 先存名且不刷新，再生成（生成成功后会 reload）
          persistMagazineName().then(function (ok) {
            if (ok) run();
          });
        } else {
          run();
        }
      });
    }

    // Studio 高级面板触发入口：服务端总闸（config.title_art）决定是否展示
    // 这一整块，以及是否展示「优先 AI 手写体」勾选框（OQ-CAL-06 · 默认勾选）。
    fetch("/__travelogue/config")
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (cfg) {
        var titleArtCfg = cfg && cfg.titleArt;
        if (!titleArtCfg || !titleArtCfg.enabled || !titleArtBlock) return;
        titleArtBlock.hidden = false;
        var routeCShown = !!(titleArtCfg.routeCEnabled && titleArtRouteCLabel);
        if (routeCShown) {
          titleArtRouteCLabel.hidden = false;
          // 默认勾选优先 AI；仅当用户曾显式取消时保持未勾选。
          var pref = null;
          try {
            pref = localStorage.getItem(TITLE_ART_ROUTE_C_PREF_KEY);
          } catch (_e) {}
          if (titleArtRouteCCheck) {
            titleArtRouteCCheck.checked = pref !== "0";
            if (!titleArtRouteCCheck._titleArtRouteCPrefBound) {
              titleArtRouteCCheck._titleArtRouteCPrefBound = true;
              titleArtRouteCCheck.addEventListener("change", function () {
                try {
                  localStorage.setItem(
                    TITLE_ART_ROUTE_C_PREF_KEY,
                    titleArtRouteCCheck.checked ? "1" : "0"
                  );
                } catch (_e2) {}
              });
            }
          }
        }
        // D-CAL-27：入口曝光——配合 title_art_resolve 可算点击转化率。
        trackStudioEvent("title_art_impression", {
          tripId: tripId,
          coverOpeningStyle: selectedStyle || "",
          routeCShown: routeCShown,
          routeCChecked: !!(titleArtRouteCCheck && titleArtRouteCCheck.checked),
        });
      })
      .catch(function () {});

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
      syncLegacyHint(style);
    }

    function syncLegacyHint(style) {
      // FE-CCF-02 / FE-CCF-04：经典版式提示；CCF 关闭时不展示
      if (!legacyEl) return;
      var craftOn = !!(coverCraft && coverCraft.enabled);
      var inOptions = options.some(function (o) {
        return o.id === style;
      });
      if (craftOn && style && !inOptions) {
        var label =
          (coverCraft && coverCraft.legacyLabel) ||
          style;
        if (coverCraft && coverCraft.legacyStyleId === style && coverCraft.legacyHint) {
          legacyEl.textContent = coverCraft.legacyHint;
        } else {
          legacyEl.textContent =
            "当前为经典版式「" + label + "」，可切换到现行三款。";
        }
        legacyEl.hidden = false;
      } else {
        legacyEl.hidden = true;
        legacyEl.textContent = "";
      }
    }

    function setBusy(busy, nextStyleId) {
      if (group) {
        group.querySelectorAll("[data-cover-style]").forEach(function (btn) {
          btn.disabled = !!busy;
          var sid = btn.getAttribute("data-cover-style");
          btn.classList.toggle(
            "is-updating",
            !!(busy && nextStyleId && sid === nextStyleId)
          );
        });
      }
      if (keepCheck) keepCheck.disabled = !!busy;
      setOpeningUpdateBusy(!!busy, {
        label: "正在更换封面版式…",
      });
    }

    function applyStyleChange(next, keepCover) {
      setBusy(true, next);
      if (fitHintEl) {
        fitHintEl.hidden = true;
        fitHintEl.textContent = "";
      }
      // Nested under Bookends: route through repick-opening for closing cascade (R-BE-14)
      if (opts.viaBookends && typeof opts.applyStyleViaBookends === "function") {
        // FE-CCF / folio：不要乐观改 data-cover-opening。旧 HTML 套新风格
        // 标题 CSS（尤其对页叠印竖排大字）会溢出闪屏；等 rerender 整页刷新。
        return Promise.resolve(opts.applyStyleViaBookends(next, keepCover))
          .then(function (ok) {
            setBusy(false);
            if (ok === false) return;
            selectedStyle = next;
            syncSelection(next);
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
          if (res.status !== 200 || !res.body.ok) {
            setBusy(false);
            showToolbarToast((res.body && res.body.error) || "保存失败", { error: true });
            return;
          }
          var prev = selectedStyle;
          selectedStyle = next;
          syncSelection(next);
          trackStudioEvent("cover_opening_style_change", {
            tripId: tripId,
            coverOpeningStyle: next,
            previousCoverOpeningStyle: prev,
            repickCover: !keepCover,
          });
          showToolbarToast(
            keepCover ? "封面版式已更新（保留当前封面图）" : "封面版式已更新，并重荐了封面图",
            { duration: 2200 }
          );
          if (keepCover && fitHintEl && res.body.fitBelowThreshold) {
            fitHintEl.hidden = false;
            fitHintEl.textContent = "当前封面图可能不太适合此版式";
          }
          var toolbar = document.querySelector(".preview-toolbar");
          // 同上：等 rerender + reload，勿 syncCoverOpeningStyleInDom
          return refreshPreviewAfterCopySave(
            res,
            tripId,
            toolbar || section
          )
            .then(function (ok) {
              if (ok && toolbar) refreshStaleHint(toolbar, tripId);
            })
            .finally(function () {
              setBusy(false);
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

    if (mode === "style") {
      renderOptions(options);
    }
    slot.appendChild(section);

    fetchEntry(tripId)
      .then(function (data) {
        if (data && data.coverCraft) {
          coverCraft = data.coverCraft;
        }
        if (
          mode === "style" &&
          data &&
          Array.isArray(data.coverStyleOptions) &&
          data.coverStyleOptions.length
        ) {
          renderOptions(data.coverStyleOptions);
        }
        if (data && data.coverOpeningStyle) {
          selectedStyle = data.coverOpeningStyle;
          if (coverCraft && coverCraft.legacyCurrent) {
            coverCraft.legacyStyleId = selectedStyle;
            coverCraft.legacyLabel =
              data.coverStyleLabel || coverCraft.legacyLabel || selectedStyle;
          }
          if (mode === "style") syncSelection(selectedStyle);
        }
        if (mode === "name" && nameInput) {
          // RCI · 回填优先封面展示名（displayTitle / DOM），勿只信裸 meta.title
          var summary = data && data.intentSummary;
          var coverDom =
            (document.querySelector(".cover-opening__title") || {}).textContent ||
            "";
          var title =
            (summary && String(summary.displayTitle || "").trim()) ||
            String(coverDom || "").trim() ||
            (summary && String(summary.title || "").trim()) ||
            "";
          savedMagazineName = String(title || "").trim();
          nameInput.value = savedMagazineName;
          syncNameMeta();
          var ta = data && data.titleArt;
          if (ta && ta.stale) {
            if (nameStaleEl) nameStaleEl.hidden = false;
          } else if (nameStaleEl) {
            nameStaleEl.hidden = true;
          }
          if (titleArtBtn && ta && ta.enabled && !ta.stale) {
            titleArtBtn.textContent = "重新生成字体";
          }
          if (ta && ta.engine) setTitleArtAttribution(ta.engine);
        }
      })
      .catch(function () {});

    if (mode === "style") {
      trackStudioEvent("cover_opening_style_selector_impression", {
        surface: "preview-sheet",
        tripId: tripId,
        coverOpeningStyle: selectedStyle,
      });
    }
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
