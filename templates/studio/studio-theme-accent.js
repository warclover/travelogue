/**
 * Studio 工作台配色 → 画册预览 journal --accent 联动。
 * 读取 localStorage travelogue.studio.v2.theme，在首屏绘制前写入 CSS 变量。
 */
(function () {
  var KEY = "travelogue.studio.v2.theme";
  var MAP = {
    mist: {
      accent: "#2d5678",
      soft: "rgba(45, 86, 120, 0.12)",
      mobile: "#4a7394",
    },
    folio: {
      accent: "#475061",
      soft: "rgba(71, 80, 97, 0.12)",
      mobile: "#5c6678",
    },
    classic: {
      accent: "#3d2b1f",
      soft: "rgba(61, 43, 31, 0.12)",
      mobile: "#c4a574",
    },
    dawn: {
      accent: "#c8553d",
      soft: "rgba(200, 85, 61, 0.12)",
      mobile: "#e86f51",
    },
    atelier: {
      accent: "#524b72",
      soft: "rgba(82, 75, 114, 0.12)",
      mobile: "#6a5f8f",
    },
    sky: {
      accent: "#3d6b5a",
      soft: "rgba(61, 107, 90, 0.12)",
      mobile: "#7cb89a",
    },
  };

  function resolveThemeId(raw) {
    if (raw && MAP[raw]) return raw;
    return "mist";
  }

  function applyAccent(themeId) {
    var palette = MAP[themeId] || MAP.mist;
    var root = document.documentElement;
    root.style.setProperty("--accent", palette.accent);
    root.style.setProperty("--accent-soft", palette.soft);
    root.style.setProperty("--accent-mobile", palette.mobile);
    root.setAttribute("data-studio-accent-theme", themeId);
  }

  try {
    applyAccent(resolveThemeId(localStorage.getItem(KEY)));
  } catch (e) {
    applyAccent("mist");
  }
})();
