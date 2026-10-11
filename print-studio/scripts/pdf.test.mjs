import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { fileURLToPath } from 'node:url';
import { DatabaseSync } from 'node:sqlite';
import { makePdf, validateItems, sortItems } from '../lib/pdf.mjs';
const data = JSON.parse(
  fs.readFileSync(new URL('../lib/event.json', import.meta.url)),
);
// The event database is the source of truth: the snapshot must agree with it.
const database = new DatabaseSync(
  fileURLToPath(new URL('../../data/valemeridian-event.sqlite', import.meta.url)),
  { readOnly: true },
);
const activeClueIds = database.prepare("select clue_id from clues where status='active'").all().map((r) => r.clue_id);
const retiredClueIds = new Set(
  database.prepare("select clue_id from clues where status<>'active'").all().map((r) => r.clue_id),
);
// Expected counts come from the database, so a smaller or larger cast needs no edits here.
const countOf = (sql) => database.prepare(sql).get().n;
const ordinaryCards = countOf(
  "select count(*) n from clues c join local_clue_record_kinds k using(clue_id) where c.status='active' and k.record_kind='ordinary'",
);
const privateCards = countOf(
  "select count(*) n from clues c join local_clue_record_kinds k using(clue_id) where c.status='active' and k.record_kind in ('performance','facilitation')",
);
const seatCount = countOf(
  "select count(*) n from seat_assignments where plan_id=(select plan_id from seating_plans where status='approved')",
);
const photoCount = countOf("select count(*) n from local_evidence_photos where status='active'");
const retiredCharacters = database
  .prepare("select character_name from characters where status='retired'")
  .all()
  .map((r) => r.character_name);
