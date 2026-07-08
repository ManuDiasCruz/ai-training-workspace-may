import * as penpot from "@penpot/library";
import { writeFile } from "fs/promises";

// Palette (also registered as library colors / design tokens)
const C = {
  primary: "#4F46E5",
  primarySoft: "#EEF2FF",
  primaryChip: "#E0E7FF",
  ink: "#111827",
  inkSoft: "#1F2937",
  slate: "#4B5563",
  muted: "#6B7280",
  faint: "#9CA3AF",
  line: "#E5E7EB",
  lineFaint: "#F3F4F6",
  surface: "#FFFFFF",
  canvas: "#F3F4F6",
  fieldBg: "#F9FAFB",
  amber: "#F59E0B",
  green: "#10B981",
  red: "#EF4444",
  maleBg: "#DBEAFE",
  maleFg: "#1D4ED8",
  femaleBg: "#FCE7F3",
  femaleFg: "#BE185D",
  indigoLight: "#C7D2FE",
  sidebarChip: "#374151",
};

const ctx = penpot.createBuildContext();

const fill = (color, opacity = 1) => [{ fillColor: color, fillOpacity: opacity }];
const stroke = (color, width = 1) => [{
  strokeColor: color, strokeOpacity: 1, strokeWidth: width,
  strokeAlignment: "center", strokeStyle: "solid",
}];

function R(name, x, y, width, height, color, opts = {}) {
  const shape = { name, x, y, width, height, fills: fill(color, opts.opacity ?? 1) };
  if (opts.rx != null) { shape.rx = opts.rx; shape.ry = opts.rx; }
  if (opts.stroke) shape.strokes = stroke(opts.stroke, opts.strokeWidth ?? 1);
  ctx.addRect(shape);
}

function Circle(name, cx, cy, r, color) {
  ctx.addCircle({ name, x: cx - r, y: cy - r, width: 2 * r, height: 2 * r, fills: fill(color) });
}

function T(name, x, y, text, opts = {}) {
  const size = opts.size ?? 13;
  const weight = opts.weight ?? "400";
  const variant = weight === "700" ? "bold" : weight === "600" ? "bold" : "regular";
  const w = opts.w ?? Math.max(20, Math.round(text.length * size * 0.62));
  const h = opts.h ?? Math.round(size * 1.4);
  ctx.addText({
    name, x, y, width: w, height: h,
    growType: "auto-width",
    content: {
      type: "root",
      children: [{
        type: "paragraph-set",
        children: [{
          type: "paragraph",
          children: [{
            text,
            fills: fill(opts.color ?? C.ink),
            fontId: "sourcesanspro",
            fontFamily: "sourcesanspro",
            fontSize: String(size),
            fontStyle: "normal",
            fontWeight: weight === "600" ? "700" : weight,
            fontVariantId: variant,
          }],
        }],
      }],
    },
  });
}

