import { jsPDF } from 'jspdf';

const MM = 25.4 / 72;
export const defaults = {
  name: 'VALE MERIDIAN',
  subtitle: 'A NIGHT OF GLAMOUR & HIDDEN TRUTHS',
  color: '#732b40',
  inkSaver: false,
  cutMarks: true,
};
export function sortItems(items, mode = 'round') {
  const cats = [
    'clues',
    'private',
    'evidence',
    'badges',
    'seating',
    'stationery',
    'gm',
  ];
  return [...items].sort(
    (a, b) =>
      cats.indexOf(a.category) - cats.indexOf(b.category) ||
      Number(a.private) - Number(b.private) ||
      (mode === 'guest'
        ? a.guest.localeCompare(b.guest)
        : mode === 'table'
          ? (a.table ?? 99) - (b.table ?? 99)
          : 0) ||
      (a.round ?? 9) - (b.round ?? 9) ||
      (a.order ?? 0) - (b.order ?? 0) ||
      (a.table ?? 99) - (b.table ?? 99) ||
      a.character.localeCompare(b.character) ||
      a.id.localeCompare(b.id),
  );
}
export function validateItems(items) {
  const errors = [],
    ids = new Set();
  for (const i of items) {
    if (ids.has(i.id)) errors.push(`Duplicate item: ${i.id}`);
    ids.add(i.id);
    if (!i.title?.trim()) errors.push(`Missing title: ${i.id}`);
    if (
      ['card', 'report', 'slip', 'taxi', 'reference', 'divider'].includes(
        i.template,
      ) &&
      !i.content?.trim()
    )
      errors.push(`Missing content: ${i.id}`);
    if (
      ['badge', 'place'].includes(i.template) &&
      (!i.character || !i.guest || !i.table)
    )
      errors.push(`Missing guest or seat: ${i.id}`);
    if (i.template === 'qnote' && (!i.content?.trim() || !i.toCharacter || !i.toTable || !i.character || !i.table))
      errors.push(`Incomplete question note: ${i.id}`);
    if (['photo', 'money'].includes(i.template) && (!i.imageWidth || !i.imageHeight))
      errors.push(`Photograph without a picture size: ${i.id}`);
    if (!Number.isInteger(i.quantity) || i.quantity < 1 || i.quantity > 500)
      errors.push(`Invalid quantity: ${i.id}`);
    if (i.template === 'seating-plan' && (
      !i.seatingPlan?.tables?.length ||
      i.seatingPlan.tables.length > 8 ||
      i.seatingPlan.tables.some((t) => !t.seats.length || !t.number ||
        t.seats.some((s) => !s.guest || !s.character || !s.seat))
    )) errors.push(`Missing or unsupported seating plan: ${i.id}`);
    if (i.template === 'table-plan' && (
      !i.tablePlan?.tables?.length ||
      i.tablePlan.outline?.length < 3 ||
      i.tablePlan.tables.some((t) => !t.number || !t.guests?.length || !i.tablePlan.rooms?.[t.room])
    )) errors.push(`Missing or unsupported table plan: ${i.id}`);
    if (i.template === 'room-plan' && (
      !i.roomPlan?.tables?.length ||
      i.roomPlan.tables.some((t) => !t.seats?.length || !t.diameter ||
        t.seats.some((s) => s.angle == null || !s.guest))
    )) errors.push(`Missing or unsupported room plan: ${i.id}`);
  }
  return errors;
}

// Both the website and CLI use this renderer. There is no browser screenshot
// conversion: text remains selectable and fonts are embedded in the PDF.
// The occasion and venue printed in card footers. They come from data/event.json (options.event),
// so each host's cards carry their own party and never anyone else's.
let footer = { occasion: 'THE ANNIVERSARY GALA', venue: '' };

