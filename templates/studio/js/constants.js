/**
 * Travelogue Studio · constants
 * Static label/error/sample data and tunable thresholds (no runtime state).
 */

/** Mirror travelogue/web/studio_constants.py STUDIO_USER_NOTES_MAX_LEN */
export const STUDIO_USER_NOTES_MAX_LEN = 200;

/** Mirror travelogue/services/copy_subject.py GENERIC_PLACES */
export const GENERIC_PLACES = new Set(["", "旅途", "未知"]);

export function isGenericPlace(name) {
  var s = (name || "").trim();
  return !s || GENERIC_PLACES.has(s);
}

/** Bundled / trial demo trips only — not user imports whose slug is demo-{hash} (CJK folder names). */
export function isDemoTrip(trip) {
  if (!trip) return false;
  var id = String(trip.tripId || "");
  if (id === "demo-album") return true;
  var title = String(trip.title || "").trim();
  if (title === "示例旅途" || title === "示例") return true;
  return false;
}

export function markSampleEngaged() {
  try { localStorage.setItem(LS.sampleViewed, "1"); } catch (e) { /* ignore */ }
}

// ── Stage labels (§8.2) ──
export const STAGE_LABELS = {
  ingest: "正在读取你的照片",
  curate: "正在挑选与排版",
  narrate: "正在撰写游记文字",
  render: "正在生成杂志预览",
};

// P5-10.1 · mirror travelogue/web/studio_errors.py USER_MESSAGES
export const STUDIO_ERROR_MESSAGES = {
  E_DEMO_EXISTS: "该游记已存在。是否覆盖？",
  E_DEMO_NOT_DIR: "所选路径不是文件夹",
  E_DEMO_TOO_FEW: "至少需要 4 张照片，请换一个文件夹",
  E_INGEST_EMPTY: "文件夹里没有找到照片",
  E_INGEST_TOO_FEW: "至少需要 4 张照片，请换一个文件夹",
  E_STUDIO_JOB_BUSY: "排队中，请稍候",
  E_STUDIO_UPLOAD_EMPTY: "未收到任何照片文件",
  E_STUDIO_CANCELLED: "已取消",
  E_STUDIO_PIPELINE: "导入失败，请重试",
  E_STUDIO_AUTH: "Studio 请求未授权",
  E_STUDIO_BODY_TOO_LARGE: "请求体过大",
  E_STUDIO_ALBUM_DENIED: "不允许从该路径导入",
  E_STUDIO_REVEAL_DENIED: "无法打开该文件",
  E_PICK_FOLDER_UNSUPPORTED: "当前环境不支持原生选文件夹，请改用路径导入或浏览器上传",
  E_PICK_FOLDER_DENIED: "仅允许本机访问选文件夹",
  E_PICK_FOLDER_FAILED: "无法打开本机文件夹选择器，请粘贴路径或安装 pip install -e \".[desktop]\"",
  E_STUDIO_CONFIG_WRITE: "无法写入 config.yaml，请检查文件权限",
  E_LNG_CAPTURE_FAILED: "长图生成失败，请重试",
  E_LNG_NO_LONGSHOT: "未找到长图页面，请先完成渲染",
  E_LNG_PLAYWRIGHT: "无法生成长图，请安装 Playwright",
  E_LLM_AUTH: "未配置 LLM API Key，无法生成杂志感文案",
  E_NARRATE_API: "文案生成失败，请重试",
  E_TRIP_NOT_FOUND: "游记不存在",
  E_EXPORT_PRIVACY: "导出 zip 需要确认隐私设置",
};

export const DEFAULT_PIPELINE_ESTIMATES = [
  { maxPhotos: 50, hint: "约 3–5 分钟" },
  { maxPhotos: 100, hint: "约 5–8 分钟" },
  { maxPhotos: 200, hint: "约 8–15 分钟" },
  { maxPhotos: 999999, hint: "约 12–25 分钟" },
];

// ── localStorage keys (§9.3) ──
export const LS = {
  firstPreviewDone: "travelogue.studio.firstPreviewDone",
  firstReturnHighlight: "travelogue.studio.firstReturnHighlight",
  demoTried: "travelogue.studio.demoTried",
  sampleViewed: "travelogue.studio.sampleViewed",
  recentPaths: "travelogue.studio.recentPaths",
  lastCancelled: "travelogue.studio.lastCancelled",
  studioIntent: "travelogue.studio.intent",
  coachImportV1: "travelogue.studio.coachImportV1",
};

export const SS = {
  activeJobId: "travelogue.studio.activeJobId",
  activePending: "travelogue.studio.activePending",
};

export const SAMPLE_LONGSHOTS = {
  kyoto: {
    title: "京都 · 雨后",
    meta: "86 张 · 4 章 · 静谧",
    thumbSrc: "/__studio/assets/sample-longshots/kyoto-thumb.jpg",
    fullSrc: "/__studio/assets/sample-longshot.jpg",
    paper: "#fbf6ee",
    ink: "#2a2520",
    colors: ["#b04331", "#3a4b3f", "#c9a85d", "#6c4a32"],
    chapters: ["雨夜抵达", "庙宇晨光", "竹林深处", "归途"],
  },
  iceland: {
    title: "冰岛 · 极光",
    meta: "120 张 · 5 章 · 壮阔",
    thumbSrc: "/__studio/assets/sample-longshots/iceland-thumb.jpg",
    fullSrc: "/__studio/assets/sample-longshot.jpg",
    paper: "#f0f3f6",
    ink: "#1a1f2e",
    colors: ["#2a2a4a", "#7cc1a8", "#5d7a9e", "#b8c5d6", "#3a4862"],
    chapters: ["落地", "黑沙滩", "极光夜", "蓝冰洞", "告别"],
  },
  linzhi: {
    title: "林芝 · 桃花",
    meta: "64 张 · 3 章 · 抒情",
    thumbSrc: "/__studio/assets/sample-longshots/linzhi-thumb.jpg",
    fullSrc: "/__studio/assets/sample-longshot.jpg",
    paper: "#fef3f5",
    ink: "#3a2530",
    colors: ["#e6a6b5", "#7a8a72", "#d68aa0"],
    chapters: ["桃花初放", "雪山之下", "夜话"],
  },
};

// ── Thresholds / limits ──
export const SLOW_JOB_MS = 30000;
export const SLOW_JOB_VISION_MS = 180000;
export const SLOW_JOB_VISION_LONG_MS = 480000;
export const HEALTH_INTERVAL = 30000;
export const UPLOAD_BYTES_SOFT_LIMIT = 200 * 1024 * 1024;
export const IMPORT_PHOTO_CAP = 250;
export const SUCCESS_LONGSHOT_SCALE = 2;
export const SUCCESS_SLOW_MS = 30000;

export const SHEET_FOCUSABLE =
  'a[href],button:not([disabled]),input:not([disabled]):not([type="hidden"]),textarea:not([disabled]),select:not([disabled]),summary,[tabindex]:not([tabindex="-1"])';
