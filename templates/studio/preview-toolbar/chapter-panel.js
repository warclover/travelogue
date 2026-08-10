/**
 * Preview Chrome Unify · F5 分章轻面板（D-PCU-12）
 * 章列表跳转 · 说明 · 重生 · 完成/确认并继续；不含拖拽。
 */
"use strict";

import { showToolbarToast, tripApiBase } from "./shell.js";
import { loadChapterExplain } from "./drawers.js";
import { fetchEntry } from "./core.js";
import { trackStudioEvent } from "../js/analytics.js";
import { postJsonConflictRetry } from "../js/http.js";
import { closeStudioExportPopover } from "./longshot.js";

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
      '<button type="button" class="preview-chapter-panel__regen">重新分章</button>' +
      '<button type="button" class="preview-chapter-panel__primary">完成</button>' +
      "</footer>";
    document.body.appendChild(panel);

    panel.querySelector(".preview-chapter-panel__close").addEventListener("click", function () {
      closePanel();
    });
    panel.querySelector(".preview-chapter-panel__regen").addEventListener("click", function () {
      var btn = panel.querySelector(".preview-chapter-panel__regen");
      var primary = panel.querySelector(".preview-chapter-panel__primary");
      if (btn) btn.disabled = true;
      if (primary) primary.disabled = true;
      var p =
        drawers && typeof drawers.regenerateStructure === "function"
          ? drawers.regenerateStructure()
          : Promise.resolve();
      Promise.resolve(p)
        .then(function () {
          // Terminal success only (CQA D-04) — drawers may reload; if not, refresh body
          dirtyAfterRegen = true;
          return renderBody();
        })
        .catch(function () {
          // Error toast owned by drawers; keep panel open for retry
        })
        .finally(function () {
          if (btn) btn.disabled = false;
          if (primary) primary.disabled = false;
        });
    });
    panel.querySelector(".preview-chapter-panel__primary").addEventListener("click", function () {
      var btn = panel.querySelector(".preview-chapter-panel__primary");
      var regen = panel.querySelector(".preview-chapter-panel__regen");
      // 实验 pending，或重生后需再次锁定
      if (pendingMode || dirtyAfterRegen) {
        if (btn) btn.disabled = true;
        if (regen) regen.disabled = true;
        var wasDirty = dirtyAfterRegen;
        var p =
          drawers && typeof drawers.confirmStructure === "function"
            ? drawers.confirmStructure()
            : Promise.resolve();
        Promise.resolve(p)
          .then(function () {
            // Only after job terminal success — drawers may reload the page
            pendingMode = false;
            dirtyAfterRegen = false;
            closePanel();
            showToolbarToast(wasDirty ? "结构调整已保存" : "章节已确认，继续成册");
          })
          .catch(function () {
            // Keep panel open; no false "已保存"
          })
          .finally(function () {
            if (btn) btn.disabled = false;
            if (regen) regen.disabled = false;
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
          : "浏览各章，可改名或重新分章。";
      }
      if (primary) {
        if (pendingMode) primary.textContent = "确认并继续";
        else if (dirtyAfterRegen) primary.textContent = "保存调整";
        else primary.textContent = "完成";
      }
      list.innerHTML = "";
      var chapters = entry.chapters || [];
      var suggestions = entry.layoutSuggestions || [];
      var sugByChapter = {};
      suggestions.forEach(function (s) {
        if (!s || !s.chapterId) return;
        if (!sugByChapter[s.chapterId]) sugByChapter[s.chapterId] = s;
      });
      chapters.forEach(function (ch, idx) {
        var li = document.createElement("li");
        li.className = "preview-chapter-panel__row";
        if (ch.isAppendix) li.className += " preview-chapter-panel__row--appendix";
        var btn = document.createElement("button");
        btn.type = "button";
        btn.className = "preview-chapter-panel__chap";
        btn.textContent = (idx + 1) + ". " + (ch.title || ch.id || "未命名");
        btn.addEventListener("click", function () {
          scrollToChapter(ch.id);
        });
        li.appendChild(btn);
        if (ch.isAppendix) {
          var reason = document.createElement("p");
          reason.className = "preview-chapter-panel__appendix-reason";
          reason.textContent =
            ch.appendixReason || "拍摄时间远离行程主时段，已归入往年旧照";
          li.appendChild(reason);
          var restore = document.createElement("button");
          restore.type = "button";
          restore.className = "preview-chapter-panel__restore";
          restore.textContent = "移回主行程";
          restore.addEventListener("click", function (ev) {
            ev.preventDefault();
            ev.stopPropagation();
            restoreAppendixChapter(ch);
          });
          li.appendChild(restore);
        } else {
          // FE-SFI-08 · 行内改名（失焦保存 · chapters.{id}.title）
          var rename = document.createElement("button");
          rename.type = "button";
          rename.className = "preview-chapter-panel__rename";
          rename.textContent = "改名";
          rename.addEventListener("click", function (ev) {
            ev.preventDefault();
            ev.stopPropagation();
            beginInlineRename(li, ch, idx, btn);
          });
          li.appendChild(rename);
          var feedback = document.createElement("button");
          feedback.type = "button";
          feedback.className = "preview-chapter-panel__feedback";
          feedback.textContent = "这章不对";
          feedback.addEventListener("click", function (ev) {
            ev.preventDefault();
            ev.stopPropagation();
            submitChapterFeedback(ch);
          });
          li.appendChild(feedback);
          var sug = sugByChapter[ch.id];
          if (sug && sug.suggestion) {
            var hint = document.createElement("p");
            hint.className = "preview-chapter-panel__ai-hint";
            hint.textContent = sug.suggestion;
            if (!sug.accepted && sug.suggestedPatternId) {
              var accept = document.createElement("button");
              accept.type = "button";
              accept.className = "preview-chapter-panel__ai-accept";
              accept.textContent = "采纳建议";
              accept.addEventListener("click", function (ev) {
                ev.preventDefault();
                ev.stopPropagation();
                acceptLayoutSuggestion(ch, sug, hint, accept);
              });
              li.appendChild(hint);
              li.appendChild(accept);
            } else {
              if (sug.accepted) hint.textContent = sug.suggestion + "（已采纳）";
              li.appendChild(hint);
            }
            trackStudioEvent("layout_critic_suggestion_shown", {
              tripId: tripId,
              chapterId: ch.id,
            });
          }
        }
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
        var freeze = document.createElement("p");
        freeze.className = "preview-chapter-panel__freeze";
        freeze.textContent = "章节按拍摄节奏切分，同一天可能出现在多章";
        explainBody.appendChild(freeze);
        loadChapterExplain(tripId, explainBody);
      }
    });
  }

  function submitChapterFeedback(ch) {
    if (!ch || !ch.id) return;
    var reason = window.prompt(
      "这章哪里不对？\n1 too_many_photos 图太多\n2 too_few_photos 图太少\n3 wrong_order 顺序不对\n4 style_mismatch 风格不搭\n5 other\n请输入编号或 reason：",
      "1"
    );
    if (reason == null) return;
    var map = {
      "1": "too_many_photos",
      "2": "too_few_photos",
      "3": "wrong_order",
      "4": "style_mismatch",
      "5": "other",
    };
    var code = map[String(reason).trim()] || String(reason).trim();
    postJsonConflictRetry(tripApiBase(tripId) + "/ai/layout-feedback", {
      chapterId: ch.id,
      reason: code,
    })
      .then(function (res) {
        if (!res || res.status < 200 || res.status >= 300) {
          showToolbarToast(
            (res && res.body && res.body.message) || "反馈未保存"
          );
          return;
        }
        showToolbarToast("已记下，下次排版建议会参考");
      })
      .catch(function () {
        showToolbarToast("反馈未保存");
      });
  }

  function acceptLayoutSuggestion(ch, sug, hintEl, acceptBtn) {
    if (!ch || !ch.id || !sug) return;
    postJsonConflictRetry(tripApiBase(tripId) + "/ai/layout-critic/accept", {
      chapterId: ch.id,
      suggestedPatternId: sug.suggestedPatternId || undefined,
    })
      .then(function (res) {
        if (!res || res.status < 200 || res.status >= 300) {
          showToolbarToast(
            (res && res.body && res.body.message) || "采纳失败"
          );
          return;
        }
        if (hintEl) hintEl.textContent = (sug.suggestion || "") + "（已采纳）";
        if (acceptBtn && acceptBtn.parentNode) acceptBtn.parentNode.removeChild(acceptBtn);
        showToolbarToast("已采纳建议（下次重生时参考）");
      })
      .catch(function () {
        showToolbarToast("采纳失败");
      });
  }

  function restoreAppendixChapter(ch) {
    if (!ch || !ch.id) return;
    postJsonConflictRetry(tripApiBase(tripId) + "/promote-tier", {
      action: "restoreTimeOutlier",
      assetIds: ch.appendixAssetIds || [],
      rerender: false,
    })
      .then(function (res) {
        if (!res || res.status < 200 || res.status >= 300) {
          showToolbarToast(
            (res && res.body && res.body.message) || "移回未完成，请稍后重试"
          );
          return;
        }
        showToolbarToast("已移回，正在重新分章…");
        if (drawers && typeof drawers.regenerateStructure === "function") {
          return drawers.regenerateStructure();
        }
      })
      .catch(function () {
        showToolbarToast("移回未完成");
      });
  }

  function beginInlineRename(li, ch, idx, titleBtn) {
    if (!ch || !ch.id) return;
    if (li.querySelector("input.preview-chapter-panel__rename-input")) return;
    var input = document.createElement("input");
    input.type = "text";
    input.className = "preview-chapter-panel__rename-input";
    input.value = ch.title || "";
    input.maxLength = 12;
    input.setAttribute("aria-label", "章名");
    titleBtn.hidden = true;
    var renameBtn = li.querySelector(".preview-chapter-panel__rename");
    if (renameBtn) renameBtn.hidden = true;
    li.insertBefore(input, titleBtn);
    input.focus();
    input.select();

    var saving = false;
    var composing = false;
    var blurTimer = null;
    function finish(commit) {
      if (saving) return;
      if (composing) return;
      saving = true;
      if (blurTimer) {
        window.clearTimeout(blurTimer);
        blurTimer = null;
      }
      var next = String(input.value || "").trim().slice(0, 12);
      input.remove();
      titleBtn.hidden = false;
      if (renameBtn) renameBtn.hidden = false;
      if (!commit || next === String(ch.title || "").trim()) {
        return;
      }
      titleBtn.textContent = idx + 1 + ". " + (next || "未命名");
      postJsonConflictRetry(tripApiBase(tripId) + "/save-copy", {
        patches: [{ path: "chapters." + ch.id + ".title", value: next }],
      })
        .then(function (res) {
          if (res && res.status >= 200 && res.status < 300) {
            ch.title = next;
            dirtyAfterRegen = true;
            showToolbarToast("章名已保存");
          } else {
            titleBtn.textContent = idx + 1 + ". " + (ch.title || ch.id || "未命名");
            showToolbarToast(
              (res && res.body && res.body.message) || "章名未保存"
            );
          }
        })
        .catch(function () {
          titleBtn.textContent = idx + 1 + ". " + (ch.title || ch.id || "未命名");
          showToolbarToast("章名未保存");
        });
    }

    // D-SFI-09 · IME 防抖：composition 期间不 blur 提交
    input.addEventListener("compositionstart", function () {
      composing = true;
    });
    input.addEventListener("compositionend", function () {
      composing = false;
    });
    input.addEventListener("blur", function () {
      if (composing) {
        blurTimer = window.setTimeout(function () {
          if (!composing) finish(true);
        }, 120);
        return;
      }
      finish(true);
    });
    input.addEventListener("keydown", function (e) {
      if (e.key === "Enter" && !composing) {
        e.preventDefault();
        input.blur();
      } else if (e.key === "Escape") {
        e.preventDefault();
        finish(false);
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
    // SAS · D-SAS-04 / SHD-SAS-02 · 与 AI Sheet 互斥
    try {
      if (root._aiSheet && root._aiSheet.isOpen && root._aiSheet.isOpen()) {
        root._aiSheet.close("chapter");
      }
    } catch (_eAi) {
      /* ignore */
    }
    if (drawers && typeof drawers.close === "function") {
      try {
        drawers.close();
      } catch (_e) {
        /* ignore */
      }
    }
    // SFP D-SFP-10 · 浮层互斥：打开分章前关掉导出设置
    try {
      closeStudioExportPopover();
    } catch (_eExp) {
      /* ignore */
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
