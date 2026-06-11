/**
 * Preview toolbar · edit/structure/cohort drawers (M-P2b · §7.1).
 */
"use strict";

import { postJson, patchJson } from "../js/http.js";
import { pollJobUntilDone } from "../js/job-poll.js";
import { STUDIO_USER_NOTES_MAX_LEN } from "../js/constants.js";
import { mountCohortDrawer } from "../cohort-drawer.js";
import { setToolbarCollapsed } from "./shell.js";
import { tripApiBase, toolbarConfirm, showToolbarToast } from "./toolbar-ui.js";
import { hasLayoutPending } from "./pending.js";
import { applyLayoutRerender } from "./mode-edit.js";
import { startLlmNarrate } from "./narrate.js";
import {
  COPY_INTENT_MOODS,
  COPY_INTENT_FOCUSES,
  trapDrawerFocus,
  buildCopyIntentChipHtml,
  copyIntentApiUrl,
  fetchEntry,
  currentChapterId,
  renderExplainBlock,
  loadChapterExplain,
  loadAestheticExplain,
} from "./drawer-support.js";

export function initPreviewDrawers(root, tripId) {
  var shell = document.createElement("div");
  shell.className = "preview-drawer-root";
  shell.hidden = true;
  shell.innerHTML =
    '<div class="preview-drawer__scrim"></div>' +
    '<div class="preview-drawer" role="dialog" aria-modal="true" aria-labelledby="preview-drawer-title" hidden>' +
    '<div class="preview-drawer__handle" aria-hidden="true"></div>' +
    '<div class="preview-drawer__head">' +
    '<h2 id="preview-drawer-title" class="preview-drawer__title"></h2>' +
    '<button type="button" class="preview-drawer__close" aria-label="关闭">×</button>' +
    "</div>" +
    '<div class="preview-drawer__body"></div>' +
    "</div>";
  document.body.appendChild(shell);

  var drawer = shell.querySelector(".preview-drawer");
  var titleEl = shell.querySelector(".preview-drawer__title");
  var bodyEl = shell.querySelector(".preview-drawer__body");
  var scrim = shell.querySelector(".preview-drawer__scrim");
  var closeBtn = shell.querySelector(".preview-drawer__close");
  var entryCache = null;
  var drawerFocusRelease = null;
  var drawerPreviousFocus = null;

  var editTpl =
    '<label class="preview-drawer__label" for="preview-drawer-title-input">杂志名</label>' +
    '<input id="preview-drawer-title-input" class="preview-drawer__title-input" type="text" maxlength="20" autocomplete="off" placeholder="我的旅途">' +
    '<label class="preview-drawer__label" for="preview-drawer-notes">写给编辑的一句话</label>' +
    '<textarea id="preview-drawer-notes" class="preview-drawer__notes" maxlength="' +
    STUDIO_USER_NOTES_MAX_LEN +
    '" rows="3" placeholder="例如：带娃慢走，想突出雨后的京都"></textarea>' +
    '<p class="preview-drawer__chapter-label">当前章：<strong class="preview-drawer__chapter-name"></strong></p>' +
    '<p class="preview-drawer__label">记忆锚点（0–3 个）</p>' +
    '<div class="preview-drawer__anchors">' +
    '<input type="text" class="preview-drawer__anchor" maxlength="24" placeholder="锚点 1">' +
    '<input type="text" class="preview-drawer__anchor" maxlength="24" placeholder="锚点 2">' +
    '<input type="text" class="preview-drawer__anchor" maxlength="24" placeholder="锚点 3">' +
    "</div>" +
    '<p class="preview-drawer__hint">短词即可，会写进图说，不会瞎编</p>' +
    '<details class="preview-drawer__copy-intent">' +
    '<summary class="preview-drawer__label">章级意图（可选）</summary>' +
    '<p class="preview-drawer__sublabel">这一章更像什么感觉？</p>' +
    '<div class="preview-drawer__chips preview-drawer__chips--mood" role="group" aria-label="章级情绪">' +
    buildCopyIntentChipHtml(COPY_INTENT_MOODS, "preview-drawer__chip-mood") +
    "</div>" +
    '<p class="preview-drawer__sublabel">更想突出什么？</p>' +
    '<div class="preview-drawer__chips preview-drawer__chips--focus" role="group" aria-label="章级关注点">' +
    buildCopyIntentChipHtml(COPY_INTENT_FOCUSES, "preview-drawer__chip-focus") +
    "</div>" +
    '<label class="preview-drawer__label" for="preview-drawer-copy-intent-note">短念头（≤30 字）</label>' +
    '<input id="preview-drawer-copy-intent-note" class="preview-drawer__copy-intent-note" type="text" maxlength="30" autocomplete="off" placeholder="例如：雨停后风很轻">' +
    '<label class="preview-drawer__copy-intent-apply">' +
    '<input type="checkbox" class="preview-drawer__copy-intent-subsequent" /> 应用到后续章节' +
    "</label>" +
    '<p class="preview-drawer__hint preview-drawer__copy-intent-hint">可选填；有语音素材时会优先用原声</p>' +
    '<p class="preview-drawer__hint preview-drawer__copy-intent-voice-skip" hidden>本章有录音，已优先用原声，无需填写意图</p>' +
    "</details>" +
    '<p class="preview-drawer__featured-help">★ 在任意一屏右下角可将照片标为精选，之后点「应用排版」生效</p>' +
    '<p class="preview-drawer__featured-help">拼图/整图屏左上角可改判媒资类型（普通照片 ↔ 拼图），改后请应用排版</p>' +
    '<button type="button" class="preview-drawer__ghost preview-drawer__narrate-anchors">保存并重新生成文案</button>' +
    '<button type="button" class="preview-drawer__primary preview-drawer__save-edit">保存编辑</button>';

  var structTpl =
    '<div class="preview-drawer__g1"></div>' +
    '<div class="preview-drawer__g1-actions" hidden>' +
    '<button type="button" class="preview-drawer__g1-confirm">章节顺序 OK</button>' +
    '<button type="button" class="preview-drawer__g1-regenerate">重新生成结构</button>' +
    "</div>" +
    '<div class="preview-drawer__explain"></div>' +
    '<div class="preview-drawer__aesthetic" hidden></div>' +
    '<button type="button" class="preview-drawer__primary preview-drawer__apply-layout">应用排版</button>';

  function pollStudioJob(jobId, onDone) {
    pollJobUntilDone(jobId, { intervalMs: 800 })
      .then(onDone)
      .catch(function () {
        onDone({ status: "failed", error: { message: "网络错误" } });
      });
  }

  function confirmG1Structure() {
    return patchJson("/__travelogue/trips/" + encodeURIComponent(tripId) + "/pipeline", {
      status: "structure_locked",
      continuePipeline: true,
    });
  }

  function chapterRow(chId) {
    if (!entryCache || !entryCache.chapters) return null;
    for (var i = 0; i < entryCache.chapters.length; i++) {
      if (entryCache.chapters[i].id === chId) return entryCache.chapters[i];
    }
    return null;
  }

  function fillAnchors(chId) {
    var inputs = bodyEl.querySelectorAll(".preview-drawer__anchor");
    var row = chapterRow(chId);
    var anchors = (row && row.memoryAnchors) || [];
    for (var i = 0; i < inputs.length; i++) {
      inputs[i].value = anchors[i] || "";
    }
    var nameEl = bodyEl.querySelector(".preview-drawer__chapter-name");
    if (nameEl) nameEl.textContent = (row && row.title) || chId || "—";
  }

  function wireChipGroup(container, chipClass) {
    if (!container) return;
    container.querySelectorAll("." + chipClass).forEach(function (btn) {
      btn.addEventListener("click", function () {
        var wasSelected = btn.classList.contains("is-selected");
        container.querySelectorAll("." + chipClass).forEach(function (b) {
          b.classList.remove("is-selected");
          b.setAttribute("aria-pressed", "false");
        });
        if (!wasSelected) {
          btn.classList.add("is-selected");
          btn.setAttribute("aria-pressed", "true");
        }
      });
    });
  }

  function fillCopyIntent(chId) {
    var row = chapterRow(chId);
    var intent = (row && row.copyIntent) || {};
    bodyEl.querySelectorAll(".preview-drawer__chip-mood").forEach(function (btn) {
      var on = btn.getAttribute("data-value") === intent.mood;
      btn.classList.toggle("is-selected", on);
      btn.setAttribute("aria-pressed", on ? "true" : "false");
    });
    bodyEl.querySelectorAll(".preview-drawer__chip-focus").forEach(function (btn) {
      var on = btn.getAttribute("data-value") === intent.focus;
      btn.classList.toggle("is-selected", on);
      btn.setAttribute("aria-pressed", on ? "true" : "false");
    });
    var noteInp = bodyEl.querySelector(".preview-drawer__copy-intent-note");
    if (noteInp) noteInp.value = intent.note || "";
    updateCopyIntentVisibility(chId);
  }

  function chapterHasVoice(chId) {
    var row = chapterRow(chId);
    return !!(row && row.hasVoice);
  }

  function updateCopyIntentVisibility(chId) {
    var details = bodyEl.querySelector(".preview-drawer__copy-intent");
    var skipNote = bodyEl.querySelector(".preview-drawer__copy-intent-voice-skip");
    var hint = bodyEl.querySelector(".preview-drawer__copy-intent-hint");
    var applyLabel = bodyEl.querySelector(".preview-drawer__copy-intent-apply");
    if (!details) return;
    var skip = chapterHasVoice(chId);
    details.open = !skip && details.open;
    details.hidden = skip;
    if (skipNote) skipNote.hidden = !skip;
    if (hint) hint.hidden = skip;
    if (applyLabel) applyLabel.hidden = skip;
  }

  function readCopyIntentPayload() {
    if (chapterHasVoice(currentChapterId())) {
      return null;
    }
    var moodBtn = bodyEl.querySelector(".preview-drawer__chip-mood.is-selected");
    var focusBtn = bodyEl.querySelector(".preview-drawer__chip-focus.is-selected");
    var noteInp = bodyEl.querySelector(".preview-drawer__copy-intent-note");
    var subsequent = bodyEl.querySelector(".preview-drawer__copy-intent-subsequent");
    var noteVal = noteInp ? (noteInp.value || "").trim() : "";
    var payload;
    if (!moodBtn && !focusBtn && !noteVal) {
      payload = { clear: true };
    } else {
      payload = {
        mood: moodBtn ? moodBtn.getAttribute("data-value") : null,
        focus: focusBtn ? focusBtn.getAttribute("data-value") : null,
        note: noteVal || null,
      };
    }
    if (subsequent && subsequent.checked) {
      payload.applyToSubsequent = true;
    }
    return payload;
  }

  function fillChapterFields(chId) {
    fillAnchors(chId);
    fillCopyIntent(chId);
  }

  function closeDrawer() {
    if (drawerFocusRelease) {
      drawerFocusRelease();
      drawerFocusRelease = null;
    }
    shell.hidden = true;
    drawer.hidden = true;
    document.body.classList.remove("preview-drawer-open");
    if (drawerPreviousFocus && drawerPreviousFocus.focus) {
      drawerPreviousFocus.focus();
    }
    drawerPreviousFocus = null;
  }

  function activateDrawerFocus() {
    drawerPreviousFocus = document.activeElement;
    if (drawerFocusRelease) drawerFocusRelease();
    closeBtn.focus();
    drawerFocusRelease = trapDrawerFocus(drawer);
  }

  function runG1Confirm(triggerBtn) {
    if (triggerBtn) triggerBtn.disabled = true;
    showToolbarToast("正在确认并继续制作…");
    return confirmG1Structure()
      .then(function (res) {
        if (res.status === 202 && res.body && res.body.jobId) {
          pollStudioJob(res.body.jobId, function (job) {
            if (triggerBtn) triggerBtn.disabled = false;
            if (job.status === "succeeded") {
              showToolbarToast("章节已确认，杂志已更新");
              window.location.reload();
              return;
            }
            var err = (job.error && (job.error.message || job.error.code)) || "确认失败";
            showToolbarToast(err, { error: true });
          });
          return;
        }
        if (triggerBtn) triggerBtn.disabled = false;
        showToolbarToast((res.body && res.body.error) || "确认失败", { error: true });
      })
      .catch(function () {
        if (triggerBtn) triggerBtn.disabled = false;
        showToolbarToast("确认失败", { error: true });
      });
  }

  function openDrawer(mode) {
    if (!entryCache) {
      fetchEntry(tripId).then(function (data) {
        entryCache = data || {};
        openDrawer(mode);
      });
      return;
    }
    shell.hidden = false;
    drawer.hidden = false;
    document.body.classList.add("preview-drawer-open");
    setToolbarCollapsed(root, false, false);
    requestAnimationFrame(activateDrawerFocus);

    if (mode === "edit") {
      titleEl.textContent = "编辑";
      bodyEl.innerHTML = editTpl;
      var titleInput = bodyEl.querySelector(".preview-drawer__title-input");
      var notes = bodyEl.querySelector(".preview-drawer__notes");
      if (titleInput && entryCache.intentSummary) {
        titleInput.value = entryCache.intentSummary.title || "";
      }
      if (notes && entryCache.intentSummary) {
        notes.value = entryCache.intentSummary.userNotes || "";
      }
      fillChapterFields(currentChapterId());
      wireChipGroup(bodyEl.querySelector(".preview-drawer__chips--mood"), "preview-drawer__chip-mood");
      wireChipGroup(bodyEl.querySelector(".preview-drawer__chips--focus"), "preview-drawer__chip-focus");

      function persistEditDrawer(btn, opts) {
        opts = opts || {};
        var chId = currentChapterId();
        var titleVal = (titleInput && titleInput.value || "").trim();
        var notesVal = (notes.value || "").trim();
        var anchorInputs = bodyEl.querySelectorAll(".preview-drawer__anchor");
        var anchors = [];
        anchorInputs.forEach(function (inp) {
          var v = (inp.value || "").trim();
          if (v) anchors.push(v);
        });
        btn.disabled = true;
        if (titleVal.length > 20) {
          btn.disabled = false;
          showToolbarToast("杂志名最多 20 个字", { error: true });
          return Promise.resolve(false);
        }
        var tasks = [
          patchJson("/__travelogue/trips/" + encodeURIComponent(tripId) + "/intent", {
            title: titleVal || null,
            userNotes: notesVal || null,
          }),
        ];
        if (chId) {
          tasks.push(
            postJson(tripApiBase(tripId) + "/save-copy", {
              patches: [{
                path: "chapters." + chId + ".curation.memoryAnchors",
                value: anchors.join(", "),
              }],
            })
          );
          var copyIntentPayload = readCopyIntentPayload();
          if (copyIntentPayload) {
            tasks.push(patchJson(copyIntentApiUrl(tripId, chId), copyIntentPayload));
          }
        }
        return Promise.all(tasks)
          .then(function (results) {
            btn.disabled = false;
            var ok = results.every(function (r) { return r.status === 200 && r.body.ok; });
            if (!ok) {
              var errMsg = "保存失败";
              results.forEach(function (r) {
                if (r.status !== 200 || !r.body.ok) {
                  errMsg = (r.body && (r.body.message || r.body.error)) || errMsg;
                }
              });
              showToolbarToast(errMsg, { error: true });
              return false;
            }
            if (entryCache.intentSummary) {
              entryCache.intentSummary.userNotes = notesVal;
              if (titleVal) entryCache.intentSummary.title = titleVal;
            }
            if (chId && entryCache.chapters) {
              var row = chapterRow(chId);
              if (row) {
                row.memoryAnchors = anchors;
                var ciResult = null;
                for (var ri = 0; ri < results.length; ri++) {
                  if (results[ri].body && "copyIntent" in results[ri].body) {
                    ciResult = results[ri];
                    break;
                  }
                }
                if (ciResult && ciResult.body) {
                  row.copyIntent = ciResult.body.copyIntent || null;
                  var appliedIds = ciResult.body.chapterIds || [chId];
                  appliedIds.forEach(function (appliedId) {
                    var appliedRow = chapterRow(appliedId);
                    if (appliedRow) {
                      appliedRow.copyIntent = ciResult.body.copyIntent || null;
                    }
                  });
                }
              }
            }
            if (!opts.skipToast) {
              var copyIntentPayload = readCopyIntentPayload();
              var hasIntent = copyIntentPayload && copyIntentPayload.clear !== true;
              showToolbarToast(
                anchors.length > 0 || hasIntent
                  ? "编辑已保存。可在 ⋯ 菜单中重新生成文案以写入锚点与点缀。"
                  : "编辑已保存"
              );
            }
            return true;
          })
          .catch(function () {
            btn.disabled = false;
            showToolbarToast("保存失败", { error: true });
            return false;
          });
      }

      bodyEl.querySelector(".preview-drawer__save-edit").addEventListener("click", function () {
        var btn = this;
        persistEditDrawer(btn).then(function (ok) {
          if (ok) closeDrawer();
        });
      });
      var narrateAnchorsBtn = bodyEl.querySelector(".preview-drawer__narrate-anchors");
      if (narrateAnchorsBtn) {
        narrateAnchorsBtn.addEventListener("click", function () {
          var btn = this;
          persistEditDrawer(btn, { skipToast: true }).then(function (ok) {
            if (!ok) return;
            closeDrawer();
            startLlmNarrate(root, tripId, btn);
          });
        });
      }
      return;
    }

    if (mode === "cohort") {
      titleEl.textContent = "旅行主角 · 同框";
      bodyEl.innerHTML = "";
      mountCohortDrawer({
        tripId: tripId,
        bodyEl: bodyEl,
        showToast: showToolbarToast,
        onClose: closeDrawer,
        onEntryRefresh: function () {
          return fetchEntry(tripId).then(function (data) {
            entryCache = data || {};
            return entryCache;
          });
        },
        onApplyLayout: function () {
          return applyLayoutRerender(tripId, root);
        },
      });
      return;
    }

    titleEl.textContent = "结构";
    bodyEl.innerHTML = structTpl;
    var g1 = bodyEl.querySelector(".preview-drawer__g1");
    var g1Actions = bodyEl.querySelector(".preview-drawer__g1-actions");
    var status = entryCache.pipelineStatus || "";
    var pending = entryCache.g1Pending || status === "structure_draft";
    if (pending) {
      g1.className = "preview-drawer__g1 preview-drawer__g1--warn";
      g1.textContent = "章节结构待确认：请浏览各章顺序，确认后将生成文案并完成排版。";
      if (g1Actions) g1Actions.hidden = false;
      var confirmBtn = bodyEl.querySelector(".preview-drawer__g1-confirm");
      var regenBtn = bodyEl.querySelector(".preview-drawer__g1-regenerate");
      if (confirmBtn) {
        confirmBtn.addEventListener("click", function () {
          runG1Confirm(confirmBtn);
        });
      }
      if (regenBtn) {
        regenBtn.addEventListener("click", function () {
          toolbarConfirm({
            title: "重新生成结构",
            body: "将重新生成章节结构，可能覆盖当前分章。继续？",
            confirmText: "继续",
            danger: true,
          }).then(function (ok) {
            if (!ok) return;
            regenBtn.disabled = true;
            return postJson("/__travelogue/trips/" + encodeURIComponent(tripId) + "/curate", { force: true });
          }).then(function (res) {
            if (!res) return;
            if (res.status === 202 && res.body && res.body.jobId) {
              pollStudioJob(res.body.jobId, function (job) {
                regenBtn.disabled = false;
                if (job.status === "succeeded") {
                  showToolbarToast("结构已重新生成");
                  window.location.reload();
                  return;
                }
                showToolbarToast("重新生成失败", { error: true });
              });
              return;
            }
            regenBtn.disabled = false;
            showToolbarToast("无法开始", { error: true });
          }).catch(function () {
            regenBtn.disabled = false;
            showToolbarToast("重新生成失败", { error: true });
          });
        });
      }
    } else {
      g1.className = "preview-drawer__g1 preview-drawer__g1--info";
      g1.textContent = "章节已按行程排好，可在预览中改字、锚点与精选。";
      if (g1Actions) g1Actions.hidden = true;
    }
    loadChapterExplain(tripId, bodyEl.querySelector(".preview-drawer__explain"));
    loadAestheticExplain(tripId, bodyEl.querySelector(".preview-drawer__aesthetic"));
    var applyBtn = bodyEl.querySelector(".preview-drawer__apply-layout");
    applyBtn.hidden = !hasLayoutPending();
    applyBtn.addEventListener("click", function () {
      closeDrawer();
      applyLayoutRerender(tripId, root);
    });
  }

  scrim.addEventListener("click", closeDrawer);
  closeBtn.addEventListener("click", closeDrawer);
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && !shell.hidden) closeDrawer();
  });

  fetchEntry(tripId).then(function (data) {
    entryCache = data || {};
  });

  return {
    openEdit: function () { openDrawer("edit"); },
    openStructure: function () { openDrawer("structure"); },
    openCohort: function () { openDrawer("cohort"); },
    confirmStructure: function () { return runG1Confirm(null); },
    close: closeDrawer,
    refreshEntry: function () {
      return fetchEntry(tripId).then(function (data) {
        entryCache = data || {};
        return entryCache;
      });
    },
  };
}