try {
  ctx.addFile({ name: "Shopping Customers — UI Design" });

  // Design tokens as library colors
  for (const [name, color] of [
    ["Primary / Indigo 600", C.primary], ["Primary / Indigo 50", C.primarySoft],
    ["Ink / Gray 900", C.ink], ["Muted / Gray 500", C.muted],
    ["Line / Gray 200", C.line], ["Canvas / Gray 100", C.canvas],
    ["Surface / White", C.surface], ["Accent / Amber 500", C.amber],
    ["Success / Emerald 500", C.green], ["Danger / Red 500", C.red],
  ]) {
    ctx.addLibraryColor({ name, color, opacity: 1 });
  }

  ctx.addPage({ name: "01 · Customers dashboard" });

  ctx.addBoard({ name: "Customers dashboard · Desktop 1440", x: 0, y: 0, width: 1440, height: 1024 });

  // ===== canvas =====
  R("canvas/bg", 0, 0, 1440, 1024, C.canvas);

  // ===== sidebar =====
  R("sidebar/bg", 0, 0, 228, 1024, C.ink);
  Circle("sidebar/logo", 36, 40, 14, C.primary);
  T("sidebar/logo-letter", 31, 31, "S", { size: 14, weight: "700", color: "#FFFFFF" });
  T("sidebar/title", 60, 30, "Shopping Customers", { size: 16, weight: "700", color: "#FFFFFF" });
  T("sidebar/subtitle", 60, 52, "Mall segmentation · v1.0.0", { size: 11, color: C.faint });

  R("sidebar/nav-active", 12, 96, 204, 40, C.primary, { rx: 8 });
  R("sidebar/nav-active-icon", 26, 108, 10, 10, C.indigoLight, { rx: 2 });
  T("sidebar/nav-dashboard", 44, 107, "Dashboard", { size: 14, weight: "600", color: "#FFFFFF" });

  R("sidebar/icon-customers", 26, 156, 10, 10, C.slate, { rx: 5 });
  T("sidebar/nav-customers", 44, 155, "Customers", { size: 14, color: C.faint });
  R("sidebar/icon-stats", 26, 204, 10, 10, C.slate, { rx: 2 });
  T("sidebar/nav-stats", 44, 203, "Statistics", { size: 14, color: C.faint });
  R("sidebar/icon-docs", 26, 252, 10, 10, C.slate, { rx: 1 });
  T("sidebar/nav-docs", 44, 251, "API docs (/docs)", { size: 14, color: C.faint });

  R("sidebar/health-card", 12, 944, 204, 56, C.inkSoft, { rx: 8 });
  Circle("sidebar/health-dot", 40, 972, 6, C.green);
  T("sidebar/health-title", 56, 956, "API healthy", { size: 12, weight: "600", color: C.line });
  T("sidebar/health-sub", 56, 974, "GET /health · 200 OK", { size: 11, color: C.muted });

  // ===== top bar =====
  R("topbar/bg", 228, 0, 1212, 76, C.surface);
  R("topbar/divider", 228, 76, 1212, 1, C.line);
  T("topbar/title", 260, 18, "Customers dashboard", { size: 20, weight: "700" });
  T("topbar/subtitle", 260, 46, "200 mall customers · SQLite · FastAPI", { size: 12, color: C.muted });

  R("topbar/search", 806, 20, 320, 38, C.fieldBg, { rx: 8, stroke: C.line });
  Circle("topbar/search-icon", 828, 39, 6, C.faint);
  Circle("topbar/search-icon-in", 828, 39, 4, C.fieldBg);
  T("topbar/search-ph", 848, 30, "Search code or gender…", { size: 13, color: C.faint });

  R("topbar/add-btn", 1146, 20, 164, 38, C.primary, { rx: 8 });
  T("topbar/add-label", 1165, 29, "+  Add customer", { size: 14, weight: "600", color: "#FFFFFF" });

  Circle("topbar/avatar", 1372, 39, 17, C.primaryChip);
  T("topbar/avatar-init", 1362, 31, "MC", { size: 13, weight: "700", color: C.primary });

  // ===== KPI tiles =====
  const KPIS = [
    { x: 260, label: "TOTAL CUSTOMERS", value: "200", note: "total_customers · /stats", noteColor: C.green },
    { x: 492, label: "AVERAGE AGE", value: "38.9", note: "avg_age · years", noteColor: C.muted },
    { x: 724, label: "AVG ANNUAL INCOME", value: "$60.6k", note: "avg_annual_income_k", noteColor: C.muted },
  ];
  for (const k of KPIS) {
    R(`kpi/${k.label}/card`, k.x, 104, 216, 108, C.surface, { rx: 12, stroke: C.line });
    T(`kpi/${k.label}/label`, k.x + 20, 122, k.label, { size: 12, weight: "600", color: C.muted });
    T(`kpi/${k.label}/value`, k.x + 20, 146, k.value, { size: 30, weight: "700" });
    T(`kpi/${k.label}/note`, k.x + 20, 186, k.note, { size: 11, color: k.noteColor });
  }
  // score tile with meter
  R("kpi/score/card", 956, 104, 216, 108, C.surface, { rx: 12, stroke: C.line });
  T("kpi/score/label", 976, 122, "AVG SPENDING SCORE", { size: 12, weight: "600", color: C.muted });
  T("kpi/score/value", 976, 146, "50.2", { size: 30, weight: "700" });
  R("kpi/score/meter-track", 976, 188, 176, 6, C.line, { rx: 3 });
  R("kpi/score/meter-fill", 976, 188, 88, 6, C.amber, { rx: 3 });
  // gender tile
  R("kpi/gender/card", 1188, 104, 216, 108, C.surface, { rx: 12, stroke: C.line });
  T("kpi/gender/label", 1208, 122, "GENDER SPLIT", { size: 12, weight: "600", color: C.muted });
  T("kpi/gender/value", 1208, 148, "112 F · 88 M", { size: 16, weight: "700" });
  R("kpi/gender/track", 1208, 178, 176, 10, C.line, { rx: 5 });
  R("kpi/gender/fill", 1208, 178, 98, 10, C.primary, { rx: 5 });
  T("kpi/gender/note", 1208, 194, "by_gender · Female 56% / Male 44%", { size: 11, color: C.muted });

  // ===== filter bar =====
  R("filters/bar", 260, 240, 1144, 64, C.surface, { rx: 12, stroke: C.line });
  T("filters/label", 284, 262, "Filters", { size: 13, weight: "600", color: C.sidebarChip });

  const SELECTS = [
    { x: 348, w: 150, label: "Gender: All" },
    { x: 510, w: 170, label: "Age: 0 – 130" },
    { x: 692, w: 190, label: "Income (k$): 0 – 140" },
    { x: 894, w: 190, label: "Score: 1 – 100" },
  ];
  for (const s of SELECTS) {
    R(`filters/${s.label}/field`, s.x, 256, s.w, 32, C.fieldBg, { rx: 8, stroke: C.line });
    T(`filters/${s.label}/text`, s.x + 14, 263, s.label, { size: 12, color: C.sidebarChip });
    T(`filters/${s.label}/chev`, s.x + s.w - 22, 262, "⌄", { size: 12, color: C.muted });
  }
  R("filters/apply", 1116, 256, 130, 32, C.primarySoft, { rx: 8 });
  T("filters/apply-label", 1134, 263, "Apply filters", { size: 12, weight: "600", color: C.primary });
  T("filters/clear", 1276, 263, "Clear all", { size: 12, color: C.muted });

  // ===== table =====
  R("table/card", 260, 328, 1144, 560, C.surface, { rx: 12, stroke: C.line });
  R("table/head-bg", 260, 328, 1144, 48, C.fieldBg, { rx: 12 });
  R("table/head-bg-sq", 260, 352, 1144, 24, C.fieldBg);
  R("table/head-divider", 260, 376, 1144, 1, C.line);

  const COLS = [
    { x: 292, label: "ID ▲" }, { x: 372, label: "CODE" }, { x: 512, label: "GENDER" },
    { x: 692, label: "AGE" }, { x: 812, label: "ANNUAL INCOME (K$)" },
    { x: 1032, label: "SPENDING SCORE" }, { x: 1312, label: "ACTIONS" },
  ];
  for (const c of COLS) T(`table/head/${c.label}`, c.x, 346, c.label, { size: 12, weight: "700", color: C.muted });

  const ROWS = [
    { id: 1, code: "0001", g: "Male", age: 19, inc: 15, score: 39 },
    { id: 2, code: "0002", g: "Male", age: 21, inc: 15, score: 81 },
    { id: 3, code: "0003", g: "Female", age: 20, inc: 16, score: 6 },
    { id: 4, code: "0004", g: "Female", age: 23, inc: 16, score: 77 },
    { id: 5, code: "0005", g: "Female", age: 31, inc: 17, score: 40 },
    { id: 6, code: "0006", g: "Female", age: 22, inc: 17, score: 76 },
    { id: 7, code: "0007", g: "Female", age: 35, inc: 18, score: 6 },
    { id: 8, code: "0008", g: "Female", age: 23, inc: 18, score: 94 },
  ];
  ROWS.forEach((r, i) => {
    const baseY = 376 + i * 56; // row top
    const textY = baseY + 20;
    const male = r.g === "Male";
    T(`row${r.id}/id`, 292, textY, String(r.id));
    T(`row${r.id}/code`, 372, textY, r.code, { color: C.inkSoft });
    R(`row${r.id}/chip`, 512, baseY + 18, male ? 52 : 64, 24, male ? C.maleBg : C.femaleBg, { rx: 12 });
    T(`row${r.id}/gender`, male ? 524 : 522, baseY + 22, r.g, { size: 12, color: male ? C.maleFg : C.femaleFg });
    T(`row${r.id}/age`, 692, textY, String(r.age));
    T(`row${r.id}/income`, 812, textY, String(r.inc));
    R(`row${r.id}/score-track`, 1032, baseY + 24, 140, 8, C.line, { rx: 4 });
    const scoreColor = r.score >= 70 ? C.green : r.score >= 30 ? C.amber : C.red;
    R(`row${r.id}/score-fill`, 1032, baseY + 24, Math.max(8, Math.round(140 * r.score / 100)), 8, scoreColor, { rx: 4 });
    T(`row${r.id}/score`, 1184, textY, String(r.score));
    T(`row${r.id}/delete`, 1320, textY, "Delete", { size: 12, color: C.red });
    if (i < ROWS.length - 1) R(`row${r.id}/divider`, 260, baseY + 56, 1144, 1, C.lineFaint);
  });

  // pagination
  R("table/footer-divider", 260, 828, 1144, 1, C.line);
  T("table/showing", 292, 850, "Showing 1–20 of 200 · page_size 20", { size: 12, color: C.muted });
  const PAGES = [
    { x: 1090, label: "‹", active: false }, { x: 1130, label: "1", active: true },
    { x: 1170, label: "2", active: false }, { x: 1210, label: "3", active: false },
    { x: 1274, label: "10", active: false }, { x: 1314, label: "›", active: false },
  ];
  for (const p of PAGES) {
    R(`pager/${p.label}/btn`, p.x, 844, 34, 32, p.active ? C.primary : C.surface, { rx: 8, stroke: p.active ? undefined : C.line });
    T(`pager/${p.label}/label`, p.x + (p.label.length > 1 ? 8 : 13), 851, p.label, { size: 13, color: p.active ? "#FFFFFF" : C.sidebarChip });
  }
  T("pager/ellipsis", 1252, 851, "…", { size: 13, color: C.muted });

  // footnotes
  T("foot/api", 260, 916,
    "Data: GET /customers (page, page_size, gender, min/max age·income·score, search, sort_by, order) · KPIs: GET /stats · Create: POST /customers · Remove: DELETE /customers/{id}",
    { size: 11, color: C.faint });
  T("foot/meta", 260, 936,
    "Shopping Customers API — first page design reference · branch task002/shopping-api-dataset3 · Stakeholder: Mary",
    { size: 11, color: C.faint });

  ctx.closeBoard();

  // ===== hand-off notes board =====
  ctx.addBoard({ name: "Hand-off notes", x: 1520, y: 0, width: 560, height: 620 });
  R("notes/bg", 1520, 0, 560, 620, C.surface);
  T("notes/title", 1552, 28, "Developer hand-off — first page", { size: 18, weight: "700" });
  T("notes/stakeholder", 1552, 60, "Stakeholder: Mary", { size: 13, weight: "600", color: C.primary });
  const NOTES = [
    "· App: Shopping Customers API (FastAPI + SQLite)",
    "· Branch: task002/shopping-api-dataset3",
    "· KPI tiles read GET /stats (total, averages, by_gender)",
    "· Table reads GET /customers with server-side pagination",
    "· Filters map 1:1 to query params (gender, min/max age,",
    "  income, score, search) — apply on commit, debounce search",
    "· Sort via sort_by + order on column headers (ID sorted asc)",
    "· “+ Add customer” → POST /customers (409 = duplicate code)",
    "· Row “Delete” → DELETE /customers/{id} after confirm",
    "· Errors: 400 inconsistent ranges · 422 invalid values —",
    "  show inline on the filter bar",
    "· Score meter colors: ≥70 emerald · 30–69 amber · <30 red",
    "· Type: Source Sans Pro · spacing grid 4px · radius 8/12",
    "· Tokens: see library colors (Primary, Ink, Muted, Line…)",
  ];
  NOTES.forEach((n, i) => T(`notes/line${i}`, 1552, 96 + i * 32, n, { size: 13, color: C.inkSoft }));
  ctx.closeBoard();

  ctx.closePage();
  ctx.closeFile();

  const bytes = await penpot.exportAsBytes(ctx);
  await writeFile("shopping-customers-dashboard.penpot", bytes);
  console.log("OK bytes:", bytes.length);
} catch (e) {
  console.error("ERR", e.type, e.code, e.hint);
  if (e.explain) console.error(JSON.stringify(e.explain, null, 2).slice(0, 5000));
  process.exit(1);
}
