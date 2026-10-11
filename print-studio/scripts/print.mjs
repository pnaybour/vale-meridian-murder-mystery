#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { makePdf } from '../lib/pdf.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const data = JSON.parse(fs.readFileSync(path.join(root, 'lib/event.json')));
const fonts = JSON.parse(fs.readFileSync(path.join(root, 'lib/fonts.json')));
const logo = 'data:image/png;base64,' + fs.readFileSync(path.join(root, 'public/valemeridian-logo.png')).toString('base64');
const picturesFile = path.join(root, 'lib/photos.json');
const pictures = fs.existsSync(picturesFile) ? JSON.parse(fs.readFileSync(picturesFile)) : {};
const args = process.argv.slice(2),
  settings = {};
const flags = new Set([
  '--ink-saver',
  '--full-page',
  '--large-print',
  '--no-manifest',
  '--no-cut-marks',
  '--envelopes',
]);
const values = new Set([
  '--category',
  '--round',
  '--table',
  '--guest',
  '--id',
  '--ids',
  '--output',
  '--sort',
  '--copies',
  '--brand',
  '--colour',
]);
for (let i = 0; i < args.length; i++) {
  const a = args[i];
  if (a === '--help') {
    console.log(
      `Vale Meridian print generator\n\nnode scripts/print.mjs [options]\n\n--category clues|badges|evidence|private|seating|stationery|gm\n--round 0..4                 Filter by release round\n--table 1..8                 Filter by table\n--guest NAME                 Match real or character name\n--id ID                      Print one exact item\n--ids ID,ID,...              Print several exact items (comma-separated)\n--copies NUMBER              Override copies per selected item\n--sort round|table|guest      Packing order\n--brand NAME                 Brand name, up to 24 characters\n--colour '#732b40'            Accent colour\n--ink-saver                  Black and white\n--full-page                  Full-page clue cards\n--large-print                Large type, one card per A4 page (for a partially sighted guest)\n--no-cut-marks               Hide cutting marks\n--envelopes                  Print envelope labels directly onto C5 envelopes instead\n--no-manifest                Omit host packing checklist\n--output PATH                PDF output (default output/valemeridian-print-pack.pdf)\n\nNo filters prints the complete inventory. Event records are never modified.`,
    );
    process.exit(0);
  }
  if (flags.has(a)) settings[a] = true;
  else if (
    values.has(a) &&
    args[i + 1] !== undefined &&
    !args[i + 1].startsWith('--')
  )
    settings[a] = args[++i];
  else throw new Error(`Unknown option or missing value: ${a}. Use --help.`);
}
if (
  settings['--sort'] &&
  !['round', 'table', 'guest'].includes(settings['--sort'])
)
  throw new Error('Sort must be round, table or guest.');
const selected = data.items
  .filter(
    (i) =>
      (!settings['--category'] || i.category === settings['--category']) &&
      (!settings['--round'] || i.round === Number(settings['--round'])) &&
      (!settings['--table'] || i.table === Number(settings['--table'])) &&
      (!settings['--id'] || i.id === settings['--id']) &&
      (!settings['--ids'] || settings['--ids'].split(',').includes(i.id)) &&
      (!settings['--guest'] ||
        [i.guest, i.character]
          .join(' ')
          .toLowerCase()
          .includes(settings['--guest'].toLowerCase())),
  )
  .map((i) => ({
    ...i,
    quantity: settings['--copies'] ? Number(settings['--copies']) : i.quantity,
    // The same guest label, printed straight onto the front of a C5 envelope.
    ...(settings['--envelopes'] && i.template === 'label' && i.labelKind === 'guest'
      ? { template: 'envelope' }
      : {}),
  }));
const brand = {
  inkSaver: !!settings['--ink-saver'],
  cutMarks: !settings['--no-cut-marks'],
};
if (settings['--brand']) brand.name = settings['--brand'];
if (settings['--colour']) brand.color = settings['--colour'];
const result = makePdf(selected, fonts, {
  brand,
  event: data.event,
  images: pictures,
  sort: settings['--sort'] ?? 'round',
  fullPage: !!settings['--full-page'],
  largePrint: !!settings['--large-print'],
  manifest: !settings['--no-manifest'],
  snapshotId: data.source.databaseHash.slice(0, 8),
  logo,
});
const output = path.resolve(
  settings['--output'] ?? path.join(root, 'output/valemeridian-print-pack.pdf'),
);
fs.mkdirSync(path.dirname(output), { recursive: true });
fs.writeFileSync(output, new Uint8Array(result.doc.output('arraybuffer')));
fs.writeFileSync(
  output.replace(/\.pdf$/i, '') + '.manifest.json',
  JSON.stringify(
    {
      snapshot: data.source,
      brand,
      items: result.manifest,
      pages: result.pages,
      printPages: result.printPages,
      placements: result.placements,
    },
    null,
    2,
  ),
);
console.log(
  `${selected.length} entries, ${selected.reduce((n, i) => n + i.quantity, 0)} pieces, ${result.printPages} print pages. Saved ${output}`,
);
