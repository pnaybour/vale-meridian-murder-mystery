#!/usr/bin/env node
// Triangular table-number tents : one A4 landscape sheet per table, to be cut out,
// folded into a three-sided prism and glued so it stands. The net is three panels in a row:
//   [front slope][back slope][base] + a glue tab on the base's free edge.
// The tab is glued to the inside of the front panel's bottom edge, so the join sits in the base and
// shows nowhere. The number is printed on both slopes, turned so it reads upright when the tent stands.
// Usage: node scripts/table-tents.mjs [output.pdf] [table ...]   (default: all eight tables)
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';
import os from 'node:os';
import { jsPDF } from 'jspdf';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const out = path.resolve(process.argv[2] ?? path.join(root, 'output/table-tents.pdf'));
const tables = process.argv.slice(3).map(Number);
if (!tables.length) for (let t = 1; t <= 8; t++) tables.push(t);

// The whole sheet is used, down to the printer's own unprintable edge (4 mm).
const EDGE = 4, TAB = 14;
const S = (297 - 2 * EDGE - TAB) / 3, L = 210 - 2 * EDGE;   // slope width and tent length, in mm
const X0 = EDGE, Y0 = EDGE;
const ACCENT = [115, 43, 64], GREY = [150, 150, 150], PALE = [238, 232, 234];
const doc = new jsPDF({ orientation: 'landscape', unit: 'mm', format: 'a4', compress: true });
doc.setProperties({ title: 'Vale Meridian table tents', author: 'Vale Meridian' });
const mm = (pt) => (pt * 25.4) / 72;
// The Vale Meridian logo, turned a quarter turn each way so it stands upright on the two slopes.
const logoFile = path.join(root, 'public/valemeridian-logo.png');
const turned = (deg) => {
  const f = path.join(os.tmpdir(), `vv-logo-${deg}.png`);
  execFileSync('sips', ['-r', String(deg), logoFile, '--out', f], { stdio: 'ignore' });
  return 'data:image/png;base64,' + fs.readFileSync(f).toString('base64');
};
const LOGO = { A: turned(90), B: turned(270) };
const LOGO_H = 18, LOGO_W = LOGO_H * 2000 / 731;             // size when upright, in mm

// Everything on a slope is placed by u (distance up from its bottom edge) and v (distance along the
// tent, from the left as it is read when standing). Slope A reads downward on the sheet, slope B upward.
const pos = (panel, u, v) => panel === 'A'
  ? { x: X0 + u, y: Y0 + v, angle: -90 }
  : { x: X0 + 2 * S - u, y: Y0 + L - v, angle: 90 };
function put(str, panel, u, v, size, style, colour, spacing = 0, centred = false) {
  doc.setFont('helvetica', style).setFontSize(size).setTextColor(...colour);
  const tw = doc.getTextWidth(str) + spacing * (str.length - 1);
  const v0 = centred ? v - tw / 2 : v;
  if (v0 < 3 || v0 + tw > L - 3) console.warn(`"${str}" runs outside the tent (${v0.toFixed(1)} to ${(v0 + tw).toFixed(1)} of ${L})`);
  const o = pos(panel, u, v0);
  doc.text(str, o.x, o.y, { angle: o.angle, charSpace: spacing });
  return tw;
}
const widthOf = (str, size, style) => { doc.setFont('helvetica', style).setFontSize(size); return doc.getTextWidth(str); };

// Who sits where: guest and character names for each table, in seat order.
const event = JSON.parse(fs.readFileSync(path.join(root, 'lib/event.json'), 'utf8'));
const seated = (t) => event.items.filter((i) => i.template === 'place' && Number(i.table) === t)
  .map((i) => ({ guest: i.guest, character: i.character }));

tables.forEach((t, i) => {
  if (i) doc.addPage('a4', 'landscape');
  // Shaded base and tab, then the outline, then the folds.
  doc.setFillColor(...PALE);
  doc.rect(X0 + 2 * S, Y0, S, L, 'F');
  doc.lines([[TAB, TAB], [0, L - 2 * TAB], [-TAB, TAB]], X0 + 3 * S, Y0, [1, 1], 'F', true);
  doc.setDrawColor(200, 200, 200).setLineWidth(0.2).setLineDashPattern([], 0);
  doc.lines([[3 * S, 0], [TAB, TAB], [0, L - 2 * TAB], [-TAB, TAB], [-3 * S, 0], [0, -L]], X0, Y0, [1, 1], 'S', true);
  // Fold marks: short ticks at each end of the fold, nothing across the faces.
  doc.setDrawColor(190, 190, 190).setLineWidth(0.2);
  for (const k of [1, 2, 3]) {
    doc.line(X0 + k * S, Y0, X0 + k * S, Y0 + 4);
    doc.line(X0 + k * S, Y0 + L - 4, X0 + k * S, Y0 + L);
  }
  // Slope faces. Left block: tagline, number, TABLE, logo. Right block: who is at the table.
  const guests = seated(t), VC = 38;
  for (const panel of ['A', 'B']) {
    // Two short lines so the tagline stays inside the tent's length.
    put('A NIGHT OF GLAMOUR', panel, 9.5, VC, 6.5, 'bold', GREY, 1, true);
    put('& HIDDEN TRUTHS', panel, 5.5, VC, 6.5, 'bold', GREY, 1, true);
    put(String(t), panel, 14, VC, 150, 'bold', ACCENT, 0, true);
    put('TABLE', panel, 58, VC, 18, 'bold', ACCENT, 3, true);
    const u0 = 68;
    if (panel === 'A') doc.addImage(LOGO.A, 'PNG', X0 + u0, Y0 + VC - LOGO_W / 2, LOGO_H, LOGO_W);
    else doc.addImage(LOGO.B, 'PNG', X0 + 2 * S - u0 - LOGO_H, Y0 + L - VC - LOGO_W / 2, LOGO_H, LOGO_W);
    // Divider, then the names: guest in bold, character in the brand colour, top to bottom.
    const o1 = pos(panel, 8, 78), o2 = pos(panel, S - 8, 78);
    doc.setDrawColor(...GREY).setLineWidth(0.3).line(o1.x, o1.y, o2.x, o2.y);
    const lead = Math.min(9.5, (S - 18) / Math.max(guests.length, 1)), size = Math.min(12, lead * 1.3);
    guests.forEach((g, k) => {
      const u = S - 12 - k * lead;
      const w = put(g.guest, panel, u, 86, size, 'bold', [40, 36, 38]);
      const w2 = put('  ' + g.character, panel, u, 86 + w, size, 'normal', ACCENT);
      if (86 + w + w2 > L - 4) console.warn(`Table ${t}: the line for ${g.guest} runs off the tent`);
    });
  }
  // Base and tab labels, turned to read along the tent's length (bottom to top).
  doc.setFont('helvetica', 'normal').setFontSize(9).setTextColor(...GREY);
  const label = (str, cx) => doc.text(str, cx + 1.5, Y0 + L / 2 + doc.getTextWidth(str) / 2, { angle: 90 });
  label('BASE  ·  fold the three panels into a triangle, glue the tab inside the first panel', X0 + 2 * S + S / 2);
  label('GLUE', X0 + 3 * S + TAB / 2);
});
fs.mkdirSync(path.dirname(out), { recursive: true });
fs.writeFileSync(out, new Uint8Array(doc.output('arraybuffer')));
console.log(`${tables.length} sheets. Saved ${out}`);
