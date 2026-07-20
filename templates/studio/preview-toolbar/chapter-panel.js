/**
 * Preview Chrome Unify · F5 分章轻面板（D-PCU-12）
 * 章列表跳转 · 说明 · 重生 · 完成/确认并继续；不含拖拽。
 */
"use strict";

import { showToolbarToast } from "./shell.js";
import { loadChapterExplain } from "./drawers.js";
import { fetchEntry } from "./core.js";
import { trackStudioEvent } from "../js/analytics.js";

var CHAP_HINT_KEY = "travelogue.studio.chapterHintSeen";

export function chapterHintStorageKey(tripId) {
  return CHAP_HINT_KEY + "." + String(tripId || "global");
}

export function hasSeenChapterHint(tripId) {
  try {
    return !!(window.localStorage && window.localStorage.getItem(chapterHintStorageKey(tripId)));
  } catch (_e) {
    return true;
  }
}

export function markChapterHintSeen(tripId) {
  try {
    if (window.localStorage) {
      window.localStorage.setItem(chapterHintStorageKey(tripId), "1");
    }
  } catch (_e) {
    /* ignore */
  }
}

export function maybeShowChapterHintTip(root, tripId) {
  if (!root || !tripId || hasSeenChapterHint(tripId)) return;
  markChapterHintSeen(tripId);
  showToolbarToast("章节顺序不对？点上方「分章」调整", { duration: 5200 });
  trackStudioEvent("pcu_chapter_hint_shown", { tripId: tripId });
}

