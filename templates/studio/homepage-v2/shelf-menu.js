/**
 * 首页 v2 · 书架 TripCardMenu（M13 · hover ⋯ + 删除确认）。
 * PDG · 预览中删除：强确认 → 先断开预览 → 卡片删除中 → DELETE。
 */
import { isDemoTrip } from "../js/constants.js";
import { trackStudioEvent } from "../js/analytics.js";
import { postJson } from "../js/http.js";
import { pollJobUntilDone } from "../js/job-poll.js";
import { editionSwitchConfirm, normalizeEdition } from "../js/portfolio-edition-logic.js";
import {
  V2,
  markTripDeleting,
  clearTripDeleting,
  isTripDeleting,
  noteTripDeleted,
} from "./store.js";
import { deleteTrip } from "./trips-client.js";
import { runShelfLongshot, openShelfLongshotFolder, canOpenShelfLongshotFolder } from "./shelf-longshot.js";
import { setBentoPreviewTripId } from "./bento-tabs.js";

var _openMenuEl = null;
var _docBound = false;

function toast(msg, opts) {
  if (typeof studioToast === "function") studioToast(msg, opts);
}

function closeMenu(menuEl) {
  if (!menuEl) return;
  menuEl.dataset.open = "false";
  menuEl.hidden = true;
  var btn = menuEl.parentElement && menuEl.parentElement.querySelector(".v2-shelf__menu-btn");
  if (btn) {
    btn.classList.remove("is-active");
    btn.setAttribute("aria-expanded", "false");
  }
  var card = menuEl.closest(".v2-shelf__card, .v2-shelf__resume");
  if (card) card.classList.remove("is-menu-open");
  if (_openMenuEl === menuEl) _openMenuEl = null;
}

export function closeAllShelfMenus() {
  if (_openMenuEl) closeMenu(_openMenuEl);
}

function bindDocDismiss() {
  if (_docBound) return;
  _docBound = true;
  document.addEventListener("click", function (e) {
    if (!_openMenuEl) return;
    if (e.target.closest(".v2-shelf__menu-btn") || e.target.closest(".v2-shelf__menu")) return;
    closeMenu(_openMenuEl);
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && _openMenuEl) closeMenu(_openMenuEl);
  });
}

function openMenu(menuEl, menuBtn) {
  if (_openMenuEl && _openMenuEl !== menuEl) closeMenu(_openMenuEl);
  _openMenuEl = menuEl;
  menuEl.dataset.open = "true";
  menuEl.hidden = false;
  menuBtn.classList.add("is-active");
  menuBtn.setAttribute("aria-expanded", "true");
  var card = menuEl.closest(".v2-shelf__card, .v2-shelf__resume");
  if (card) card.classList.add("is-menu-open");
}

function findShelfCards(tripId) {
  var nodes = [];
  document.querySelectorAll(
    '.v2-shelf__card[data-trip-id="' + tripId + '"], .v2-shelf__resume[data-trip-id="' + tripId + '"]'
  ).forEach(function (el) { nodes.push(el); });
  return nodes;
}

function setCardDeletingUi(tripId, deleting) {
  findShelfCards(tripId).forEach(function (card) {
    if (deleting) {
      card.dataset.deleting = "1";
      card.setAttribute("aria-busy", "true");
      card.classList.add("is-deleting");
    } else {
      delete card.dataset.deleting;
      card.removeAttribute("aria-busy");
      card.classList.remove("is-deleting");
    }
    card.querySelectorAll(".v2-shelf__menu-item--danger").forEach(function (btn) {
      if (deleting) {
        btn.disabled = true;
        btn.textContent = "删除中";
      } else if (!btn.dataset.demoLocked) {
        btn.disabled = false;
        btn.textContent = "删除画册";
      }
    });
  });
}

function previewDeleteCopy(title) {
  return {
    title: "删除正在展示的画册？",
    body:
      "「" + title + "」是当前首页预览。删除后将切回示例作品，并移除其排版与预览记录。" +
      "你电脑上的原始照片不会被删除，之后可以用同一文件夹重新导入。",
  };
}

function genericDeleteCopy(title) {
  return {
    title: "删除这本画册？",
    body:
      "将移除画册「" + title + "」及其排版与预览记录。" +
      "你电脑上的原始照片不会被删除，之后可以用同一文件夹重新导入。",
  };
}

