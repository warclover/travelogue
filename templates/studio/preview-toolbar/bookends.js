/**
 * Studio · 「封面与封底」合页面板（Bookends B2b · PRD §7.2）
 */
"use strict";

import { getJson, postJson } from "../js/http.js";
import { showToolbarToast, toolbarConfirm } from "./shell.js";
import { applyLayoutRerender, syncCoverOpeningStyleInDom } from "./core.js";

function bookendsApi(tripId, suffix) {
  return "/__travelogue/trips/" + encodeURIComponent(tripId) + "/bookends" + (suffix || "");
}

function thumbUrl(tripId, assetId, displayFile) {
  if (displayFile) {
    var rel = String(displayFile).replace(/^\//, "");
    return "/" + encodeURIComponent(tripId) + "/" + rel;
  }
  if (!assetId) return "";
  return (
    "/" +
    encodeURIComponent(tripId) +
    "/assets/" +
    encodeURIComponent(assetId) +
    "-w400.webp"
  );
}

function setHero(el, tripId, assetId, displayFile, emptyText) {
  if (!el) return;
  if (!assetId) {
    el.classList.add("is-empty");
    el.style.backgroundImage = "";
    el.innerHTML = emptyText
      ? '<span class="preview-sheet__bookends-hero-empty">' + emptyText + "</span>"
      : "";
    return;
  }
  el.classList.remove("is-empty");
  el.innerHTML = "";
  el.style.backgroundImage = "url('" + thumbUrl(tripId, assetId, displayFile) + "')";
}

function candidateButton(tripId, item, kind, selectedId, index) {
  var aid = item.assetId || item.id || "";
  var btn = document.createElement("button");
  btn.type = "button";
  btn.className = "preview-sheet__bookends-thumb";
  var isOn = !!(aid && aid === selectedId);
  if (isOn) btn.classList.add("is-on");
  else btn.classList.add("is-muted");
  if (item.preview) btn.classList.add("is-preview");
  btn.setAttribute("data-bookends-" + kind, aid);
  // asset-id 仅保留 title（调试）；可见 UI 用缩略图 + aria-label
  btn.title = aid;
  var kindLabel = kind === "closing" ? "封底" : "封面";
  var n = (index == null ? 0 : index) + 1;
  btn.setAttribute(
    "aria-label",
    isOn ? "当前" + kindLabel : kindLabel + "候选 " + n
  );
  btn.innerHTML =
    '<span class="preview-sheet__bookends-thumb-media" style="background-image:url(\'' +
    thumbUrl(tripId, aid, item.displayFile) +
    "')\"></span>" +
    (isOn ? '<span class="preview-sheet__bookends-thumb-badge">当前</span>' : "");
  return btn;
}

export function mountBookendsPanel(slot, tripId, opts) {
  opts = opts || {};
  if (!slot || slot.querySelector(".preview-sheet__bookends")) return;

  var root = document.createElement("section");
  root.className = "preview-sheet__section preview-sheet__bookends";
  root.innerHTML =
    '<div class="preview-sheet__bookends-head">' +
    '<span class="preview-sheet__label">封面与封底</span>' +
    '<p class="preview-sheet__hint preview-sheet__hint--compact preview-sheet__bookends-sub">游记的第一眼与最后一眼</p>' +
    "</div>" +
    '<p class="preview-sheet__bookends-oneliner" data-bookends-oneliner></p>' +
    '<p class="preview-sheet__bookends-status" data-bookends-status hidden role="status"></p>' +
    '<div class="preview-sheet__bookends-spread" aria-label="合页预览">' +
    '<div class="preview-sheet__bookends-pane" data-bookends-opening>' +
    '<div class="preview-sheet__bookends-pane-head">' +
    '<span class="preview-sheet__bookends-pane-label">封面</span>' +
    '<span class="preview-sheet__bookends-lock" data-bookends-opening-lock hidden>手选 · 可恢复自动</span>' +
    "</div>" +
    '<div class="preview-sheet__bookends-hero" data-bookends-opening-hero aria-hidden="true"></div>' +
    '<p class="preview-sheet__bookends-style" data-bookends-style></p>' +
    '<div class="preview-sheet__bookends-cands" data-bookends-opening-cands role="group" aria-label="换封面"></div>' +
    '<p class="preview-sheet__bookends-empty-hint" data-bookends-opening-empty hidden>暂无其它封面候选</p>' +
    "</div>" +
    '<div class="preview-sheet__bookends-pane" data-bookends-closing>' +
    '<div class="preview-sheet__bookends-pane-head">' +
    '<span class="preview-sheet__bookends-pane-label">封底</span>' +
    '<span class="preview-sheet__bookends-lock" data-bookends-closing-lock hidden>手选 · 可恢复自动</span>' +
    "</div>" +
    '<div class="preview-sheet__bookends-hero" data-bookends-closing-hero aria-hidden="true"></div>' +
    '<p class="preview-sheet__bookends-pending" data-bookends-pending hidden>排版完成后自动选择</p>' +
    '<p class="preview-sheet__bookends-preview-note" data-bookends-preview-note hidden>以下为预览候选，排版完成后才会固定</p>' +
    '<div class="preview-sheet__bookends-cands" data-bookends-closing-cands role="group" aria-label="换封底"></div>' +
    '<p class="preview-sheet__bookends-empty-hint" data-bookends-closing-empty hidden>暂无封底候选</p>' +
    "</div>" +
    "</div>" +
    '<details class="preview-sheet__bookends-mobile" data-bookends-mobile>' +
    "<summary>手机封面 · 预览手机效果</summary>" +
    '<div class="preview-sheet__bookends-mobile-body">' +
    '<div class="preview-sheet__bookends-mobile-thumb" data-bookends-mobile-thumb aria-hidden="true"></div>' +
    '<p class="preview-sheet__hint" data-bookends-mobile-hint>电脑与手机版式可能不同；此处为竖屏封面对照。封底目前仅网页成书。</p>' +
    "</div>" +
    "</details>" +
    '<div class="preview-sheet__bookends-actions">' +
    '<button type="button" class="preview-sheet__ghost" data-bookends-scroll-opening>看封面</button>' +
    '<button type="button" class="preview-sheet__ghost" data-bookends-scroll-closing>看封底</button>' +
    '<button type="button" class="preview-sheet__ghost" data-bookends-restore>恢复自动挑选</button>' +
    "</div>" +
    '<div class="preview-sheet__bookends-style-slot" data-bookends-style-slot></div>';

  slot.appendChild(root);

  // D-REFUX-06 · 首次展开「手机封面」以强化对照发现性
  var mobileDetails = root.querySelector("[data-bookends-mobile]");
  var MOBILE_OPEN_KEY = "travelogue.preview.bookendsMobileOnce";
  if (mobileDetails) {
    try {
      if (localStorage.getItem(MOBILE_OPEN_KEY) !== "1") {
        mobileDetails.open = true;
        localStorage.setItem(MOBILE_OPEN_KEY, "1");
      }
    } catch (_eMob) {
      mobileDetails.open = true;
    }
  }

  var onelinerEl = root.querySelector("[data-bookends-oneliner]");
  var statusEl = root.querySelector("[data-bookends-status]");
  var styleEl = root.querySelector("[data-bookends-style]");
  var pendingEl = root.querySelector("[data-bookends-pending]");
  var previewNoteEl = root.querySelector("[data-bookends-preview-note]");
  var openingCands = root.querySelector("[data-bookends-opening-cands]");
  var closingCands = root.querySelector("[data-bookends-closing-cands]");
  var openingHero = root.querySelector("[data-bookends-opening-hero]");
  var closingHero = root.querySelector("[data-bookends-closing-hero]");
  var openingLock = root.querySelector("[data-bookends-opening-lock]");
  var closingLock = root.querySelector("[data-bookends-closing-lock]");
  var openingEmpty = root.querySelector("[data-bookends-opening-empty]");
  var closingEmpty = root.querySelector("[data-bookends-closing-empty]");
  var mobileThumb = root.querySelector("[data-bookends-mobile-thumb]");
  var mobileHint = root.querySelector("[data-bookends-mobile-hint]");
  var restoreBtn = root.querySelector("[data-bookends-restore]");
  var styleSlot = root.querySelector("[data-bookends-style-slot]");

  var state = {
    coverAssetId: "",
    webCoverAssetId: "",
    mobileCoverAssetId: "",
    closingAssetId: "",
    coverOpeningStyle: "",
    closingPending: false,
    closingPreviewOnly: false,
  };

  function setBusy(busy) {
    root.querySelectorAll("button").forEach(function (btn) {
      btn.disabled = !!busy;
    });
  }

  function renderStatus(payload) {
    if (!statusEl) return;
    var banner = payload.statusBanner;
    var soft = (payload.softWarnings || [])[0];
    var kind = banner && banner.kind;
    var msg = (banner && banner.message) || "";
    if (!msg && soft && soft.message) {
      kind = "warn";
      msg = soft.message;
    }
    root.classList.remove(
      "is-degraded",
      "is-low-confidence",
      "is-pending-status",
      "is-soft-warn"
    );
    if (!msg) {
      statusEl.hidden = true;
      statusEl.textContent = "";
      return;
    }
    statusEl.hidden = false;
    statusEl.textContent = msg;
    if (kind === "degraded") root.classList.add("is-degraded");
    else if (kind === "lowConfidence") root.classList.add("is-low-confidence");
    else if (kind === "pending") root.classList.add("is-pending-status");
    else root.classList.add("is-soft-warn");
  }

  function render(payload) {
    if (!payload) return;
    state.coverAssetId = payload.coverAssetId || "";
    state.webCoverAssetId =
      payload.webCoverAssetId ||
      (payload.webCoverThumb && payload.webCoverThumb.assetId) ||
      payload.coverAssetId ||
      "";
    state.mobileCoverAssetId =
      payload.mobileCoverAssetId ||
      (payload.mobileCoverThumb && payload.mobileCoverThumb.assetId) ||
      "";
    state.closingAssetId = payload.closingAssetId || "";
    state.coverOpeningStyle = payload.coverOpeningStyle || "";
    state.closingPending = !!payload.closingPending;
    state.closingPreviewOnly = !!payload.closingPreviewOnly;

    if (onelinerEl) {
      onelinerEl.textContent = payload.userOneLiner || "";
    }
    renderStatus(payload);
    if (styleEl) {
      styleEl.textContent = payload.coverStyleLabel
        ? "版式 · " + payload.coverStyleLabel
        : "";
    }
    if (pendingEl) {
      pendingEl.hidden = !payload.closingPending;
    }
    if (previewNoteEl) {
      previewNoteEl.hidden = !(payload.closingPreviewOnly && (payload.closingCandidates || []).length);
    }
    if (openingLock) {
      openingLock.hidden = !(
        payload.openingLocked ||
        (payload.lock && payload.lock.opening)
      );
    }
    if (closingLock) {
      closingLock.hidden = !(
        payload.closingUserPicked ||
        payload.closingLocked ||
        (payload.lock && payload.lock.closing)
      );
    }

    var coverThumb = payload.coverThumb || payload.webCoverThumb || {};
    setHero(
      openingHero,
      tripId,
      state.webCoverAssetId || coverThumb.assetId,
      coverThumb.displayFile,
      "暂无封面"
    );
    if (payload.degraded || (!state.closingAssetId && !payload.closingPending)) {
      setHero(closingHero, tripId, "", null, "已省略封底图");
    } else {
      var closingThumb = payload.closingThumb || {};
      setHero(
        closingHero,
        tripId,
        state.closingAssetId || closingThumb.assetId,
        closingThumb.displayFile,
        state.closingPending ? "待排版后选择" : "暂无封底"
      );
    }

    var mobile = payload.mobileCoverThumb || {};
    setHero(
      mobileThumb,
      tripId,
      state.mobileCoverAssetId || mobile.assetId,
      mobile.displayFile,
      ""
    );
    if (mobileHint) {
      mobileHint.textContent =
        payload.mobileCoverHint ||
        "为竖屏另选；封底目前仅网页成书。";
    }

    if (openingCands) {
      openingCands.innerHTML = "";
      var opens = payload.openingCandidates || [];
      opens.forEach(function (item, idx) {
        var btn = candidateButton(
          tripId,
          item,
          "opening",
          state.webCoverAssetId || state.coverAssetId,
          idx
        );
        btn.addEventListener("click", function () {
          applyOpening(item.assetId || item.id);
        });
        openingCands.appendChild(btn);
      });
      if (openingEmpty) openingEmpty.hidden = opens.length > 0;
    }
    if (closingCands) {
      closingCands.innerHTML = "";
      var closes = payload.closingCandidates || [];
      // Pending: still show preview candidates (PRD §4.5)
      closes.forEach(function (item, idx) {
        var btn = candidateButton(tripId, item, "closing", state.closingAssetId, idx);
        if (payload.closingPreviewOnly && !payload.hasScreens) {
          btn.disabled = true;
          btn.title = "排版完成后可选";
        } else {
          btn.addEventListener("click", function () {
            applyClosing(item.assetId || item.id);
          });
        }
        closingCands.appendChild(btn);
      });
      if (closingEmpty) {
        closingEmpty.hidden = closes.length > 0 || !!payload.degraded;
        if (!closes.length && payload.degraded) {
          closingEmpty.hidden = false;
          closingEmpty.textContent = "可选照片太少，已省略封底图";
        } else if (!closes.length) {
          closingEmpty.textContent = "暂无封底候选";
        }
      }
    }
  }

  function refresh() {
    return getJson(bookendsApi(tripId, ""))
      .then(function (res) {
        if (res.status === 200 && res.body && res.body.ok !== false) {
          render(res.body);
        }
      })
      .catch(function () {});
  }

  function afterMutation(res, mutOpts) {
    mutOpts = mutOpts || {};
    setBusy(false);
    if (res.status === 409 && res.body && res.body.error === "E_BOOKENDS_CLOSING_CONFLICT") {
      return toolbarConfirm({
        title: "封底与新封面冲突",
        body: res.body.message || "需要重选封底",
        confirmText: "重选",
        cancelText: "取消换封面",
      }).then(function (ok) {
        if (!ok) return false;
        return applyOpening(mutOpts.assetId, mutOpts.styleId, true, mutOpts.keepCover);
      });
    }
    if (res.status !== 200 || !res.body || !res.body.ok) {
      showToolbarToast((res.body && (res.body.message || res.body.error)) || "保存失败", {
        error: true,
      });
      return false;
    }
    if (res.body.toast) showToolbarToast(res.body.toast);
    if (res.body.coverOpeningStyle) {
      syncCoverOpeningStyleInDom(res.body.coverOpeningStyle);
    }
    render(res.body);
    applyLayoutRerender(tripId);
    return true;
  }

  function applyOpening(assetId, styleId, confirmConflict, keepCover) {
    setBusy(true);
    var body = {
      confirmClosingConflict: !!confirmConflict,
    };
    if (styleId || state.coverOpeningStyle) {
      body.styleId = styleId || state.coverOpeningStyle;
    }
    if (keepCover) {
      body.keepCover = true;
      if (assetId || state.coverAssetId) body.assetId = assetId || state.coverAssetId;
    } else if (assetId) {
      body.assetId = assetId;
    }
    return postJson(bookendsApi(tripId, "/repick-opening"), body).then(function (res) {
      return afterMutation(res, {
        assetId: assetId,
        styleId: styleId,
        keepCover: keepCover,
      });
    });
  }

  function applyClosing(assetId) {
    setBusy(true);
    return postJson(bookendsApi(tripId, "/repick-closing"), {
      assetId: assetId,
    }).then(function (res) {
      afterMutation(res);
    });
  }

  /** FE-BE-05 · style change via bookends cascade */
  function applyStyleViaBookends(styleId, keepCover) {
    return applyOpening(
      keepCover ? state.coverAssetId : null,
      styleId,
      false,
      !!keepCover
    );
  }

  if (restoreBtn) {
    restoreBtn.addEventListener("click", function () {
      toolbarConfirm({
        title: "恢复自动挑选？",
        body: "将覆盖你的手选封面与封底，并重新自动挑选。",
        confirmText: "恢复",
        cancelText: "取消",
        danger: true,
      }).then(function (ok) {
        if (!ok) return;
        setBusy(true);
        postJson(bookendsApi(tripId, "/restore-auto"), { confirmed: true }).then(
          function (res) {
            afterMutation(res);
          }
        );
      });
    });
  }

  if (styleSlot && typeof opts.mountCoverStyleControls === "function") {
    opts.mountCoverStyleControls(styleSlot, {
      viaBookends: true,
      applyStyleViaBookends: applyStyleViaBookends,
    });
  }

  refresh();
  return {
    refresh: refresh,
    styleSlot: styleSlot,
    applyStyleViaBookends: applyStyleViaBookends,
  };
}
