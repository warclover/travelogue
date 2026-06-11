/**
 * Preview toolbar · longshot result side drawer (§6.4).
 */
"use strict";

import { setToolbarCollapsed } from "./shell.js";
import { revealTripPath, tripIdFromPath } from "./toolbar-ui.js";

var _longshotDrawerTimer = null;
var LONGSHOT_DRAWER_AUTO_MS = 3000;

function clearLongshotDrawerTimer() {
  if (_longshotDrawerTimer) {
    clearTimeout(_longshotDrawerTimer);
    _longshotDrawerTimer = null;
  }
}

function scheduleLongshotDrawerAutoHide(root) {
  clearLongshotDrawerTimer();
  _longshotDrawerTimer = setTimeout(function () {
    _longshotDrawerTimer = null;
    hideLongshotDrawer(root);
  }, LONGSHOT_DRAWER_AUTO_MS);
}

function getLongshotDrawer(root, create) {
  if (create === undefined) create = true;
  var drawer = document.getElementById("preview-toolbar-longshot-drawer");
  if (drawer) return drawer;
  if (!create) return null;
  drawer = document.createElement("aside");
  drawer.className = "preview-toolbar__drawer preview-toolbar__drawer--side";
  drawer.id = "preview-toolbar-longshot-drawer";
  drawer.setAttribute("role", "status");
  drawer.setAttribute("aria-label", "长图保存结果");
  drawer.hidden = true;
  document.body.appendChild(drawer);
  return drawer;
}

export function hideLongshotDrawer(root) {
  clearLongshotDrawerTimer();
  var drawer = getLongshotDrawer(root, false);
  if (!drawer) return;
  drawer.classList.remove("preview-toolbar__drawer--open");
  drawer.hidden = true;
}

export function openLongshotResultDrawer(root) {
  setToolbarCollapsed(root, false, false);
  clearLongshotDrawerTimer();
  var drawer = getLongshotDrawer(root);
  if (!drawer) return;
  if (root._lastLongshotJob && drawer.childElementCount === 0) {
    showLongshotDrawer(root, root._lastLongshotJob, { autoHide: false });
    return;
  }
  drawer.hidden = false;
  drawer.classList.add("preview-toolbar__drawer--open");
}

export function showLongshotDrawer(root, job, opts) {
  opts = opts || {};
  root._lastLongshotJob = job;
  var tripId = tripIdFromPath();
  var drawer = getLongshotDrawer(root);
  setToolbarCollapsed(root, false, false);
  drawer.hidden = false;
  drawer.classList.add("preview-toolbar__drawer--open");
  drawer.textContent = "";

  var head = document.createElement("div");
  head.className = "preview-toolbar__drawer-head";
  var title = document.createElement("p");
  title.className = "preview-toolbar__drawer-title";
  var closeBtn = document.createElement("button");
  closeBtn.type = "button";
  closeBtn.className = "preview-toolbar__drawer-close";
  closeBtn.setAttribute("aria-label", "关闭");
  closeBtn.textContent = "×";
  closeBtn.addEventListener("click", function () {
    hideLongshotDrawer(root);
  });
  head.appendChild(title);
  head.appendChild(closeBtn);
  drawer.appendChild(head);

  if (job.status === "failed") {
    title.textContent = "保存失败";
    var err = (job.error && (job.error.message || job.error.code)) || "导出失败";
    var errEl = document.createElement("p");
    errEl.className = "preview-toolbar__longshot-error";
    errEl.textContent = err;
    drawer.appendChild(errEl);
    return;
  }

  title.textContent = "✓ 长图已保存";

  var result = job.result || {};
  var outputs = result.outputs || [];
  var method = result.captureMethod || "p0";
  var segmented = result.segmented || outputs.length > 1;

  var homeHint = document.createElement("p");
  homeHint.className = "preview-toolbar__longshot-compat";
  homeHint.textContent = "已写入画册目录；返回 Studio 首页即可在手机框预览。";
  drawer.appendChild(homeHint);

  if (segmented && outputs.length > 1) {
    var segEl = document.createElement("p");
    segEl.className = "preview-toolbar__longshot-compat";
    segEl.textContent =
      result.userHint ||
      "已按章导出 " + outputs.length + " 张，底部含页码（如 2/5）便于微信按序发送。";
    drawer.appendChild(segEl);
  }
  if (method === "p1") {
    var compatEl = document.createElement("p");
    compatEl.className = "preview-toolbar__longshot-compat";
    compatEl.textContent = "已使用兼容模式导出，与预览可能有细微差异。";
    drawer.appendChild(compatEl);
  }

  var actions = document.createElement("div");
  actions.className = "preview-toolbar__drawer-actions";

  if (outputs.length) {
    var list = document.createElement("ul");
    list.className = "preview-toolbar__longshot-paths";
    outputs.forEach(function (rel) {
      var li = document.createElement("li");
      li.textContent = rel;
      list.appendChild(li);
    });
    drawer.appendChild(list);

    var revealBtn = document.createElement("button");
    revealBtn.type = "button";
    revealBtn.className = "preview-toolbar__reveal";
    revealBtn.textContent = "在文件夹中显示";
    revealBtn.addEventListener("click", function () {
      revealTripPath(tripId, outputs[0]);
    });
    actions.appendChild(revealBtn);
  }

  var dismissBtn = document.createElement("button");
  dismissBtn.type = "button";
  dismissBtn.className = "preview-toolbar__drawer-secondary";
  dismissBtn.textContent = "收起";
  dismissBtn.addEventListener("click", function () {
    hideLongshotDrawer(root);
  });
  actions.appendChild(dismissBtn);
  drawer.appendChild(actions);

  if (opts.autoHide !== false) {
    scheduleLongshotDrawerAutoHide(root);
  }
}