function confirmShelfEditionSwitch(trip, to, surface) {
  var tripId = trip.tripId;
  var copy = editionSwitchConfirm(trip.edition, to);
  var runSwitch = function () {
    toast("正在按成册类型重排页面…", { duration: 3200 });
    return postJson("/__travelogue/trips/" + encodeURIComponent(tripId) + "/edition", {
      edition: to,
      confirmed: true,
    })
      .then(function (res) {
        if (res.status === 200 && res.body && res.body.unchanged) {
          if (typeof V2.reroute === "function") V2.reroute();
          return;
        }
        if (!(res.status === 202 && res.body && res.body.jobId)) {
          var msg = (res.body && (res.body.message || res.body.error)) || "无法改回游记";
          toast(msg, { duration: 3200 });
          return;
        }
        return pollJobUntilDone(res.body.jobId, { intervalMs: 800 }).then(function (job) {
          if (!job || job.status !== "succeeded") {
            toast((job && job.error && job.error.message) || "改回游记失败", {
              duration: 3200,
            });
            return;
          }
          trackStudioEvent("shelf_edition_change", {
            trip_id: tripId,
            surface: surface,
            edition: "journal",
          });
          toast("已改回游记并重排页面", { duration: 3000 });
          if (typeof V2.reroute === "function") V2.reroute();
        });
      })
      .catch(function () {
        toast("改回游记失败，请重试", { duration: 3200 });
      });
  };

  if (typeof studioModal !== "function") {
    if (window.confirm(copy.title + "\n\n" + copy.body)) runSwitch();
    return;
  }

  studioModal({
    title: copy.title,
    body: copy.body,
    confirmText: copy.confirmText,
    cancelText: copy.cancelText,
  }).then(function (ok) {
    if (!ok) {
      trackStudioEvent("shelf_edition_cancel", {
        trip_id: tripId,
        surface: surface,
      });
      return;
    }
    runSwitch();
  });
}

function confirmDelete(trip, surface, onSuccess) {
  var tripId = trip.tripId;
  if (isTripDeleting(tripId)) return;

  var title = trip.title || tripId;
  var wasPreviewing = !!(V2.bentoPreviewTripId && V2.bentoPreviewTripId === tripId);
  var copy = wasPreviewing ? previewDeleteCopy(title) : genericDeleteCopy(title);

  var runDelete = function () {
    if (isTripDeleting(tripId)) return Promise.resolve();
    markTripDeleting(tripId);
    setCardDeletingUi(tripId, true);
    trackStudioEvent("shelf_delete_confirm", {
      trip_id: tripId,
      surface: surface,
      was_previewing: wasPreviewing,
    });

    var disconnectP = Promise.resolve();
    if (wasPreviewing || (V2.bentoPreviewTripId && V2.bentoPreviewTripId === tripId)) {
      try {
        // PDG §8 · 打点 bento_preview_select source=shelf_delete（trip_id:null）
        disconnectP = setBentoPreviewTripId(null, {
          source: "shelf_delete",
        });
      } catch (e) {
        clearTripDeleting(tripId);
        setCardDeletingUi(tripId, false);
        toast("无法切换预览，删除已取消", { duration: 3200 });
        trackStudioEvent("shelf_delete_fail", {
          trip_id: tripId,
          surface: surface,
          was_previewing: wasPreviewing,
          error: "disconnect_throw",
        });
        return Promise.resolve();
      }
    }

    return Promise.resolve(disconnectP).catch(function () {
      /* storage / async stale sync failures: still DELETE (D-PDG-07) */
    }).then(function () {
      return deleteTrip(tripId).then(function () {
        noteTripDeleted(tripId);
        trackStudioEvent("shelf_delete_success", {
          trip_id: tripId,
          surface: surface,
          was_previewing: wasPreviewing,
          remaining_count: Math.max(0, (V2.tripsTotal || 1) - 1),
        });
        toast(
          wasPreviewing
            ? "已删除「" + title + "」，已切回示例"
            : "已删除「" + title + "」",
          { duration: 3000 }
        );
        if (typeof onSuccess === "function") onSuccess(trip);
        if (typeof V2.reroute === "function") V2.reroute();
      }).catch(function (err) {
        clearTripDeleting(tripId);
        setCardDeletingUi(tripId, false);
        var msg = (err && err.message) ? err.message : "删除失败，请重试";
        if (err && err.status === 401) msg = "未授权，请刷新页面后重试";
        toast(msg, { duration: 3200 });
        trackStudioEvent("shelf_delete_fail", {
          trip_id: tripId,
          surface: surface,
          was_previewing: wasPreviewing,
          error: (err && err.code) || (err && err.status) || "delete_failed",
        });
      });
    });
  };

  if (typeof studioModal !== "function") {
    if (window.confirm(copy.title + "\n\n" + copy.body)) runDelete();
    return;
  }

  studioModal({
    title: copy.title,
    body: copy.body,
    confirmText: "删除",
    cancelText: "取消",
    danger: true,
    focusCancel: true,
  }).then(function (ok) {
    if (!ok) {
      trackStudioEvent("shelf_delete_cancel", {
        trip_id: tripId,
        surface: surface,
        was_previewing: wasPreviewing,
      });
      return;
    }
    runDelete();
  });
}