// The seat that plays both Vincent and Peter Vale (one performer, two badges).
const twinSeat = data.seats.find((s) => s.character_name === 'Vincent Vale / Peter Vale');
const fonts = JSON.parse(
  fs.readFileSync(new URL('../lib/fonts.json', import.meta.url)),
);
const event = data.event;
const logo = 'data:image/png;base64,' + fs.readFileSync(new URL('../public/valemeridian-logo.png', import.meta.url)).toString('base64');
const pictures = JSON.parse(
  fs.readFileSync(new URL('../lib/photos.json', import.meta.url)),
);
test('all active database clue records are present once, with lab counted once', () => {
  for (const clueId of activeClueIds) {
    const matching = data.items.filter((i) => i.id === clueId);
    assert.equal(matching.length, 1);
    assert.equal(matching[0].source, 'Local database');
    assert.ok(matching[0].content.length > 0);
  }
  const databaseItems = data.items.filter((i) => i.source === 'Local database');
  assert.equal(databaseItems.length, data.source.clueCount);
  assert.equal(new Set(databaseItems.map((i) => i.id)).size, data.source.clueCount);
  assert.equal(data.items.filter((i) => i.category === 'clues').length, ordinaryCards);
  assert.ok(data.items.every((i) => !retiredClueIds.has(i.id)));
  assert.equal(data.items.filter((i) => i.category === 'private').length, privateCards);
  assert.equal(
    data.items.find((i) => i.id === 'CLUE_VV_R0').character,
    'Vincent Vale',
  );
  assert.equal(
    data.items.find((i) => i.id === 'CLUE_VV_R2').category,
    'evidence',
  );
});
test('badge and arrival identities are correct for shared performer', () => {
  const badges = data.items.filter((i) => i.category === 'badges');
  assert.equal(badges.length, seatCount + (twinSeat ? 1 : 0));
  const twins = badges.filter((i) => i.guest === twinSeat.guest_name);
  assert.deepEqual(twins.map((i) => i.character).sort(), [
    'Peter Vale',
    'Vincent Vale',
  ]);
  assert.equal(twins.find((i) => i.character === 'Peter Vale').private, true);
  assert.equal(
    data.items.find(
      (i) => i.template === 'place' && i.guest === twinSeat.guest_name,
    ).character,
    'Vincent Vale',
  );
});
test('the roster is complete: every seat has a player, cards, a badge and a place', () => {
  assert.equal(data.seats.length, seatCount);
  assert.equal(data.validation.guests, seatCount);
  // Retired characters are never printed, and nobody is left without a character.
  assert.ok(data.items.every((i) => !retiredCharacters.includes(i.character)));
  const noCards = ['Family Solicitor', 'Helicopter Pilot', 'Vincent Vale / Peter Vale'];
  for (const seat of data.seats) {
    assert.ok(
      data.items.some((i) => i.template === 'badge' && i.guest === seat.guest_name),
      `${seat.character_name} has no badge`,
    );
    assert.ok(
      data.items.some((i) => i.template === 'place' && i.guest === seat.guest_name),
      `${seat.character_name} has no place card`,
    );
    if (noCards.includes(seat.character_name)) continue;
    // Every other player has one card in each of Rounds 0 to 3, all in their own character.
    const cards = data.items.filter((i) => i.category === 'clues' && i.guest === seat.guest_name);
    assert.ok(cards.every((i) => i.character === seat.character_name), seat.character_name);
    assert.deepEqual(cards.map((i) => i.round).sort(), [0, 1, 2, 3], seat.character_name);
  }
  assert.deepEqual(data.pendingGuests, []);
  assert.deepEqual(data.unallocatedCharacters, []);
});
test('release order handles historic IDs and the toast cue', () => {
  assert.equal(
    data.items.find((i) => i.id === 'CLUE_SPINNY_TOAST_01').round,
    0,
  );
  // Round 4 no longer hands out cards at all: the six staging cards became two documents.
  assert.deepEqual(
    data.items.filter((i) => i.category === 'private' && i.round === 4).map((i) => i.id),
    [],
  );
  const closing = data.items.find(
    (i) => i.id === 'reference-round4-closing-sequence',
  );
  const gmCopy = data.items.find(
    (i) => i.id === 'reference-round4-closing-sequence-gm',
  );
  const speech = data.items.find((i) => i.id === 'reference-round4-murderer-speech');
  assert.equal(closing.quantity, 2, 'one closing sheet each for Spinny and Donna');
  assert.equal(gmCopy.quantity, 1);
  assert.equal(speech.quantity, 1);
  // Spinny's and Donna's copies must be rehearsable without learning who did it.
  for (const name of ['veronica'])
    assert.ok(!closing.content.toLowerCase().includes(name), `shared copy names ${name}`);
  assert.ok(gmCopy.content.includes('Veronica Vane'), 'the GM copy must carry the name');
});
test('the guest table plan matches the seating and names no characters', () => {
  const plan = data.items.find((i) => i.id === 'table-plan');
  assert.equal(plan.private, false, 'the table plan is handed to guests');
  const named = plan.tablePlan.tables.flatMap((t) => t.guests);
  assert.equal(named.length, data.seats.length);
  // Every seated guest appears exactly once, at the table they are seated at.
  for (const seat of data.seats) {
    const table = plan.tablePlan.tables.find((t) => t.number === seat.table_number);
    assert.ok(table, `no plan entry for table ${seat.table_number}`);
    assert.ok(table.guests.includes(seat.guest_name), `${seat.guest_name} missing from table ${seat.table_number}`);
  }
  assert.equal(new Set(named).size, named.length, 'a guest is listed twice');
  // It must give nothing away: no character names, no seat numbers.
  const characters = new Set(data.seats.map((s) => s.character_name));
  const text = JSON.stringify(plan.tablePlan);
  for (const character of characters)
    assert.ok(!text.includes(character), `the guest plan names ${character}`);
  // Every positioned table sits in a room the plan describes.
  for (const table of plan.tablePlan.tables)
    assert.ok(plan.tablePlan.rooms[table.room], `table ${table.number} has no room`);
  assert.ok(plan.tablePlan.outline.length >= 3);
});
test('every printable fits with readable minimum type', () => {
  for (const i of data.items)
    assert.doesNotThrow(
      () => makePdf([{ ...i, quantity: 1 }], fonts, { manifest: false, images: pictures, logo, event }),
      i.id,
    );
});
test('full pack places each required copy exactly once and keeps private cards separate', () => {
  const result = makePdf(data.items, fonts, { manifest: false, images: pictures, logo, event });
  const references = data.items.filter((i) => i.template === 'reference');
  // Reference documents paginate as whole documents rather than being placed on sheets, and a
  // reference may print more than once (the Round 4 script prints three times), so discount
  // their copies rather than their count.
  assert.equal(
    result.placements.length,
    data.items.reduce((n, i) => n + i.quantity, 0) -
      references.reduce((n, i) => n + i.quantity, 0),
  );
  for (const item of data.items.filter((i) => i.template !== 'reference'))
    assert.equal(
      result.placements.filter((p) => p.id === item.id).length,
      item.quantity,
    );
  const pageKinds = new Map();
  for (const p of result.placements) {
    const i = data.items.find((i) => i.id === p.id);
    if (!pageKinds.has(p.page)) pageKinds.set(p.page, new Set());
    pageKinds.get(p.page).add(i.category);
    assert.ok(p.page >= 1);
  }
  for (const cats of pageKinds.values())
    if (cats.has('private')) assert.equal(cats.size, 1);
  const peterPage = result.placements.find(
    (p) => p.id === `badge-${twinSeat.person_id}-Peter`,
  ).page;
  assert.equal(
    result.placements.filter((p) => p.page === peterPage).length,
    1,
    'Peter badge needs its own private sheet',
  );
});
test('public seating plan includes every approved seat and only arrival identities', () => {
  const plan = data.items.find((i) => i.id === 'seating-plan');
  assert.equal(plan.private, false);
  const guests = plan.seatingPlan.tables.flatMap((t) => t.seats.map((s) => ({
    table: t.number, seat: s.seat, guest: s.guest, character: s.character,
  })));
  assert.deepEqual(guests, data.seats.map((s) => ({
    table: s.table_number, seat: s.seat_number, guest: s.guest_name,
    character: s.character_name === 'Vincent Vale / Peter Vale' ? 'Vincent Vale' : s.character_name,
  })));
  assert.ok(!JSON.stringify(plan).includes('Peter Vale'));
  for (const table of plan.seatingPlan.tables)
    for (const seat of table.seats)
      assert.deepEqual(Object.keys(seat).sort(), ['character', 'guest', 'seat']);
});

