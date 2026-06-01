/**
 * 首页 v2 · demo-showcase manifest 加载与派生。
 * 契约：docs/studio-homepage-v2/DATA-CONTRACT.md §1 + manifest.schema.json
 */
import { STUDIO_DEMO_SHOWCASE_BASE } from "./store.js";

const MANIFEST_URL = STUDIO_DEMO_SHOWCASE_BASE + "manifest.json";

/** 将 manifest 中的相对路径拼成可访问的静态 URL。 */
export function assetUrl(relPath) {
  if (!relPath) return "";
  return STUDIO_DEMO_SHOWCASE_BASE + String(relPath).replace(/^\/+/, "");
}

/** 基本结构校验（轻量；权威 schema 见 manifest.schema.json）。 */
export function isValidManifest(m) {
  if (!m || typeof m !== "object") return false;
  if (!m.version || !m.title) return false;
  if (!m.assets || !m.assets.background || !m.assets.longshot) return false;
  if (!Array.isArray(m.pages) || m.pages.length < 3) return false;
  return m.pages.every(function (p) {
    return p && p.id && p.role && p.label && p.webp;
  });
}

/**
 * 加载 manifest。失败 / 不合法时 resolve(null)，由调用方走 §11.4 降级
 * （Slogan + CTA + 占位，不白屏）。
 */
export function loadManifest() {
  return fetch(MANIFEST_URL)
    .then(function (r) {
      if (!r.ok) throw new Error("manifest unavailable");
      return r.json();
    })
    .then(function (m) {
      return isValidManifest(m) ? m : null;
    })
    .catch(function () {
      return null;
    });
}
