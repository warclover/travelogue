# Preview toolbar modules (M-C5 Phase 2)

Physical ESM split from `preview-toolbar.js` (entry URL unchanged).

| Module | Domain |
|--------|--------|
| `dock.js` | Icon dock, screenplay control, tooltips, scroll fade |
| `share.js` | `?share=1` minimal toolbar |
| `inline-edit.js` | Cover title inline edit (AC-ARC-14b) |
| `longshot.js` | Longshot export, stale hint, zip export, job poll (AC-ARC-14c) |
| `shell.js` | Shared chrome: toast, collapse, toolbar height, trip path helpers |
| `drawers.js` | Overlay drawers: edit, structure, cohort (G1) |
| `core.js` | Layout pending state, sheet dirty tracking, rerender/narrate jobs |
| `bootstrap.js` | v4 shell mount, share short-circuit, DOM ready wiring |
| `features.js` | Template/cover/featured/reader-mode preview UX |
| `init-v3.js` | `initToolbarV3`: bridges, sheet/task dock, longshot mount |

## CSS partials (`../preview-toolbar.css` aggregates via `@import`)

| File | Domain |
|------|--------|
| `tokens.css` | CSS variables (`--preview-toolbar-h`, sheet timing) |
| `shell.css` | Base chrome, reader mode, ghost controls, mode seg |
| `longshot.css` | Export zone, popover, effects, pending/result rows |
| `legacy-bar.css` | Legacy title/menu/featured bar |
| `drawers.css` | Edit/structure overlay drawers |
| `modal-chrome.css` | Studio modal preview chrome |
| `cohort.css` | Cohort seed picker |
| `v3-bar.css` | v3 single-row toolbar |
| `dock.css` | v4 icon dock (AC-ARC-14a) |
| `inline-edit.css` | Cover title inline edit |
| `task-dock.css` | Task dock (G1/pending/export) |
| `sheet.css` | Unified settings sheet |

Entry `../preview-toolbar.js` only registers bootstrap bridge. Bootstrap (`bootstrap.js`) mounts v4 shell and wires DOM ready.

Type-check (M-C5 gate): `npm run tsc:preview-toolbar` — uses `jsconfig.json` + `global.d.ts` for ambient DOM/window shims.

## Pure logic / Node tests (SFH)

Decision helpers without DOM belong in `*-logic.js` and are covered by `npm run test:js` (`tests/js/*.test.mjs`).

| Module | Pure logic | Notes |
|--------|------------|--------|
| `longshot.js` | `longshot-logic.js` | stale / title risk / side-effect window |
| (Studio FE) | see [PRD-STUDIO-FE-TEST-HARDENING-V1](../../../docs/PRD-STUDIO-FE-TEST-HARDENING-V1.md) | recipe / import / wizard logic likewise |

When adding toolbar decision branches, prefer extracting to `*-logic.js` first (DoD · SFH).
