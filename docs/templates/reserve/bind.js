// 设计工坊成册样例柜 · gallery.html「成册」tab。引擎不读。
(function () {
  const FACES = window.RESERVE_FACES || [];
  const ROLES = window.RESERVE_ROLES || {};
  const GOLD_ID = "folio-16-standard";
  const STORE_V1 = "reserve-series-draft-v1";
  const STORE_V2 = "reserve-series-drafts-v2";
  const PROGRAMS = ["opener", "hero", "mosaic", "grid", "breath", "peak", "closer"];
  const ID_RE = /^[a-z][a-z0-9-]{1,47}$/;
  const PAGE_CHIPS = [8, 16, 20, 24, 28, 32];

  const faceById = new Map(FACES.map((f) => [f.id, f]));
  let getStars = function () { return 0; };
  let onSeriesChange = function () {};
  let series = makeSeries({ id: GOLD_ID, pageCount: 16 });
  let fileSeries = makeSeries({ id: GOLD_ID, pageCount: 16 });
  let repoSeries = makeSeries({ id: GOLD_ID, pageCount: 16 });
  let onDisk = false;
  let books = [];
  let viaHttp = false;
  let store = { currentId: GOLD_ID, drafts: {} };
  let selected = -1;
  let invStar = -1;
  let rejectAt = -1;
  let rejectTimer = 0;
  let drag = null;
  let renderQueued = false;
  let modalBusy = false;
  const els = {};

  function meta(id) {
    return ROLES[id] || { role: "unknown", program: "mosaic", familyId: id };
  }

  function slotCount(face) {
    if (!face) return 0;
    if (face.slots) return face.slots.length;
    if (face.slot) return 1;
    return 0;
  }

  function photoSpanFor(pageCount) {
    const n = Math.max(1, Number(pageCount) || 1);
    return [n * 3, n * 5];
  }

  function makeSeries(src) {
    const pageCount = Math.max(1, Number(src && src.pageCount) || 16);
    const span = src && Array.isArray(src.photoSpan) && src.photoSpan.length === 2
      ? [Number(src.photoSpan[0]), Number(src.photoSpan[1])]
      : photoSpanFor(pageCount);
    return {
      id: (src && src.id) || GOLD_ID,
      kind: "series",
      status: (src && src.status) || "sketch",
      stage: (src && src.stage) || "16:9",
      pageCount,
      density: (src && src.density) || "standard",
      photoSpan: span,
      coverHint: (src && src.coverHint) || "veil-footer",
      backHint: (src && src.backHint) || "closing-default",
      sequence: ((src && src.sequence) || []).map((row) => ({
        i: Number(row.i),
        role: String(row.role || ""),
        program: String(row.program || "mosaic"),
        faceHint: String(row.faceHint || ""),
        flex: !!row.flex
      }))
    };
  }

  function cloneSeries(src) {
    return makeSeries(src);
  }

  function pct(box) {
    return `left:${box.left}%;top:${box.top}%;width:${box.width}%;height:${box.height}%`;
  }

  function slotOrient(box) {
    if (box.orient === "landscape" || box.orient === "portrait" || box.orient === "square") {
      return box.orient === "landscape" ? "l" : box.orient === "portrait" ? "p" : "s";
    }
    const ratio = (box.width / box.height) * (16 / 9);
    if (ratio > 1.08) return "l";
    if (ratio < 0.92) return "p";
    return "s";
  }

  function glyphHtml(face, showCopy) {
    if (!face) return "";
    const copyBoxes = face.copies || (face.copy ? [face.copy] : []);
    const slotBoxes = face.slots || (face.slot ? [face.slot] : []);
    const copyClass = showCopy ? "region copy" : "region copy is-empty";
    const copyHtml = copyBoxes.map((box) => `<div class="${copyClass}" style="${pct(box)}"></div>`).join("");
    const slotHtml = slotBoxes.map((box) => `<div class="region slot ${slotOrient(box)}" style="${pct(box)}"></div>`).join("");
    return `${copyHtml}${slotHtml}<span class="badge">${face.badge || "?"}</span>`;
  }

  function orientsOf(face) {
    const boxes = face && (face.slots || (face.slot ? [face.slot] : [])) || [];
    return boxes.map(slotOrient);
  }

  function admitText(face) {
    const set = new Set(orientsOf(face));
    const forbid = [];
    if (!set.has("p")) forbid.push("竖禁入");
    if (!set.has("l")) forbid.push("横禁入");
    if (!set.has("s") && set.size && !set.has("p") && !set.has("l")) forbid.push("方禁入");
    if (!forbid.length) return "按槽禁入";
    return forbid.join(" · ");
  }

  function starText(n) {
    return n ? "★".repeat(n) : "无星";
  }

  function reindex() {
    series.sequence.forEach((row, idx) => { row.i = idx + 1; });
  }

  function serializeSeries(src) {
    const s = cloneSeries(src);
    const lines = [
      `# 备用库成册样例 · ${s.id}。引擎不读。`,
      "# 在 gallery.html「成册」tab 编排后用「写入系列」覆盖本文件。",
      "# 书衣沿用现网默认；本波不编封面封底砖。",
      "",
      `id: ${s.id}`,
      "kind: series",
      `status: ${s.status}`,
      `stage: "${s.stage}"`,
      `pageCount: ${s.pageCount}`,
      `density: ${s.density}`,
      `photo_span: [${s.photoSpan[0]}, ${s.photoSpan[1]}]`,
      `coverHint: ${s.coverHint}`,
      `backHint: ${s.backHint}`
    ];
    if (!s.sequence.length) {
      lines.push("sequence: []");
    } else {
      lines.push("sequence:");
      for (const row of s.sequence) {
        const flex = row.flex ? ", flex: true" : "";
        lines.push(`  - { i: ${row.i}, role: ${row.role}, program: ${row.program}, faceHint: ${row.faceHint}${flex} }`);
      }
    }
    return `${lines.join("\n")}\n`;
  }

  function parseSeries(text) {
    const raw = String(text || "");
    const grab = (key) => {
      const m = new RegExp(`^${key}:\\s*(.+)$`, "m").exec(raw);
      return m ? m[1].trim().replace(/^["']|["']$/g, "") : "";
    };
    const pageCount = Number(grab("pageCount")) || 16;
    const span = /photo_span:\s*\[\s*(\d+)\s*,\s*(\d+)\s*\]/.exec(raw);
    const out = makeSeries({
      id: grab("id") || GOLD_ID,
      status: grab("status"),
      stage: grab("stage"),
      pageCount,
      density: grab("density"),
      photoSpan: span ? [Number(span[1]), Number(span[2])] : photoSpanFor(pageCount),
      coverHint: grab("coverHint"),
      backHint: grab("backHint"),
      sequence: []
    });
    const rowRe = /-\s*\{\s*i:\s*(\d+)\s*,\s*role:\s*([a-z0-9-]+)\s*,\s*program:\s*([a-z0-9-]+)\s*,\s*faceHint:\s*([a-z0-9-]+)(?:\s*,\s*flex:\s*(true|false))?\s*\}/g;
    let m;
    while ((m = rowRe.exec(raw))) {
      out.sequence.push({
        i: Number(m[1]),
        role: m[2],
        program: m[3],
        faceHint: m[4],
        flex: m[5] === "true"
      });
    }
    out.sequence.sort((a, b) => a.i - b.i);
    out.sequence.forEach((row, idx) => { row.i = idx + 1; });
    return out;
  }

  function looksLikeSeries(text, expectedId) {
    const raw = String(text || "");
    if (!/(?:^|\n)kind:\s*series\b/.test(raw)) return false;
    const id = /(?:^|\n)id:\s*([a-z][a-z0-9-]*)/.exec(raw);
    if (!id) return false;
    if (expectedId && id[1] !== expectedId) return false;
    return true;
  }

  function isDirty() {
    if (!onDisk) return true;
    return serializeSeries(series) !== serializeSeries(fileSeries);
  }

  function persistStore() {
    try {
      localStorage.setItem(STORE_V2, JSON.stringify(store));
    } catch (_) { /* ignore */ }
  }

  function persistDraft() {
    store.currentId = series.id;
    store.drafts[series.id] = {
      series: cloneSeries(series),
      file: onDisk
        ? cloneSeries(fileSeries)
        : makeSeries({ id: series.id, pageCount: series.pageCount, photoSpan: photoSpanFor(series.pageCount) })
    };
    persistStore();
  }

  function loadStore() {
    store = { currentId: GOLD_ID, drafts: {} };
    try {
      const v2 = JSON.parse(localStorage.getItem(STORE_V2) || "null");
      if (v2 && v2.drafts && typeof v2.drafts === "object") {
        store.currentId = v2.currentId || GOLD_ID;
        store.drafts = v2.drafts;
        return;
      }
    } catch (_) { /* ignore */ }
    try {
      const v1 = JSON.parse(localStorage.getItem(STORE_V1) || "null");
      if (v1 && v1.series && (v1.series.id || GOLD_ID) === GOLD_ID) {
        store.drafts[GOLD_ID] = { series: v1.series, file: v1.file || null };
      }
      localStorage.removeItem(STORE_V1);
    } catch (_) { /* ignore */ }
  }

  function slotSum() {
    return series.sequence.reduce((n, row) => n + slotCount(faceById.get(row.faceHint)), 0);
  }

  function densClass(n) {
    if (n <= 1) return "";
    if (n <= 3) return "m";
    return "d";
  }

  function canSwap(faceId, row) {
    const face = faceById.get(faceId);
    const cur = faceById.get(row.faceHint);
    if (!face || !cur) return false;
    const a = meta(faceId);
    const b = meta(row.faceHint);
    return a.familyId === b.familyId && slotCount(face) === slotCount(cur);
  }

  function flashReject(index) {
    rejectAt = index;
    clearTimeout(rejectTimer);
    rejectTimer = setTimeout(() => {
      rejectAt = -1;
      render();
    }, 420);
    render();
  }

  function insertFace(faceId, at) {
    const face = faceById.get(faceId);
    if (!face) return;
    const info = meta(faceId);
    const row = {
      i: 0,
      role: info.role,
      program: info.program,
      faceHint: faceId,
      flex: false
    };
    const idx = Math.max(0, Math.min(at, series.sequence.length));
    series.sequence.splice(idx, 0, row);
    reindex();
    selected = idx;
    persistDraft();
    scheduleRender();
  }

  function swapFace(faceId, index) {
    const row = series.sequence[index];
    if (!row) return false;
    if (!canSwap(faceId, row)) {
      flashReject(index);
      return false;
    }
    row.faceHint = faceId;
    persistDraft();
    scheduleRender();
    return true;
  }

  function movePage(from, to) {
    if (from === to || from < 0 || to < 0) return;
    const row = series.sequence.splice(from, 1)[0];
    const dest = to > from ? to - 1 : to;
    series.sequence.splice(Math.max(0, Math.min(dest, series.sequence.length)), 0, row);
    reindex();
    selected = series.sequence.indexOf(row);
    persistDraft();
    scheduleRender();
  }

  function removePage(index) {
    if (index < 0 || index >= series.sequence.length) return;
    series.sequence.splice(index, 1);
    reindex();
    if (selected >= series.sequence.length) selected = series.sequence.length - 1;
    persistDraft();
    render();
  }

  function setProgram(index, program) {
    const row = series.sequence[index];
    if (!row || PROGRAMS.indexOf(program) < 0) return;
    row.program = program;
    persistDraft();
    render();
  }

  function toggleFlex(index) {
    const row = series.sequence[index];
    if (!row) return;
    row.flex = !row.flex;
    persistDraft();
    render();
  }

  function setPageCount(next) {
    const n = Math.max(1, Math.floor(Number(next) || 0));
    if (!n || n === series.pageCount) return;
    series.pageCount = n;
    series.photoSpan = photoSpanFor(n);
    persistDraft();
    render();
  }

  function alignPageCount() {
    const n = series.sequence.length;
    if (n) setPageCount(n);
  }

  function caliberHtml() {
    const n = series.sequence.length;
    const target = series.pageCount;
    const align = n && n !== target
      ? `<button type="button" class="btn" data-align-pages>目标改为现有 ${n} 页</button>`
      : "";
    return `
      <h3>口径</h3>
      <label class="flex-toggle">目标页数
        <input type="number" min="1" step="1" data-page-count value="${target}">
      </label>
      ${align}
      <p class="hint">只改开口径和照片带（页数×3–5），id 与轨上的页都不动。改完请写入系列。</p>`;
  }

  function lights() {
    const out = [];
    const rows = series.sequence;
    const target = series.pageCount;
    for (let i = 0; i < rows.length - 1; i++) {
      const a = slotCount(faceById.get(rows[i].faceHint));
      const b = slotCount(faceById.get(rows[i + 1].faceHint));
      if (a >= 5 && b >= 5) out.push(`${i + 1}/${i + 2} 相邻密页（${a}+${b} 槽）`);
      if (rows[i].program === "opener" && rows[i + 1].program === "opener") {
        out.push(`${i + 1}/${i + 2} opener 连 opener`);
      }
    }
    rows.forEach((row) => {
      if (row.program === "closer" && row.i <= target - 2) {
        out.push(`${row.i}/${target} closer 在中段`);
      }
    });
    return out;
  }

  function familyStats() {
    const byProgram = {};
    const byFamily = {};
    let flex = 0;
    for (const row of series.sequence) {
      byProgram[row.program] = (byProgram[row.program] || 0) + 1;
      const fam = meta(row.faceHint).familyId;
      byFamily[fam] = (byFamily[fam] || 0) + 1;
      if (row.flex) flex += 1;
    }
    return { byProgram, byFamily, flex };
  }

  function invFaces() {
    return FACES.filter((f) => invStar < 0 || getStars(f.id) === invStar);
  }

  function groupedInv() {
    const buckets = new Map();
    for (const face of invFaces()) {
      const n = slotCount(face);
      const key = n >= 6 ? 6 : n;
      if (!buckets.has(key)) buckets.set(key, []);
      buckets.get(key).push(face);
    }
    const keys = [...buckets.keys()].sort((a, b) => a - b);
    return keys.map((n) => ({
      n,
      label: n >= 6 ? "6+" : String(n),
      faces: buckets.get(n).sort((a, b) => getStars(b.id) - getStars(a.id) || a.id.localeCompare(b.id))
    }));
  }

  function selectedFamily() {
    const row = series.sequence[selected];
    return row ? meta(row.faceHint).familyId : "";
  }

  function occupiedIds() {
    const ids = new Set(books.map((b) => b.id));
    Object.keys(store.drafts).forEach((id) => ids.add(id));
    ids.add(GOLD_ID);
    return ids;
  }

  function suggestId(pageCount) {
    const base = `folio-${pageCount}-standard`;
    const taken = occupiedIds();
    if (!taken.has(base)) return base;
    let i = 2;
    while (taken.has(`${base}-r${i}`)) i += 1;
    return `${base}-r${i}`;
  }

  function cabinetOptions() {
    const seen = new Set();
    const rows = [];
    for (const book of books) {
      if (seen.has(book.id)) continue;
      seen.add(book.id);
      rows.push({ id: book.id, pageCount: book.pageCount, saved: true });
    }
    for (const id of Object.keys(store.drafts)) {
      if (seen.has(id)) continue;
      seen.add(id);
      const draft = store.drafts[id] && store.drafts[id].series;
      rows.push({ id, pageCount: draft && draft.pageCount ? draft.pageCount : 1, saved: false });
    }
    if (!seen.has(series.id)) {
      rows.push({ id: series.id, pageCount: series.pageCount, saved: onDisk });
    }
    rows.sort((a, b) => {
      if (a.id === GOLD_ID) return -1;
      if (b.id === GOLD_ID) return 1;
      return a.id.localeCompare(b.id);
    });
    return rows;
  }

  function rememberBook(book) {
    const hit = books.findIndex((b) => b.id === book.id);
    const row = {
      id: book.id,
      pageCount: book.pageCount,
      density: book.density || "standard",
      status: book.status || "sketch",
      pages: (book.sequence || []).length,
      slots: (book.sequence || []).reduce((n, row) => n + slotCount(faceById.get(row.faceHint)), 0),
      photoSpan: book.photoSpan ? book.photoSpan.slice() : photoSpanFor(book.pageCount)
    };
    if (hit >= 0) books[hit] = row;
    else books.push(row);
  }

  function seedSeries() {
    const seed = window.RESERVE_SERIES_SEED;
    if (seed && seed.id === GOLD_ID) return cloneSeries(seed);
    return makeSeries({ id: GOLD_ID, pageCount: 16, photoSpan: [48, 80] });
  }

  function renderBar() {
    const n = series.sequence.length;
    const target = series.pageCount;
    const sum = slotSum();
    const [lo, hi] = series.photoSpan;
    let spanChip = `当前 ${sum} 槽 · 带 ${lo}–${hi}`;
    let spanClass = "chip";
    if (sum && sum < lo) {
      spanChip += ` · 差 ${lo - sum}`;
      spanClass += " amber";
    } else if (sum > hi) {
      spanChip += ` · 超 ${sum - hi}`;
      spanClass += " amber";
    } else if (sum) {
      spanClass += " ok";
    }
    const pageChip = `目标 ${target} / 现 ${n}`;
    const pageClass = n === target || n === 0 ? "chip" : "chip amber";
    const alignBtn = n && n !== target
      ? `<button type="button" class="btn" data-align-pages>目标改为 ${n}</button>`
      : "";
    const opts = cabinetOptions().map((row) => {
      const mark = row.saved ? "" : " · 未保存";
      return `<option value="${escapeHtml(row.id)}"${row.id === series.id ? " selected" : ""}>${escapeHtml(row.id)}${mark}</option>`;
    }).join("");
    const httpHint = viaHttp ? "" : `<span class="chip amber">file:// 只保证金样 · 请用设计工坊打开方式（serve.cmd）</span>`;
    els.bar.innerHTML = `
      <span class="brand">设计工坊 · 成册</span>
      <label class="book-pick">本
        <select data-book>${opts}</select>
      </label>
      <span class="${pageClass}">${pageChip}</span>
      ${alignBtn}
      <span class="chip">正 · PPC 3–5</span>
      <span class="${spanClass}">${spanChip}</span>
      <span class="chip ${isDirty() ? "amber" : "mute"}">${isDirty() ? "未保存" : "已与文件一致"}</span>
      <span class="chip mute">不写 trip.json</span>
      ${httpHint}
      <span class="bind-bar-spacer"></span>
      <button type="button" class="btn js-new-series">新建</button>
      <button type="button" class="btn js-copy-as">复制为本</button>
      <a class="btn" href="./preview.html#series=${encodeURIComponent(series.id)}">按本序试印</a>
      <button type="button" class="btn js-copy-series">复制 YAML</button>
      <button type="button" class="btn pri js-save-series">写入系列</button>
      <button type="button" class="btn warn js-promote-series">导出升格系列</button>`;
  }

  function renderBanner() {
    const dirty = isDirty();
    const fileNote = viaHttp ? "" : " file:// 新本请改用本夹 serve.cmd。";
    els.banner.classList.toggle("is-on", dirty || !viaHttp);
    if (dirty) {
      els.banner.innerHTML = `<span>浏览器草稿还没写进本夹 <code>series/${escapeHtml(series.id)}.yaml</code>。写入时请覆盖这个文件，不要只下到「下载」。${fileNote}</span>
         <button type="button" class="js-save-series">写入系列</button>
         <button type="button" class="js-copy-series">复制 YAML</button>`;
      return;
    }
    els.banner.innerHTML = viaHttp
      ? ""
      : `<span>当前是 file://，目录列不出新本。日常请用设计工坊打开方式：双击本夹 <code>serve.cmd</code>。</span>`;
  }

  function renderInv() {
    const kin = selectedFamily();
    const groups = groupedInv();
    const starCounts = [0, 1, 2, 3].map((n) => [n, FACES.filter((f) => getStars(f.id) === n).length]);
    const starChips = [
      { n: -1, label: "全部" },
      ...starCounts.filter(([, c]) => c).map(([n, c]) => ({ n, label: `${starText(n)} ${c}` }))
    ];
    const chips = starChips.map((chip) =>
      `<button type="button" data-inv-star="${chip.n}" aria-pressed="${invStar === chip.n}">${chip.label}</button>`
    ).join("");
    const body = groups.map((g) => {
      const caution = g.n >= 5 ? " · 慎用" : "";
      const cards = g.faces.map((face) => {
        const info = meta(face.id);
        const stars = getStars(face.id);
        const isKin = kin && info.familyId === kin;
        return `<div class="inv-card${isKin ? " is-kin" : ""}${g.n >= 5 ? " is-care" : ""}" draggable="true" data-face="${face.id}" title="${face.id}">
          <div class="stage mini">${glyphHtml(face, false)}</div>
          <div class="inv-meta">
            <code>${face.badge}</code>
            <span class="inv-star">${starText(stars)}</span>
          </div>
          <div class="inv-name">${face.displayName}</div>
        </div>`;
      }).join("");
      return `<div class="inv-group"><h3>${g.label} 槽${caution}<small>${g.faces.length}</small></h3><div class="inv-grid">${cards}</div></div>`;
    }).join("");
    els.inv.innerHTML = `
      <h3>页型 · 全部可选 · 主拖</h3>
      <p class="hint">拖到金色「再加一页」或砖缝 = 插入下一页。拖到已有砖且同族才换脸。</p>
      <div class="inv-filters">${chips}</div>
      ${body || "<p class=\"hint\">没有可显示的脸。</p>"}`;
  }

  function renderRail() {
    const rows = series.sequence;
    const target = series.pageCount;
    const dens = Array.from({ length: target }, (_, i) => {
      const row = rows[i];
      const n = row ? slotCount(faceById.get(row.faceHint)) : 0;
      return `<i class="${densClass(n)}" title="${row ? `${i + 1}/${target} · ${n} 槽` : `${i + 1}/${target} 空`}"></i>`;
    }).join("");
    if (!rows.length) {
      els.rail.innerHTML = `
        <p class="mid-label">全书密度（中间 1→${target}）</p>
        <div class="dens" style="grid-template-columns:repeat(${target},1fr)">${dens}</div>
        <h3>中间轨 · 目标 ${target} 页 · 砖角 + 为插入 · 不对页 · 不编书衣</h3>
        <div class="rail-empty" data-gap="0">
          中间轨是空的。从左侧拖页型到这里铺阅读序。<br>
          不预填空页。书衣沿用现网默认，不出现在这轨上。
        </div>`;
      return;
    }
    const tiles = rows.map((row, idx) => {
      const face = faceById.get(row.faceHint);
      const sel = idx === selected ? " sel" : "";
      const reject = idx === rejectAt ? " is-reject" : "";
      const flex = row.flex ? " flex" : "";
      return `
        <div class="gap" data-gap="${idx}" title="插入到 ${idx + 1} 之前"></div>
        <article class="tile${sel}${reject}${flex}" data-index="${idx}" draggable="true">
          <div class="pg"><span>${row.i}/${target}</span><span>${row.program}</span></div>
          <div class="stage mini">${glyphHtml(face, false)}</div>
          <div class="name">${row.role}${row.flex ? " <em>弹性位</em>" : ""}${face ? "" : " <em>缺脸</em>"}</div>
          <button type="button" class="plus" data-gap="${idx + 1}" title="在后面插入">+</button>
        </article>`;
    }).join("");
    els.rail.innerHTML = `
      <p class="mid-label">全书密度（中间 1→${target}）</p>
      <div class="dens" style="grid-template-columns:repeat(${target},1fr)">${dens}</div>
      <h3>中间轨 · 目标 ${target} 页 · 现 ${rows.length} 页 · 砖角 + 为插入 · 不对页 · 不编书衣</h3>
      <div class="rail">${tiles}<div class="gap" data-gap="${rows.length}" title="插到末尾"></div>
        <div class="rail-add" data-gap="${rows.length}">再加一页<br><small>拖到这里插入第 ${rows.length + 1} 页</small></div>
      </div>`;
  }

  function renderInsp() {
    const row = series.sequence[selected];
    const alerts = lights();
    const stats = familyStats();
    const sum = slotSum();
    const [lo, hi] = series.photoSpan;
    const target = series.pageCount;
    let spanNote = `槽合计 ${sum}，正带 ${lo}–${hi}。`;
    if (sum && sum < lo) spanNote += ` 差 ${lo - sum}。不要为了凑数去锁密网。`;
    else if (sum > hi) spanNote += ` 超 ${sum - hi}。`;
    const progLine = PROGRAMS.filter((p) => stats.byProgram[p]).map((p) => `${p} ${stats.byProgram[p]}`).join(" · ") || "还没有页";
    const famLine = Object.entries(stats.byFamily).sort((a, b) => b[1] - a[1]).slice(0, 8)
      .map(([k, n]) => `${k} ${n}`).join(" · ") || "—";

    if (!row) {
      els.insp.innerHTML = `
        <h3>本页</h3>
        <p class="stat">还没选砖。空轨不发明页序。</p>
        <h3>全书 · 按纲领 / 家族</h3>
        <p class="stat">${progLine}<br>${famLine}<br>弹性位 ${stats.flex}</p>
        ${caliberHtml()}
        <div class="amber-box">${spanNote}<br>书衣 ${series.coverHint} / ${series.backHint} · 本波不编。</div>
        ${alerts.length ? `<div class="red-box">${alerts.map((t) => escapeHtml(t)).join("<br>")}</div>` : ""}`;
      return;
    }
    const face = faceById.get(row.faceHint);
    const info = meta(row.faceHint);
    const prev = series.sequence[selected - 1];
    const next = series.sequence[selected + 1];
    const progBtns = PROGRAMS.map((p) =>
      `<button type="button" data-program="${p}" aria-pressed="${row.program === p}">${p}</button>`
    ).join("");
    const pair = (item, label) => {
      if (!item) return `<div class="tile ghost"><div class="pg">${label}</div><div class="name">无</div></div>`;
      const f = faceById.get(item.faceHint);
      return `<div class="tile"><div class="pg">${item.i}/${target}</div><div class="stage mini">${glyphHtml(f, false)}</div><div class="name">${item.role}</div></div>`;
    };
    els.insp.innerHTML = `
      <h3>本页 · ${row.i}/${target}</h3>
      <p class="stat">
        角色 <b>${escapeHtml(row.role)}</b><br>
        纲领 ${escapeHtml(row.program)} · 家族 <b>${escapeHtml(info.familyId)}</b><br>
        脸 <b>${escapeHtml(row.faceHint)}</b><br>
        槽 ${face ? face.badge : "?"} · ${face ? admitText(face) : "缺脸"}
      </p>
      <div class="prog-pick">${progBtns}</div>
      <label class="flex-toggle"><input type="checkbox" data-flex ${row.flex ? "checked" : ""}> 弹性位 · 匹配器以后只许改这些页</label>
      <button type="button" class="btn danger" data-remove>移出本轨</button>
      <h3>翻开相邻页 · 胶装打开</h3>
      <div class="pair-strip">${pair(prev, "左")} ${pair(next, "右")}</div>
      <p class="hint">同时可见。不是跨页单位，只是软检查。</p>
      <h3>全书 · 按纲领 / 家族</h3>
      <p class="stat">${progLine}<br>${famLine}<br>弹性位 ${stats.flex}</p>
      ${caliberHtml()}
      <div class="amber-box">${spanNote}<br>书衣 ${series.coverHint} / ${series.backHint} · 本波不编。</div>
      ${alerts.length ? `<div class="red-box">${alerts.map((t) => escapeHtml(t)).join("<br>")}</div>` : ""}`;
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, (ch) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    }[ch]));
  }

  function scheduleRender() {
    if (drag) {
      renderQueued = true;
      return;
    }
    render();
  }

  function render() {
    if (!els.bar) return;
    renderQueued = false;
    renderBar();
    renderBanner();
    renderInv();
    renderRail();
    renderInsp();
    onSeriesChange();
  }

  function hideModal() {
    if (!els.modal) return;
    els.modal.hidden = true;
    els.modal.innerHTML = "";
    modalBusy = false;
  }

  function showModal(html, wide) {
    if (!els.modal) return;
    els.modal.innerHTML = `<div class="sheet${wide ? " wide" : ""}">${html}</div>`;
    els.modal.hidden = false;
  }

  function confirmIfDirty() {
    if (!isDirty()) return Promise.resolve(true);
    if (modalBusy) return Promise.resolve(false);
    modalBusy = true;
    return new Promise((resolve) => {
      showModal(`
        <h2>当前本还没写入</h2>
        <p>浏览器草稿还没写进 <code>series/${escapeHtml(series.id)}.yaml</code>。切换前请先留下或丢掉。</p>
        <div class="actions">
          <button type="button" class="btn" data-act="cancel">取消</button>
          <button type="button" class="btn" data-act="discard">丢掉草稿</button>
          <button type="button" class="btn pri" data-act="save">写入系列</button>
        </div>`);
      const finish = (ok) => {
        hideModal();
        resolve(ok);
      };
      els.modal.querySelector("[data-act=cancel]").onclick = () => finish(false);
      els.modal.querySelector("[data-act=discard]").onclick = async () => {
        const unsaved = !onDisk && series.id !== GOLD_ID;
        delete store.drafts[series.id];
        if (onDisk) series = cloneSeries(repoSeries);
        persistStore();
        if (unsaved) await openBook(GOLD_ID);
        finish(true);
      };
      els.modal.querySelector("[data-act=save]").onclick = async () => {
        await saveSeries();
        if (isDirty()) {
          modalBusy = true;
          return;
        }
        finish(true);
      };
    });
  }

  function idError(id, { allowGold } = {}) {
    if (!ID_RE.test(id)) return "id 须为小写字母开头、字母数字和连字符，最长 48。";
    if (!allowGold && id === GOLD_ID) return "不能占用金样 folio-16-standard。请另起 id。";
    if (id !== series.id && occupiedIds().has(id) && books.some((b) => b.id === id)) {
      return `柜里已有 ${id}。`;
    }
    if (id !== series.id && store.drafts[id] && !books.some((b) => b.id === id)) {
      return `已有未保存的 ${id}。请先打开那本，或换一个 id。`;
    }
    return "";
  }

  function openNewDialog({ copyFrom } = {}) {
    if (modalBusy) return;
    modalBusy = true;
    const pageCount = copyFrom ? series.pageCount : 16;
    const savedBooks = books.slice().sort((a, b) => a.id.localeCompare(b.id));
    let srcOpts = savedBooks.map((b) =>
      `<option value="${escapeHtml(b.id)}"${(copyFrom || GOLD_ID) === b.id ? " selected" : ""}>${escapeHtml(b.id)}</option>`
    ).join("");
    if (copyFrom && !savedBooks.some((b) => b.id === copyFrom)) {
      srcOpts = `<option value="${escapeHtml(copyFrom)}" selected>${escapeHtml(copyFrom)} · 当前未保存</option>${srcOpts}`;
    }
    const chips = PAGE_CHIPS.map((n) => `<button type="button" class="btn" data-chip="${n}">${n}</button>`).join("");
    showModal(`
      <h2>${copyFrom ? "复制为本" : "新建样例"}</h2>
      <label>目标页数</label>
      <div class="bind-chips">${chips}</div>
      <input type="number" min="1" step="1" data-pages value="${pageCount}" />
      <label>id</label>
      <input type="text" data-id spellcheck="false" value="${escapeHtml(suggestId(pageCount))}" />
      <label>起点</label>
      <select data-start>
        <option value="empty"${copyFrom ? "" : " selected"}>空轨</option>
        <option value="copy"${copyFrom ? " selected" : ""} ${savedBooks.length || copyFrom ? "" : "disabled"}>从已有本复制</option>
      </select>
      <label>复制源</label>
      <select data-from ${savedBooks.length || copyFrom ? "" : "disabled"}>${srcOpts || "<option value=\"\">柜里还没有已写入的本</option>"}</select>
      <p class="err" data-err hidden></p>
      <div class="actions">
        <button type="button" class="btn" data-act="cancel">取消</button>
        <button type="button" class="btn pri" data-act="ok">开始编排</button>
      </div>`);
    const pagesEl = els.modal.querySelector("[data-pages]");
    const idEl = els.modal.querySelector("[data-id]");
    const startEl = els.modal.querySelector("[data-start]");
    const fromEl = els.modal.querySelector("[data-from]");
    const errEl = els.modal.querySelector("[data-err]");
    if (copyFrom && fromEl) fromEl.value = copyFrom;
    const syncId = () => {
      const n = Math.max(1, Number(pagesEl.value) || 1);
      idEl.value = suggestId(n);
    };
    els.modal.querySelectorAll("[data-chip]").forEach((btn) => {
      btn.onclick = () => {
        pagesEl.value = btn.dataset.chip;
        syncId();
      };
    });
    pagesEl.addEventListener("change", syncId);
    els.modal.querySelector("[data-act=cancel]").onclick = () => hideModal();
    els.modal.querySelector("[data-act=ok]").onclick = async () => {
      const n = Math.max(1, Math.floor(Number(pagesEl.value) || 0));
      const id = String(idEl.value || "").trim();
      const err = !n ? "页数须 ≥ 1。" : idError(id);
      if (err) {
        errEl.hidden = false;
        errEl.textContent = err;
        return;
      }
      const start = startEl.value;
      const fromId = start === "copy" ? ((fromEl && fromEl.value) || copyFrom || "") : "";
      hideModal();
      await createBook(id, n, fromId);
    };
  }

  async function createBook(id, pageCount, fromId) {
    let sequence = [];
    if (fromId) {
      if (fromId === series.id) {
        sequence = cloneSeries(series).sequence;
      } else {
        const src = await fetchYaml(fromId);
        sequence = src ? src.sequence : (fromId === GOLD_ID ? seedSeries().sequence : []);
      }
    }
    series = makeSeries({
      id,
      pageCount,
      photoSpan: photoSpanFor(pageCount),
      sequence
    });
    reindex();
    fileSeries = makeSeries({ id, pageCount, photoSpan: photoSpanFor(pageCount) });
    repoSeries = cloneSeries(fileSeries);
    onDisk = false;
    selected = -1;
    persistDraft();
    render();
  }

  async function saveSeries() {
    if (!ID_RE.test(series.id)) return;
    const text = serializeSeries(series);
    const parsed = parseSeries(text);
    if (parsed.id !== series.id) return;
    try {
      if (window.showSaveFilePicker) {
        const handle = await window.showSaveFilePicker({
          suggestedName: `${series.id}.yaml`,
          id: `reserve-series-${series.id}`,
          types: [{ description: "YAML", accept: { "text/yaml": [".yaml"], "text/plain": [".yaml"] } }]
        });
        const writable = await handle.createWritable();
        await writable.write(text);
        await writable.close();
        fileSeries = cloneSeries(series);
        repoSeries = cloneSeries(series);
        onDisk = true;
        persistDraft();
        await loadIndex();
        rememberBook(series);
        render();
        return;
      }
    } catch (err) {
      if (err && err.name === "AbortError") return;
    }
    const blob = new Blob([text], { type: "text/yaml" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `${series.id}.yaml`;
    a.click();
    URL.revokeObjectURL(a.href);
    persistDraft();
    render();
  }

  async function copySeries() {
    const text = serializeSeries(series);
    try {
      await navigator.clipboard.writeText(text);
    } catch (_) {
      const hint = document.createElement("textarea");
      hint.value = text;
      document.body.appendChild(hint);
      hint.select();
      document.execCommand("copy");
      hint.remove();
    }
  }

  async function fetchYaml(id) {
    try {
      const res = await fetch(`./series/${id}.yaml`, { cache: "no-store" });
      if (!res.ok) return null;
      const text = await res.text();
      if (!looksLikeSeries(text, id)) return null;
      return parseSeries(text);
    } catch (_) {
      return null;
    }
  }

  async function loadIndex() {
    try {
      const res = await fetch("./series/index.json", { cache: "no-store" });
      if (res.ok) {
        const data = await res.json();
        if (data && Array.isArray(data.books)) {
          books = data.books;
          viaHttp = true;
          return;
        }
      }
    } catch (_) { /* file:// 或未用本夹 serve */ }
    viaHttp = false;
    if (!books.length) {
      books = [{
        id: GOLD_ID,
        pageCount: 16,
        density: "standard",
        status: "sketch",
        pages: 16,
        slots: 53,
        photoSpan: [48, 80]
      }];
    }
  }

  function applyDraft(id, fallback) {
    const draft = store.drafts[id];
    if (!draft || !draft.series) return fallback;
    const draftSeries = cloneSeries(draft.series);
    if (draftSeries.id !== id) return fallback;
    if (id === GOLD_ID && !draftSeries.sequence.length && fallback.sequence.length) return fallback;
    return draftSeries;
  }

  async function openBook(id) {
    selected = -1;
    const fromFile = await fetchYaml(id);
    if (fromFile) {
      repoSeries = fromFile;
      fileSeries = cloneSeries(fromFile);
      series = applyDraft(id, fromFile);
      onDisk = true;
      rememberBook(fromFile);
    } else if (id === GOLD_ID) {
      repoSeries = seedSeries();
      fileSeries = cloneSeries(repoSeries);
      series = applyDraft(id, repoSeries);
      onDisk = true;
    } else if (store.drafts[id] && store.drafts[id].series) {
      series = cloneSeries(store.drafts[id].series);
      fileSeries = makeSeries({ id, pageCount: series.pageCount, photoSpan: photoSpanFor(series.pageCount) });
      repoSeries = cloneSeries(fileSeries);
      onDisk = false;
    } else {
      return false;
    }
    store.currentId = series.id;
    persistDraft();
    render();
    return true;
  }

  async function switchBook(nextId) {
    if (!nextId || nextId === series.id) return;
    const ok = await confirmIfDirty();
    if (!ok) {
      render();
      return;
    }
    const opened = await openBook(nextId);
    if (!opened) render();
  }

  function checklistRows(report) {
    return report.checklist.map((row) => {
      const cls = !row.ok ? "bad" : row.amber ? "amber" : "ok";
      const mark = !row.ok ? "硬拒" : row.amber ? "琥珀" : "过";
      return `<tr><td>${escapeHtml(row.item)}</td><td class="${cls}">${escapeHtml(mark)}${row.detail ? ` · ${escapeHtml(row.detail)}` : ""}</td></tr>`;
    }).join("");
  }

  async function openPromoteDialog() {
    if (!window.AtelierPromote) return;
    if (modalBusy) return;
    modalBusy = true;
    const P = window.AtelierPromote;
    const roleMap = await P.loadRoleMap();
    const overrides = {};
    const unset = [];
    for (const row of series.sequence) {
      const role = row.role;
      if (!role || P.appendixBHas(role) || roleMap[role]) continue;
      if (unset.indexOf(role) < 0) unset.push(role);
    }
    const bOpts = P.APPENDIX_B.map((r) => `<option value="${r}">映射到 ${r}</option>`).join("");
    const unsetHtml = unset.length
      ? `<label>附录 B 未收、映射表也没有</label>
         ${unset.map((role) => `
           <p>${escapeHtml(role)}</p>
           <select data-role-act="${escapeHtml(role)}">
             <option value="unset">未处理 · 硬拒</option>
             <option value="add">请附录 B 增收</option>
             ${bOpts}
           </select>`).join("")}`
      : "";
    showModal(`
      <h2>导出升格系列</h2>
      <p>另存给现网评审的角色包。写入系列只覆盖工坊自己的本。正式 id 禁止任何 folio-*。点完不是已同步。</p>
      <label>现网将用的正式 id</label>
      <input type="text" data-official spellcheck="false" value="${escapeHtml(P.defaultOfficialId(series.pageCount, series.density))}" />
      <label>三星覆盖理由（未达建议三星时必填）</label>
      <input type="text" data-overlay placeholder="几何已审，常用度覆盖" />
      ${unsetHtml}
      <div data-check></div>
      <p class="ok" data-ok hidden></p>
      <div class="actions">
        <button type="button" class="btn" data-act="cancel">取消</button>
        <button type="button" class="btn warn" data-act="copy" disabled>复制 YAML</button>
      </div>`, true);
    const officialEl = els.modal.querySelector("[data-official]");
    const overlayEl = els.modal.querySelector("[data-overlay]");
    const checkEl = els.modal.querySelector("[data-check]");
    const copyBtn = els.modal.querySelector("[data-act=copy]");
    const okEl = els.modal.querySelector("[data-ok]");
    const collectOverrides = () => {
      els.modal.querySelectorAll("[data-role-act]").forEach((sel) => {
        const role = sel.dataset.roleAct;
        const val = sel.value;
        if (val === "add") overrides[role] = { kind: "add" };
        else if (val && val !== "unset") overrides[role] = { kind: "map", role: val };
        else delete overrides[role];
      });
    };
    const currentReport = () => {
      collectOverrides();
      return P.buildSeriesPromote({
        series,
        officialId: officialEl.value.trim(),
        roleMap,
        overrides,
        overlay: overlayEl.value.trim(),
        getStars,
        neighborLights: lights()
      });
    };
    const paint = () => {
      const report = currentReport();
      const hardHtml = report.hard.length
        ? `<div class="red-box">${report.hard.map((t) => escapeHtml(t)).join("<br>")}</div>`
        : "";
      checkEl.innerHTML = `
        <table class="check-table">
          <thead><tr><th>项</th><th>结果</th></tr></thead>
          <tbody>${checklistRows(report)}</tbody>
        </table>
        ${hardHtml}`;
      copyBtn.disabled = !report.canCopy;
      okEl.hidden = true;
    };
    officialEl.addEventListener("input", paint);
    overlayEl.addEventListener("input", paint);
    els.modal.querySelectorAll("[data-role-act]").forEach((sel) => sel.addEventListener("change", paint));
    els.modal.querySelector("[data-act=cancel]").onclick = hideModal;
    copyBtn.onclick = async () => {
      const latest = currentReport();
      if (!latest.canCopy) {
        paint();
        return;
      }
      await P.copyText(P.bundleCopy(latest));
      const blob = new Blob([latest.yaml], { type: "text/yaml" });
      if (window.showSaveFilePicker) {
        try {
          const handle = await window.showSaveFilePicker({
            suggestedName: latest.filename,
            id: `atelier-promote-${latest.officialId}`,
            types: [{ description: "YAML", accept: { "text/yaml": [".yaml"], "text/plain": [".yaml"] } }]
          });
          if (/^folio-/.test(handle.name.replace(/\.ya?ml$/i, ""))) {
            okEl.hidden = false;
            okEl.className = "bad";
            okEl.textContent = "不能把升格包存成 folio-*。YAML 已复制，请另存 magazine-* 文件名。";
            return;
          }
          const writable = await handle.createWritable();
          await writable.write(latest.yaml);
          await writable.close();
        } catch (err) {
          if (!err || err.name !== "AbortError") P.downloadBlob(blob, latest.filename);
        }
      } else {
        P.downloadBlob(blob, latest.filename);
      }
      okEl.hidden = false;
      okEl.className = "ok";
      okEl.textContent = P.SUCCESS;
    };
    paint();
  }

  function bindEvents() {
    document.addEventListener("click", (ev) => {
      if (ev.target.closest(".js-save-series")) saveSeries();
      if (ev.target.closest(".js-copy-series")) copySeries();
      if (ev.target.closest(".js-promote-series")) openPromoteDialog();
      if (ev.target.closest(".js-new-series")) {
        confirmIfDirty().then((ok) => { if (ok) openNewDialog(); });
      }
      if (ev.target.closest(".js-copy-as")) {
        confirmIfDirty().then((ok) => { if (ok) openNewDialog({ copyFrom: series.id }); });
      }
      if (ev.target.closest("[data-align-pages]")) alignPageCount();
    });
    els.bar.addEventListener("change", (ev) => {
      const sel = ev.target.closest("[data-book]");
      if (!sel) return;
      switchBook(sel.value);
    });
    els.inv.addEventListener("click", (ev) => {
      const star = ev.target.closest("[data-inv-star]");
      if (star) {
        invStar = Number(star.dataset.invStar);
        render();
      }
    });
    els.inv.addEventListener("dragstart", (ev) => {
      const card = ev.target.closest("[data-face]");
      if (!card) return;
      drag = { kind: "face", id: card.dataset.face };
      try {
        ev.dataTransfer.effectAllowed = "copy";
        ev.dataTransfer.setData("text/plain", card.dataset.face);
      } catch (_) { /* some browsers */ }
    });
    els.rail.addEventListener("click", (ev) => {
      const plus = ev.target.closest(".plus[data-gap]");
      if (plus) {
        ev.preventDefault();
        return;
      }
      const tile = ev.target.closest("[data-index]");
      if (!tile) return;
      selected = Number(tile.dataset.index);
      render();
    });
    els.rail.addEventListener("dragstart", (ev) => {
      const tile = ev.target.closest("[data-index]");
      if (!tile || ev.target.closest(".plus")) return;
      drag = { kind: "page", index: Number(tile.dataset.index) };
      ev.dataTransfer.effectAllowed = "move";
      ev.dataTransfer.setData("text/plain", String(tile.dataset.index));
    });
    function clearHot() {
      els.rail.querySelectorAll(".is-hot").forEach((n) => n.classList.remove("is-hot"));
    }
    els.rail.addEventListener("dragover", (ev) => {
      if (!drag) return;
      const zone = ev.target.closest("[data-gap], .rail-empty, .rail-add, .tile");
      if (!zone) {
        ev.preventDefault();
        return;
      }
      ev.preventDefault();
      clearHot();
      const hot = ev.target.closest("[data-gap], .rail-empty, .rail-add");
      if (hot) hot.classList.add("is-hot");
    });
    els.rail.addEventListener("dragleave", (ev) => {
      if (!els.rail.contains(ev.relatedTarget)) clearHot();
    });
    els.rail.addEventListener("drop", (ev) => {
      ev.preventDefault();
      clearHot();
      const gap = ev.target.closest("[data-gap]");
      const tile = ev.target.closest("[data-index]");
      const empty = ev.target.closest(".rail-empty");
      const add = ev.target.closest(".rail-add");
      if (empty && drag && drag.kind === "face") insertFace(drag.id, 0);
      else if (add && drag && drag.kind === "face") insertFace(drag.id, series.sequence.length);
      else if (add && drag && drag.kind === "page") movePage(drag.index, series.sequence.length);
      else if (gap) {
        const at = Number(gap.dataset.gap);
        if (drag && drag.kind === "face") insertFace(drag.id, at);
        else if (drag && drag.kind === "page") movePage(drag.index, at);
      } else if (tile && drag && drag.kind === "face") {
        const idx = Number(tile.dataset.index);
        const row = series.sequence[idx];
        if (row && canSwap(drag.id, row)) swapFace(drag.id, idx);
        else insertFace(drag.id, idx + 1);
      } else if (tile && drag && drag.kind === "page") {
        movePage(drag.index, Number(tile.dataset.index));
      } else if (drag && drag.kind === "face") {
        insertFace(drag.id, series.sequence.length);
      }
      drag = null;
      if (renderQueued) render();
    });
    els.insp.addEventListener("click", (ev) => {
      const prog = ev.target.closest("[data-program]");
      if (prog) setProgram(selected, prog.dataset.program);
      if (ev.target.closest("[data-remove]")) removePage(selected);
    });
    els.insp.addEventListener("change", (ev) => {
      if (ev.target.matches("[data-flex]")) toggleFlex(selected);
      if (ev.target.matches("[data-page-count]")) setPageCount(ev.target.value);
    });
    document.addEventListener("dragend", () => {
      drag = null;
      if (renderQueued) render();
    });
    if (els.modal) {
      els.modal.addEventListener("click", (ev) => {
        if (ev.target === els.modal && !modalBusy) hideModal();
      });
    }
  }

  window.ReserveBind = {
    async init(opts) {
      getStars = opts.getStars || getStars;
      onSeriesChange = opts.onChange || onSeriesChange;
      els.bar = document.getElementById("bind-bar");
      els.banner = document.getElementById("bind-banner");
      els.inv = document.getElementById("bind-inv");
      els.rail = document.getElementById("bind-rail");
      els.insp = document.getElementById("bind-insp");
      els.modal = document.getElementById("bind-modal");
      if (!els.bar) return;
      loadStore();
      bindEvents();
      await loadIndex();
      const wanted = opts.initialId || store.currentId || GOLD_ID;
      const opened = await openBook(wanted);
      if (!opened) await openBook(GOLD_ID);
    },
    render,
    get currentId() {
      return series.id;
    },
    confirmLeave() {
      return confirmIfDirty().then(async (ok) => {
        if (!ok) return false;
        if (!onDisk && !store.drafts[series.id]) await openBook(GOLD_ID);
        return true;
      });
    },
    openFromHash(id) {
      if (!id || id === series.id) return Promise.resolve();
      return switchBook(id);
    }
  };
})();
