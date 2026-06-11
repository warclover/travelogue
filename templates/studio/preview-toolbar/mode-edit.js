/**
 * Preview toolbar · edit mode overlays + apply layout (§6.1–6.3).
 */
"use strict";

import { postJson, patchJson } from "../js/http.js";
import { trackStudioEvent } from "../js/analytics.js";
import {
  setLayoutPending,
  setPendingUndoHandler,
  getPendingCount,
} from "./pending.js";
import { fetchEntry } from "./drawer-support.js";
import { tripApiBase, showToolbarToast, revealTripPath } from "./toolbar-ui.js";

var _assetMediaById = {};

export function applyLayoutRerender(tripId, root) {
  var btn = root.querySelector(".preview-toolbar__apply-layout");
  var pendingBtn = root.querySelector(".preview-toolbar__pending-apply");
  var applyMain = root.querySelector(".preview-toolbar__apply-layout-main");
  if (btn) btn.disabled = true;
  if (pendingBtn) pendingBtn.disabled = true;
  if (applyMain) applyMain.disabled = true;
  trackStudioEvent("pending_apply", {
    count: getPendingCount(),
    tripId: tripId,
  });
  return postJson(tripApiBase(tripId) + "/rerender", {})
    .then(function (res) {
      if (btn) btn.disabled = false;
      if (pendingBtn) pendingBtn.disabled = false;
      if (applyMain) applyMain.disabled = false;
      if (res.status !== 200 || !res.body.ok) {
        showToolbarToast((res.body && res.body.error) || "排版失败", { error: true });
        return;
      }
      setLayoutPending(false, { reset: true });
      showToolbarToast("已应用");
      window.location.reload();
    })
    .catch(function () {
      if (btn) btn.disabled = false;
      if (pendingBtn) pendingBtn.disabled = false;
      if (applyMain) applyMain.disabled = false;
      showToolbarToast("排版失败", { error: true });
    });
}

export function initDisplayedAestheticTitles(tripId) {
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
          img.setAttribute(
            "title",
            (pct != null ? "审美 " + pct + " · " : "") + tips
          );
        });
    })
    .catch(function () { /* fail-open */ });
}

export function revertFeaturedUi(assetId) {
  document
    .querySelectorAll('.layout-screen[data-block="layout-screen"][data-asset-ids]')
    .forEach(function (screen) {
      var id = (screen.getAttribute("data-asset-ids") || "").split(",")[0];
      if (id !== assetId) return;
      screen.setAttribute("data-featured", "false");
      var star = screen.querySelector(".preview-toolbar__featured-star");
      if (star) {
        star.classList.remove("preview-toolbar__featured-star--on");
        star.setAttribute("aria-pressed", "false");
      }
    });
}

export function revertMediaUi(assetId, mediaClass) {
  document
    .querySelectorAll('.layout-screen[data-block="layout-screen"][data-asset-ids]')
    .forEach(function (screen) {
      var id = (screen.getAttribute("data-asset-ids") || "").split(",")[0];
      if (id !== assetId) return;
      var sel = screen.querySelector(".preview-toolbar__collage-select");
      if (sel) sel.value = mediaClass === "collage" ? "collage" : "photo";
    });
}

export function initPendingUndo(tripId) {
  var mediaApi =
    "/__travelogue/trips/" + encodeURIComponent(tripId) + "/asset-media-class";
  setPendingUndoHandler(function (item) {
    if (item.kind === "media") {
      return patchJson(mediaApi, {
        assetId: item.assetId,
        mediaClass: item.prevMediaClass || "photo",
      }).then(function (res) {
        if (res.status !== 200 || !res.body.ok) {
          showToolbarToast((res.body && res.body.error) || "撤销失败", { error: true });
          return false;
        }
        _assetMediaById[item.assetId] = item.prevMediaClass || "photo";
        revertMediaUi(item.assetId, item.prevMediaClass || "photo");
        showToolbarToast("已撤销媒资改判");
        return true;
      });
    }
    if (item.kind === "featured") {
      return postJson(tripApiBase(tripId) + "/promote-tier", {
        assetIds: [item.assetId],
        rerender: false,
        demote: true,
      }).then(function (res) {
        if (res.status !== 200 || !res.body.ok) {
          showToolbarToast((res.body && res.body.error) || "撤销失败", { error: true });
          return false;
        }
        revertFeaturedUi(item.assetId);
        showToolbarToast("已撤销精选标记");
        return true;
      });
    }
    return Promise.resolve(true);
  });
}