test('seating plan uses one landscape A4 per copy and table signs return to portrait', () => {
  const plan = { ...data.items.find((i) => i.id === 'seating-plan'), quantity: 2 };
  const sign = data.items.find((i) => i.template === 'table');
  const result = makePdf([plan, sign], fonts, { manifest: false });
  assert.equal(result.printPages, 3);
  for (const page of [1, 2]) {
    result.doc.setPage(page);
    assert.ok(Math.abs(result.doc.internal.pageSize.getWidth() - 297) < 0.05);
    assert.ok(Math.abs(result.doc.internal.pageSize.getHeight() - 210) < 0.05);
  }
  result.doc.setPage(3);
  assert.ok(Math.abs(result.doc.internal.pageSize.getWidth() - 210) < 0.05);
  assert.equal(result.placements.filter((p) => p.template === 'seating-plan').length, 2);
  assert.throws(() => makePdf([{ ...plan, seatingPlan: undefined }], fonts));
});

test('empty selections, missing text, duplicate records and invalid copies are rejected', () => {
  assert.throws(() => makePdf([], fonts));
  const item = data.items[0];
  assert.ok(validateItems([item, item]).length);
  assert.ok(validateItems([{ ...item, content: '' }]).length);
  for (const quantity of [0, -1, 1.5, 501, NaN])
    assert.throws(() => makePdf([{ ...item, quantity }], fonts));
});

