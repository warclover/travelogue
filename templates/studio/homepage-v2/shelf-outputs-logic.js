/**
 * OLT M2 · 票根副券纯函数（无 DOM · node --test）。
 * 副券文本不得含数字（铁律 6）。C 端禁词见 FORBIDDEN_COPY。
 */

export var SURFACE_RANK = {
  folio: 0,
  scroll: 1,
  card: 2,
  grid: 3,
  spread: 4,
  bundle: 5,
};

export var TICKET_SURFACES = ["folio", "scroll", "card", "grid", "spread"];

export var CHIP_LIMIT = 3;

export var FORBIDDEN_COPY = [
  "output",
  "surface",
  "ledger",
  "profile",
  "指纹",
  "fingerprint",
  "stale",
  "账本",
  "副券",
  "更新版面",
  "过期",
];

var CHIP_TEXT_RE = /^[^\d]+$/;

/** 票面副券短名。账本 / 管理成品仍用写入时的 label。 */
export var TICKET_CHIP_LABELS = {
  作品集页图: "作品集",
};

export function ticketChipLabel(label) {
  var raw = String(label || "").trim();
  return TICKET_CHIP_LABELS[raw] || raw;
}

export function isTicketSurface(surface) {
  return TICKET_SURFACES.indexOf(String(surface || "")) >= 0;
}

export function sortOutputs(rows) {
  var list = Array.isArray(rows) ? rows.slice() : [];
  list.sort(function (a, b) {
    return String((b && b.createdAt) || "").localeCompare(String((a && a.createdAt) || ""));
  });
  list.sort(function (a, b) {
    var ra = SURFACE_RANK[a && a.surface];
    var rb = SURFACE_RANK[b && b.surface];
    if (ra == null) ra = 50;
    if (rb == null) rb = 50;
    return ra - rb;
  });
  return list;
}

function decorateChip(raw) {
  var label = ticketChipLabel(String((raw && raw.label) || "").trim());
  var state = raw && raw.state === "outdated" ? "outdated" : "ready";
  var title =
    state === "outdated"
      ? label + " · 内容有更新，可重新导出"
      : label + " · 在文件夹中显示";
  return {
    outputId: String((raw && raw.outputId) || ""),
    label: label,
    state: state,
    text: label,
    title: title,
    ariaLabel: title,
    revealRelPath: raw && raw.revealRelPath ? String(raw.revealRelPath) : "",
    profile: raw && raw.profile ? String(raw.profile) : "",
  };
}

export function outputChips(row) {
  var total = 0;
  var ticket = [];
  if (row && row.outputSummary && Array.isArray(row.outputSummary.chips)) {
    total = Number(row.outputSummary.total || 0);
    ticket = row.outputSummary.chips.slice();
  } else if (row && Array.isArray(row.outputs)) {
    total = row.outputs.length;
    ticket = sortOutputs(row.outputs.filter(function (item) {
      return isTicketSurface(item && item.surface);
    }));
  }
  var visible = ticket.slice(0, CHIP_LIMIT).map(decorateChip);
  return {
    chips: visible,
    overflow: Math.max(0, total - visible.length),
    total: total,
  };
}

/** AC-OLT-14 · 零成品不插副券行，票面孩子与改前一致。 */
export var ZERO_OUTPUT_TICKET_SHAPE = Object.freeze({
  openMetaClass: "v2-shelf__open v2-shelf__open--meta v2-shelf__stub",
  children: Object.freeze(["v2-shelf__stub-main"]),
});

export function shouldInsertOutputStubs(row) {
  var view = outputChips(row);
  return view.chips.length > 0 || view.overflow > 0;
}

export function ticketOpenMetaShape(row) {
  var children = ["v2-shelf__stub-main"];
  var classes = ["v2-shelf__open", "v2-shelf__open--meta", "v2-shelf__stub"];
  if (shouldInsertOutputStubs(row)) {
    children.push("v2-shelf__stubs");
    classes.push("v2-shelf__stub--chips");
  }
  return { openMetaClass: classes.join(" "), children: children };
}

export function chipTextHasNoDigits(text) {
  return CHIP_TEXT_RE.test(String(text || ""));
}

export function visibleCopyIsClean(text) {
  var lower = String(text || "").toLowerCase();
  for (var i = 0; i < FORBIDDEN_COPY.length; i++) {
    if (lower.indexOf(FORBIDDEN_COPY[i].toLowerCase()) >= 0) return false;
  }
  return true;
}

export function overflowAriaLabel(n) {
  return "还有 " + Number(n || 0) + " 种成品，点击查看";
}

export function manageDateLabel(iso) {
  var raw = String(iso || "").trim();
  if (!raw) return "";
  var d = new Date(raw);
  if (isNaN(d.getTime())) {
    var m = raw.match(/^(\d{4})-(\d{2})-(\d{2})/);
    if (!m) return "";
    return m[1] + " · " + m[2] + " · " + m[3];
  }
  var y = d.getUTCFullYear();
  var mo = String(d.getUTCMonth() + 1).padStart(2, "0");
  var day = String(d.getUTCDate()).padStart(2, "0");
  return y + " · " + mo + " · " + day;
}

export function manageFileLabel(count) {
  var n = Number(count || 0);
  if (!isFinite(n) || n < 0) n = 0;
  return n + " 个文件";
}

export function manageStateLabel(state) {
  return state === "outdated" ? "有更新" : "最新";
}

export function manageRows(outputs) {
  var list = sortOutputs(Array.isArray(outputs) ? outputs : []);
  return list.map(function (item) {
    var date = manageDateLabel(item && item.createdAt);
    var files = manageFileLabel(item && (item.fileCount != null ? item.fileCount : (item.files || []).length));
    var bits = [files];
    if (date) bits.push(date);
    return {
      outputId: String((item && item.outputId) || ""),
      profile: String((item && item.profile) || ""),
      label: String((item && item.label) || ""),
      state: item && item.state === "outdated" ? "outdated" : "ready",
      stateLabel: manageStateLabel(item && item.state),
      sub: bits.join(" · "),
      revealRelPath: item && item.revealRelPath ? String(item.revealRelPath) : "",
    };
  });
}

export function deleteConfirmCopy(title, label) {
  return "删除《" + String(title || "") + "》的" + String(label || "") + "？只删这份成品，不影响这本书本身。";
}

export function revealFailToast() {
  return "没找到这份文件，可能已被移动或删除。";
}

export function hasManageOutputs(row) {
  var summary = row && row.outputSummary;
  if (summary && Number(summary.total || 0) > 0) return true;
  return !!(row && Array.isArray(row.outputs) && row.outputs.length);
}

/** AC-OLT-26 helper: ready badge + outdated chip must not share a card. */
export function readyConflictsOutdated(row) {
  if (!row || row.longshotStale) return false;
  var view = outputChips(row);
  return view.chips.some(function (chip) {
    return chip.state === "outdated";
  });
}

/** Belt-and-suspenders: hide「分享图已就绪」when chips already say outdated. */
export function allowReadyBadge(row) {
  return !readyConflictsOutdated(row);
}

export function reexportRequest(item) {
  var outputId = String((item && (item.outputId || item.profile)) || "");
  var profile = String((item && item.profile) || outputId.split(":")[0] || "");
  var next = { platform: profile };
  if (outputId === "wechat_chat:whole") {
    next.platform = "wechat_chat";
    next.segmentMode = "full";
  } else if (outputId === "wechat_chat:chapter") {
    next.platform = "wechat_chat";
    next.segmentMode = "chapter";
  }
  return next;
}