export function initCollageMediaControls(tripId, assetMediaById) {
  _assetMediaById = assetMediaById || {};
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
    var prevMediaClass = _assetMediaById[assetId] || "photo";
    selectEl.disabled = true;
    patchJson(apiUrl, { assetId: assetId, mediaClass: mediaClass })
      .then(function (res) {
        selectEl.disabled = false;
        if (res.status !== 200 || !res.body.ok) {
          showToolbarToast((res.body && res.body.error) || "改判失败", { error: true });
          selectEl.value = prevMediaClass === "collage" ? "collage" : "photo";
          return;
        }
        _assetMediaById[assetId] = mediaClass;
        selectEl.value = mediaClass;
        var toLabel = mediaClass === "collage" ? "拼图" : "普通照片";
        setLayoutPending(true, {
          kind: "media",
          assetId: assetId,
          mediaClass: mediaClass,
          prevMediaClass: prevMediaClass,
          label: "媒资改判 · " + assetId + " → " + toLabel,
        });
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
      sel.value = _assetMediaById[assetId] === "collage" ? "collage" : "photo";
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
      var wasFeatured = screen.getAttribute("data-featured") === "true";
      star.disabled = true;
      postJson(tripApiBase(tripId) + "/promote-tier", {
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
          setLayoutPending(true, {
            kind: "featured",
            assetId: assetId,
            wasFeatured: wasFeatured,
            label: "标为精选 · " + assetId,
          });
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

export function initTemplateBadge(root, tripId) {
  var editMenu = root.querySelector(".preview-toolbar__edit-tools-menu");
  var metaEl = root.querySelector(".preview-toolbar__trip-meta");
  if (!editMenu || editMenu.querySelector(".preview-toolbar__template-adjust")) return;
  fetchEntry(tripId).then(function (data) {
    var t = data && data.template;
    if (!t) return;
    trackStudioEvent("template_selector_impression", { surface: "preview", tripId: tripId });
    if (metaEl) {
      var parts = [];
      if (data.photoCount) parts.push(data.photoCount + " 张");
      var label = t.sourceLabel || "模板";
      if (t.locked) label += " · 已锁定";
      parts.push(label);
      metaEl.textContent = parts.join(" · ");
    }
    if (t.locked) return;
    var structBtn = editMenu.querySelector(".preview-toolbar__open-structure");
    var wrap = document.createElement("div");
    wrap.className = "preview-toolbar__template-adjust preview-toolbar__template-adjust--menu";
    wrap.setAttribute("role", "none");
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
    btn.className = "preview-toolbar__template-apply";
    btn.textContent = "应用模板";
    btn.addEventListener("click", function () {
      var v = String(sel.value || "smart");
      var body = { mode: v.indexOf("manual:") === 0 ? "manual" : "smart" };
      if (body.mode === "manual") body.templateId = v.slice(7);
      fetch("/__travelogue/trips/" + encodeURIComponent(tripId) + "/template", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      })
        .then(function (r) { return r.json().then(function (j) { return { ok: r.ok, j: j }; }); })
        .then(function (res) {
          if (!res.ok) {
            showToolbarToast((res.j && res.j.message) || "模板调整失败", { error: true });
            return;
          }
          showToolbarToast("模板策略已更新", { duration: 2000 });
          if (metaEl && res.j.template) {
            var next = (res.j.template.sourceLabel || "已更新") + " · 模板";
            metaEl.textContent = next;
          }
        })
        .catch(function () {
          showToolbarToast("模板调整失败", { error: true });
        });
    });
    wrap.appendChild(sel);
    wrap.appendChild(btn);
    if (structBtn) editMenu.insertBefore(wrap, structBtn);
    else editMenu.appendChild(wrap);
  }).catch(function () { /* ignore */ });
}

export function initEditToolsMenu(root, tripId, drawers) {
  var btn = root.querySelector(".preview-toolbar__edit-tools-btn");
  var menu = root.querySelector(".preview-toolbar__edit-tools-menu");
  if (!btn || !menu) return;

  var editBtn = menu.querySelector(".preview-toolbar__open-edit");
  var cohortBtn = menu.querySelector(".preview-toolbar__open-cohort");
  var structBtn = menu.querySelector(".preview-toolbar__open-structure");
  var applyMain = root.querySelector(".preview-toolbar__apply-layout-main");

  function closeMenu() {
    menu.hidden = true;
    btn.setAttribute("aria-expanded", "false");
  }

  btn.addEventListener("click", function (e) {
    e.stopPropagation();
    var willOpen = menu.hidden;
    menu.hidden = !willOpen;
    btn.setAttribute("aria-expanded", willOpen ? "true" : "false");
  });

  if (editBtn) {
    editBtn.addEventListener("click", function () {
      closeMenu();
      drawers.openEdit();
    });
  }
  if (cohortBtn) {
    fetch("/__travelogue/config")
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (cfg) {
        if (cfg && cfg.cohort && cfg.cohort.enabled) cohortBtn.hidden = false;
      })
      .catch(function () {});
    cohortBtn.addEventListener("click", function () {
      closeMenu();
      drawers.openCohort();
    });
  }
  if (structBtn) {
    structBtn.addEventListener("click", function () {
      closeMenu();
      drawers.openStructure();
    });
  }
  if (applyMain) {
    applyMain.addEventListener("click", function () {
      if (applyMain.disabled) return;
      applyLayoutRerender(tripId, root);
    });
  }

  document.addEventListener("click", function (ev) {
    if (!menu.contains(ev.target) && !btn.contains(ev.target)) {
      closeMenu();
    }
  });
}
