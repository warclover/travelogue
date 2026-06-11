/**
 * Preview toolbar · ⋯ 菜单动作（M-P2b）。
 */
"use strict";

import { postJson } from "../js/http.js";
import { toolbarAlert, toolbarConfirm, revealTripPath } from "./toolbar-ui.js";

export function exportZip(tripId) {
  toolbarConfirm({
    title: "导出 zip",
    body: "导出 zip 包用于自行托管或备份，不是微信分享主路径。继续？",
    confirmText: "继续",
  }).then(function (ok) {
    if (!ok) return;
    return postJson("/__travelogue/export", { tripId: tripId, confirmPrivacy: true });
  }).then(function (res) {
    if (!res) return;
    if (res.status !== 200 || !res.body.ok) {
      toolbarAlert((res.body && res.body.message) || "导出失败", { error: true });
      return;
    }
    var zipRel = res.body.zipRelPath;
    if (!zipRel) return;
    return toolbarConfirm({
      title: "zip 已生成",
      body: "是否在文件夹中显示？",
      confirmText: "显示",
      cancelText: "关闭",
    }).then(function (reveal) {
      if (reveal) revealTripPath(tripId, zipRel);
    });
  }).catch(function () {
    toolbarAlert("导出失败", { error: true });
  });
}
