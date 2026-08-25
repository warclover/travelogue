// 设计工坊升格 · 检查单与导出。引擎不读。现网不引用。
(function () {
  const APPENDIX_A = [
    "page-1-hero-land",
    "page-2-pair-port",
    "page-3-port",
    "page-4-grid-land",
    "page-3-2l1p-right",
    "page-3-2l1p-left"
  ];
  const APPENDIX_B = [
    "title-opener", "chapter-opener",
    "hero-land", "hero-port",
    "pair-port", "pair-land", "pair-land-hero",
    "row-port-3", "row-land-3",
    "stack-l-port", "port-stack-l", "mix-1p2l",
    "grid-4-land", "grid-4-port", "grid-2p2l", "hero-rail-4", "grid-dense",
    "breath", "journal", "peak", "closer"
  ];
  const PROGRAMS = ["opener", "hero", "mosaic", "grid", "breath", "peak", "closer"];
  const ID_RE = /^[a-z][a-z0-9-]{1,47}$/;
  const SUCCESS = "已复制升格 YAML 与检查单。交给现网评审。现网尚未收下。薄柜未建，升格未闭环。";
  const FORBIDDEN_COPY = /已同步|已收入现网|引擎将使用|引擎会读/;

  let roleMapCache = null;

  function appendixAHas(id) {
    return APPENDIX_A.indexOf(id) >= 0;
  }

  function appendixBHas(role) {
    return APPENDIX_B.indexOf(role) >= 0;
  }

  function stamp() {
    const d = new Date();
    const p = (n) => String(n).padStart(2, "0");
    return `${d.getFullYear()}${p(d.getMonth() + 1)}${p(d.getDate())}`;
  }

  function grab(text, key) {
    const m = new RegExp(`^${key}:\\s*(.+)$`, "m").exec(String(text || ""));
    return m ? m[1].trim().replace(/^["']|["']$/g, "") : "";
  }

  function parseMix(raw) {
    const src = String(raw || "");
    const out = { portrait: 0, landscape: 0, square: 0 };
    const p = /portrait:\s*(\d+)/.exec(src);
    const l = /landscape:\s*(\d+)/.exec(src);
    const s = /square:\s*(\d+)/.exec(src);
    if (p) out.portrait = Number(p[1]);
    if (l) out.landscape = Number(l[1]);
    if (s) out.square = Number(s[1]);
    return out;
  }

  function slotOrient(box) {
    if (!box) return "s";
    if (box.orient === "landscape" || box.orient === "portrait" || box.orient === "square") {
      return box.orient === "landscape" ? "l" : box.orient === "portrait" ? "p" : "s";
    }
    const ratio = (box.width / box.height) * (16 / 9);
    if (ratio > 1.08) return "l";
    if (ratio < 0.92) return "p";
    return "s";
  }

  function slotBoxes(face) {
    if (!face) return [];
    if (face.slots) return face.slots;
    if (face.slot) return [face.slot];
    return [];
  }

  function mixFromFace(face) {
    const out = { portrait: 0, landscape: 0, square: 0 };
    for (const box of slotBoxes(face)) {
      const o = slotOrient(box);
      if (o === "p") out.portrait += 1;
      else if (o === "l") out.landscape += 1;
      else out.square += 1;
    }
    return out;
  }

  function slotCount(face) {
    return slotBoxes(face).length;
  }

  function idSlotCount(id) {
    const m = /^page-(\d+)-/.exec(String(id || ""));
    return m ? Number(m[1]) : 0;
  }

  function defaultOfficialId(pageCount, density) {
    const n = Math.max(1, Number(pageCount) || 1);
    const d = String(density || "standard").replace(/[^a-z0-9-]/g, "") || "standard";
    return `magazine-${n}-${d}`;
  }

  function officialIdError(id) {
    const value = String(id || "").trim();
    if (!ID_RE.test(value)) return "正式 id 须为小写字母开头、字母数字和连字符，最长 48。";
    if (/^folio-/.test(value)) return "正式 id 禁止任何 folio-*。请改用 magazine-{页数}-{密度}。";
    return "";
  }

  function parseRoleMap(text) {
    const out = {};
    for (const raw of String(text || "").split(/\r?\n/)) {
      const m = /\|\s*`([a-z0-9-]+)`\s*\|\s*(.+?)\s*\|/.exec(raw.trim());
      if (!m) continue;
      const role = m[1];
      const cell = m[2];
      if (appendixBHas(role)) continue;
      if (/请附录 B 增收|请增收/.test(cell)) {
        out[role] = { kind: "add" };
        continue;
      }
      const mapped = /映射到\s*`([a-z0-9-]+)`/.exec(cell);
      if (mapped && appendixBHas(mapped[1])) {
        out[role] = { kind: "map", role: mapped[1] };
      }
    }
    return out;
  }

  async function loadRoleMap() {
    if (roleMapCache) return roleMapCache;
    try {
      const res = await fetch("./PROMOTE-ROLE-MAP.md", { cache: "no-store" });
      if (res.ok) roleMapCache = parseRoleMap(await res.text());
    } catch (_) { /* file:// */ }
    if (!roleMapCache) roleMapCache = {};
    return roleMapCache;
  }

  function resolveRole(role, map, overrides) {
    if (!role) return { kind: "missing" };
    if (appendixBHas(role)) return { kind: "official", role };
    if (overrides && overrides[role]) return overrides[role];
    if (map && map[role]) return map[role];
    return { kind: "unset" };
  }

  function buildSeriesPromote(src) {
    const series = src.series || {};
    const officialId = String(src.officialId || "").trim();
    const map = src.roleMap || {};
    const overrides = src.overrides || {};
    const overlay = String(src.overlay || "").trim();
    const getStars = src.getStars || function () { return 0; };
    const getDisabled = src.getDisabled || function () { return false; };
    const neighborLights = src.neighborLights || [];
    const idErr = officialIdError(officialId);
    const hard = [];
    const amber = [];
    const rows = Array.isArray(series.sequence) ? series.sequence : [];

    if (!rows.length) hard.push("轨上没有页，无法交角色序。");
    if (idErr) hard.push(idErr);

    const roleNotes = [];
    const seenRoles = new Set();
    let atelierOnly = 0;
    let requestAdd = 0;
    const exported = [];

    for (const row of rows) {
      const role = String(row.role || "").trim();
      const program = String(row.program || "").trim();
      const faceHint = String(row.faceHint || "").trim();
      if (!role || !program) hard.push(`第 ${row.i || "?"} 行缺 role 或 program。`);
      if (program && PROGRAMS.indexOf(program) < 0) hard.push(`第 ${row.i || "?"} 行 program 不在七词内：${program}`);
      const resolved = resolveRole(role, map, overrides);
      if (resolved.kind === "unset") {
        if (!seenRoles.has(role)) {
          hard.push(`未收角色 ${role} 未映射且未声明增收。`);
          seenRoles.add(role);
        }
      } else if (resolved.kind === "missing") {
        hard.push(`第 ${row.i || "?"} 行没有角色。`);
      } else if (resolved.kind === "add") {
        requestAdd += 1;
        if (!seenRoles.has(role)) {
          roleNotes.push(`${role} · 请附录 B 增收`);
          seenRoles.add(role);
        }
      } else if (resolved.kind === "map") {
        if (!seenRoles.has(role)) {
          roleNotes.push(`${role} → ${resolved.role}`);
          seenRoles.add(role);
        }
      }

      const inA = appendixAHas(faceHint);
      if (faceHint && !inA) atelierOnly += 1;
      const outRole = resolved.kind === "map" || resolved.kind === "official" ? resolved.role : role;
      const extra = [];
      if (faceHint && !inA) extra.push("faceStatus: atelier-only");
      if (resolved.kind === "map") extra.push(`atelierRole: ${role}`);
      if (resolved.kind === "add") extra.push("roleStatus: appendix-b-request");
      if (row.flex) extra.push("flex: true");
      exported.push({
        i: row.i,
        role: outRole || role,
        program,
        faceHint: faceHint || "",
        extra
      });
    }

    const disabledFaces = [];
    const lowStar = [];
    for (const row of rows) {
      if (getDisabled(row.faceHint) && disabledFaces.indexOf(row.faceHint) < 0) {
        disabledFaces.push(row.faceHint);
      }
      const n = Number(getStars(row.faceHint) || 0);
      if (n < 3 && lowStar.indexOf(row.faceHint) < 0) lowStar.push(row.faceHint);
    }
    if (disabledFaces.length) {
      hard.push(`已禁用，所有管线不用：${disabledFaces.join(" · ")}。先在页型 tab 取消禁用。`);
    }
    if (lowStar.length && !overlay) {
      hard.push("建议三星未达，须写覆盖理由。覆盖是常态。");
    } else if (lowStar.length) {
      amber.push(`建议三星未达 ${lowStar.length} 张，已写覆盖理由。`);
    }
    if (atelierOnly) amber.push(`${atelierOnly} 行 faceHint 为 atelier-only（只交角色，现网顶岗）。`);
    if (neighborLights.length) amber.push(`邻页红灯仍在：${neighborLights.join(" · ")}`);
    if (Number(series.pageCount) !== rows.length) {
      amber.push(`pageCount ${series.pageCount} ≠ 轨上 ${rows.length} 页。`);
    }

    const checklist = [
      { item: "每一行有 role + program", ok: !rows.some((r) => !r.role || !r.program), hard: true },
      { item: "正式 id 不是 folio-*", ok: !idErr, detail: officialId || "（空）", hard: true },
      { item: "sourceAtelier", ok: !!series.id, detail: series.id || "（空）", hard: true },
      { item: "附录 A 以外的脸", ok: true, detail: atelierOnly ? `${atelierOnly} 行 atelier-only` : "全部在附录 A", amber: !!atelierOnly },
      { item: "附录 B 未收角色", ok: !hard.some((t) => /未收角色/.test(t)), detail: roleNotes.join(" · ") || "无未收角色", hard: true },
      { item: "邻页红灯", ok: true, detail: neighborLights.length ? "已看 · 仍可导出" : "无", amber: neighborLights.length > 0 },
      { item: "照片 / 星表", ok: true, detail: "未夹带" }
    ];

    const yaml = serializePromote({
      officialId,
      series,
      exported,
      overlay
    });
    if (FORBIDDEN_COPY.test(yaml)) hard.push("导出文案含禁语。");

    return {
      officialId,
      yaml,
      checklist,
      hard,
      amber,
      roleNotes,
      atelierOnly,
      requestAdd,
      canCopy: hard.length === 0 && !idErr,
      success: SUCCESS,
      filename: `promote-${officialId || "series"}-roles-${stamp()}.yaml`
    };
  }

  function serializePromote({ officialId, series, exported, overlay }) {
    const s = series || {};
    const span = s.photoSpan || [0, 0];
    const lines = [
      "# 设计工坊升格系列。交给现网评审。现网尚未收下。薄柜未建，升格未闭环。",
      "# 不是同步盘。引擎不读本文件所在工坊柜。",
      "",
      `id: ${officialId}`,
      "kind: series",
      "status: promote-ready",
      `stage: "${s.stage || "16:9"}"`,
      `pageCount: ${s.pageCount || exported.length}`,
      `density: ${s.density || "standard"}`,
      `photo_span: [${span[0] || 0}, ${span[1] || 0}]`,
      `coverHint: ${s.coverHint || "veil-footer"}`,
      `backHint: ${s.backHint || "closing-default"}`,
      `sourceAtelier: ${s.id || ""}`
    ];
    if (overlay) lines.push(`starOverlay: ${JSON.stringify(overlay)}`);
    if (!exported.length) {
      lines.push("sequence: []");
    } else {
      lines.push("sequence:");
      for (const row of exported) {
        const extra = row.extra && row.extra.length ? `, ${row.extra.join(", ")}` : "";
        lines.push(`  - { i: ${row.i}, role: ${row.role}, program: ${row.program}, faceHint: ${row.faceHint}${extra} }`);
      }
    }
    return `${lines.join("\n")}\n`;
  }

  function formatChecklist(report) {
    const lines = [
      "# 设计工坊升格检查单",
      "",
      `- 正式 id：${report.officialId || "（空）"}`,
      `- 文件名：${report.filename}`,
      ""
    ];
    for (const row of report.checklist) {
      const mark = !row.ok ? "硬拒" : row.amber ? "琥珀" : "过";
      lines.push(`- ${row.item}：${mark}${row.detail ? ` · ${row.detail}` : ""}`);
    }
    if (report.hard.length) {
      lines.push("", "## 硬拒");
      report.hard.forEach((t) => lines.push(`- ${t}`));
    }
    if (report.amber.length) {
      lines.push("", "## 琥珀");
      report.amber.forEach((t) => lines.push(`- ${t}`));
    }
    lines.push("", SUCCESS);
    return `${lines.join("\n")}\n`;
  }

  function bundleCopy(report) {
    return `${formatChecklist(report)}\n---\n\n${report.yaml}`;
  }

  async function copyText(text) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch (_) {
      const hint = document.createElement("textarea");
      hint.value = text;
      document.body.appendChild(hint);
      hint.select();
      document.execCommand("copy");
      hint.remove();
      return true;
    }
  }

  function parseCatalog(text) {
    const faces = [];
    let cur = null;
    for (const raw of String(text || "").split(/\r?\n/)) {
      const id = /^\s+-\s+id:\s+([a-z0-9-]+)/.exec(raw);
      if (id) {
        if (cur) faces.push(cur);
        cur = { id: id[1] };
        continue;
      }
      if (!cur) continue;
      const st = /^\s+status:\s+(\S+)/.exec(raw);
      if (st) cur.status = st[1].replace(/^["']|["']$/g, "");
      const role = /^\s+role:\s+(\S+)/.exec(raw);
      if (role) cur.role = role[1].replace(/^["']|["']$/g, "");
      const fam = /^\s+familyId:\s+(\S+)/.exec(raw);
      if (fam) cur.familyId = fam[1].replace(/^["']|["']$/g, "");
    }
    if (cur) faces.push(cur);
    return faces;
  }

  function parsePacketMeta(text) {
    return {
      id: grab(text, "id"),
      status: grab(text, "status"),
      role: grab(text, "role"),
      program: grab(text, "program"),
      familyId: grab(text, "familyId"),
      slotCount: Number(grab(text, "slotCount") || 0),
      mix: (function () {
        const raw = (/^mix:\s*\{[^}]*\}/m.exec(text) || [""])[0];
        return raw ? parseMix(raw) : null;
      }())
    };
  }

  async function exists(url) {
    try {
      const res = await fetch(url, { cache: "no-store", method: "GET" });
      return res.ok;
    } catch (_) {
      return false;
    }
  }

  async function reconcile({ faces, roles, rolesFile, facesFileIds }) {
    const fileRoles = rolesFile || roles || {};
    const fileFaceIds = Array.isArray(facesFileIds)
      ? facesFileIds.slice()
      : (faces || []).map((f) => f.id);
    const faceIds = (faces || []).map((f) => f.id);
    const faceById = new Map((faces || []).map((f) => [f.id, f]));
    const roleIds = Object.keys(fileRoles);
    const issues = [];
    let catalog = [];
    let viaHttp = true;
    try {
      const res = await fetch("./catalog.yaml", { cache: "no-store" });
      if (!res.ok) throw new Error("catalog");
      catalog = parseCatalog(await res.text());
    } catch (_) {
      viaHttp = false;
      return {
        ok: null,
        viaHttp: false,
        issues: ["file:// 或静态服读不到 catalog.yaml。对账请用设计工坊打开方式（serve.cmd）。"],
        catalog: [],
        packets: {}
      };
    }

    const catIds = catalog.map((c) => c.id);
    const onlyCat = catIds.filter((id) => faceIds.indexOf(id) < 0);
    const onlyFace = faceIds.filter((id) => catIds.indexOf(id) < 0);
    if (onlyCat.length) issues.push(`catalog.yaml 有、微缩没有：${onlyCat.join(" · ")}`);
    if (onlyFace.length) issues.push(`微缩有、catalog.yaml 没有：${onlyFace.join(" · ")}`);

    const onlyRole = roleIds.filter((id) => catIds.indexOf(id) < 0 && fileFaceIds.indexOf(id) < 0);
    const missingRole = fileFaceIds.filter((id) => roleIds.indexOf(id) < 0);
    if (onlyRole.length) issues.push(`roles.js 多出：${onlyRole.join(" · ")}`);
    if (missingRole.length) issues.push(`roles.js 缺：${missingRole.join(" · ")}`);

    const packets = {};
    const jobs = faceIds.map(async (id) => {
      try {
        const res = await fetch(`./${id}/packet.yaml`, { cache: "no-store" });
        if (!res.ok) {
          issues.push(`${id} 读不到 packet.yaml`);
          return;
        }
        const meta = parsePacketMeta(await res.text());
        packets[id] = meta;
        if (fileRoles[id]) {
          const js = fileRoles[id];
          const drift = [];
          if ((js.role || "") !== (meta.role || "")) drift.push(`role ${js.role || "?"} ≠ ${meta.role || "?"}`);
          if ((js.program || "") !== (meta.program || "")) drift.push(`program ${js.program || "?"} ≠ ${meta.program || "?"}`);
          if ((js.familyId || "") !== (meta.familyId || "")) drift.push(`familyId ${js.familyId || "?"} ≠ ${meta.familyId || "?"}`);
          if (drift.length) issues.push(`${id} roles.js 与 packet 不一致：${drift.join(" · ")}`);
        }
        const face = faceById.get(id);
        if (face && meta.mix) {
          const geo = mixFromFace(face);
          if (
            meta.mix.portrait !== geo.portrait
            || meta.mix.landscape !== geo.landscape
            || (meta.mix.square || 0) !== geo.square
          ) {
            issues.push(
              `${id} 微缩朝向账 ≠ packet mix（微缩 ${geo.portrait}P/${geo.landscape}L/${geo.square}S · 包 ${meta.mix.portrait}P/${meta.mix.landscape}L/${meta.mix.square || 0}S）`
            );
          }
        }
      } catch (_) {
        issues.push(`${id} 对账失败`);
      }
    });
    await Promise.all(jobs);
    return {
      ok: issues.length === 0,
      viaHttp,
      issues,
      catalog,
      packets
    };
  }

  async function inspectPage(face, getStars, getDisabled) {
    const id = face && face.id;
    const hard = [];
    const amber = [];
    if (!id) return { hard: ["没有页型。"], amber, canExport: false };
    const packetOk = await exists(`./${id}/packet.yaml`);
    const usageOk = await exists(`./${id}/USAGE.md`);
    const sketchOk = await exists(`./${id}/sketch.png`);
    if (!packetOk) hard.push("没有 packet.yaml。");
    if (!usageOk) hard.push("没有 USAGE.md。");
    if (!sketchOk) hard.push("没有 sketch.png，导出页型包硬拒。");

    let packetText = "";
    let meta = {};
    if (packetOk) {
      try {
        packetText = await (await fetch(`./${id}/packet.yaml`, { cache: "no-store" })).text();
        meta = parsePacketMeta(packetText);
      } catch (_) {
        hard.push("packet.yaml 读失败。");
      }
    }
    const n = slotCount(face);
    const named = idSlotCount(id);
    if (named && named !== n) hard.push(`id 中数字 ${named} ≠ slotCount ${n}。`);
    if (meta.slotCount && meta.slotCount !== n) hard.push(`packet slotCount ${meta.slotCount} ≠ 微缩 ${n}。`);
    if (meta.program && PROGRAMS.indexOf(meta.program) < 0) hard.push(`program 不在七词内：${meta.program}`);
    if (!meta.program) hard.push("packet 没有 program。");
    const geo = mixFromFace(face);
    if (meta.mix) {
      if (
        meta.mix.portrait !== geo.portrait
        || meta.mix.landscape !== geo.landscape
        || (meta.mix.square || 0) !== geo.square
      ) {
        hard.push(
          `mix 与槽朝向对不上（包 ${meta.mix.portrait}P/${meta.mix.landscape}L/${meta.mix.square || 0}S · 微缩 ${geo.portrait}P/${geo.landscape}L/${geo.square}S）。`
        );
      }
    }
    if (getDisabled && getDisabled(id)) hard.push("已禁用，所有管线不用。先在页型 tab 取消禁用。");
    const stars = Number(getStars ? getStars(id) : 0);
    return {
      id,
      hard,
      amber,
      packetText,
      meta,
      stars,
      sketchOk,
      usageOk,
      canExport: hard.length === 0
    };
  }

  function rewritePacketStatus(text, status) {
    if (/^status:\s*\S+/m.test(text)) return text.replace(/^status:\s*\S+/m, `status: ${status}`);
    return `status: ${status}\n${text}`;
  }

  function crcTable() {
    const table = new Uint32Array(256);
    for (let i = 0; i < 256; i += 1) {
      let c = i;
      for (let k = 0; k < 8; k += 1) c = (c & 1) ? (0xedb88320 ^ (c >>> 1)) : (c >>> 1);
      table[i] = c >>> 0;
    }
    return table;
  }

  const CRC = crcTable();

  function crc32(bytes) {
    let c = 0xffffffff;
    for (let i = 0; i < bytes.length; i += 1) c = CRC[(c ^ bytes[i]) & 0xff] ^ (c >>> 8);
    return (c ^ 0xffffffff) >>> 0;
  }

  function u16(n) {
    return new Uint8Array([n & 0xff, (n >>> 8) & 0xff]);
  }

  function u32(n) {
    return new Uint8Array([n & 0xff, (n >>> 8) & 0xff, (n >>> 16) & 0xff, (n >>> 24) & 0xff]);
  }

  function concat(parts) {
    const size = parts.reduce((n, p) => n + p.length, 0);
    const out = new Uint8Array(size);
    let at = 0;
    for (const p of parts) {
      out.set(p, at);
      at += p.length;
    }
    return out;
  }

  function zipStore(files) {
    const locals = [];
    const centrals = [];
    let offset = 0;
    const enc = new TextEncoder();
    for (const file of files) {
      const name = enc.encode(file.name);
      const data = file.bytes;
      const crc = crc32(data);
      const local = concat([
        u32(0x04034b50), u16(20), u16(0), u16(0), u16(0), u16(0),
        u32(crc), u32(data.length), u32(data.length), u16(name.length), u16(0),
        name, data
      ]);
      locals.push(local);
      const central = concat([
        u32(0x02014b50), u16(20), u16(20), u16(0), u16(0), u16(0), u16(0),
        u32(crc), u32(data.length), u32(data.length), u16(name.length), u16(0),
        u16(0), u16(0), u16(0), u32(0), u32(offset), name
      ]);
      centrals.push(central);
      offset += local.length;
    }
    const centralBlob = concat(centrals);
    const end = concat([
      u32(0x06054b50), u16(0), u16(0), u16(files.length), u16(files.length),
      u32(centralBlob.length), u32(offset), u16(0)
    ]);
    return new Blob([concat([...locals, centralBlob, end])], { type: "application/zip" });
  }

  function downloadBlob(blob, filename) {
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    a.click();
    URL.revokeObjectURL(a.href);
  }

  async function exportPageZip(face, overlay) {
    const id = face.id;
    const packetRes = await fetch(`./${id}/packet.yaml`, { cache: "no-store" });
    const usageRes = await fetch(`./${id}/USAGE.md`, { cache: "no-store" });
    const sketchRes = await fetch(`./${id}/sketch.png`, { cache: "no-store" });
    if (!packetRes.ok || !usageRes.ok || !sketchRes.ok) {
      throw new Error("页型包三件不齐。");
    }
    let packet = await packetRes.text();
    packet = rewritePacketStatus(packet, "promote-ready");
    if (overlay) packet = `${packet.replace(/\s+$/, "")}\n\n# starOverlay: ${overlay.replace(/\s+/g, " ")}\n`;
    const folder = `promote-${id}-${stamp()}`;
    const enc = new TextEncoder();
    const zip = zipStore([
      { name: `${folder}/packet.yaml`, bytes: enc.encode(packet) },
      { name: `${folder}/USAGE.md`, bytes: enc.encode(await usageRes.text()) },
      { name: `${folder}/sketch.png`, bytes: new Uint8Array(await sketchRes.arrayBuffer()) }
    ]);
    downloadBlob(zip, `${folder}.zip`);
    return folder;
  }

  window.AtelierPromote = {
    APPENDIX_A,
    APPENDIX_B,
    PROGRAMS,
    SUCCESS,
    officialIdError,
    defaultOfficialId,
    loadRoleMap,
    parseRoleMap,
    resolveRole,
    appendixAHas,
    appendixBHas,
    buildSeriesPromote,
    formatChecklist,
    bundleCopy,
    copyText,
    reconcile,
    inspectPage,
    mixFromFace,
    rewritePacketStatus,
    syncPacketStatus: async function syncPacketStatus(id, status) {
      try {
        const res = await fetch("./atelier/status", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ id, status })
        });
        if (res.ok) return { ok: true, via: "serve" };
        const data = await res.json().catch(() => ({}));
        if (res.status !== 404) return { ok: false, error: data.error || "源文件未写上。" };
      } catch (_) { /* file:// 或旧静态服 */ }
      try {
        const res = await fetch(`./${id}/packet.yaml`, { cache: "no-store" });
        if (!res.ok) return { ok: false, error: "读不到 packet.yaml" };
        const text = rewritePacketStatus(await res.text(), status);
        if (window.showSaveFilePicker) {
          const handle = await window.showSaveFilePicker({
            suggestedName: "packet.yaml",
            id: `atelier-packet-${id}`,
            types: [{ description: "YAML", accept: { "text/yaml": [".yaml"], "text/plain": [".yaml"] } }]
          });
          const writable = await handle.createWritable();
          await writable.write(text);
          await writable.close();
          return { ok: true, via: "picker" };
        }
        downloadBlob(new Blob([text], { type: "text/yaml" }), "packet.yaml");
        return { ok: true, via: "download" };
      } catch (err) {
        if (err && err.name === "AbortError") return { ok: false, aborted: true };
        return { ok: false, error: (err && err.message) || "源文件未写上。" };
      }
    },
    exportPageZip,
    downloadBlob,
    stamp
  };
})();
