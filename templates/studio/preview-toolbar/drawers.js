/**
 * Preview toolbar · overlay drawers (edit / structure / cohort).
 */
"use strict";

import {
  patchJson,
  postJson,
  patchJsonConflictRetry,
  postJsonConflictRetry,
} from "../js/http.js";
import { pollJobUntilDone } from "../js/job-poll.js";
import { STUDIO_USER_NOTES_MAX_LEN } from "../js/constants.js";
import { mountCohortDrawer } from "../cohort-drawer.js";
import {
  showToolbarToast,
  setToolbarCollapsed,
  toolbarConfirm,
  tripApiBase,
} from "./shell.js";

var DRAWER_FOCUSABLE =
  'a[href],button:not([disabled]),input:not([disabled]),textarea:not([disabled]),select:not([disabled]),[tabindex="0"]';
var COPY_INTENT_MOODS = ["松弛", "热闹", "赶路", "意外", "仪式感", "平静"];
var COPY_INTENT_FOCUSES = ["人", "地方", "食物", "关系", "自我感受"];
var AESTHETIC_STRATUM_LABELS = {
  person: "人像",
  landscape: "风景",
  food: "美食",
  group: "合影",
  general: "通用",
};

/** Studio dogfood gate · default off. Enable with ?debug=aesthetic or localStorage travelogue.aestheticDebug=1 */
export function isAestheticDebugEnabled() {
  try {
    var q = new URLSearchParams(window.location.search || "");
    if (q.get("debug") === "aesthetic" || q.get("aestheticDebug") === "1") {
      return true;
    }
    if (
      window.localStorage &&
      window.localStorage.getItem("travelogue.aestheticDebug") === "1"
    ) {
      return true;
    }
  } catch (_err) {
    /* ignore */
  }
  return false;
}

var AESTHETIC_PURPOSE_LABELS = {
  cover: "封面",
  hero: "主图",
  moment: "瞬间",
};

var _fetchEntry = function (_tripId) {
  return Promise.resolve({});
};
var _currentChapterId = function () {
  return "";
};
var _markSheetEditBaseline = function (_root, _panel) {};
var _wireSheetEditDirty = function (_root, _panel) {};
var _startLlmNarrate = function (_root, _tripId, _btn, _opts) {};
/** @type {function(string, Element=): Promise<void>} */
var _applyLayoutRerender = function (_tripId, _root) {
  return Promise.resolve();
};
var _getLayoutPending = function () {
  return false;
};

export function registerDrawersBridge(api) {
  if (typeof api.fetchEntry === "function") _fetchEntry = api.fetchEntry;
  if (typeof api.currentChapterId === "function") _currentChapterId = api.currentChapterId;
  if (typeof api.markSheetEditBaseline === "function") {
    _markSheetEditBaseline = api.markSheetEditBaseline;
  }
  if (typeof api.wireSheetEditDirty === "function") _wireSheetEditDirty = api.wireSheetEditDirty;
  if (typeof api.startLlmNarrate === "function") _startLlmNarrate = api.startLlmNarrate;
  if (typeof api.applyLayoutRerender === "function") {
    _applyLayoutRerender = api.applyLayoutRerender;
  }
  if (typeof api.getLayoutPending === "function") _getLayoutPending = api.getLayoutPending;
}


export function copyIntentApiUrl(tripId, chapterId) {
    return (
      "/__travelogue/trips/" +
      encodeURIComponent(tripId) +
      "/chapters/" +
      encodeURIComponent(chapterId) +
      "/copy-intent"
    );
  }

export function buildCopyIntentChipHtml(values, chipClass) {
    return values
      .map(function (value) {
        return (
          '<button type="button" class="preview-drawer__chip ' +
          chipClass +
          '" data-value="' +
          value +
          '" aria-pressed="false">' +
          value +
          "</button>"
        );
      })
      .join("");
  }

