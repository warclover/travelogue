(function () {
  "use strict";

  var HINT_KEY = "travelogue.studio.editHint.dismissed";
  var LONGSHOT_SCALE = 2;
  var pollTimer = null;

  function tripIdFromPath() {
    var parts = window.location.pathname.replace(/^\/+|\/+$/g, "").split("/");
    return parts[0] || "";
  }

  function postJson(url, payload) {
    return fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload || {}),
    }).then(function (resp) {
      return resp.json().then(function (body) {
        return { status: resp.status, body: body };
      });
    });
  }

  function pollJob(jobId, onDone) {
    if (pollTimer) {
      clearInterval(pollTimer);
      pollTimer = null;
    }
    pollTimer = setInterval(function () {
      fetch("/__travelogue/status?jobId=" + encodeURIComponent(jobId))
        .then(function (resp) { return resp.json(); })
        .then(function (job) {
          if (job.status === "succeeded" || job.status === "failed") {
            clearInterval(pollTimer);
            pollTimer = null;
            onDone(job);
          }
        })
        .catch(function () {});
    }, 800);
  }

  function showLongshotPanel(root, job) {
    var panel = root.querySelector(".studio-chrome__longshot-panel");
    if (!panel) {
      panel = document.createElement("div");
      panel.className = "studio-chrome__longshot-panel";
      root.appendChild(panel);
    }
    panel.hidden = false;

    if (job.status === "failed") {
      var err = (job.error && (job.error.message || job.error.code)) || "导出失败";
      panel.innerHTML = '<p class="studio-chrome__longshot-error">' + err + "</p>";
      return;
    }

    var result = job.result || {};
    var outputs = result.outputs || [];
    var method = result.captureMethod || "p0";
    var html = '<p class="studio-chrome__longshot-ok">长图已保存</p>';
    if (method === "p1") {
      html += '<p class="studio-chrome__longshot-compat">已使用兼容模式导出，与预览可能有细微差异。</p>';
    }
    if (outputs.length) {
      html += '<ul class="studio-chrome__longshot-paths">';
      outputs.forEach(function (p) {
        html += "<li>" + p + "</li>";
      });
      html += "</ul>";
      html +=
        '<button type="button" class="studio-chrome__reveal" data-path="' +
        outputs[0].replace(/"/g, "&quot;") +
        '">在文件夹中显示</button>';
    }
    panel.innerHTML = html;
    var revealBtn = panel.querySelector(".studio-chrome__reveal");
    if (revealBtn) {
      revealBtn.addEventListener("click", function () {
        postJson("/__travelogue/reveal", { path: revealBtn.getAttribute("data-path") });
      });
    }
  }

  function initLongshot(root) {
    var tripId = tripIdFromPath();
    if (!tripId) return;

    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "studio-chrome__longshot";
    btn.textContent = "保存长图";
    root.querySelector(".studio-chrome__bar").appendChild(btn);

    var status = document.createElement("span");
    status.className = "studio-chrome__longshot-status";
    status.hidden = true;
    root.querySelector(".studio-chrome__bar").appendChild(status);

    btn.addEventListener("click", function () {
      if (btn.disabled) return;
      btn.disabled = true;
      status.hidden = false;
      status.textContent = "正在生成长图…";

      postJson("/__travelogue/longshot", {
        tripId: tripId,
        scale: LONGSHOT_SCALE,
        format: "png",
      })
        .then(function (res) {
          if (res.status === 409) {
            status.textContent = (res.body && res.body.message) || "请稍候再试";
            btn.disabled = false;
            return;
          }
          if (res.status !== 202 || !res.body.jobId) {
            status.textContent = "无法开始导出";
            btn.disabled = false;
            return;
          }
          pollJob(res.body.jobId, function (job) {
            btn.disabled = false;
            status.hidden = true;
            showLongshotPanel(root, job);
          });
        })
        .catch(function () {
          btn.disabled = false;
          status.textContent = "网络错误";
        });
    });
  }

  function init() {
    document.documentElement.setAttribute("data-studio-chrome", "on");

    var root = document.createElement("div");
    root.className = "studio-chrome";
    root.innerHTML =
      '<div class="studio-chrome__bar">' +
      '<a class="studio-chrome__back" href="/">← 返回工作台</a>' +
      "</div>";

    var hintHidden = false;
    try {
      hintHidden = localStorage.getItem(HINT_KEY) === "1";
    } catch (e) {}

    if (!hintHidden) {
      var hint = document.createElement("div");
      hint.className = "studio-chrome__hint";
      hint.innerHTML =
        '<span>点击标题、导语、图注即可修改 · 修改后自动保存</span>' +
        '<button type="button" class="studio-chrome__dismiss" aria-label="关闭提示">知道了</button>';
      hint.querySelector(".studio-chrome__dismiss").addEventListener("click", function () {
        hint.hidden = true;
        try { localStorage.setItem(HINT_KEY, "1"); } catch (e2) {}
      });
      root.appendChild(hint);
    }

    document.body.insertBefore(root, document.body.firstChild);
    initLongshot(root);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