function scrollToChapter(chId) {
  if (!chId) return;
  var el = document.querySelector(
    'section.chapter[data-chapter-id="' + chId.replace(/"/g, "") + '"]'
  );
  if (!el) return;
  try {
    el.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (_e) {
    el.scrollIntoView(true);
  }
}

/**
 * @param {HTMLElement} root preview toolbar root
 * @param {string} tripId
 * @param {{ confirmStructure?: Function, regenerateStructure?: Function, close?: Function }} drawers
 * @param {{ close?: Function, isOpen?: Function }} sheet
 */
export function mountChapterPanel(root, tripId, drawers, sheet) {
  var panel = null;
  var open = false;
  var pendingMode = false;
  var dirtyAfterRegen = false;

  function ensureDom() {
    if (panel) return panel;
    panel = document.createElement("aside");
    panel.className = "preview-chapter-panel";
    panel.setAttribute("role", "dialog");
    panel.setAttribute("aria-label", "分章");
    panel.hidden = true;
    panel.innerHTML =
      '<header class="preview-chapter-panel__head">' +
      "<h2>分章</h2>" +
      '<button type="button" class="preview-chapter-panel__close" aria-label="关闭">×</button>' +
      "</header>" +
      '<p class="preview-chapter-panel__lead"></p>' +
      '<ul class="preview-chapter-panel__list"></ul>' +
      '<details class="preview-chapter-panel__explain"><summary>为什么这样分章</summary>' +
      '<div class="preview-chapter-panel__explain-body"></div></details>' +
      '<footer class="preview-chapter-panel__foot">' +
      '<button type="button" class="preview-chapter-panel__regen">重新生成</button>' +
      '<button type="button" class="preview-chapter-panel__primary">完成</button>' +
      "</footer>";
    document.body.appendChild(panel);

    panel.querySelector(".preview-chapter-panel__close").addEventListener("click", function () {
      closePanel();
    });
    panel.querySelector(".preview-chapter-panel__regen").addEventListener("click", function () {
      var btn = panel.querySelector(".preview-chapter-panel__regen");
      if (btn) btn.disabled = true;
      var p =
        drawers && typeof drawers.regenerateStructure === "function"
          ? drawers.regenerateStructure()
          : Promise.resolve();
      Promise.resolve(p)
        .then(function () {
          dirtyAfterRegen = true;
          return renderBody();
        })
        .finally(function () {
          if (btn) btn.disabled = false;
        });
    });
    panel.querySelector(".preview-chapter-panel__primary").addEventListener("click", function () {
      var btn = panel.querySelector(".preview-chapter-panel__primary");
      // 实验 pending，或重生后需再次锁定
      if (pendingMode || dirtyAfterRegen) {
        if (btn) btn.disabled = true;
        var wasDirty = dirtyAfterRegen;
        var p =
          drawers && typeof drawers.confirmStructure === "function"
            ? drawers.confirmStructure()
            : Promise.resolve();
        Promise.resolve(p)
          .then(function () {
            pendingMode = false;
            dirtyAfterRegen = false;
            closePanel();
            showToolbarToast(wasDirty ? "结构调整已保存" : "章节已确认，继续成册");
          })
          .finally(function () {
            if (btn) btn.disabled = false;
          });
        return;
      }
      closePanel();
    });

    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && open) {
        e.preventDefault();
        closePanel();
      }
    });
    return panel;
  }

  function setChapBtnPressed(on) {
    var btn = root && root.querySelector(".preview-toolbar__dock-btn--chapters");
    if (!btn) return;
    btn.classList.toggle("is-active", !!on);
    btn.setAttribute("aria-pressed", on ? "true" : "false");
  }

  function renderBody() {
    var el = ensureDom();
    var lead = el.querySelector(".preview-chapter-panel__lead");
    var list = el.querySelector(".preview-chapter-panel__list");
    var primary = el.querySelector(".preview-chapter-panel__primary");
    var explainBody = el.querySelector(".preview-chapter-panel__explain-body");

    return fetchEntry(tripId).then(function (entry) {
      entry = entry || {};
      pendingMode = !!(
        entry.g1Pending || String(entry.pipelineStatus || "") === "structure_draft"
      );
      if (lead) {
        lead.textContent = pendingMode
          ? "请浏览各章顺序，确认后继续成册。"
          : "浏览各章，或重新生成结构。深改请用「精修 · 这本」。";
      }
      if (primary) {
        if (pendingMode) primary.textContent = "确认并继续";
        else if (dirtyAfterRegen) primary.textContent = "保存调整";
        else primary.textContent = "完成";
      }
      list.innerHTML = "";
      var chapters = entry.chapters || [];
      chapters.forEach(function (ch, idx) {
        var li = document.createElement("li");
        var btn = document.createElement("button");
        btn.type = "button";
        btn.className = "preview-chapter-panel__chap";
        btn.textContent = (idx + 1) + ". " + (ch.title || ch.id || "未命名");
        btn.addEventListener("click", function () {
          scrollToChapter(ch.id);
        });
        li.appendChild(btn);
        list.appendChild(li);
      });
      if (!chapters.length) {
        var empty = document.createElement("li");
        empty.className = "preview-chapter-panel__empty";
        empty.textContent = "暂无章节";
        list.appendChild(empty);
      }
      if (explainBody) {
        explainBody.innerHTML = "";
        loadChapterExplain(tripId, explainBody);
      }
    });
  }

  function openPanel(opts) {
    opts = opts || {};
    if (sheet && typeof sheet.isOpen === "function" && sheet.isOpen() && typeof sheet.close === "function") {
      sheet.close("chapter", function () {
        openPanel(opts);
      });
      return;
    }
    if (drawers && typeof drawers.close === "function") {
      try {
        drawers.close();
      } catch (_e) {
        /* ignore */
      }
    }
    ensureDom();
    open = true;
    panel.hidden = false;
    setChapBtnPressed(true);
    trackStudioEvent("pcu_chapter_panel_open", {
      tripId: tripId,
      auto: !!opts.auto,
      pending: !!opts.pending,
    });
    renderBody();
  }

  function closePanel() {
    if (!panel) return;
    open = false;
    panel.hidden = true;
    setChapBtnPressed(false);
  }

  function toggle() {
    if (open) closePanel();
    else openPanel({});
  }

  return {
    open: openPanel,
    close: closePanel,
    toggle: toggle,
    isOpen: function () {
      return open;
    },
  };
}
