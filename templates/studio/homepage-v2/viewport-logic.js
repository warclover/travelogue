/**
 * 首页 v2 · 视口分类纯逻辑（无 DOM，可被浏览器与 node --test 导入）。
 *
 * 契约：PRD §10.1 支持矩阵
 *  - ≥1024px          → wide（Bento 双列）
 *  - 768–1023 横屏    → tablet_landscape（iPad 横屏 · 同 Bento 双列）
 *  - 768–1023 竖屏    → unsupported_rotate（旋转提示）
 *  - <768 触屏(phone) → unsupported_phone（去电脑/小程序）
 *  - <768 桌面窄窗    → unsupported_narrow（拉宽窗口）
 * 拒绝 768 三行堆叠。
 */

export const WIDE_MIN_WIDTH = 1024;
export const TABLET_MIN_WIDTH = 768;
export const MINIAPP_QR_SRC = "/__studio/assets/miniapp-qr.webp";

/** @returns {'wide'|'tablet_landscape'|'unsupported_rotate'|'unsupported_phone'|'unsupported_narrow'} */
export function classifyViewport(width, height, coarsePointer) {
  var w = Number(width) || 0;
  var h = Number(height) || 0;
  if (w >= WIDE_MIN_WIDTH) return "wide";
  if (w >= TABLET_MIN_WIDTH) {
    return w >= h ? "tablet_landscape" : "unsupported_rotate";
  }
  // 窄视口
  return coarsePointer ? "unsupported_phone" : "unsupported_narrow";
}

export function isSupported(layout) {
  return layout === "wide" || layout === "tablet_landscape";
}

/**
 * Unsupported 文案与动作区（§10.3 · D-20）。
 * @param {string} layout
 * @param {{ width?: number, miniappQrAvailable?: boolean }} [ctx]
 *   width：narrow 态 lead 提示；miniappQrAvailable：FE-DFX-40 无能力时不塞 QR 位
 */
export function unsupportedCopy(layout, ctx) {
  ctx = ctx || {};
  var width = Number(ctx.width) || 0;
  var qrAvailable = ctx.miniappQrAvailable !== false;
  if (layout === "unsupported_rotate") {
    return {
      title: "请旋转至横屏使用 Studio",
      lead: "Studio 工作台为横屏双列设计，请将设备旋转至横屏。",
      actions: [],
    };
  }
  if (layout === "unsupported_phone") {
    var phoneActions = [];
    if (qrAvailable) {
      phoneActions.push({
        type: "miniapp_qr",
        src: MINIAPP_QR_SRC,
        fallback: "小程序即将上线",
      });
    }
    phoneActions.push({ type: "copy_link", label: "复制电脑打开地址" });
    return {
      title: "请在电脑浏览器打开 Studio",
      lead: qrAvailable
        ? "手机端的阅读与分享请使用微信小程序；工作台导入请在电脑浏览器打开。"
        : "请在电脑浏览器打开本页以使用工作台；手机端小程序即将上线。",
      actions: phoneActions,
    };
  }
  var widthHint = width > 0 ? "当前 " + Math.round(width) + "px · " : "";
  return {
    title: "请拉宽窗口至 1024px 以上",
    lead: widthHint + "拉宽窗口即可进入 Studio 工作台。",
    actions: [],
  };
}
