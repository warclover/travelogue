// 设计工坊星级 + 禁用 · 权威解析。gallery / preview / bind / promote 共用。
// 引擎不读。数据包 / 总表 / USAGE 不写星、不写禁用。
(function (global) {
  const SEED = {
    "page-1-hero-land-right": 3,
    "page-1-hero-land-wide": 3,
    "page-1-hero-port": 3,
    "page-10-grid-port": 3,
    "page-2-1l1p-wide": 3,
    "page-2-1p1l-wide": 3,
    "page-2-pair-land": 3,
    "page-2-pair-port": 3,
    "page-3-2l1p-left": 3,
    "page-3-2l1p-right": 3,
    "page-3-2l1p-wide-left": 3,
    "page-3-2l1p-wide-right": 3,
    "page-3-land": 3,
    "page-3-port": 3,
    "page-4-1p3l-wide-left": 3,
    "page-4-1p3l-wide-right": 3,
    "page-4-2p2l-cross": 3,
    "page-4-grid-land": 3,
    "page-4-grid-land-wide": 3,
    "page-4-port": 3,
    "page-5-3p2l-center": 3,
    "page-5-3p2l-center-flip": 3,
    "page-6-1l5l-wide-left": 3,
    "page-6-2l4p-wide-flip": 3,
    "page-6-grid-land": 3,
    "page-7-1p6l-center": 3,
    "page-8-2l6p": 3,
    "page-8-grid-land": 3,
    "page-8-grid-port": 3,
    "page-9-grid-land-wide": 3,
    "page-4-1l3l-left": 2,
    "page-4-1l3l-right": 2,
    "page-4-1l3l-wide-left": 2,
    "page-4-1l3l-wide-right": 2,
    "page-5-1p4l-center": 2,
    "page-5-3p2l-left": 2,
    "page-5-3p2l-right": 2,
    "page-5-3p2l-stack-center": 2,
    "page-5-3p2l-stack-right": 2,
    "page-6-1l5l-wide-right": 2,
    "page-6-2l4p-left": 2,
    "page-6-2l4p-right": 2,
    "page-7-1p6l-left": 2,
    "page-7-1p6l-right": 2,
    "page-4-1p3l-left": 1
  };

  function normalizeStars(map) {
    const out = {};
    for (const [id, raw] of Object.entries(map || {})) {
      const n = Number(raw);
      if (n >= 1 && n <= 3) out[id] = n;
    }
    return out;
  }

  function normalizeDisabled(list) {
    const out = [];
    const seen = new Set();
    for (const raw of list || []) {
      const id = String(raw || "").trim();
      if (!id || seen.has(id)) continue;
      seen.add(id);
      out.push(id);
    }
    out.sort((a, b) => a.localeCompare(b));
    return out;
  }

  function parseStarsYaml(text) {
    const stars = {};
    const disabled = [];
    let inDisabled = false;
    for (const raw of String(text).split(/\r?\n/)) {
      const line = raw.trim();
      if (!line || line.startsWith("#")) continue;
      if (/^disabled:\s*\[\s*\]\s*$/.test(line)) {
        inDisabled = false;
        continue;
      }
      if (/^disabled:\s*$/.test(line)) {
        inDisabled = true;
        continue;
      }
      if (inDisabled) {
        const item = /^-\s+([a-z0-9-]+)\s*$/.exec(line);
        if (item) {
          disabled.push(item[1]);
          continue;
        }
        inDisabled = false;
      }
      const m = /^([a-z0-9-]+):\s*([0-3])\s*$/.exec(line);
      if (m) stars[m[1]] = Number(m[2]);
    }
    return {
      stars: normalizeStars(stars),
      disabled: normalizeDisabled(disabled)
    };
  }

  function serializeStarsYaml(stars, disabled, faceIds) {
    const norm = normalizeStars(stars);
    const off = normalizeDisabled(disabled);
    const pool = faceIds && faceIds.length ? faceIds : Object.keys(norm);
    const ids = pool.filter((id) => (norm[id] || 0) > 0);
    ids.sort((a, b) => (norm[b] - norm[a]) || a.localeCompare(b));
    const lines = [
      "# 备用库星级 · 权威。未列出 = 0。镜像不自动继承。",
      "# 0 无星 · 1 · 2 · 3 最常用",
      "# disabled: 下列页型所有工坊管线不用（试印 / 成册库存 / 升格）。星级仍保留。",
      "# 在 gallery.html 点星或禁用后用「写入本库」覆盖本文件。",
      ""
    ];
    for (const id of ids) lines.push(`${id}: ${norm[id]}`);
    lines.push("");
    if (off.length) {
      lines.push("disabled:");
      for (const id of off) lines.push(`  - ${id}`);
    } else {
      lines.push("disabled: []");
    }
    return `${lines.join("\n")}\n`;
  }

  function looksLikeStarsYaml(text) {
    return /(?:^|\n)\s*(?:#|[a-z0-9-]+:\s*[0-3]\s*$|disabled:\s*)/m.test(String(text));
  }

  function cloneStars(map) {
    return normalizeStars(map);
  }

  function cloneDisabled(list) {
    return normalizeDisabled(list);
  }

  function starsSubset(small, big) {
    const a = normalizeStars(small);
    const b = normalizeStars(big);
    return Object.keys(a).every((id) => a[id] === b[id]);
  }

  function disabledSubset(small, big) {
    const b = new Set(normalizeDisabled(big));
    return normalizeDisabled(small).every((id) => b.has(id));
  }

  function sameDisabled(a, b) {
    return normalizeDisabled(a).join("\n") === normalizeDisabled(b).join("\n");
  }

  function isDisabled(id, disabled) {
    return normalizeDisabled(disabled).indexOf(id) >= 0;
  }

  function starOf(id, stars) {
    const n = Number((stars || {})[id] || 0);
    return n >= 1 && n <= 3 ? n : 0;
  }

  function starText(n) {
    return n ? "★".repeat(n) : "无星";
  }

  global.ReserveStars = {
    SEED,
    parse: parseStarsYaml,
    serialize: serializeStarsYaml,
    normalizeStars,
    normalizeDisabled,
    looksLike: looksLikeStarsYaml,
    cloneStars,
    cloneDisabled,
    starsSubset,
    disabledSubset,
    sameDisabled,
    isDisabled,
    starOf,
    starText
  };
})(window);
