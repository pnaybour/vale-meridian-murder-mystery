#!/usr/bin/env node
// A plain one-page seating list: guest, character and table, alphabetical by guest, so anyone can be
// found by name if the room is laid out differently on the day.
// Usage: node scripts/seating-list.mjs [output.pdf]
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { jsPDF } from 'jspdf';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const out = path.resolve(process.argv[2] ?? path.join(root, 'output/seating-list.pdf'));
const event = JSON.parse(fs.readFileSync(path.join(root, 'lib/event.json'), 'utf8'));
const rows = event.items.filter((i) => i.template === 'place')
  .map((i) => ({ guest: i.guest, character: i.character, table: Number(i.table) }))
  .sort((a, b) => a.guest.localeCompare(b.guest, 'en'));
const ACCENT = [115, 43, 64];
const doc = new jsPDF({ unit: 'mm', format: 'a4', compress: true });
doc.setProperties({ title: 'Vale Meridian seating list', author: 'Vale Meridian' });
const logo = 'data:image/png;base64,' + fs.readFileSync(path.join(root, 'public/valemeridian-logo.png')).toString('base64');

const M = 14, W = 210 - 2 * M, cols = [W * 0.40, W * 0.46, W * 0.14];
doc.addImage(logo, 'PNG', 210 - M - 40, 10, 40, 40 * 731 / 2000);
doc.setFont('helvetica', 'bold').setFontSize(22).setTextColor(...ACCENT).text('Who is where', M, 19);
doc.setFont('helvetica', 'normal').setFontSize(9.5).setTextColor(90, 90, 90)
  .text(`${event.event.hosts}  ·  ${event.event.venue}  ·  ${event.event.date}  ·  ${rows.length} guests, alphabetical by guest`, M, 26);

let y = 34;
const head = ['Guest', 'Character', 'Table'];
doc.setFillColor(...ACCENT).rect(M, y, W, 7, 'F');
doc.setFont('helvetica', 'bold').setFontSize(10).setTextColor(255, 255, 255);
let x = M; head.forEach((h, i) => { doc.text(h, x + 2.5 + (i === 2 ? 0 : 0), y + 4.8); x += cols[i]; });
y += 7;
const lead = Math.min(4.8, (297 - 12 - y) / rows.length);
rows.forEach((r, k) => {
  if (k % 2 === 0) doc.setFillColor(246, 240, 242).rect(M, y, W, lead, 'F');
  const base = y + lead * 0.72;
  doc.setFont('helvetica', 'bold').setFontSize(9.5).setTextColor(35, 32, 34).text(r.guest, M + 2.5, base);
  doc.setFont('helvetica', 'normal').setTextColor(...ACCENT).text(r.character, M + cols[0] + 2.5, base);
  doc.setFont('helvetica', 'bold').setFontSize(11).setTextColor(35, 32, 34).text(String(r.table), M + cols[0] + cols[1] + 2.5, base);
  y += lead;
});
fs.mkdirSync(path.dirname(out), { recursive: true });
fs.writeFileSync(out, new Uint8Array(doc.output('arraybuffer')));
console.log(`${rows.length} guests on one sheet (row height ${lead.toFixed(2)} mm). Saved ${out}`);