test('A5 notes print two per landscape A4 and later documents return to portrait', () => {
  const note = {
    ...data.items.find((i) => i.template === 'note'),
    quantity: 3,
  };
  const divider = data.items.find((i) => i.template === 'divider');
  const result = makePdf([note, divider], fonts, { manifest: false });
  assert.equal(result.printPages, 3);
  const first = result.placements.filter((p) => p.page === 1);
  assert.equal(first.length, 2);
  assert.deepEqual(
    first.map((p) => [p.x, p.y, p.width, p.height]),
    [
      [0, 0, 148, 210],
      [149, 0, 148, 210],
    ],
  );
  result.doc.setPage(1);
  assert.ok(Math.abs(result.doc.internal.pageSize.getWidth() - 297) < 0.05);
  assert.ok(Math.abs(result.doc.internal.pageSize.getHeight() - 210) < 0.05);
  result.doc.setPage(3);
  assert.ok(Math.abs(result.doc.internal.pageSize.getWidth() - 210) < 0.05);
  assert.ok(Math.abs(result.doc.internal.pageSize.getHeight() - 297) < 0.05);
});
test('cross-table question notes: one per keyed card, pre-filled question, blank reply, two per A4', () => {
  const notes = data.items.filter((i) => i.template === 'qnote');
  const keyed = data.items.filter((i) => i.category === 'clues' && i.noteKey);
  assert.ok(notes.length > 0);
  assert.equal(new Set(notes.map((n) => n.title)).size, notes.length);
  for (const n of notes) {
    assert.match(n.title, /^Q[123]-\d{2}$/);
    assert.ok([1, 2, 3].includes(n.round));
    assert.notEqual(n.table, n.toTable);
    const card = keyed.find((c) => c.id === n.clueId);
    assert.ok(card && card.noteKey.split(', ').includes(n.title));
    assert.equal(card.character === 'Vincent Vale' ? 'Peter Vale' : card.character, n.character);
  }
  const result = makePdf(notes.slice(0, 3), fonts, { manifest: false });
  assert.equal(result.pages, 2);
  assert.ok(result.placements.every((p) => p.template === 'qnote'));
});
test('photographic evidence prints with its picture, and is refused without one', () => {
  const photos = data.items.filter((i) => i.template === 'photo');
  assert.equal(photos.length, photoCount);
  for (const p of photos) {
    assert.ok(pictures[p.id]?.startsWith('data:image/jpeg;base64,'), `no picture for ${p.id}`);
    assert.ok(p.imageWidth > 0 && p.imageHeight > 0);
    assert.ok(p.content.trim().length > 0, `no caption for ${p.id}`);
  }
  // The decanter frame must not be separable from the rest of Vance's pack: it matches the Veronica
  // player's hair, gown and bracelet, so handed over on its own it would identify Veronica on sight.
  const decanter = photos.find((i) => i.id === 'photo-decanter');
  const pack = photos.filter((i) => i.character === 'Vance Vellum');
  assert.equal(pack.length, 9);
  for (const p of pack) {
    assert.equal(p.round, decanter.round, `${p.id} is released apart from the decanter frame`);
    assert.equal(p.quantity, decanter.quantity, `${p.id} prints a different number of times`);
  }
  assert.equal(data.items.find((i) => i.id === 'photo-vale-microphone').private, true);
  assert.throws(() => makePdf([decanter], fonts, { manifest: false }), /Photograph not supplied/);
  const result = makePdf(photos, fonts, { manifest: false, images: pictures, logo, event });
  assert.ok(result.pages >= 3);
});
test('every clue envelope prints directly onto a C5 envelope', () => {
  const envelopes = data.items
    .filter((i) => i.template === 'label' && i.labelKind === 'guest')
    .map((i) => ({ ...i, template: 'envelope' }));
  // A name that does not fit throws, so rendering the whole set is the check.
  const { doc, pages } = makePdf(envelopes, fonts, { manifest: false });
  assert.equal(pages, envelopes.length, 'one envelope per page');
  for (let p = 1; p <= pages; p++) {
    doc.setPage(p);
    assert.equal(Math.round(doc.internal.pageSize.getWidth()), 229);
    assert.equal(Math.round(doc.internal.pageSize.getHeight()), 162);
  }
});
test('each round of clue cards prints in the same order as its envelopes', () => {
  for (const round of [0, 1, 2, 3]) {
    const cards = sortItems(data.items.filter((i) => i.category === 'clues' && i.round === round), 'table');
    const envelopes = sortItems(
      data.items.filter((i) => i.template === 'label' && i.labelKind === 'guest' && i.round === round),
      'table',
    );
    assert.deepEqual(
      cards.map((i) => `${i.table} ${i.character} ${i.guest}`),
      envelopes.map((i) => `${i.table} ${i.character} ${i.guest}`),
      `round ${round} cards and envelopes are in different orders`,
    );
  }
});
