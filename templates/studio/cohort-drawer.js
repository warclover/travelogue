/**
 * Studio · featured-subject / duo cohort seed picker (preview drawer).
 */
"use strict";

import { patchJson } from "./js/http.js";

function assetThumbUrl(tripId, displayFile) {
  if (!displayFile) return "";
  var rel = String(displayFile).replace(/^\//, "");
  return "/" + encodeURIComponent(tripId) + "/" + rel;
}

function fetchCohort(tripId) {
  return fetch("/__travelogue/trips/" + encodeURIComponent(tripId) + "/cohort")
    .then(function (r) {
      return r.ok ? r.json() : null;
    })
    .catch(function () {
      return null;
    });
}

function normalizeSubjects(raw) {
  var list = raw || [];
  var out = [];
  for (var i = 0; i < list.length; i++) {
    var s = list[i];
    if (!s || !s.id) continue;
    out.push({
      id: String(s.id),
      label: String(s.label || s.id).slice(0, 16),
      seedAssetIds: (s.seedAssetIds || []).slice(),
    });
  }
  if (!out.length) {
    return [
      { id: "alice", label: "主角 A", seedAssetIds: [] },
      { id: "bob", label: "主角 B", seedAssetIds: [] },
    ];
  }
  if (out.length === 1) {
    var other = out[0].id === "alice" ? "bob" : "alice";
    out.push({ id: other, label: "主角 B", seedAssetIds: [] });
  }
  return out.slice(0, 2);
}

function buildCandidateList(data, subjects) {
  var used = {};
  subjects.forEach(function (subj) {
    (subj.seedAssetIds || []).forEach(function (id) {
      used[id] = true;
    });
  });
  var byId = {};
  (data.assets || []).forEach(function (a) {
    if (a && a.id) byId[a.id] = a;
  });
  var rows = (data.assets || [])
    .filter(function (a) {
      return a && a.id && (a.faceCount || 0) >= 1;
    })
    .sort(function (a, b) {
      var da = a.duo ? 1 : 0;
      var db = b.duo ? 1 : 0;
      if (da !== db) return db - da;
      return String(a.takenAt || "").localeCompare(String(b.takenAt || ""));
    });
  return { byId: byId, rows: rows, used: used };
}

/**
 * @param {object} opts
 * @param {string} opts.tripId
 * @param {HTMLElement} opts.bodyEl
 * @param {function(string, object=): void} opts.showToast
 * @param {function(): void} [opts.onClose]
 * @param {function(): Promise<object>} [opts.onEntryRefresh]
 * @param {function(): Promise<void>} [opts.onApplyLayout]
 */
export function mountCohortDrawer(opts) {
  var tripId = opts.tripId;
  var bodyEl = opts.bodyEl;
  var showToast = opts.showToast;
  var state = { data: null, subjects: [] };

  bodyEl.innerHTML =
    '<p class="cohort-drawer__lead">选择两位旅行主角的清晰正脸照作为「种子」，系统会标记两人同框的照片，并在排版/拼图中优先聚在一起。</p>' +
    '<p class="cohort-drawer__status" hidden></p>' +
    '<div class="cohort-drawer__subjects"></div>' +
    '<p class="cohort-drawer__hint">每张种子需包含该主角清晰正脸；保存后将重新识别同框。</p>' +
    '<div class="cohort-drawer__actions">' +
    '<button type="button" class="preview-drawer__ghost cohort-drawer__refresh-only">仅重新识别</button>' +
    '<button type="button" class="preview-drawer__primary cohort-drawer__save">保存种子并识别</button>' +
    "</div>" +
    '<button type="button" class="preview-drawer__ghost cohort-drawer__save-layout" hidden>保存并更新版面</button>';

  var statusEl = bodyEl.querySelector(".cohort-drawer__status");
  var subjectsRoot = bodyEl.querySelector(".cohort-drawer__subjects");
  var saveBtn = bodyEl.querySelector(".cohort-drawer__save");
  var refreshBtn = bodyEl.querySelector(".cohort-drawer__refresh-only");
  var layoutBtn = bodyEl.querySelector(".cohort-drawer__save-layout");

  function setBusy(on) {
    saveBtn.disabled = !!on;
    refreshBtn.disabled = !!on;
    if (layoutBtn) layoutBtn.disabled = !!on;
  }

  function updateStatus(data) {
    if (!statusEl) return;
    if (!data || !data.enabled) {
      statusEl.hidden = false;
      statusEl.className = "cohort-drawer__status cohort-drawer__status--warn";
      statusEl.textContent =
        "同框识别未开启：请在 config.yaml 中设置 cohort.enabled: true 后刷新 Studio。";
      saveBtn.disabled = true;
      refreshBtn.disabled = true;
      return;
    }
    var summary = data.summary || {};
    var duo = summary.duoCount != null ? summary.duoCount : 0;
    var tagged = summary.tagged != null ? summary.tagged : 0;
    statusEl.hidden = false;
    statusEl.className = "cohort-drawer__status cohort-drawer__status--info";
    statusEl.textContent =
      "已分析 " +
      tagged +
      " 张 · 同框 " +
      duo +
      " 张" +
      (summary.method ? "（" + summary.method + "）" : "");
  }

  function renderSubjectPanel(subj, data, candidates) {
    var panel = document.createElement("section");
    panel.className = "cohort-drawer__subject";
    panel.dataset.subjectId = subj.id;

    var head = document.createElement("div");
    head.className = "cohort-drawer__subject-head";
    head.innerHTML =
      '<label class="preview-drawer__label">主角 ID</label>' +
      '<input type="text" class="cohort-drawer__id" maxlength="32" readonly value="">' +
      '<label class="preview-drawer__label">显示名</label>' +
      '<input type="text" class="cohort-drawer__label-input" maxlength="16" value="">';
    head.querySelector(".cohort-drawer__id").value = subj.id;
    head.querySelector(".cohort-drawer__label-input").value = subj.label || subj.id;
    panel.appendChild(head);

    var seedsWrap = document.createElement("div");
    seedsWrap.className = "cohort-drawer__seeds";
    var seedsLabel = document.createElement("p");
    seedsLabel.className = "preview-drawer__label";
    seedsLabel.textContent = "已选种子（" + (subj.seedAssetIds || []).length + "）";
    seedsWrap.appendChild(seedsLabel);

    var chips = document.createElement("div");
    chips.className = "cohort-drawer__chips";
    (subj.seedAssetIds || []).forEach(function (aid) {
      var asset = candidates.byId[aid];
      chips.appendChild(renderChip(tripId, aid, asset, subj.id));
    });
    if (!(subj.seedAssetIds || []).length) {
      var empty = document.createElement("p");
      empty.className = "cohort-drawer__empty";
      empty.textContent = "点击下方照片添加种子";
      chips.appendChild(empty);
    }
    seedsWrap.appendChild(chips);
    panel.appendChild(seedsWrap);

    var gridLabel = document.createElement("p");
    gridLabel.className = "preview-drawer__label";
    gridLabel.textContent = "候选照片（检测到人脸）";
    panel.appendChild(gridLabel);

    var grid = document.createElement("div");
    grid.className = "cohort-drawer__grid";
    var suggested = (data.suggestedSeeds && data.suggestedSeeds[subj.id]) || [];
    var ordered = [];
    suggested.forEach(function (id) {
      if (ordered.indexOf(id) < 0) ordered.push(id);
    });
    candidates.rows.forEach(function (a) {
      if (ordered.indexOf(a.id) < 0) ordered.push(a.id);
    });
    ordered.forEach(function (aid) {
      var asset = candidates.byId[aid];
      if (!asset) return;
      var selected = (subj.seedAssetIds || []).indexOf(aid) >= 0;
      grid.appendChild(renderTile(tripId, asset, selected, subj.id));
    });
    panel.appendChild(grid);

    head.querySelector(".cohort-drawer__label-input").addEventListener("input", function () {
      subj.label = this.value.slice(0, 16);
    });

    return panel;
  }

  function renderChip(tripId, aid, asset, subjectId) {
    var chip = document.createElement("button");
    chip.type = "button";
    chip.className = "cohort-drawer__chip";
    chip.title = "移除种子";
    var img = document.createElement("img");
    img.alt = "";
    img.loading = "lazy";
    img.src = assetThumbUrl(tripId, asset && asset.displayFile);
    chip.appendChild(img);
    var x = document.createElement("span");
    x.className = "cohort-drawer__chip-x";
    x.textContent = "×";
    chip.appendChild(x);
    chip.addEventListener("click", function () {
      toggleSeed(subjectId, aid, false);
    });
    return chip;
  }

  function renderTile(tripId, asset, selected, subjectId) {
    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "cohort-drawer__tile" + (selected ? " cohort-drawer__tile--on" : "");
    if (asset.duo) btn.classList.add("cohort-drawer__tile--duo");
    var img = document.createElement("img");
    img.alt = "";
    img.loading = "lazy";
    img.src = assetThumbUrl(tripId, asset.displayFile);
    btn.appendChild(img);
    if (asset.duo) {
      var badge = document.createElement("span");
      badge.className = "cohort-drawer__badge";
      badge.textContent = "同框";
      btn.appendChild(badge);
    }
    btn.addEventListener("click", function () {
      toggleSeed(subjectId, asset.id, !selected);
    });
    return btn;
  }

  function findSubject(id) {
    for (var i = 0; i < state.subjects.length; i++) {
      if (state.subjects[i].id === id) return state.subjects[i];
    }
    return null;
  }

  function toggleSeed(subjectId, assetId, add) {
    var subj = findSubject(subjectId);
    if (!subj) return;
    var seeds = subj.seedAssetIds || [];
    var idx = seeds.indexOf(assetId);
    if (add && idx < 0) {
      if (seeds.length >= 12) {
        showToast("每位主角最多 12 张种子", { error: true });
        return;
      }
      seeds.push(assetId);
    } else if (!add && idx >= 0) {
      seeds.splice(idx, 1);
    }
    subj.seedAssetIds = seeds;
    rerender();
  }

  function rerender() {
    if (!state.data) return;
    var candidates = buildCandidateList(state.data, state.subjects);
    subjectsRoot.innerHTML = "";
    state.subjects.forEach(function (subj) {
      subjectsRoot.appendChild(renderSubjectPanel(subj, state.data, candidates));
    });
  }

  function payloadFromState(refresh) {
    return {
      featuredSubjects: state.subjects.map(function (s) {
        return {
          id: s.id,
          label: s.label || s.id,
          seedAssetIds: (s.seedAssetIds || []).slice(),
        };
      }),
      refresh: !!refresh,
    };
  }

  function validateSeeds() {
    for (var i = 0; i < state.subjects.length; i++) {
      if (!(state.subjects[i].seedAssetIds || []).length) {
        showToast("请为每位主角至少选择 1 张种子照", { error: true });
        return false;
      }
    }
    return true;
  }

  function persist(refresh, thenLayout) {
    if (!validateSeeds()) return Promise.resolve(false);
    setBusy(true);
    return patchJson(
      "/__travelogue/trips/" + encodeURIComponent(tripId) + "/cohort",
      payloadFromState(refresh)
    )
      .then(function (res) {
        setBusy(false);
        if (!res || res.status !== 200 || !res.body || !res.body.ok) {
          var err =
            (res && res.body && (res.body.error || res.body.message)) || "保存失败";
          showToast(String(err), { error: true });
          return false;
        }
        state.data = res.body;
        state.subjects = normalizeSubjects(res.body.featuredSubjects);
        updateStatus(state.data);
        rerender();
        showToast(thenLayout ? "已识别，正在更新版面…" : "同框标记已更新");
        if (typeof opts.onEntryRefresh === "function") {
          opts.onEntryRefresh();
        }
        if (thenLayout && typeof opts.onApplyLayout === "function") {
          return opts.onApplyLayout().then(function () {
            return true;
          });
        }
        return true;
      })
      .catch(function () {
        setBusy(false);
        showToast("网络错误", { error: true });
        return false;
      });
  }

  saveBtn.addEventListener("click", function () {
    persist(true, false).then(function (ok) {
      if (ok && typeof opts.onClose === "function") opts.onClose();
    });
  });
  refreshBtn.addEventListener("click", function () {
    if (!validateSeeds()) return;
    persist(true, false);
  });
  if (layoutBtn) {
    layoutBtn.hidden = false;
    layoutBtn.addEventListener("click", function () {
      persist(true, true).then(function (ok) {
        if (ok && typeof opts.onClose === "function") opts.onClose();
      });
    });
  }

  setBusy(true);
  fetchCohort(tripId).then(function (data) {
    setBusy(false);
    if (!data || !data.ok) {
      subjectsRoot.innerHTML = '<p class="cohort-drawer__empty">无法加载同框数据</p>';
      return;
    }
    state.data = data;
    state.subjects = normalizeSubjects(data.featuredSubjects);
    updateStatus(data);
    rerender();
  });
}