/**
 * 在封面容器上挂载 ⋯ 菜单。
 * @param {HTMLElement} coverWrap
 * @param {object} trip
 * @param {{ surface: string, onDeleted?: function }} opts
 */
export function attachShelfTripMenu(coverWrap, trip, opts) {
  opts = opts || {};
  var surface = opts.surface || "grid";
  var demo = isDemoTrip(trip);
  var deleting = isTripDeleting(trip.tripId);

  var menuBtn = document.createElement("button");
  menuBtn.type = "button";
  menuBtn.className = "v2-shelf__menu-btn";
  menuBtn.setAttribute("aria-label", "更多操作");
  menuBtn.setAttribute("aria-haspopup", "menu");
  menuBtn.setAttribute("aria-expanded", "false");
  menuBtn.textContent = "⋯";

  var menu = document.createElement("div");
  menu.className = "v2-shelf__menu";
  menu.setAttribute("role", "menu");
  menu.dataset.open = "false";
  menu.hidden = true;

  var previewItem = document.createElement("button");
  previewItem.type = "button";
  previewItem.className = "v2-shelf__menu-item";
  previewItem.setAttribute("role", "menuitem");
  previewItem.textContent = "在上方预览";
  if (demo) {
    previewItem.disabled = true;
    previewItem.title = "示例画册无法设为预览";
  }

  var longshotItem = document.createElement("button");
  longshotItem.type = "button";
  longshotItem.className = "v2-shelf__menu-item";
  longshotItem.setAttribute("role", "menuitem");
  longshotItem.textContent = "保存长图";

  var openLongshotItem = document.createElement("button");
  openLongshotItem.type = "button";
  openLongshotItem.className = "v2-shelf__menu-item";
  openLongshotItem.setAttribute("role", "menuitem");
  openLongshotItem.textContent = "打开长图文件夹";
  if (!canOpenShelfLongshotFolder(trip)) {
    openLongshotItem.disabled = true;
    openLongshotItem.title = "尚未导出长图";
  }

  var deleteItem = document.createElement("button");
  deleteItem.type = "button";
  deleteItem.className = "v2-shelf__menu-item v2-shelf__menu-item--danger";
  deleteItem.setAttribute("role", "menuitem");
  deleteItem.textContent = deleting ? "删除中" : "删除画册";
  if (demo) {
    deleteItem.disabled = true;
    deleteItem.dataset.demoLocked = "1";
    deleteItem.title = "示例画册无法删除";
  } else if (deleting) {
    deleteItem.disabled = true;
  }

  menu.appendChild(previewItem);
  menu.appendChild(longshotItem);
  menu.appendChild(openLongshotItem);
  if (!demo && normalizeEdition(trip.edition) === "portfolio") {
    var toJournalItem = document.createElement("button");
    toJournalItem.type = "button";
    toJournalItem.className = "v2-shelf__menu-item";
    toJournalItem.setAttribute("role", "menuitem");
    toJournalItem.textContent = "改为游记重排";
    toJournalItem.addEventListener("click", function (e) {
      e.preventDefault();
      e.stopPropagation();
      closeMenu(menu);
      confirmShelfEditionSwitch(trip, "journal", surface);
    });
    menu.appendChild(toJournalItem);
  }
  menu.appendChild(deleteItem);
  coverWrap.appendChild(menuBtn);
  coverWrap.appendChild(menu);

  menuBtn.addEventListener("click", function (e) {
    e.preventDefault();
    e.stopPropagation();
    if (menu.dataset.open === "true") {
      closeMenu(menu);
      return;
    }
    trackStudioEvent("shelf_menu_open", { trip_id: trip.tripId, surface: surface });
    openMenu(menu, menuBtn);
  });

  previewItem.addEventListener("click", function (e) {
    e.preventDefault();
    e.stopPropagation();
    if (previewItem.disabled) return;
    closeMenu(menu);
    setBentoPreviewTripId(trip.tripId, { source: "shelf" }).then(function () {
      var frame = document.getElementById("v2-frame");
      if (frame) frame.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });

  longshotItem.addEventListener("click", function (e) {
    e.preventDefault();
    e.stopPropagation();
    closeMenu(menu);
    runShelfLongshot(trip, { surface: surface });
  });

  openLongshotItem.addEventListener("click", function (e) {
    e.preventDefault();
    e.stopPropagation();
    if (openLongshotItem.disabled) return;
    closeMenu(menu);
    openShelfLongshotFolder(trip, { surface: surface });
  });

  deleteItem.addEventListener("click", function (e) {
    e.preventDefault();
    e.stopPropagation();
    if (deleteItem.disabled || isTripDeleting(trip.tripId)) return;
    closeMenu(menu);
    confirmDelete(trip, surface, opts.onDeleted);
  });

  bindDocDismiss();
}