export function trapDrawerFocus(container) {
    function onKeydown(e) {
      if (e.key !== "Tab") return;
      var items = container.querySelectorAll(DRAWER_FOCUSABLE);
      if (!items.length) return;
      var first = items[0];
      var last = items[items.length - 1];
      if (e.shiftKey) {
        if (document.activeElement === first) {
          e.preventDefault();
          last.focus();
        }
      } else if (document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    }
    container.addEventListener("keydown", onKeydown);
    return function () {
      container.removeEventListener("keydown", onKeydown);
    };
  }

export function formatAestheticPurposeLine(row) {
    var purposes = row && row.purposes;
    if (!purposes) return "";
    return ["cover", "hero", "moment"]
      .filter(function (p) { return purposes[p] != null; })
      .map(function (p) {
        var label = (row.purposeLabels && row.purposeLabels[p]) || AESTHETIC_PURPOSE_LABELS[p] || p;
        return label + " " + Math.round(Number(purposes[p]) * 100);
      })
      .join(" · ");
  }

export function renderAestheticAlbumProfile(container, profile, pref, tripId) {
    if (!profile || !container) return;
    var block = document.createElement("div");
    block.className = "preview-drawer__aesthetic-album";
    var head = document.createElement("p");
    head.className = "preview-drawer__aesthetic-head";
    var skew = profile.isSkewed ? " · 层偏斜" : "";
    head.textContent =
      "成册分层 · 主层 " +
      (profile.dominantLabel || profile.dominantStratum || "—") +
      skew;
    block.appendChild(head);
    var meta = document.createElement("p");
    meta.className = "preview-drawer__aesthetic-meta";
    var parts = [];
    var pct = profile.strataPct || {};
    Object.keys(pct).forEach(function (key) {
      var label =
        (profile.strataLabels && profile.strataLabels[key]) ||
        AESTHETIC_STRATUM_LABELS[key] ||
        key;
      parts.push(label + " " + pct[key] + "%");
    });
    meta.textContent = parts.length ? parts.join(" · ") : "—";
    block.appendChild(meta);
    if (pref && pref.options && pref.options.length) {
      var hint = document.createElement("p");
      hint.className = "preview-drawer__aesthetic-meta";
      hint.textContent = pref.selectionHint || "";
      block.appendChild(hint);
      var prefRow = document.createElement("div");
      prefRow.className = "preview-drawer__aesthetic-pref";
      pref.options.forEach(function (opt) {
        var btn = document.createElement("button");
        btn.type = "button";
        btn.className = "preview-drawer__aesthetic-pref-btn";
        if (opt.value === pref.value) btn.classList.add("is-active");
        btn.textContent = opt.label || opt.value;
        btn.addEventListener("click", function () {
          if (opt.value === pref.value) return;
          patchJsonConflictRetry(
            "/__travelogue/trips/" +
              encodeURIComponent(tripId) +
              "/aesthetic/preference",
            { stratumPreference: opt.value }
          ).then(function (result) {
            var data = result && (result.data || result.body);
            if (!data || !data.ok) return;
            renderAestheticAlbumProfile(container, profile, data.stratumPreference, tripId);
          });
        });
        prefRow.appendChild(btn);
      });
      block.appendChild(prefRow);
      if (pref.recurateHint) {
        var recurate = document.createElement("p");
        recurate.className = "preview-drawer__aesthetic-meta";
        recurate.textContent = pref.recurateHint;
        block.appendChild(recurate);
      }
    }
    container.querySelectorAll(".preview-drawer__aesthetic-album").forEach(function (node) {
      node.remove();
    });
    container.appendChild(block);
  }

export function loadAestheticExplain(tripId, container) {
    if (!container) return;
    if (!isAestheticDebugEnabled()) {
      container.hidden = true;
      container.innerHTML = "";
      return;
    }
    fetch("/__travelogue/trips/" + encodeURIComponent(tripId) + "/aesthetic")
      .then(function (resp) { return resp.ok ? resp.json() : null; })
      .then(function (data) {
        if (!data || !data.ok || !data.enabled) {
          container.hidden = true;
          return;
        }
        var assets = data.assets || [];
        if (!assets.length) {
          container.hidden = true;
          return;
        }
        container.hidden = false;
        container.innerHTML = "";
        renderExplainBlock(container, "照片审美分项", {
          summary:
            "已评分 " +
            (data.scoredCount != null ? data.scoredCount : assets.length) +
            " 张 · 成册中各图分层 / purpose / top-3 维度",
          details: [],
        });
        if (data.albumProfile) {
          renderAestheticAlbumProfile(
            container,
            data.albumProfile,
            data.stratumPreference,
            tripId
          );
        }
        assets.forEach(function (row) {
          var block = document.createElement("div");
          block.className = "preview-drawer__aesthetic-asset";
          var head = document.createElement("p");
          head.className = "preview-drawer__aesthetic-head";
          var overall =
            row.overall != null ? Math.round(Number(row.overall) * 100) + " 分" : "—";
          var stratum = row.stratumLabel || row.stratum || "";
          head.textContent =
            (row.id || "?") +
            " · overall " +
            overall +
            (stratum ? " · " + stratum : "");
          block.appendChild(head);
          var purposeLine = formatAestheticPurposeLine(row);
          if (purposeLine) {
            var purposeMeta = document.createElement("p");
            purposeMeta.className = "preview-drawer__aesthetic-meta";
            purposeMeta.textContent = purposeLine;
            block.appendChild(purposeMeta);
          }
          if (row.mllmScore != null) {
            var mllmMeta = document.createElement("p");
            mllmMeta.className = "preview-drawer__aesthetic-meta";
            mllmMeta.textContent =
              "MLLM " + Math.round(Number(row.mllmScore) * 100) + " 分";
            block.appendChild(mllmMeta);
          }
          if (row.critique) {
            var critique = document.createElement("p");
            critique.className = "preview-drawer__aesthetic-critique";
            critique.textContent =
              typeof row.critique === "string"
                ? row.critique
                : row.critique.summary || row.critique.text || "";
            block.appendChild(critique);
          }
          var list = document.createElement("ul");
          list.className = "preview-drawer__explain-list";
          (row.explain || []).forEach(function (item) {
            var li = document.createElement("li");
            li.textContent = item.reason || item.label || item.code || "";
            list.appendChild(li);
          });
          block.appendChild(list);
          container.appendChild(block);
        });
      })
      .catch(function () {
        container.hidden = true;
      });
  }

export function renderExplainBlock(container, title, block) {
    if (!container || !block || !block.summary) return;
    var head = document.createElement("h3");
    head.className = "preview-drawer__subhead";
    head.textContent = title;
    container.appendChild(head);
    var lead = document.createElement("p");
    lead.className = "preview-drawer__explain-lead";
    lead.textContent = block.summary;
    container.appendChild(lead);
    if (block.details && block.details.length) {
      var list = document.createElement("ul");
      list.className = "preview-drawer__explain-list";
      block.details.forEach(function (line) {
        var li = document.createElement("li");
        li.textContent = line;
        list.appendChild(li);
      });
      container.appendChild(list);
    }
  }

export function loadChapterExplain(tripId, container) {
    if (!container) return;
    fetch("/__travelogue/chapter-layout?tripId=" + encodeURIComponent(tripId))
      .then(function (resp) { return resp.json(); })
      .then(function (data) {
        if (!data || !data.ok || !data.summary) {
          container.textContent = "暂无分章说明";
          return;
        }
        container.innerHTML = "";
        renderExplainBlock(container, "为什么这样分章？", {
          summary: data.summary,
          details: data.details,
        });
        if (data.layoutExplain) {
          renderExplainBlock(container, "排版引擎", data.layoutExplain);
        }
      })
      .catch(function () {
        container.textContent = "无法加载分章说明";
      });
  }

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
    var drawerBodyEl = bodyEl;
    var scrim = shell.querySelector(".preview-drawer__scrim");
    var closeBtn = shell.querySelector(".preview-drawer__close");
    var entryCache = null;
    var drawerFocusRelease = null;
    var drawerPreviousFocus = null;
    var drawerEmbedTarget = null;

    // V1.1 · 整本字段（杂志名 / 一句话）与章字段（锚点 / 意图）分模板
    var bookEditTpl =
      '<label class="preview-drawer__label" for="preview-drawer-title-input">杂志名</label>' +
      '<input id="preview-drawer-title-input" class="preview-drawer__title-input" type="text" maxlength="20" autocomplete="off" placeholder="我的旅途">' +
      '<label class="preview-drawer__label" for="preview-drawer-notes">给这本游记的一句话</label>' +
      '<textarea id="preview-drawer-notes" class="preview-drawer__notes" maxlength="' +
      STUDIO_USER_NOTES_MAX_LEN +
      '" rows="3" placeholder="例如：带娃慢走，想突出雨后的京都"></textarea>' +
      '<p class="preview-drawer__notes-saved" hidden aria-live="polite">✓ 已保存 · 将显示在封面副标题与辑封</p>';

    var pageEditTpl =
      '<p class="preview-drawer__chapter-label">当前章：<strong class="preview-drawer__chapter-name"></strong></p>' +
      '<p class="preview-drawer__label">想写进图说的词（最多 3 个）</p>' +
      '<div class="preview-drawer__anchors">' +
      '<input type="text" class="preview-drawer__anchor" maxlength="24" placeholder="例如：雨停了">' +
      '<input type="text" class="preview-drawer__anchor" maxlength="24" placeholder="词 2">' +
      '<input type="text" class="preview-drawer__anchor" maxlength="24" placeholder="词 3">' +
      "</div>" +
      '<p class="preview-drawer__hint">短词即可，会写进图说，不会瞎编</p>' +
      '<details class="preview-drawer__copy-intent">' +
      '<summary class="preview-drawer__label">本章想强调的感觉（可选）</summary>' +
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
      '<button type="button" class="preview-drawer__primary preview-drawer__narrate-anchors">按新感觉重写这段</button>';

    var structTpl =
      '<div class="preview-drawer__g1"></div>' +
      '<div class="preview-drawer__g1-actions" hidden>' +
      '<button type="button" class="preview-drawer__g1-confirm">章节顺序 OK</button>' +
      '<button type="button" class="preview-drawer__g1-regenerate">重新生成结构</button>' +
      "</div>" +
      '<div class="preview-drawer__explain"></div>' +
      '<div class="preview-drawer__aesthetic" hidden></div>' +
      '<button type="button" class="preview-drawer__primary preview-drawer__apply-layout">更新版面</button>';

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
      var inputs = drawerBodyEl.querySelectorAll(".preview-drawer__anchor");
      var row = chapterRow(chId);
      var anchors = (row && row.memoryAnchors) || [];
      for (var i = 0; i < inputs.length; i++) {
        inputs[i].value = anchors[i] || "";
      }
      var nameEl = drawerBodyEl.querySelector(".preview-drawer__chapter-name");
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
      drawerBodyEl.querySelectorAll(".preview-drawer__chip-mood").forEach(function (btn) {
        var on = btn.getAttribute("data-value") === intent.mood;
        btn.classList.toggle("is-selected", on);
        btn.setAttribute("aria-pressed", on ? "true" : "false");
      });
      drawerBodyEl.querySelectorAll(".preview-drawer__chip-focus").forEach(function (btn) {
        var on = btn.getAttribute("data-value") === intent.focus;
        btn.classList.toggle("is-selected", on);
        btn.setAttribute("aria-pressed", on ? "true" : "false");
      });
      var noteInp = drawerBodyEl.querySelector(".preview-drawer__copy-intent-note");
      if (noteInp) noteInp.value = intent.note || "";
      updateCopyIntentVisibility(chId);
    }

    function chapterHasVoice(chId) {
      var row = chapterRow(chId);
      return !!(row && row.hasVoice);
    }

    function updateCopyIntentVisibility(chId) {
      var details = drawerBodyEl.querySelector(".preview-drawer__copy-intent");
      var skipNote = drawerBodyEl.querySelector(".preview-drawer__copy-intent-voice-skip");
      var hint = drawerBodyEl.querySelector(".preview-drawer__copy-intent-hint");
      var applyLabel = drawerBodyEl.querySelector(".preview-drawer__copy-intent-apply");
      if (!details) return;
      var skip = chapterHasVoice(chId);
      details.open = !skip && details.open;
      details.hidden = skip;
      if (skipNote) skipNote.hidden = !skip;
      if (hint) hint.hidden = skip;
      if (applyLabel) applyLabel.hidden = skip;
    }

    function readCopyIntentPayload() {
      if (!drawerBodyEl.querySelector(".preview-drawer__copy-intent")) {
        return null;
      }
      if (chapterHasVoice(_currentChapterId())) {
        return null;
      }
      var moodBtn = drawerBodyEl.querySelector(".preview-drawer__chip-mood.is-selected");
      var focusBtn = drawerBodyEl.querySelector(".preview-drawer__chip-focus.is-selected");
      var noteInp = drawerBodyEl.querySelector(".preview-drawer__copy-intent-note");
      var subsequent = drawerBodyEl.querySelector(".preview-drawer__copy-intent-subsequent");
      var noteVal = noteInp ? (noteInp.value || "").trim() : "";
      /** @type {{ clear?: boolean; mood?: string | null; focus?: string | null; note?: string | null; applyToSubsequent?: boolean }} */
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
      if (drawerEmbedTarget) {
        drawerEmbedTarget = null;
        return;
      }
      drawerBodyEl = bodyEl;
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

    function runG1Regenerate(triggerBtn) {
      return toolbarConfirm({
        title: "重新生成结构",
        body: "将重新生成章节结构，可能覆盖当前分章。继续？",
        confirmText: "继续",
        danger: true,
      }).then(function (ok) {
        if (!ok) return false;
        if (triggerBtn) triggerBtn.disabled = true;
        return postJson("/__travelogue/trips/" + encodeURIComponent(tripId) + "/curate", { force: true })
          .then(function (res) {
            if (res.status === 202 && res.body && res.body.jobId) {
              pollStudioJob(res.body.jobId, function (job) {
                if (triggerBtn) triggerBtn.disabled = false;
                if (job.status === "succeeded") {
                  var changed = true;
                  try {
                    if (job.result && typeof job.result.structureChanged === "boolean") {
                      changed = job.result.structureChanged;
                    }
                  } catch (_err) {
                    changed = true;
                  }
                  showToolbarToast(
                    changed
                      ? "结构已重新生成"
                      : "已重跑，章节结构与上次相同（照片集合未变时属正常）"
                  );
                  window.location.reload();
                  return;
                }
                showToolbarToast("重新生成失败", { error: true });
              });
              return true;
            }
            if (triggerBtn) triggerBtn.disabled = false;
            showToolbarToast("无法开始", { error: true });
            return false;
          })
          .catch(function () {
            if (triggerBtn) triggerBtn.disabled = false;
            showToolbarToast("无法开始", { error: true });
            return false;
          });
      });
    }

    function openDrawer(mode) {
      if (!entryCache) {
        _fetchEntry(tripId).then(function (data) {
          entryCache = data || {};
          openDrawer(mode);
        });
        return;
      }
      var targetBody = drawerEmbedTarget || bodyEl;
      var useOverlay = !drawerEmbedTarget;
      drawerBodyEl = targetBody;

      if (useOverlay) {
        shell.hidden = false;
        drawer.hidden = false;
        document.body.classList.add("preview-drawer-open");
        setToolbarCollapsed(root, false, false);
        requestAnimationFrame(activateDrawerFocus);
      } else {
        targetBody.innerHTML = "";
      }

      if (mode === "edit" || mode === "edit-page") {
        if (useOverlay) titleEl.textContent = "编辑";
        // overlay openEdit：整本+章字段；sheet embed 按 mode 分流
        var editHtml =
          mode === "edit-page"
            ? pageEditTpl
            : useOverlay
              ? bookEditTpl + pageEditTpl
              : bookEditTpl;
        targetBody.innerHTML = editHtml;
        var titleInput = targetBody.querySelector(".preview-drawer__title-input");
        var notes = targetBody.querySelector(".preview-drawer__notes");
        if (titleInput && entryCache.intentSummary) {
          titleInput.value = entryCache.intentSummary.title || "";
        }
        if (notes && entryCache.intentSummary) {
          notes.value = entryCache.intentSummary.userNotes || "";
        }
        if (targetBody.querySelector(".preview-drawer__anchor")) {
          fillChapterFields(_currentChapterId());
        }
        wireChipGroup(targetBody.querySelector(".preview-drawer__chips--mood"), "preview-drawer__chip-mood");
        wireChipGroup(targetBody.querySelector(".preview-drawer__chips--focus"), "preview-drawer__chip-focus");
        if (drawerEmbedTarget) {
          _markSheetEditBaseline(root, targetBody);
          _wireSheetEditDirty(root, targetBody);
        }

        function persistEditDrawer(btn, opts) {
          opts = opts || {};
          var chId = _currentChapterId();
          var hasBookFields = !!titleInput || !!notes;
          var hasPageFields = !!targetBody.querySelector(".preview-drawer__anchor");
          var titleVal = titleInput ? (titleInput.value || "").trim() : "";
          var notesVal = notes ? (notes.value || "").trim() : "";
          var anchorInputs = targetBody.querySelectorAll(".preview-drawer__anchor");
          var anchors = [];
          anchorInputs.forEach(function (inp) {
            var v = (inp.value || "").trim();
            if (v) anchors.push(v);
          });
          if (btn) btn.disabled = true;
          if (hasBookFields && titleVal.length > 20) {
            if (btn) btn.disabled = false;
            showToolbarToast("杂志名最多 20 个字", { error: true });
            return Promise.resolve(false);
          }
          var tasks = [];
          if (hasBookFields) {
            tasks.push(
              patchJsonConflictRetry("/__travelogue/trips/" + encodeURIComponent(tripId) + "/intent", {
                title: titleVal || null,
                userNotes: notesVal || null,
              })
            );
          }
          if (hasPageFields && chId) {
            tasks.push(
              postJsonConflictRetry(tripApiBase(tripId) + "/save-copy", {
                patches: [{
                  path: "chapters." + chId + ".curation.memoryAnchors",
                  value: anchors.join(", "),
                }],
              })
            );
            var copyIntentPayload = readCopyIntentPayload();
            if (copyIntentPayload) {
              tasks.push(patchJsonConflictRetry(copyIntentApiUrl(tripId, chId), copyIntentPayload));
            }
          }
          if (!tasks.length) {
            if (btn) btn.disabled = false;
            return Promise.resolve(true);
          }
          return Promise.all(tasks)
            .then(function (results) {
              if (btn) btn.disabled = false;
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
              if (hasBookFields && entryCache.intentSummary) {
                entryCache.intentSummary.userNotes = notesVal;
                if (titleVal) entryCache.intentSummary.title = titleVal;
              }
              if (hasBookFields && titleVal) {
                var coverTitle = document.querySelector(".cover-opening__title");
                if (coverTitle) {
                  coverTitle.textContent = titleVal;
                  coverTitle.dataset.title = titleVal;
                  coverTitle.classList.add("cover-opening__title--saved");
                  window.clearTimeout(coverTitle._savedMarkTimer);
                  coverTitle._savedMarkTimer = window.setTimeout(function () {
                    coverTitle.classList.remove("cover-opening__title--saved");
                  }, 1500);
                }
                try {
                  document.title = titleVal;
                } catch (eDoc) {}
              }
              if (hasBookFields && notes) {
                var notesSaved = targetBody.querySelector(".preview-drawer__notes-saved");
                if (notesSaved) {
                  notesSaved.hidden = false;
                  window.clearTimeout(notes._savedHintTimer);
                  notes._savedHintTimer = window.setTimeout(function () {
                    notesSaved.hidden = true;
                  }, 1500);
                }
                // R2.2 · 热刷新封面副标题（一句话）
                if (notesVal) {
                  var subEl =
                    document.querySelector(".cover-opening__subtitle") ||
                    document.querySelector(".cover-hero__text .subtitle");
                  if (!subEl) {
                    var titleHost = document.querySelector(".cover-opening__title");
                    if (titleHost && titleHost.parentElement) {
                      subEl = document.createElement("p");
                      subEl.className = "cover-opening__subtitle subtitle";
                      subEl.setAttribute("data-block", "cover-subtitle");
                      titleHost.parentElement.insertBefore(subEl, titleHost.nextSibling);
                    }
                  }
                  if (subEl) {
                    subEl.textContent = notesVal;
                    subEl.hidden = false;
                  }
                }
              }
              if (hasPageFields && chId && entryCache.chapters) {
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
                var savedIntentPayload = readCopyIntentPayload();
                var hasIntent = savedIntentPayload && savedIntentPayload.clear !== true;
                showToolbarToast(
                  (hasPageFields && (anchors.length > 0 || hasIntent))
                    ? "编辑已保存。可在「精修」中重新生成文案以写入锚点与点缀。"
                    : "编辑已保存"
                );
              }
              if (drawerEmbedTarget) {
                _markSheetEditBaseline(root, targetBody);
              }
              return true;
            })
            .catch(function () {
              if (btn) btn.disabled = false;
              showToolbarToast("保存失败", { error: true });
              return false;
            });
        }

        // D-REF-05 · 文案类立即保存（失焦 / chip 变更），不再依赖「保存编辑」主按钮
        // FE-DFX-20 · IME 组合态下不提交（composition / isComposing）
        var autoPersistTimer = null;
        var autoPersisting = false;
        var imeComposing = false;
        function scheduleAutoPersist() {
          if (imeComposing) return;
          if (autoPersistTimer) window.clearTimeout(autoPersistTimer);
          autoPersistTimer = window.setTimeout(function () {
            if (autoPersisting || imeComposing) return;
            autoPersisting = true;
            persistEditDrawer(null, { skipToast: true }).then(function () {
              autoPersisting = false;
            });
          }, 320);
        }
        targetBody
          .querySelectorAll(
            ".preview-drawer__title-input, .preview-drawer__notes, .preview-drawer__anchor, .preview-drawer__copy-intent-note"
          )
          .forEach(function (el) {
            el.addEventListener("compositionstart", function () {
              imeComposing = true;
            });
            el.addEventListener("compositionend", function () {
              imeComposing = false;
            });
            el.addEventListener("keydown", function (e) {
              if (e.key !== "Enter" || e.shiftKey) return;
              if (el.tagName === "TEXTAREA") return;
              if (e.isComposing || imeComposing) {
                e.preventDefault();
                return;
              }
              e.preventDefault();
              el.blur();
            });
            el.addEventListener("blur", function () {
              if (imeComposing || (el.isComposing === true)) return;
              scheduleAutoPersist();
            });
          });
        var subsequent = targetBody.querySelector(".preview-drawer__copy-intent-subsequent");
        if (subsequent) {
          subsequent.addEventListener("change", scheduleAutoPersist);
        }
        targetBody
          .querySelectorAll(".preview-drawer__chip-mood, .preview-drawer__chip-focus")
          .forEach(function (chip) {
            chip.addEventListener("click", function () {
              window.setTimeout(scheduleAutoPersist, 0);
            });
          });

        var narrateAnchorsBtn = targetBody.querySelector(".preview-drawer__narrate-anchors");
        if (narrateAnchorsBtn) {
          narrateAnchorsBtn.addEventListener("click", function () {
            var btn = this;
            if (btn.disabled) return;
            // D-REF-13 · 二次确认；确认后 busy，完成前不可连点
            toolbarConfirm({
              title: "按新感觉重写这段",
              body: "将按当前词与本章感觉重新生成文案，可能覆盖未锁定的内容。继续？",
              confirmText: "重写",
            }).then(function (ok) {
              if (!ok) return;
              btn.disabled = true;
              btn.dataset.labelIdle = "按新感觉重写这段";
              btn.textContent = "正在重写…";
              return persistEditDrawer(btn, { skipToast: true }).then(function (saved) {
                if (!saved) {
                  btn.disabled = false;
                  btn.textContent = btn.dataset.labelIdle;
                  return;
                }
                return _startLlmNarrate(root, tripId, btn, {
                  skipConfirm: true,
                  busyHint: "正在按新感觉重写这段…",
                });
              });
            });
          });
        }
        return;
      }

      if (mode === "cohort") {
        if (useOverlay) titleEl.textContent = "旅行主角 · 同框";
        targetBody.innerHTML = "";
        mountCohortDrawer({
          tripId: tripId,
          bodyEl: targetBody,
          showToast: showToolbarToast,
          onClose: closeDrawer,
          onEntryRefresh: function () {
            return _fetchEntry(tripId).then(function (data) {
              entryCache = data || {};
              return entryCache;
            });
          },
          onApplyLayout: function () {
            return _applyLayoutRerender(tripId, root);
          },
        });
        return;
      }

      if (useOverlay) titleEl.textContent = "结构";
      targetBody.innerHTML = structTpl;
      var g1 = targetBody.querySelector(".preview-drawer__g1");
      var g1Actions = targetBody.querySelector(".preview-drawer__g1-actions");
      var status = entryCache.pipelineStatus || "";
      var pending = entryCache.g1Pending || status === "structure_draft";
      if (pending) {
        g1.className = "preview-drawer__g1 preview-drawer__g1--warn";
        g1.textContent =
          "章节结构待确认：请先看顶栏横幅确认顺序；也可在此确认或重新生成。";
        if (g1Actions) g1Actions.hidden = false;
        var confirmBtn = targetBody.querySelector(".preview-drawer__g1-confirm");
        var regenBtn = targetBody.querySelector(".preview-drawer__g1-regenerate");
        if (confirmBtn) {
          confirmBtn.addEventListener("click", function () {
            runG1Confirm(confirmBtn);
          });
        }
        if (regenBtn) {
          regenBtn.addEventListener("click", function () {
            runG1Regenerate(regenBtn);
          });
        }
      } else {
        g1.className = "preview-drawer__g1 preview-drawer__g1--info";
        g1.textContent = "章节已按行程排好，可在预览中改字、锚点与精选。结构确认见顶栏横幅（若开启）。";
        if (g1Actions) g1Actions.hidden = true;
      }
      loadChapterExplain(tripId, targetBody.querySelector(".preview-drawer__explain"));
      // Aesthetic score dump is dogfood-only (?debug=aesthetic).
      var aestheticEl = targetBody.querySelector(".preview-drawer__aesthetic");
      if (aestheticEl) {
        if (isAestheticDebugEnabled()) {
          loadAestheticExplain(tripId, aestheticEl);
        } else {
          aestheticEl.hidden = true;
          aestheticEl.innerHTML = "";
        }
      }
      var applyBtn = targetBody.querySelector(".preview-drawer__apply-layout");
      if (applyBtn) {
        applyBtn.hidden = !_getLayoutPending();
        applyBtn.addEventListener("click", function () {
          closeDrawer();
          _applyLayoutRerender(tripId, root);
        });
      }
    }

    scrim.addEventListener("click", closeDrawer);
    closeBtn.addEventListener("click", closeDrawer);
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && !shell.hidden) closeDrawer();
    });

    _fetchEntry(tripId).then(function (data) {
      entryCache = data || {};
    });

    return {
      openEdit: function () { openDrawer("edit"); },
      openStructure: function () { openDrawer("structure"); },
      openCohort: function () { openDrawer("cohort"); },
      openEmbed: function (mode, el) {
        drawerEmbedTarget = el;
        openDrawer(mode);
      },
      confirmStructure: function () { return runG1Confirm(null); },
      regenerateStructure: function () { return runG1Regenerate(null); },
      close: closeDrawer,
      refreshEntry: function () {
        return _fetchEntry(tripId).then(function (data) {
          entryCache = data || {};
          return entryCache;
        });
      },
    };
  }
