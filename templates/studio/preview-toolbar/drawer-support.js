/**
 * Preview toolbar · drawer helpers (M-P2b).
 */
"use strict";

export var DRAWER_FOCUSABLE =
  'a[href],button:not([disabled]),input:not([disabled]),textarea:not([disabled]),select:not([disabled]),[tabindex="0"]';
export var COPY_INTENT_MOODS = ["松弛", "热闹", "赶路", "意外", "仪式感", "平静"];
export var COPY_INTENT_FOCUSES = ["人", "地方", "食物", "关系", "自我感受"];

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

export function loadAestheticExplain(tripId, container) {
  if (!container) return;
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
          " 张 · 成册中各图 top-3 维度",
        details: [],
      });
      assets.forEach(function (row) {
        var block = document.createElement("div");
        block.className = "preview-drawer__aesthetic-asset";
        var head = document.createElement("p");
        head.className = "preview-drawer__aesthetic-head";
        var overall =
          row.overall != null ? Math.round(Number(row.overall) * 100) + " 分" : "—";
        head.textContent = (row.id || "?") + " · overall " + overall;
        block.appendChild(head);
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

export function fetchEntry(tripId) {
  return fetch("/__travelogue/trips/" + encodeURIComponent(tripId) + "/entry")
    .then(function (r) { return r.ok ? r.json() : null; })
    .catch(function () { return null; });
}

export function currentChapterId() {
  var sections = document.querySelectorAll("section.chapter[data-chapter-id]");
  var best = null;
  var bestVis = 0;
  sections.forEach(function (sec) {
    var rect = sec.getBoundingClientRect();
    var vis = Math.min(rect.bottom, window.innerHeight) - Math.max(rect.top, 0);
    if (vis > bestVis) {
      bestVis = vis;
      best = sec.getAttribute("data-chapter-id");
    }
  });
  return best;
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
