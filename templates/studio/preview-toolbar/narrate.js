/**
 * Preview toolbar · LLM narrate (⋯ 菜单).
 */
"use strict";

import { postJson } from "../js/http.js";
import { setToolbarCollapsed } from "./shell.js";
import { toolbarConfirm, toolbarAlert, setSlowHint } from "./toolbar-ui.js";
import { pollJob } from "./export-run.js";

var narrateJobId = null;

export function startLlmNarrate(root, tripId, btn) {
  if (!btn || btn.disabled) return;
  toolbarConfirm({
    title: "生成杂志感文案",
    body: "将调用 LLM 重写 hook、导语与图注，可能覆盖未锁定的文案。继续？",
    confirmText: "继续",
  }).then(function (ok) {
    if (!ok) return;
    setToolbarCollapsed(root, false, false);
    btn.disabled = true;
    setSlowHint(root, "", false);
    setSlowHint(root, "正在生成杂志感文案…", true);
    return postJson("/__travelogue/narrate", { tripId: tripId });
  }).then(function (res) {
    if (!res) return;
    if (res.status === 409 || res.status === 400) {
      setSlowHint(root, (res.body && res.body.message) || "无法开始", true);
      btn.disabled = false;
      return;
    }
    if (res.status !== 202 || !res.body.jobId) {
      setSlowHint(root, "无法开始文案生成", true);
      btn.disabled = false;
      return;
    }
    narrateJobId = res.body.jobId;
    pollJob(
      res.body.jobId,
      root,
      function (job) {
        btn.disabled = false;
        narrateJobId = null;
        setSlowHint(root, "", false);
        if (job.status === "succeeded") {
          window.location.reload();
          return;
        }
        var err = (job.error && (job.error.message || job.error.code)) || "文案生成失败";
        toolbarAlert(err, { error: true });
      },
      function () {
        setSlowHint(root, "比预期久一些，请耐心等待…", true);
      },
      "narrate"
    );
  }).catch(function () {
    btn.disabled = false;
    setSlowHint(root, "网络错误", true);
  });
}
