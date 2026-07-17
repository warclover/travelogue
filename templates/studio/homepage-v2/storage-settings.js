/**
 * 设置 · 存储与磁盘（PRD-MEDIA-REFERENCE-STORAGE-V1）
 */
import { $, studioAuthHeaders } from "../js/dom.js";
import { trackStudioEvent } from "../js/analytics.js";
import { V2 } from "./store.js";

function formatBytes(n) {
  var v = Number(n) || 0;
  if (v < 1024) return v + " B";
  if (v < 1024 * 1024) return (v / 1024).toFixed(1) + " KB";
  if (v < 1024 * 1024 * 1024) return (v / (1024 * 1024)).toFixed(1) + " MB";
  return (v / (1024 * 1024 * 1024)).toFixed(2) + " GB";
}

function toast(msg, opts) {
  if (typeof studioToast === "function") studioToast(msg, opts || { duration: 2500 });
}

function storageModeLabel(mode) {
  if (mode === "referenced") return "引用原相册";
  if (mode === "mixed") return "混合";
  if (mode === "copied") return "已复制源文件";
  return "";
}

export function bindStorageSettings() {
  var copySelect = $("studio-cfg-copy-source");
  var usageLine = $("studio-storage-usage-line");
  var modeLine = $("studio-storage-mode-line");
  var cleanupBtn = $("studio-storage-cleanup-btn");
  if (!copySelect) return null;

  var _patchPending = false;

  function syncCopySeg() {
    var group = document.querySelector('[data-seg-for="studio-cfg-copy-source"]');
    if (!group || !copySelect) return;
    var val = copySelect.value;
    Array.prototype.forEach.call(group.querySelectorAll(".v2-settings-seg__btn"), function (btn) {
      btn.classList.toggle("is-on", btn.getAttribute("data-value") === val);
    });
  }

  function applyConfig(data) {
    if (!data || data.ok === false) return;
    if (data.ingest && typeof data.ingest.copySourceFiles === "boolean") {
      copySelect.value = data.ingest.copySourceFiles ? "true" : "false";
      syncCopySeg();
    }
  }

  function refreshTripStorageMode() {
    if (!modeLine) return Promise.resolve();
    var tripId =
      (typeof V2 !== "undefined" && V2 && V2.bentoPreviewTripId) ||
      "";
    if (!tripId) {
      modeLine.hidden = true;
      modeLine.textContent = "";
      return Promise.resolve();
    }
    return fetch(
      "/__travelogue/trips/" + encodeURIComponent(tripId) + "/source-status",
      { headers: studioAuthHeaders() }
    )
      .then(function (r) {
        return r.json();
      })
      .then(function (data) {
        if (!data || data.ok === false) {
          modeLine.hidden = true;
          return;
        }
        var label = storageModeLabel(data.storageMode);
        if (!label) {
          modeLine.hidden = true;
          return;
        }
        modeLine.hidden = false;
        modeLine.textContent = "当前预览作品存储模式：" + label;
      })
      .catch(function () {
        modeLine.hidden = true;
      });
  }

  function refreshUsage() {
    return fetch("/__travelogue/storage/usage", {
      headers: studioAuthHeaders(),
    })
      .then(function (r) {
        return r.json();
      })
      .then(function (data) {
        if (!usageLine || !data || data.ok === false) return;
        var total = formatBytes(data.bytesTotal);
        var warn = data.overThreshold
          ? " · 占用较高，建议清理"
          : "";
        usageLine.textContent =
          "作品库约 " +
          total +
          "（源文件 " +
          formatBytes(data.bytesSource) +
          " · 预览图 " +
          formatBytes(data.bytesAssets) +
          " · 缓存 " +
          formatBytes(data.bytesCache) +
          "）" +
          warn;
        if (data.tripsDir) {
          usageLine.title = data.tripsDir;
        }
        var meta = $("v2-settings-meta-storage");
        if (meta) {
          var copyBit =
            copySelect && copySelect.value === "false" ? "引用相册" : "复制开";
          meta.textContent = data.overThreshold
            ? total + " · 建议清理"
            : total + " · " + copyBit;
          meta.classList.toggle("is-warn", !!data.overThreshold);
        }
      })
      .catch(function () {
        if (usageLine) usageLine.textContent = "无法估算占用";
        var metaFail = $("v2-settings-meta-storage");
        if (metaFail) metaFail.textContent = "无法估算";
      })
      .then(function () {
        return refreshTripStorageMode();
      });
  }

  function fetchConfig() {
    return fetch("/__travelogue/config", { headers: studioAuthHeaders() })
      .then(function (r) {
        return r.json();
      })
      .then(function (data) {
        applyConfig(data);
        return refreshUsage();
      })
      .catch(function () {});
  }

  function patchCopySource() {
    if (_patchPending) return;
    _patchPending = true;
    var enabled = copySelect.value === "true";
    trackStudioEvent("storage_copy_source_toggle", { enabled: enabled });
    fetch("/__travelogue/config", {
      method: "PATCH",
      headers: studioAuthHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({ ingest: { copySourceFiles: enabled } }),
    })
      .then(function (r) {
        return r.json();
      })
      .then(function (data) {
        applyConfig(data);
        toast("存储设置已保存", { duration: 2000 });
      })
      .catch(function () {
        toast("保存失败，请重试");
      })
      .finally(function () {
        _patchPending = false;
      });
  }

  function runCleanup() {
    var deep = window.confirm(
      "将清理可再生缓存（安全）。\n\n若还要删除作品内已拷贝的源照片，请在下一步确认。\n\n继续安全清理？"
    );
    if (!deep) return;
    var deepSource = window.confirm(
      "将删除作品内已拷贝的源照片文件。预览用图片会保留，但重导出原图像素可能需要你的原相册仍可访问。此操作无法撤销。\n\n是否同时删除源文件拷贝？\n（选「取消」则仅做安全清理）"
    );
    var acceptOnly = false;
    if (deepSource) {
      acceptOnly = window.confirm(
        "部分旧作品可能没有原相册引用。\n\n若仍要删除它们的源文件拷贝，请确认：\n我接受仅保留衍生图，放弃这些照片的原图像素能力。\n\n确定？"
      );
      if (!acceptOnly) {
        acceptOnly = false;
      }
    }
    cleanupBtn.disabled = true;
    fetch("/__travelogue/storage/cleanup", {
      method: "POST",
      headers: studioAuthHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({
        safe: true,
        deepSource: !!deepSource,
        acceptDerivativesOnly: !!acceptOnly,
        devScratch: true,
      }),
    })
      .then(function (r) {
        return r.json().then(function (data) {
          return { status: r.status, data: data };
        });
      })
      .then(function (res) {
        trackStudioEvent("storage_cleanup_run", {
          ok: !!(res.data && res.data.ok),
          deep_source: !!deepSource,
          bytes_freed: (res.data && res.data.bytesFreed) || 0,
        });
        if (!res.data || res.data.ok === false) {
          toast((res.data && res.data.message) || "清理未完成");
          return;
        }
        var msg = "已释放约 " + formatBytes(res.data.bytesFreed);
        if (res.data.hint) msg += "。" + res.data.hint;
        toast(msg, { duration: 4000 });
        refreshUsage();
      })
      .catch(function () {
        toast("清理失败，请重试");
      })
      .finally(function () {
        cleanupBtn.disabled = false;
      });
  }

  copySelect.addEventListener("change", patchCopySource);
  if (cleanupBtn) cleanupBtn.addEventListener("click", runCleanup);

  return {
    fetchConfig: fetchConfig,
    refreshUsage: refreshUsage,
    refreshTripStorageMode: refreshTripStorageMode,
  };
}