export function makePdf(items, fonts, options = {}) {
  footer = {
    occasion: String(options.event?.hosts ?? 'The Anniversary Gala').toUpperCase(),
    venue: String(options.event?.venue ?? '').toUpperCase(),
  };
  // Photographs are passed in as data URLs (lib/photos.json), so the renderer stays offline.
  const pictures = options.images ?? {};
  for (const i of items)
    if (['photo', 'money'].includes(i.template) && !pictures[i.id])
      throw new Error(`Photograph not supplied: ${i.id}. Load lib/photos.json and pass it as options.images.`);
  const brand = { ...defaults, ...options.brand };
  if (!items.length) throw new Error('Select at least one item.');
  const errors = validateItems(items);
  if (errors.length) throw new Error(errors.join('\n'));
  if (!/^#[0-9a-f]{6}$/i.test(brand.color))
    throw new Error('Choose a valid brand colour.');
  if (
    !brand.name.trim() ||
    brand.name.length > 24 ||
    brand.subtitle.length > 64
  )
    throw new Error(
      'Keep the brand name within 24 characters and subtitle within 64.',
    );
  const doc = new jsPDF({ unit: 'mm', format: 'a4', compress: true });
  for (const style of ['normal', 'bold', 'italic']) {
    doc.addFileToVFS(`VV-${style}.ttf`, fonts[style]);
    doc.addFont(`VV-${style}.ttf`, 'VV', style);
  }
  const accent = brand.inkSaver ? '#252525' : brand.color;
  let fresh = true,
    slot = 0,
    group = '';
  const pageRows = [],
    manifest = [];
  const font = (size = 11, style = 'normal', color = '#242326') => {
    doc.setFont('VV', style);
    doc.setFontSize(size);
    doc.setTextColor(color);
  };
  const text = (
    s,
    x,
    y,
    size = 11,
    style = 'normal',
    color = '#242326',
    extra = {},
  ) => {
    font(size, style, color);
    doc.text(Array.isArray(s) ? s.map(String) : String(s), x, y, extra);
  };
  const lines = (s, w, size, style = 'normal') => {
    font(size, style);
    return doc.splitTextToSize(String(s), w);
  };
  function reverseCenteredText(s, cx, y, size, style, color) {
    font(size, style, color);
    // At 180 degrees text extends left from its anchor. jsPDF applies
    // align: 'center' before rotating, which shifts the whole line left.
    doc.text(s, cx + doc.getTextWidth(s) / 2, y, { angle: 180 });
  }
  function fitted(s, w, h, start = 12, min = 10, style = 'normal') {
    for (let size = start; size >= min; size -= 0.5) {
      const l = lines(s, w, size, style),
        lineHeight = size * MM * 1.32;
      if (l.length * lineHeight <= h) return { lines: l, size, lineHeight };
    }
    return null;
  }
  // The laboratory report: the exact clue text sits in one unbroken block, with the official
  // furniture of a police laboratory report above and below it. The laboratory and its reference
  // numbers are invented for the game.
  function drawLabReport(item, x, y, w, h) {
    const ink = brand.inkSaver ? '#252525' : '#1f2b44',
      stamp = brand.inkSaver ? '#252525' : accent,
      rule = '#8a8f9c',
      L = x + 14,
      R = x + w - 14,
      cx = x + w / 2;
    doc.setDrawColor(ink);
    doc.setLineWidth(0.7);
    doc.rect(x + 2, y + 2, w - 4, h - 4);
    doc.setLineWidth(0.2);
    doc.rect(x + 4, y + 4, w - 8, h - 8);
    // Letterhead: crest, name, section.
    doc.setLineWidth(0.5);
    doc.circle(L + 9, y + 22, 8.5);
    doc.setLineWidth(0.2);
    doc.circle(L + 9, y + 22, 7);
    text('FS', L + 9, y + 24, 12, 'bold', ink, { align: 'center' });
    text('NAILSWORTH & STROUD', cx + 8, y + 17, 15, 'bold', ink, { align: 'center' });
    text('FORENSIC SCIENCE LABORATORY', cx + 8, y + 24, 15, 'bold', ink, { align: 'center' });
    text('Toxicology and Trace Evidence Section  ·  Gloucestershire', cx + 8, y + 30, 8.5, 'normal', '#4b5160', {
      align: 'center',
    });
    doc.setDrawColor(ink);
    doc.setLineWidth(0.8);
    doc.line(L, y + 36, R, y + 36);
    doc.setLineWidth(0.2);
    doc.line(L, y + 37.6, R, y + 37.6);
    // Classification band.
    doc.setDrawColor(stamp);
    doc.setLineWidth(0.4);
    doc.rect(cx - 45, y + 42, 90, 7);
    text('CONFIDENTIAL  —  POLICE USE ONLY', cx, y + 46.8, 9.5, 'bold', stamp, { align: 'center' });
    // Reference table.
    const rows = [
      ['Laboratory ref.', 'NSFL / 86 / 1010 / VV', 'Subject', 'Vincent Vale (deceased)'],
      ['Submitted by', 'Inspector Donna Reed', 'Date of report', '10 October 1986'],
      ['Examined by', 'Duty Forensic Scientist', 'Copy', 'Original, 1 of 1'],
    ];
    const ty = y + 55,
      rh = 8,
      c1 = 30,
      c2 = 60,
      c3 = 28;
    doc.setDrawColor(rule);
    doc.setLineWidth(0.25);
    doc.rect(L, ty, R - L, rh * rows.length);
    rows.forEach((row, i) => {
      const ry = ty + i * rh;
      if (i) doc.line(L, ry, R, ry);
      doc.line(L + c1, ty, L + c1, ty + rh * rows.length);
      doc.line(L + c1 + c2, ty, L + c1 + c2, ty + rh * rows.length);
      doc.line(L + c1 + c2 + c3, ty, L + c1 + c2 + c3, ty + rh * rows.length);
      text(row[0], L + 2, ry + 5.2, 8, 'bold', '#4b5160');
      text(row[1], L + c1 + 2, ry + 5.2, 9, 'normal', ink);
      text(row[2], L + c1 + c2 + 2, ry + 5.2, 8, 'bold', '#4b5160');
      text(row[3], L + c1 + c2 + c3 + 2, ry + 5.2, 9, 'normal', ink);
    });
    // The report itself: the unbroken clue text.
    const [heading, subject, ...rest] = item.content.split('\n');
    let by = ty + rh * rows.length + 14;
    text(heading, cx, by, 20, 'bold', ink, { align: 'center' });
    text(subject, cx, by + 8, 12, 'normal', ink, { align: 'center' });
    doc.setDrawColor(ink);
    doc.setLineWidth(0.3);
    doc.line(cx - 40, by + 12, cx + 40, by + 12);
    const body = rest.join('\n').trim();
    const fit = fitted(body, R - L - 4, 100, 11.5, 10);
    if (!fit) throw new Error('Text does not fit. Use the full-page layout for this selection.');
    text(fit.lines, L + 2, by + 21, fit.size, 'normal', '#191919', { lineHeightFactor: 1.5 });
    // Specimen key.
    const ky = y + 192;
    text('SPECIMEN KEY', L, ky, 9, 'bold', ink);
    doc.setDrawColor(rule);
    doc.setLineWidth(0.25);
    const key = [
      ['C1', 'Silver compact marked VV (residue)'],
      ['W1', 'Wine from the private decanter and final glass'],
      ['D1', 'Separate dish'],
      ['F1', 'Fabric swab'],
    ];
    key.forEach(([id, label], i) => {
      const ry = ky + 3 + i * 6.2;
      doc.rect(L, ry, R - L, 6.2);
      doc.line(L + 14, ry, L + 14, ry + 6.2);
      text(id, L + 7, ry + 4.3, 8.5, 'bold', ink, { align: 'center' });
      text(label, L + 17, ry + 4.3, 8.5, 'normal', '#191919');
    });
    // Sign-off and stamp.
    const sy = y + h - 30;
    doc.setDrawColor(ink);
    doc.setLineWidth(0.3);
    doc.line(L, sy, L + 70, sy);
    text('Duty Forensic Scientist', L, sy + 4.5, 8.5, 'normal', '#4b5160');
    text('For and on behalf of the Laboratory', L, sy + 8.5, 7.5, 'normal', '#4b5160');
    doc.setDrawColor(stamp);
    doc.setLineWidth(0.8);
    doc.rect(R - 52, sy - 10, 50, 18);
    doc.setLineWidth(0.25);
    doc.rect(R - 50.5, sy - 8.5, 47, 15);
    text('CHECKED & ISSUED', R - 27, sy - 1.2, 9.5, 'bold', stamp, { align: 'center' });
    text('10 OCT 1986', R - 27, sy + 4, 8.5, 'bold', stamp, { align: 'center' });
    text(
      'Results relate only to the items received. This report is issued without opinion as to who handled any item.',
      cx,
      y + h - 10,
      7,
      'normal',
      '#6b7080',
      { align: 'center' },
    );
  }

  function write(
    s,
    x,
    y,
    w,
    h,
    size = 12,
    min = 10,
    style = 'normal',
    color = '#242326',
  ) {
    const fit = fitted(s, w, h, size, min, style);
    if (!fit)
      throw new Error(
        'Text does not fit. Use the full-page layout for this selection.',
      );
    text(fit.lines, x, y + fit.size * MM, fit.size, style, color, {
      lineHeightFactor: 1.32,
    });
    return fit.lines.length * fit.lineHeight;
  }
  function courseLine(label, value) {
    const shortValue = String(value || 'Not supplied')
      .replace(/\s+[–-]\s+.*$/, '')
      .replace(/\s*\([^)]*\)\s*$/, '')
      .trim();
    return `${label}: ${shortValue}`;
  }
  function placeMenuText(item) {
    const menu = item.menu ?? {};
    if (menu.missing) return 'Menu choices to confirm';
    // No menu recorded for anyone (the sample roster has none): print no menu lines at all.
    if (!menu.starter && !menu.main && !menu.dessert) return '';
    return [
      courseLine('Starter', menu.starter),
      courseLine('Main', menu.main),
      courseLine('Dessert', menu.dessert),
    ].join('\n');
  }
  function next(orientation = 'portrait', format = 'a4') {
    if (!fresh) doc.addPage(format, orientation);
    fresh = false;
    slot = 0;
  }
  function brandLine(x, y, w) {
    text(brand.name, x, y, 13, 'bold', accent);
    doc.setDrawColor(accent);
    doc.setLineWidth(0.6);
    doc.line(x, y + 3, x + w, y + 3);
  }
  function trim(x, y, w, h, badge = false) {
    if (!brand.cutMarks) return;
    doc.setDrawColor(badge ? '#4e454a' : '#a5a0a2');
    doc.setLineWidth(badge ? 0.25 : 0.15);
    for (const [cx, cy, sx, sy] of [
      [x, y, -1, -1],
      [x + w, y, 1, -1],
      [x, y + h, -1, 1],
      [x + w, y + h, 1, 1],
    ]) {
      doc.line(cx + sx * 0.7, cy, cx + sx * 2.5, cy);
      doc.line(cx, cy + sy * 0.7, cx, cy + sy * 2.5);
    }
  }  // Reference documents are written in Markdown. Render the common constructs rather than
  // printing their punctuation: headings, tables, bullets, block quotes, rules and bold runs.
  const mdRuns = (s) => {
    const runs = [];
    const token = /(\*\*\*[^*]+\*\*\*|\*\*[^*]+\*\*|\*[^*\n]+\*)/g;
    let last = 0, m;
    while ((m = token.exec(s))) {
      if (m.index > last) runs.push({ t: s.slice(last, m.index), style: 'normal' });
      // The embedded family has no bold italic, so ***strong emphasis*** prints bold.
      runs.push({ t: m[0].replace(/^\*+|\*+$/g, ''), style: m[0].startsWith('**') ? 'bold' : 'italic' });
      last = m.index + m[0].length;
    }
    if (last < s.length) runs.push({ t: s.slice(last), style: 'normal' });
    return runs.filter((r) => r.t);
  };
  const wrapRuns = (runs, width, size) => {
    const out = [];
    let line = [], used = 0;
    for (const run of runs)
      for (const part of run.t.split(/(\s+)/)) {
        if (!part) continue;
        font(size, run.style);
        const w = doc.getTextWidth(part);
        if (used + w > width && line.length && part.trim()) { out.push(line); line = []; used = 0; }
        if (!line.length && !part.trim()) continue;
        line.push({ t: part, style: run.style, w });
        used += w;
      }
    if (line.length) out.push(line);
    return out.length ? out : [[]];
  };
  const drawRuns = (line, x, y, size, color) => {
    let cx = x;
    for (const r of line) { text(r.t, cx, y, size, r.style, color); cx += r.w; }
  };
  const mdCells = (row) => row.trim().replace(/^\||\|$/g, '').split('|').map((c) => c.trim());
  const isDivider = (row) => mdCells(row).every((c) => /^:?-{2,}:?$/.test(c));

  function paginateReference(item) {
    const L = 16, W = 178, BOTTOM = 277, LH = 5.2;
    let y = 0;
    const newPage = () => { next(); brandLine(L, 20, W); y = 34; };
    const room = (h) => { if (y + h > BOTTOM) newPage(); };

    next();
    brandLine(L, 20, W);
    y = 32;
    text(item.title, L, y, 16, 'bold', accent);
    y += 12;

    const src = item.content.split('\n');
    if (/^#\s/.test(src[0] || '')) src.shift();   // its H1 repeats the title above
    for (let i = 0; i < src.length; i++) {
      const raw = src[i];
      if (!raw.trim()) { y += 3; continue; }

      if (/^\s*-{3,}\s*$/.test(raw)) {
        room(8);
        doc.setDrawColor('#c9c4c6'); doc.setLineWidth(0.3);
        doc.line(L, y - 1, L + W, y - 1);
        y += 5;
        continue;
      }

      if (raw.trim().startsWith('|')) {
        const rows = [];
        while (i < src.length && src[i].trim().startsWith('|')) {
          if (!isDivider(src[i])) rows.push(mdCells(src[i]));
          i++;
        }
        i--;
        drawMarkdownTable(rows);
        continue;
      }

      const heading = /^(#{1,6})\s+(.*)$/.exec(raw);
      if (heading) {
        const level = heading[1].length;
        const size = level === 1 ? 14 : level === 2 ? 12.5 : 11.5;
        y += level === 1 ? 5 : 3.5;
        // Never leave a heading stranded at the foot of a page.
        room(size + LH * 2);
        const bold = mdRuns(heading[2]).map((r) => ({ ...r, style: 'bold' }));
        drawRuns(wrapRuns(bold, W, size)[0], L, y, size, level <= 2 ? accent : '#242326');
        y += size * 0.62 + 2.5;
        continue;
      }

      const bullet = /^\s*[-*]\s+(.*)$/.exec(raw);
      const quote = /^>\s?(.*)$/.exec(raw);
      const indent = bullet ? 5 : quote ? 7 : 0;
      for (const [n, line] of wrapRuns(mdRuns(bullet ? bullet[1] : quote ? quote[1] : raw), W - indent, 11).entries()) {
        room(LH + 1);
        if (bullet && n === 0) text('•', L + 1, y, 11, 'normal', accent);
        if (quote) {
          doc.setDrawColor(accent); doc.setLineWidth(0.6);
          doc.line(L + 2.5, y - 3.6, L + 2.5, y + 1.2);
        }
        drawRuns(line, L + indent, y, 11, '#242326');
        y += LH;
      }
      if (bullet || quote) y += 0.4;
    }

    function drawMarkdownTable(rows) {
      const columns = Math.max(...rows.map((r) => r.length));
      const gap = 4;
      const natural = [];
      for (let c = 0; c < columns; c++) {
        let max = 0;
        rows.forEach((r, index) => {
          font(11, index === 0 ? 'bold' : 'normal');
          max = Math.max(max, doc.getTextWidth((r[c] || '').replace(/\*/g, '')));
        });
        natural.push(Math.max(max, 10));
      }
      const usable = W - gap * (columns - 1);
      const total = natural.reduce((a, b) => a + b, 0);
      const widths = natural.map((w) => (total > usable ? (w / total) * usable : w));
      y += 1.5;
      rows.forEach((row, index) => {
        const cells = row.map((cell, c) => {
          const runs = mdRuns(cell);
          return wrapRuns(index === 0 ? runs.map((r) => ({ ...r, style: 'bold' })) : runs,
            widths[c] || 10, 10.5);
        });
        const height = Math.max(...cells.map((c) => c.length)) * LH;
        room(height + 3);
        let x = L;
        cells.forEach((cell, c) => {
          cell.forEach((line, n) =>
            drawRuns(line, x, y + n * LH, 10.5, index === 0 ? accent : '#242326'));
          x += (widths[c] || 10) + gap;
        });
        y += height;
        if (index === 0) {
          doc.setDrawColor(accent); doc.setLineWidth(0.4);
          doc.line(L, y - 3, L + W, y - 3);
          y += 1;
        }
      });
      y += 3;
    }
  }
  // Letter-spaced text. jsPDF aligns text before applying charSpace, so a right-aligned or
  // centred spaced line would drift; measure the spaced width and place it by hand.
  function spaced(s, x, y, size, style, color, space, align = 'left') {
    font(size, style, color);
    const w = doc.getTextWidth(s) + space * (s.length - 1);
    doc.text(s, align === 'right' ? x - w : align === 'center' ? x - w / 2 : x, y, { charSpace: space });
  }
  // A C5 envelope (229 x 162 mm), printed directly on its front: one clue card goes inside.
  // Everything stays at least 12 mm from the edges, clear of where envelopes skew in the feed.
  // An alignment envelope shows the safe area so the first run can check the tray.
  function drawEnvelope(item) {
    const W = 229, H = 162, M = 12, muted = brand.inkSaver ? '#555555' : '#6a5960';
    if (item.alignment) {
      doc.setDrawColor(accent);
      doc.setLineWidth(0.3);
      doc.setLineDashPattern([2, 1.5], 0);
      doc.rect(M, M, W - M * 2, H - M * 2);
      doc.setLineDashPattern([], 0);
      doc.setLineWidth(0.2);
      doc.line(W / 2 - 6, H / 2, W / 2 + 6, H / 2);
      doc.line(W / 2, H / 2 - 6, W / 2, H / 2 + 6);
      for (const mm of [5, 10]) {
        doc.line(mm, H / 2 - 3, mm, H / 2 + 3);
        doc.line(W - mm, H / 2 - 3, W - mm, H / 2 + 3);
        doc.line(W / 2 - 3, mm, W / 2 + 3, mm);
        doc.line(W / 2 - 3, H - mm, W / 2 + 3, H - mm);
      }
      text('TOP EDGE', W / 2, M + 7, 9, 'bold', accent, { align: 'center' });
      text('ENVELOPE TEST · C5 · 229 x 162 mm', W / 2, H / 2 - 14, 13, 'bold', accent, { align: 'center' });
      text([
        'The dashed box is 12 mm in from every edge, where the printing stays.',
        'The short ticks at each edge are 5 mm and 10 mm in.',
        'If the box is whole and square to the edges, the clue envelopes will print correctly.',
        'If TOP EDGE is at the bottom, turn the envelopes round in the tray.',
      ], W / 2, H / 2 + 14, 9, 'normal', '#242326', { align: 'center', lineHeightFactor: 1.5 });
      return;
    }
    const ink = '#242326', clueId = item.clueId ?? item.id.replace(/^label-r\d+-/, '');
    // Branding, top left: the Vale Meridian logo artwork when supplied, otherwise the name-badge
    // logo (white on a theme-colour block); the strapline sits underneath either way.
    if (options.logo) {
      const lw = 80, lh = lw * 731 / 2000;
      doc.addImage(options.logo, 'PNG', W - M - 2 - lw, M + 2, lw, lh);
      spaced(brand.subtitle.toUpperCase(), W - M - 2, M + 2 + lh + 6, 6.5, 'bold', muted, 0.7, 'right');
    } else {
    font(22, 'bold');
    const logoW = doc.getTextWidth(brand.name) + 14;
    if (!brand.inkSaver) {
      doc.setFillColor(accent);
      doc.rect(M + 2, M + 2, logoW, 14, 'F');
    }
    text(brand.name, M + 2 + logoW / 2, M + 12, 22, 'bold', brand.inkSaver ? accent : '#ffffff', { align: 'center' });
    spaced(brand.subtitle.toUpperCase(), M + 2, M + 21.5, 6.5, 'bold', muted, 0.7);
    }

    // Left: the round, large, because envelopes are sorted and handed out by it.
    const rx = M + 20;
    spaced('ROUND', rx, 72, 8, 'bold', muted, 1.2, 'center');
    text(item.round === null ? '·' : String(item.round), rx, 98, 66, 'bold', accent, { align: 'center' });
    doc.setDrawColor(accent);
    doc.setLineWidth(0.4);
    doc.line(M + 44, 63, M + 44, 108);

    // The recipient: the character leads, as everybody wears it on a badge; the guest confirms it.
    const ax = M + 54, aw = W - M - 2 - ax;
    spaced('TO BE OPENED BY', ax, 72, 7, 'bold', muted, 0.9);
    const nameFit = fitted(item.character, aw, 24, 28, 18, 'bold');
    if (!nameFit) throw new Error(`Envelope name does not fit: ${item.character}`);
    text(nameFit.lines, ax, 85, nameFit.size, 'bold', accent, { lineHeightFactor: 1.32 });
    const below = 85 + (nameFit.lines.length - 1) * nameFit.lineHeight;
    text(item.guest, ax, below + 10, 13, 'normal', ink);
    spaced(`TABLE ${item.table}`, ax, below + 17.5, 8.5, 'bold', muted, 0.8);

    // What goes inside, just above the foot, as a reminder while the envelopes are filled.
    if (item.enclosures?.length) {
      const enclose = fitted(`Enclose: ${item.enclosures.join('  ·  ')}`, W - M * 2 - 4, 9, 8, 6, 'bold');
      if (!enclose) throw new Error(`Envelope enclosures do not fit: ${item.id}`);
      text(enclose.lines, M + 2, H - M - 14 - (enclose.lines.length - 1) * enclose.lineHeight,
        enclose.size, 'bold', muted, { lineHeightFactor: 1.32 });
    }
    // The foot: a double rule, the occasion and the venue, and the clue ID small in the corner.
    doc.setDrawColor(accent);
    doc.setLineWidth(0.6);
    doc.line(M + 2, H - M - 10.5, W - M - 2, H - M - 10.5);
    doc.setLineWidth(0.2);
    doc.line(M + 2, H - M - 9.2, W - M - 2, H - M - 9.2);
    const occasion = footer.occasion;
    spaced(occasion, M + 2, H - M - 3, 7.5, 'bold', accent, 0.5);
    font(7.5, 'bold');
    const after = M + 2 + doc.getTextWidth(occasion) + 0.5 * occasion.length;
    if (footer.venue) spaced('·  ' + footer.venue, after + 2, H - M - 3, 7.5, 'normal', muted, 0.5);
    spaced(clueId, W - M - 2, H - M - 3, 6, 'normal', muted, 0.3, 'right');
  }
  // The front of a table's A4 (C4) envelope for Rounds 2 and 3, printed on A4 landscape and stuck
  // on. It sits on the table before the round: the instruction not to open it leads, then what is
  // inside, so the GM can check it is complete and every guest can see their name.
  function drawTableEnvelope(item) {
    const W = 297, H = 210, M = 14, muted = brand.inkSaver ? '#555555' : '#6a5960', ink = '#242326';
    if (options.logo) {
      const lw = 84, lh = lw * 731 / 2000;
      doc.addImage(options.logo, 'PNG', W - M - lw, M, lw, lh);
      spaced(brand.subtitle.toUpperCase(), W - M, M + lh + 5, 7, 'bold', muted, 0.7, 'right');
    } else spaced(brand.name, W - M, M + 12, 20, 'bold', accent, 0.9, 'right');
    // The table and round, large, top left.
    spaced('TABLE', M, M + 8, 10, 'bold', muted, 1.4);
    text(String(item.table), M, M + 38, 80, 'bold', accent);
    spaced(`ROUND ${item.round}`, M + 42, M + 38, 22, 'bold', accent, 1.2);
    // The instruction, white on a theme-colour band (an outline in ink-saver mode).
    const by = 66, bh = 17;
    if (!brand.inkSaver) { doc.setFillColor(accent); doc.rect(M, by, W - M * 2, bh, 'F'); }
    else { doc.setDrawColor(accent); doc.setLineWidth(0.8); doc.rect(M, by, W - M * 2, bh); }
    const on = brand.inkSaver ? accent : '#ffffff';
    spaced('PLEASE DO NOT OPEN', M + 8, by + 11.3, 16, 'bold', on, 1.2);
    text(`until the Game Master announces Round ${item.round}.`, M + 104, by + 11.3, 15, 'normal', on);
    // What is inside.
    spaced(`INSIDE: ${item.contents.length} CLUE ENVELOPES`, M, 98, 9, 'bold', muted, 1);
    const rows = Math.ceil(item.contents.length / 2), colW = (W - M * 2) / 2;
    if (rows > 6) throw new Error(`Too many envelopes for one table envelope: ${item.id}`);
    item.contents.forEach((c, i) => {
      const cx = M + (i < rows ? 0 : colW), cy = 108 + (i % rows) * 11;
      const fit = fitted(c.character, colW - 70, 6, 13, 9, 'bold');
      text(fit.lines[0], cx, cy, fit.size, 'bold', accent);
      font(fit.size, 'bold');
      text(c.guest, cx + doc.getTextWidth(fit.lines[0]) + 3, cy, 11, 'normal', ink);
    });
    const fy = 108 + rows * 11 + 2;
    text('When it is announced, open this envelope and hand each clue envelope to the person named on it.',
      M, Math.max(fy + 4, 180), 11, 'normal', ink);
    // The foot, as on the clue envelopes.
    doc.setDrawColor(accent);
    doc.setLineWidth(0.6);
    doc.line(M, H - M - 10.5, W - M, H - M - 10.5);
    doc.setLineWidth(0.2);
    doc.line(M, H - M - 9.2, W - M, H - M - 9.2);
    spaced(footer.occasion, M, H - M - 3, 8, 'bold', accent, 0.5);
    if (footer.venue) spaced(footer.venue, W - M, H - M - 3, 8, 'normal', muted, 0.5, 'right');
  }
  // The guest "Find your table" sheet: a small plan of the floor, then the eight tables by name.
  // Portrait A4, no characters, no seat numbers, nothing that gives the game away.
  function drawTablePlan(item) {
    const plan = item.tablePlan, W = 210, muted = '#6a5960', rule = '#d6c4ca';
    text(brand.name, W / 2, 16, 26, 'bold', accent, { align: 'center' });
    text(brand.subtitle.toUpperCase(), W / 2, 21, 7, 'bold', accent, { align: 'center' });
    text('Find your table', W / 2, 32, 16, 'bold', '#242326', { align: 'center' });

    // Floor plan, scaled to fit its corner and never wider than the space beside the captions.
    const xs = plan.outline.map(p => p[0]), ys = plan.outline.map(p => p[1]);
    const w = Math.max(...xs) - Math.min(...xs), h = Math.max(...ys) - Math.min(...ys);
    const s = Math.min(42 / w, 46 / h), ox = 26 - Math.min(...xs) * s, oy = 40 - Math.min(...ys) * s;
    const at = (x, y) => [ox + x * s, oy + y * s];
    doc.setDrawColor(rule);
    doc.setFillColor('#f8f1f3');
    doc.setLineWidth(0.4);
    const [x0, y0] = at(...plan.outline[0]);
    const path = plan.outline.slice(1).map(([x, y]) => {
      const [px, py] = at(x, y);
      return { op: 'l', c: [px, py] };
    });
    doc.path([{ op: 'm', c: [x0, y0] }, ...path, { op: 'h' }]).fillStroke();
    for (const table of plan.tables) {
      const [cx, cy] = at(table.x, table.y);
      doc.setFillColor('#ffffff');
      doc.circle(cx, cy, 3.4, 'FD');
      text(String(table.number), cx, cy + 1.2, 8, 'bold', '#242326', { align: 'center' });
    }

    // Captions beside the plan, one block per room, in the order the rooms were recorded.
    let y = 46;
    for (const [key, room] of Object.entries(plan.rooms)) {
      const numbers = plan.roomTables[key] ?? [];
      if (!numbers.length) continue;
      text(room.name, 80, y, 12, 'bold', '#242326');
      y += 6;
      text(numbers.length === 1 ? `Table ${numbers[0]}`
        : `Tables ${numbers.slice(0, -1).join(', ')} and ${numbers[numbers.length - 1]}`,
        80, y, 10.5, 'normal', '#242326');
      y += room.caption ? 5 : 11;
      if (room.caption) { text(room.caption, 80, y, 9, 'normal', muted); y += 11; }
    }

    doc.setDrawColor(rule);
    doc.setLineWidth(0.3);
    doc.line(14, 93, W - 14, 93);

    // Two columns of tables, each block kept whole, in table order down then across. The rows
    // are measured against the space available so the longest tables cannot run off the page.
    const columns = [14, 112], head = 6.5, gap = 5, footer = 283, top0 = 100;
    const pairs = [];
    for (let i = 0; i < plan.tables.length; i += 2) pairs.push(plan.tables.slice(i, i + 2));
    const guestRows = pairs.reduce((n, pair) => n + Math.max(...pair.map(t => t.guests.length)), 0);
    const lead = Math.min(5.1, (footer - top0 - pairs.length * (head + gap)) / guestRows);
    const size = lead < 4.4 ? 9.5 : 10.5;
    let top = top0;
    for (const pair of pairs) {
      for (const [n, table] of pair.entries()) {
        const x = columns[n];
        text(`Table ${table.number}`, x, top, 13, 'bold', accent);
        font(13, 'bold');
        text(plan.rooms[table.room].short ?? plan.rooms[table.room].name,
          x + doc.getTextWidth(`Table ${table.number}`) + 4, top - 0.3, 8, 'normal', muted);
        table.guests.forEach((guest, g) =>
          text(guest, x, top + head + g * lead, size, 'normal', '#242326'));
      }
      top += head + Math.max(...pair.map(t => t.guests.length)) * lead + gap;
    }
    text(`${plan.hosts}  |  ${plan.date}  |  ${plan.venue}`, W / 2, 289, 8, 'normal', accent,
      { align: 'center' });
  }
  // Working documents for laying the room out on the day. Landscape A4: the whole floor on one
  // page, then one page per table with every chair placed, so a place card can be walked round.
  // Top of every drawing is 12 o'clock, which is the far wall of the beamed main room.
  const CHAIR = 0.55;   // metres beyond the tabletop for an occupied chair
  function planScale(plan, box) {
    const pad = Math.max(...plan.tables.map(t => t.diameter / 2 + CHAIR));
    const xs = plan.outline.map(p => p[0]), ys = plan.outline.map(p => p[1]);
    const [x0, x1] = [Math.min(...xs) - pad, Math.max(...xs) + pad];
    const [y0, y1] = [Math.min(...ys) - pad, Math.max(...ys) + pad];
    const s = Math.min(box.w / (x1 - x0), box.h / (y1 - y0));
    return { s, at: (x, y) => [box.x + (x - x0) * s, box.y + (y - y0) * s] };
  }
  const seatPoint = (cx, cy, radius, angle) => {
    const r = ((angle - 90) * Math.PI) / 180;   // 0 degrees is the top of the drawing
    return [cx + radius * Math.cos(r), cy + radius * Math.sin(r)];
  };

  function planHeader(title, subtitle) {
    text(brand.name, 283, 17, 15, 'bold', accent, { align: 'right' });
    text(brand.subtitle.toUpperCase(), 283, 22, 6.5, 'bold', accent, { align: 'right' });
    doc.setDrawColor(accent);
    doc.setLineWidth(0.5);
    doc.line(14, 26, 283, 26);
    text(title, 14, 18, 19, 'bold', accent);
    if (subtitle) text(subtitle, 14, 24, 9.5, 'normal', '#6a5960');
  }

  function drawRoomPlan(item) {
    const plan = item.roomPlan, muted = '#6a5960', rule = '#c9c4c6';
    planHeader('Proposed room layout and seating',
      `${plan.tables.reduce((n, t) => n + t.seats.length, 0)} guests  ·  ${plan.tables.length} round tables  ·  ${plan.venue}  ·  ${plan.date}`);
    const { s, at } = planScale(plan, { x: 16, y: 36, w: 150, h: 156 });
    doc.setDrawColor(rule); doc.setFillColor('#f8f1f3'); doc.setLineWidth(0.4);
    const [ox, oy] = at(...plan.outline[0]);
    doc.path([{ op: 'm', c: [ox, oy] },
      ...plan.outline.slice(1).map(([x, y]) => ({ op: 'l', c: at(x, y) })),
      { op: 'h' }]).fillStroke();
    for (const table of plan.tables) {
      const [cx, cy] = at(table.x, table.y);
      const top = table.diameter / 2 * s, ring = (table.diameter / 2 + CHAIR) * s;
      doc.setDrawColor('#e4dcdf'); doc.setFillColor('#eef2f4'); doc.setLineWidth(0.2);
      doc.circle(cx, cy, ring, 'FD');
      doc.setDrawColor(rule); doc.setFillColor('#dfe7ea'); doc.setLineWidth(0.3);
      doc.circle(cx, cy, top, 'FD');
      for (const seat of table.seats) {
        const [sx, sy] = seatPoint(cx, cy, (top + ring) / 2, seat.angle);
        doc.setFillColor(accent);
        doc.circle(sx, sy, 0.7, 'F');
      }
      text(`T${table.number}`, cx, cy + 1.6, 11, 'bold', '#242326', { align: 'center' });
    }
    text('TOP OF PLAN — FAR WALL OF THE BEAMED MAIN ROOM', 16 + 75, 33, 7.5, 'bold', muted, { align: 'center' });

    let y = 41;
    text('Rooms and tables', 180, y, 12, 'bold', '#242326'); y += 7;
    for (const [key, room] of Object.entries(plan.rooms)) {
      const list = plan.tables.filter(t => t.room === key).map(t => t.number);
      if (!list.length) continue;
      text(`${room.name}: ${list.join(', ')}`, 180, y, 10, 'normal', '#242326'); y += 5.5;
      if (room.caption) { text(room.caption, 180, y, 9, 'normal', muted); y += 5.5; }
    }
    y += 4;
    text('Table sizes', 180, y, 12, 'bold', '#242326'); y += 7;
    for (const table of plan.tables) {
      text(`Table ${table.number}: ${table.diameter.toFixed(1)} m, ${table.seats.length} guests`,
        180, y, 10, 'normal', '#242326');
      y += 5.2;
    }
    text(`${brand.name}  ·  room layout  ·  positions are provisional`, 14, 203, 8, 'normal', accent);
    // One document, so it can be printed once and carried round: the floor, then every table.
    for (const table of [...plan.tables].sort((a, b) => a.number - b.number)) {
      next('landscape');
      drawTableDiagram(plan, table);
    }
  }

  function drawTableDiagram(plan, table) {
    const muted = '#6a5960';
    const room = plan.rooms[table.room];
    planHeader(`Table ${table.number}`,
      `${room.name}  ·  ${table.seats.length} guests  ·  ${table.diameter.toFixed(1)} m table`);
    text('Set the place cards to match. The top of this page is the far wall of the beamed main room.',
      14, 33, 9.5, 'normal', '#242326');

    const cx = 105, cy = 122, top = 34, ring = 46;
    doc.setDrawColor('#e4dcdf'); doc.setFillColor('#f4f7f8'); doc.setLineWidth(0.3);
    doc.circle(cx, cy, ring, 'FD');
    doc.setDrawColor('#c9c4c6'); doc.setFillColor('#dfe7ea'); doc.setLineWidth(0.4);
    doc.circle(cx, cy, top, 'FD');
    text(`T${table.number}`, cx, cy + 2, 15, 'bold', '#242326', { align: 'center' });
    // 12 o'clock marker
    doc.setDrawColor(accent); doc.setLineWidth(0.5);
    doc.line(cx, cy - ring - 4, cx, cy - ring - 9);
    text('12', cx, cy - ring - 11, 8, 'bold', accent, { align: 'center' });

    for (const seat of table.seats) {
      const [sx, sy] = seatPoint(cx, cy, (top + ring) / 2, seat.angle);
      doc.setDrawColor(accent); doc.setFillColor('#ffffff'); doc.setLineWidth(0.4);
      doc.circle(sx, sy, 4.2, 'FD');
      text(String(seat.seat), sx, sy + 1.4, 9, 'bold', accent, { align: 'center' });
      // Name outside the chair ring, on whichever side the chair sits.
      const [lx, ly] = seatPoint(cx, cy, ring + 9, seat.angle);
      const side = Math.sin(((seat.angle - 90) * Math.PI) / 180);
      const align = Math.abs(side) < 0.999 && lx < cx - 1 ? 'right' : lx > cx + 1 ? 'left' : 'center';
      text(seat.guest, lx, ly, 11, 'bold', '#242326', { align });
      text(seat.character, lx, ly + 4.4, 9, 'normal', muted, { align });
    }
    let y = 45;
    text('Clockwise from 12', 236, y, 11, 'bold', '#242326'); y += 7;
    for (const seat of [...table.seats].sort((a, b) => a.angle - b.angle)) {
      text(`${clockFace(seat.angle)}`, 236, y, 9.5, 'bold', accent);
      text(seat.guest, 251, y, 9.5, 'normal', '#242326');
      y += 5.4;
    }
    text(`${brand.name}  ·  ${plan.venue}  ·  ${plan.date}`, 14, 203, 8, 'normal', accent);
  }
  const clockFace = (angle) => {
    const minutes = Math.round((angle / 360) * 720) % 720;
    const hour = Math.floor(minutes / 60) || 12;
    return `${hour}:${String(minutes % 60).padStart(2, '0')}`;
  };
  function drawSeatingPlan(item) {
    const plan = item.seatingPlan;
    const count = plan.tables.reduce((n, t) => n + t.seats.length, 0);
    text(brand.name, 12, 18, 15, 'bold', accent);
    text(plan.hosts, 285, 18, 10, 'normal', accent, { align: 'right' });
    text('Seating plan', 12, 32, 25, 'bold', accent);
    text(brand.subtitle, 12, 40, 9, 'normal', accent);
    text(`${plan.date}  /  ${plan.venue}`, 285, 40, 9, 'normal', '#625b60', { align: 'right' });
    doc.setDrawColor(accent);
    doc.setLineWidth(0.6);
    doc.line(12, 46, 285, 46);
    for (const [index, table] of plan.tables.entries()) {
      const left = 12 + (index % 4) * 69.75;
      const top = 54 + Math.floor(index / 4) * 75;
      text(`TABLE ${table.number}`, left, top + 5, 12, 'bold', accent);
      text(`${table.seats.length} guests`, left + 63.75, top + 5, 8, 'normal', '#625b60', { align: 'right' });
      doc.setDrawColor('#c9b9bf');
      doc.setLineWidth(0.2);
      doc.line(left, top + 8, left + 63.75, top + 8);
      for (const [index, seat] of table.seats.entries()) {
        const baseline = top + 14 + index * 6;
        if (baseline + 3 > top + 67)
          throw new Error(`Table ${table.number} has too many seats for the seating plan.`);
        text(seat.seat, left, baseline, 8, 'normal', '#625b60');
        // Keep every name on one line so seat rows stay aligned.
        const single = (value, y, size, min, style, color) => {
          while (size >= min) {
            font(size, style, color);
            if (doc.getTextWidth(value) <= 57.75) {
              text(value, left + 6, y, size, style, color);
              return;
            }
            size -= 0.5;
          }
          throw new Error(`Seating plan name does not fit: ${value}`);
        };
        single(seat.guest, baseline, 10, 9, 'bold', '#242326');
        single(seat.character, baseline + 3, 7.5, 7, 'normal', '#625b60');
      }
    }
    text(`${count} guests  /  ${plan.tables.length} tables  /  Numbers beside names show seat order`, 12, 200, 8, 'normal', '#625b60');
  }
  for (const item of sortItems(items, options.sort)) {
    const template = item.template;
    const full =
      (options.fullPage || options.largePrint || item.id === 'CLUE_VER_R4') &&
      ['card', 'divider', 'taxi', 'report', 'slip'].includes(template);
    // Large print: one card per A4 page with type about twice the usual size, for a
    // partially sighted guest.
    const large = options.largePrint && full && template === 'card';
    const config =
      template === 'seating-plan'
        ? [297, 210, 1, 1]
        : template === 'table-plan'
        ? [210, 297, 1, 1]
        : template === 'room-plan'
        ? [297, 210, 1, 1]
        : template === 'table'
        ? [210, 297, 1, 1]
        : template === 'label'
        ? [63.5, 46.6, 3, 6]
        : template === 'envelope'
        ? [229, 162, 1, 1]
        : template === 'table-envelope'
        ? [297, 210, 1, 1]
        : template === 'badge'
        ? [90, 56, 2, 4]
        : template === 'money'
        ? [130, 130 * item.imageHeight / item.imageWidth, 2, 3]
        : template === 'photo'
          ? item.photoSize === 'document'
            ? [186, 134, 1, 2]
            : [95, 124, 2, 2]
        : ['note', 'qnote'].includes(template)
          ? [148, 210, 2, 1]
          : template === 'place'
            ? [90, 80, 2, 3]
            : template === 'ballot'
              ? [90, 80, 2, 3]
              : ['report', 'table', 'reference'].includes(template) || full
                ? [186, 267, 1, 1]
                : [186, 130, 1, 2];
    const [w, h, cols, rows] = config;
    // Private material, different rounds and evidence start separate sheets.
    const key = [item.category, template, item.round, item.private, full].join(
      ':',
    );
    if (key !== group) {
      slot = 0;
      group = key;
      fresh = false;
    }
    const firstPage = doc.getNumberOfPages() + (slot === 0 && !fresh ? 1 : 0);
    for (let copy = 0; copy < item.quantity; copy++) {
      if (template === 'reference') {
        paginateReference(item);
        slot = 0;
        continue;
      }
      const a5 = ['note', 'qnote'].includes(template);
      const whole = ['seating-plan', 'table-plan', 'room-plan', 'table'].includes(template);
      const wide = ['seating-plan', 'room-plan', 'money'].includes(template);
      const sticker = template === 'label';
      const envelope = ['envelope', 'table-envelope'].includes(template);
      if (slot === 0)
        template === 'envelope' ? next('landscape', [229, 162])
          : next(a5 || wide || envelope ? 'landscape' : 'portrait');
      const x = whole || envelope ? 0 : a5 ? slot * 149
          : sticker ? 7.25 + (slot % cols) * 66
          : 12 + (slot % cols) * (w + 6),
        y = a5 || whole || envelope ? 0
          : sticker ? 8.7 + Math.floor(slot / cols) * 46.6
          : 12 + Math.floor(slot / cols) * (h + 6);
      // Labels are die-cut, so crop marks would print onto the sticker itself.
      if (!a5 && !whole && !sticker && !envelope) trim(x, y, w, h, template === 'badge');
      if (template === 'table-plan') {
        drawTablePlan(item);
      } else if (template === 'room-plan') {
        drawRoomPlan(item);

      } else if (template === 'seating-plan') {
        drawSeatingPlan(item);
      } else if (['card', 'divider'].includes(template)) {
        const pad = 9;
        // Type sizes in points: [round label, name, name minimum, guest line, title, title
        // minimum, body, body minimum]. Large print roughly doubles the reading sizes.
        const [roundPt, namePt, nameMin, guestPt, titlePt, titleMin, bodyPt, bodyMin] = large
          ? [14, 30, 22, 16, 22, 18, 24, 18]
          : [9, 17, 12, 9, 12, 10, 12, 10];
        // Leave the paper unfilled; cream paper/card supplies the background. The design
        // matches the clue envelopes: round top left, the Vale Meridian logo top right, and the
        // anniversary line with the clue ID along the foot.
        const muted = brand.inkSaver ? '#555555' : '#6a5960';
        spaced(item.private ? 'PRIVATE · RELEASE AT CUE' : `ROUND ${item.round}`, x + pad, y + 13, roundPt + 2, 'bold', accent, 0.6);
        const lw = large ? 52 : 40, lh = lw * 731 / 2000;
        if (options.logo) doc.addImage(options.logo, 'PNG', x + w - pad - lw, y + 5, lw, lh);
        else spaced(brand.name, x + w - pad, y + 13, 13, 'bold', accent, 0.6, 'right');
        let cy = y + (large ? 30 : 25);
        cy +=
          write(
            item.character || 'Game Master',
            x + pad,
            cy,
            w - pad * 2,
            large ? 26 : 16,
            namePt,
            nameMin,
            'bold',
            accent,
          ) + 2;
        if (item.guest) {
          text(
            item.table ? `${item.guest}  /  Table ${item.table}` : item.guest,
            x + pad,
            cy + 3 + (large ? 3 : 0),
            guestPt,
          );
          cy += large ? 16 : 9;
        }
        cy +=
          write(item.title, x + pad, cy, w - pad * 2, large ? 36 : 25, titlePt, titleMin, 'bold') + (large ? 8 : 4);
        const bodyH = y + h - (item.footnote ? 19 : 14) - cy;
        if (item.content.includes('**')) {
          // **bold** runs inside the card text (a lead-in the owner wants to stand out).
          for (let pt = bodyPt; pt >= bodyMin; pt -= 0.25) {
            const lead = pt * MM * 1.32;
            const lines = item.content.split('\n\n').flatMap((p, k) =>
              [...(k ? [[]] : []), ...wrapRuns(mdRuns(p.replace(/\n/g, ' ')), w - pad * 2, pt)]);
            if (lines.length * lead <= bodyH || pt - 0.25 < bodyMin) {
              lines.forEach((ln, k) => drawRuns(ln, x + pad, cy + pt * MM + k * lead, pt, '#242326'));
              break;
            }
          }
        } else write(item.content, x + pad, cy, w - pad * 2, bodyH, bodyPt, bodyMin);
        // What is enclosed with this card, and whether it is private or shared.
        if (item.footnote) {
          font(6.5, 'bold');
          const line = doc.splitTextToSize(item.footnote, w - pad * 2)[0];
          text(line, x + pad, y + h - 14.8, 6.5, 'bold', muted);
        }
        doc.setDrawColor(accent);
        doc.setLineWidth(0.5);
        doc.line(x + pad, y + h - 11.5, x + w - pad, y + h - 11.5);
        doc.setLineWidth(0.2);
        doc.line(x + pad, y + h - 10.5, x + w - pad, y + h - 10.5);
        spaced(footer.occasion, x + pad, y + h - 6, 6.5, 'bold', accent, 0.4);
        // The clue ID, and for cross-table cards the key of their pre-printed question note.
        spaced(item.noteKey ? `${item.id} · NOTE ${item.noteKey}` : item.id, x + w - pad, y + h - 6, 6.5,
          item.noteKey ? 'bold' : 'normal', item.noteKey ? accent : muted, 0.3, 'right');
      } else if (template === 'envelope') {
        drawEnvelope(item);
      } else if (template === 'table-envelope') {
        drawTableEnvelope(item);
      } else if (template === 'label') {
        const pad = 5;
        text(brand.name, x + w / 2, y + 7, 6.5, 'bold', accent, { align: 'center' });
        text(`ROUND ${item.round}`, x + w / 2, y + 13.5, 8, 'normal', '#6a5960', { align: 'center' });
        if (item.labelKind === 'guest') {
          // One envelope per card, handed to its guest: their own name has to be the thing
          // you read across a table, with the character underneath to confirm the right card.
          const nameFit = fitted(item.guest, w - pad * 2, 15, 16, 9, 'bold');
          if (!nameFit) throw new Error(`Label name does not fit: ${item.guest}`);
          text(nameFit.lines, x + w / 2, y + 22 + (nameFit.lines.length - 1) * -2, nameFit.size,
            'bold', accent, { align: 'center', lineHeightFactor: 1.15 });
          const charFit = fitted(item.character, w - pad * 2, 8, 9, 7);
          if (!charFit) throw new Error(`Label character does not fit: ${item.character}`);
          text(charFit.lines, x + w / 2, y + 32, charFit.size, 'normal', '#242326', {
            align: 'center',
            lineHeightFactor: 1.2,
          });
          text(`Table ${item.table}`, x + w / 2, y + 41, 8, 'normal', '#6a5960', { align: 'center' });
        } else {
          text(`TABLE ${item.table}`, x + w / 2, y + 26, 22, 'bold', accent, { align: 'center' });
          text(item.content, x + w / 2, y + 33, 8, 'normal', '#242326', { align: 'center' });
          if (item.guests?.length) {
            const fit = fitted(item.guests.join(' · '), w - pad * 2, 8, 6.5, 5);
            if (fit)
              text(fit.lines, x + w / 2, y + 38 + fit.size * MM, fit.size, 'normal', '#6a5960', {
                align: 'center',
                lineHeightFactor: 1.2,
              });
          }
        }
      } else if (['badge', 'place'].includes(template)) {
        const isPlace = template === 'place';
        const top = isPlace ? y + 40 : y;
        if (isPlace) {
          doc.setDrawColor('#ccc');
          doc.setLineDashPattern([1, 1], 0);
          doc.line(x, y + 40, x + w, y + 40);
          doc.setLineDashPattern([], 0);
          reverseCenteredText(brand.name, x + w / 2, y + 35.5, 7.5, 'bold', accent);
          const menuText = placeMenuText(item);
          const menuLines = menuText
            ? menuText.split('\n').flatMap((line) => lines(line, w - 12, 6.2))
            : [];
          if (menuLines.length > 6)
            throw new Error(`Place menu does not fit: ${item.guest}`);
          menuLines.forEach((line, index) => {
            reverseCenteredText(line, x + w / 2, y + 30.5 - index * 4, 6.2, 'normal', '#242326');
          });
          if (item.hasFoodIntolerance && item.dietaryNote) {
            const dietLines = lines(`DIET: ${item.dietaryNote}`, w - 34, 4.5);
            if (dietLines.length > 4)
              throw new Error(`Place diet note does not fit: ${item.guest}`);
            dietLines.forEach((line, index) => {
              text(line, x + w - 8, y + 16 - index * 3, 4.5, 'bold', accent, {
                angle: 180,
              });
            });
          }
        }
        const brandTop = isPlace ? top + 31 : top;
        if (!brand.inkSaver) {
          doc.setFillColor(accent);
          doc.rect(x, brandTop, w, 9, 'F');
        }
        text(
          brand.name,
          x + w / 2,
          brandTop + 6,
          10,
          'bold',
          brand.inkSaver ? accent : '#ffffff',
          { align: 'center' },
        );
        const nameFit = fitted(
          item.character,
          w - 10,
          isPlace ? 16 : 23,
          isPlace ? 14 : 18,
          11,
          'bold',
        );
        if (!nameFit) throw new Error(`Name does not fit: ${item.character}`);
        text(nameFit.lines, x + w / 2, top + (isPlace ? 8 : 17), nameFit.size, 'bold', accent, {
          align: 'center',
          lineHeightFactor: 1.25,
        });
        if (!isPlace && item.description) {
          const descriptionTop =
            21 + (nameFit.lines.length - 1) * nameFit.size * MM * 1.25;
          const descriptionFit = fitted(
            item.description,
            w - 12,
            44 - descriptionTop,
            10.5,
            10,
          );
          if (!descriptionFit)
            throw new Error(
              `Badge description does not fit: ${item.character}`,
            );
          text(
            descriptionFit.lines,
            x + w / 2,
            top + descriptionTop + descriptionFit.size * MM,
            descriptionFit.size,
            'normal',
            '#242326',
            {
              align: 'center',
              lineHeightFactor: 1.32,
            },
          );
        }
        const base = top + (isPlace ? 29 : 51);
        if (isPlace && item.hasFoodIntolerance) {
          doc.setDrawColor(accent);
          doc.setLineWidth(0.2);
          doc.roundedRect(x + 5, base - 9.5, 14, 5.5, 1.2, 1.2);
          text('DIET', x + 12, base - 5.8, 5.5, 'bold', accent, {
            align: 'center',
          });
        }
        write(item.guest, x + (isPlace && item.hasFoodIntolerance ? 22 : 5), base - 5, w - (isPlace && item.hasFoodIntolerance ? 39 : 22), 8, 10, 9);
        text(`T${item.table}`, x + w - 5, base, 10, 'bold', accent, {
          align: 'right',
        });
      } else if (template === 'table') {
        // Full A4 sheet, folded at 148.5 mm into two landscape A5 faces.
        // Reflect each baseline about the fold and rotate the upper face.
        const half = h / 2;
        const faceLine = (value, baseline, size, style = 'normal', cx = w / 2) => {
          text(value, cx, half + baseline, size, style, accent, { align: 'center' });
          reverseCenteredText(String(value), w - cx, half - baseline, size, style, accent);
        };
        // The logo heads each face: upright on the lower face, turned 180 degrees on the upper.
        if (options.logo) {
          const lw = 62, lh = lw * 731 / 2000, top = 6;
          doc.addImage(options.logo, 'PNG', (w - lw) / 2, half + top, lw, lh);
          // jsPDF turns an image about its bottom-left corner, so anchor it a further two image
          // heights up for the turned copy to land in the matching place on the upper face.
          doc.addImage(options.logo, 'PNG', (w + lw) / 2, half - top - lh * 2, lw, lh, 'logo-turned', 'NONE', 180);
        } else faceLine(brand.name, 16, 21, 'bold');
        faceLine(brand.subtitle.toUpperCase(), 34, 7.5, 'bold');
        faceLine(`TABLE ${item.table}`, 50, 28, 'bold');
        const guests = item.tableGuests ?? [];
        const guestRows = Math.ceil(guests.length / 2);
        if (!guests.length || guestRows > 5) throw new Error(`Missing or excessive guests for table sign: ${item.id}`);
        guests.forEach((guest, index) => {
          const cx = index < guestRows ? 57 : 153;
          const y = 62 + (index % guestRows) * 14;
          for (const [value, offset, size, style] of [
            [guest.character, 0, 12, 'bold'],
            [`(${guest.guest})`, 5, 10.5, 'normal'],
            [guest.flags.join(' · '), 10, 8.5, 'bold'],
          ]) {
            if (!value) continue;
            const fit = fitted(value, 86, 6, size, 8, style);
            if (!fit || fit.lines.length !== 1) throw new Error(`Text too long for table sign: ${value}`);
            faceLine(value, y + offset, fit.size, style, cx);
          }
        });
        faceLine('GF = gluten free   ·   V = vegetarian   ·   PESC = pescatarian', 134, 8);
        faceLine(footer.occasion, 141, 7, 'bold');
        doc.setDrawColor('#b8adb1');
        doc.setLineWidth(0.15);
        doc.setLineDashPattern([1, 2], 0);
        doc.line(8, half, w - 8, half);
        doc.setLineDashPattern([], 0);
      } else if (template === 'money') {
        // Prop banknote at its own proportions, six to a landscape sheet, cut along the marks.
        doc.addImage(pictures[item.id], 'JPEG', x, y, w, h, item.id, 'MEDIUM');
      } else if (template === 'photo') {
        // The picture prints as large as it can inside its cell, with a caption beneath.
        const pad = 4,
          captionSpace = 13,
          boxW = w - pad * 2,
          boxH = h - pad * 2 - captionSpace,
          scale = Math.min(boxW / item.imageWidth, boxH / item.imageHeight),
          pw = item.imageWidth * scale,
          ph = item.imageHeight * scale;
        doc.addImage(pictures[item.id], 'JPEG', x + (w - pw) / 2, y + pad, pw, ph, item.id, 'MEDIUM');
        const caption = lines(item.content, boxW, 7.5);
        text(caption.slice(0, 3), x + pad, y + pad + ph + 5, 7.5, 'normal', '#625b60', {
          lineHeightFactor: 1.35,
        });
      } else if (template === 'qnote') {
        // A pre-filled question note for a cross-table conversation, A5 like the
        // private note. The draft is the asker's; the reply space is left blank.
        // Branded like the clue envelopes: round top left, the logo top right, and the
        // anniversary line along the foot with the note key in the corner.
        const pad = 14, muted = brand.inkSaver ? '#555555' : '#6a5960';
        spaced(`A NOTE · ROUND ${item.round}`, x + pad, y + 20, 10, 'bold', accent, 0.6);
        spaced(item.title, x + pad, y + 27, 8, 'bold', muted, 0.5);
        if (options.logo) doc.addImage(options.logo, 'PNG', x + w - pad - 44, y + 10, 44, 44 * 731 / 2000);
        else spaced(brand.name, x + w - pad, y + 20, 13, 'bold', accent, 0.6, 'right');
        text('To:', x + pad, y + 45, 10, 'normal', '#625b60');
        write(`${item.toCharacter}  /  Table ${item.toTable}`, x + pad + 13, y + 41, w - pad * 2 - 13, 10, 12, 10, 'bold');
        text('From:', x + pad, y + 54, 10, 'normal', '#625b60');
        write(`${item.character}  /  Table ${item.table}`, x + pad + 13, y + 50, w - pad * 2 - 13, 10, 11, 9.5);
        let cy = y + 64;
        cy += write(item.content, x + pad, cy, w - pad * 2, 56, 12, 10);
        doc.setDrawColor('#a5a0a2');
        doc.setLineWidth(0.2);
        for (let i = 0; i < 2; i++) {
          cy += 9;
          doc.line(x + pad, cy, x + w - pad, cy);
        }
        cy += 13;
        text('Reply', x + pad, cy, 12, 'bold', accent);
        for (let offset = cy + 9; offset <= y + 178; offset += 9)
          doc.line(x + pad, offset, x + w - pad, offset);
        text('You can ask face to face, or send this note; the reply comes back on it.',
             x + pad, y + 185, 7.5, 'normal', '#7a6d74');
        doc.setDrawColor(accent);
        doc.setLineWidth(0.5);
        doc.line(x + pad, y + 189.5, x + w - pad, y + 189.5);
        doc.setLineWidth(0.2);
        doc.line(x + pad, y + 190.5, x + w - pad, y + 190.5);
        spaced(footer.occasion, x + pad, y + 196, 6, 'bold', accent, 0.35);
        spaced(item.title, x + w - pad, y + 196, 6, 'normal', muted, 0.3, 'right');
        if (slot === 0 && brand.cutMarks) {
          doc.setDrawColor('#6b6066');
          doc.setLineWidth(0.2);
          for (const edge of [148, 149]) {
            doc.line(edge, 4, edge, 10);
            doc.line(edge, 200, edge, 206);
          }
        }
      } else if (template === 'note') {
        // Two exact ISO A5 notes (148 × 210 mm) on landscape A4. The 1 mm
        // centre strip accounts for the ISO rounding between A4 and A5.
        const pad = 14;
        brandLine(x + pad, y + 20, w - pad * 2);
        text('A private note', x + pad, y + 38, 20, 'bold', accent);
        text('To:', x + pad, y + 54, 11);
        text('From:', x + pad, y + 68, 11);
        text('Message', x + pad, y + 89, 12, 'bold', accent);
        doc.setDrawColor('#a5a0a2');
        doc.setLineWidth(0.2);
        doc.line(x + pad + 15, y + 56, x + w - pad, y + 56);
        doc.line(x + pad + 15, y + 70, x + w - pad, y + 70);
        for (let offset = 100; offset <= 190; offset += 10)
          doc.line(x + pad, y + offset, x + w - pad, y + offset);
        if (slot === 0 && brand.cutMarks) {
          doc.setDrawColor('#6b6066');
          doc.setLineWidth(0.2);
          // Cut on both guides to remove the 1 mm centre strip. Other sides
          // use the paper edges, keeping all writing inside printer margins.
          for (const edge of [148, 149]) {
            doc.line(edge, 4, edge, 10);
            doc.line(edge, 200, edge, 206);
          }
        }
      } else if (template === 'ballot') {
        // A discussion aid for each table, not a vote: one name, then the three parts of a
        // case. Nobody collects it (owner, 29 September 2026). The 80 mm card is tight, so
        // the brand line is smaller than elsewhere and each section keeps 13 mm to itself.
        // Branded as the clue cards are: the label top left, the logo top right, the double rule
        // and the anniversary line along the foot.
        const bm = brand.inkSaver ? '#555555' : '#6a5960';
        // Four type sizes only: 13 for the question, 10 for the labels, 8 for the words that
        // explain them, 6.5 spaced for the brand lines (the clue cards' size).
        spaced('ACCUSATION SLIP', x + 6, y + 10.5, 6.5, 'bold', accent, 0.6);
        if (options.logo) doc.addImage(options.logo, 'PNG', x + w - 6 - 25, y + 4.5, 25, 25 * 731 / 2000);
        else spaced(brand.name, x + w - 6, y + 10.5, 9, 'bold', accent, 0.5, 'right');
        doc.setDrawColor(accent);
        doc.setLineWidth(0.5);
        doc.line(x + 6, y + 14.5, x + w - 6, y + 14.5);
        doc.setLineWidth(0.2);
        doc.line(x + 6, y + 15.5, x + w - 6, y + 15.5);
        const ask = fitted('Who do you think did the murder?', w - 12, 6, 13, 10, 'bold');
        text(ask.lines, x + 6, y + 22, ask.size, 'bold', accent);
        const how = fitted('What was the motive, means and opportunity? Discuss on your table, then fill in one each.', w - 12, 8, 8, 6.5);
        text(how.lines, x + 6, y + 24.5 + how.size * MM, how.size, 'normal', '#4e454a', { lineHeightFactor: 1.2 });
        // One fill-in line for the name; the three parts of the case have a label, a hint in a
        // shared column, and open space to write in.
        const col = x + 32;
        text('I accuse:', x + 6, y + 38, 10, 'bold', accent);
        doc.setDrawColor('#a5a0a2');
        doc.setLineWidth(0.3);
        doc.line(col, y + 38.6, x + w - 6, y + 38.6);
        for (const [label, hint, offset] of [
          ['Motive', 'why they wanted him dead', 45.5],
          ['Means', 'what they used, and how they got it', 54.5],
          ['Opportunity', 'how they could have done it: were they near?', 63.5],
        ]) {
          text(label, x + 6, y + offset, 10, 'bold', accent);
          font(8, 'normal', '#7a6d74');
          const lines = doc.splitTextToSize(hint, x + w - 6 - col);
          text(lines, col, y + offset, 8, 'normal', '#7a6d74', { lineHeightFactor: 1.2 });
        }
        doc.setDrawColor(accent);
        doc.setLineWidth(0.5);
        doc.line(x + 6, y + h - 8.2, x + w - 6, y + h - 8.2);
        doc.setLineWidth(0.2);
        doc.line(x + 6, y + h - 7.2, x + w - 6, y + h - 7.2);
        spaced(footer.occasion, x + w / 2, y + h - 3.6, 6.5, 'bold', accent, 0.4, 'center');
      } else if (template === 'slip') {
        // Anonymous evidence has no event logo, recipient, ID or modern date.
        const fit = fitted(item.content, w - 40, h - 40, 15, 12);
        text(fit.lines, x + 20, y + 40, fit.size, 'normal', '#191919', {
          lineHeightFactor: 1.5,
        });
      } else if (template === 'report' && pictures['art-lab-report'] && item.id === 'CLUE_VV_R2') {
        // The artwork version fills the sheet. The exact report text is kept underneath it,
        // invisible, so the page stays searchable and the wording can be checked.
        doc.addImage(pictures['art-lab-report'], 'JPEG', 0, 0, 210, 297, 'art-lab-report', 'MEDIUM');
        font(8, 'normal', '#000000');
        doc.text(item.content.split('\n'), 20, 20, { renderingMode: 'invisible' });
      } else if (template === 'report') {
        drawLabReport(item, x, y, w, h);
      } else {
        // The report content is the exact stored text, including its own heading.
        if (template === 'taxi')
          text('DRIVER’S JOURNEY NOTE', x + 14, y + 23, 14, 'bold');
        write(
          item.content,
          x + 14,
          y + (template === 'taxi' ? 34 : 18),
          w - 28,
          h - 42,
          13,
          11,
        );
      }
      pageRows.push({
        page: doc.getNumberOfPages(),
        id: item.id,
        copy: copy + 1,
        template: template === 'report' && pictures['art-lab-report'] && item.id === 'CLUE_VV_R2' ? 'report-art' : template,
        x,
        y,
        width: w,
        height: h,
      });
      slot++;
      if (slot >= cols * rows) slot = 0;
    }
    manifest.push({
      id: item.id,
      title: item.title,
      character: item.character,
      guest: item.guest,
      round: item.round,
      table: item.table,
      quantity: item.quantity,
      revision: item.revision,
      private: item.private,
      firstPage: Math.max(1, firstPage),
    });
  }
  // The constructor starts with a blank page; remove it after first next().
  doc.deletePage(1);
  for (const row of pageRows) row.page--;
  for (const row of manifest) row.firstPage--;
  const printPages = doc.getNumberOfPages();
  if (options.manifest !== false) {
    next();
    let y = 36;
    brandLine(14, 20, 182);
    text('PRINT MANIFEST · HOST ONLY', 14, y, 15, 'bold', accent);
    y += 10;
    text(
      `${items.length} entries · ${items.reduce((n, i) => n + i.quantity, 0)} pieces · ${printPages} print pages`,
      14,
      y,
      10,
    );
    y += 7;
    text(
      'A4 · Actual size / 100% · Single-sided · Cut at marks; fold place cards and table signs.',
      14,
      y,
      9,
    );
    y += 10;
    for (const row of manifest) {
      const label = `${row.quantity} × ${row.title}${row.guest ? ' / ' + row.guest : ''}${row.round !== null ? ' / R' + row.round : ''}${row.private ? ' / PRIVATE' : ''}`;
      const ls = lines(label, 172, 9);
      if (y + ls.length * 4.4 > 278) {
        next();
        brandLine(14, 20, 182);
        y = 34;
      }
      doc.setDrawColor('#777');
      doc.rect(14, y - 2.5, 2.8, 2.8);
      text(ls, 20, y, 9, 'normal', '#242326', { lineHeightFactor: 1.35 });
      y += ls.length * 4.4 + 3;
    }
  }
  for (let p = 1; p <= doc.getNumberOfPages(); p++) {
    if (pageRows.some((row) => row.page === p && ['note', 'qnote', 'seating-plan', 'table-plan', 'room-plan', 'table', 'report-art', 'envelope', 'table-envelope'].includes(row.template)))
      continue;
    doc.setPage(p);
    text(
      `VALE MERIDIAN PRINT STUDIO  /  ${options.snapshotId ?? 'PRINT PROOF'}  /  ${p} of ${doc.getNumberOfPages()}`,
      12,
      doc.internal.pageSize.getHeight() - 4,
      7,
      'normal',
      '#6b6569',
    );
  }
  doc.setProperties({
    title: 'Vale Meridian print pack',
    subject: 'Event print snapshot',
    creator: 'Vale Meridian Print Studio',
  });
  return {
    doc,
    manifest,
    pages: doc.getNumberOfPages(),
    printPages,
    placements: pageRows,
  };
}
