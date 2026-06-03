function $(id) {
  return document.getElementById(id);
}

function setStatus(text) {
  var el = $("classic-status");
  if (el) el.textContent = text || "";
}

async function requestPickFolder() {
  try {
    var resp = await fetch("/__travelogue/pick-folder", { method: "POST" });
    var data = await resp.json();
    if (data && data.path) {
      $("classic-album-path").value = data.path;
      setStatus("已选择文件夹");
      return;
    }
    if (data && data.cancelled) {
      setStatus("已取消选择");
      return;
    }
    setStatus("当前环境不支持选择文件夹");
  } catch (_err) {
    setStatus("选择文件夹失败");
  }
}

async function pollJob(jobId) {
  for (var i = 0; i < 180; i += 1) {
    var resp = await fetch("/__travelogue/status?jobId=" + encodeURIComponent(jobId));
    var data = await resp.json();
    if (data.status === "succeeded") {
      var url = data.previewUrl || ("/" + data.tripId + "/index.html");
      window.location.href = url;
      return;
    }
    if (data.status === "failed" || data.status === "cancelled") {
      setStatus("导入失败，请重试");
      return;
    }
    setStatus(data.stageHint || "正在导入，请稍候...");
    await new Promise(function (resolve) { setTimeout(resolve, 1000); });
  }
  setStatus("导入耗时较长，请稍后查看");
}

async function startImport() {
  var path = ($("classic-album-path").value || "").trim();
  if (!path) {
    setStatus("请先输入或选择文件夹路径");
    return;
  }
  setStatus("正在提交导入任务...");
  try {
    var resp = await fetch("/__travelogue/import", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        albumPath: path,
        title: "",
        place: "",
      }),
    });
    var data = await resp.json();
    if (!resp.ok || !data.jobId) {
      setStatus((data && data.error) || "导入请求失败");
      return;
    }
    await pollJob(String(data.jobId));
  } catch (_err) {
    setStatus("导入请求失败");
  }
}

document.addEventListener("DOMContentLoaded", function () {
  var pick = $("classic-pick");
  var start = $("classic-start");
  if (pick) pick.addEventListener("click", requestPickFolder);
  if (start) start.addEventListener("click", startImport);
});
