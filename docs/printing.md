# Printing

Everything guests see is printed from the Print Studio ([../print-studio/README.md](../print-studio/README.md)), a small web app with a command-line twin, from data in the event database. This page says what to print, how many, on what, and in what order. For the buttons and options, see the Print Studio README.

## One-time setup

1. Edit [../data/event.json](../data/event.json): `hosts`, `date` and `venue` print in card footers, the seating plan and the table plan. `name` and `subtitle` are the brand. Leave `fictionalDate` alone.
2. Seat your guests ([casting-and-seating.md](casting-and-seating.md)).
3. Refresh the snapshot: `cd print-studio && npm run snapshot`.
4. Start the studio: `npm run dev` (or double-click `start-print-studio.command` on a Mac). Choose a document type in the sidebar, open a proof, and tick the items you want. **Prepare print pack** builds one PDF.

If the studio says the data are stale, press **Reload from database** or run `npm run snapshot`. `npm run check:data` reports the same thing from the command line.

## What to print

Default quantities; every one can be changed. In all, 646 selectable items and about 800 pieces.

| Item | Qty | Paper and size | Notes |
|---|---:|---|---|
| **Clue cards** | 207 (51 in Round 0, 52 in each of Rounds 1 to 3) | A4 cream card, two 186 × 130 mm cards per sheet | One per character per round. Cut at the corner marks |
| **Private performer and Game Master cards** | 3 | As above | Vincent's card, Spinny's toast card, the Game Master's Round 2 card. Printed on their own sheets and kept private |
| **Envelope labels** | 207 | Avery J8161 or L7161 (63.5 × 46.6 mm, 18 per sheet) | Each round starts a new sheet, so sorting stays honest. Or print directly onto C5 envelopes with `--envelopes` |
| **Round 2 and 3 table envelope fronts** | 16 | A4 landscape, stuck onto a C4 envelope | One per table per round, holding that table's clue envelopes |
| **Question notes** | 59 | Two per A4 | Pre-printed drafts for cross-table conversations, keyed Q1-01 and so on |
| **Name badges** | 55 | 90 × 56 mm, eight per A4 | One performer has two badges (Vincent and Peter); Peter's prints on a private sheet |
| **Place cards** | 54 | 90 × 80 mm before folding | Guest and character; menu if the database has one |
| **Table signs** | 8 | One portrait A4 each, folded to an A5 stand | Character names with real names in brackets, plus dietary flags |
| **Seating plan** | 1 | Landscape A4 | For the venue and guests; print as many as you like |
| **"Find your table" sheet** | 4 | Portrait A4 | A floor plan and a list of names by table: no characters, no seat numbers |
| **Room plan and seating diagrams** | 1 | A4 | Game Master's copy |
| **Accusation slips** | 56 | 90 × 80 mm, six per A4 | Each guest writes their own conclusion; nobody collects them |
| **Private notes** | 12 | A5, two per landscape A4 | To, From and a lined message area |
| **Laboratory report** | 8 | A4 | One for every table in Round 3 (Donna carries them) |
| **Photographs** | 81 + 1 | 95 × 124 mm, four per A4 | Nine pictures × nine packs, plus the toast portrait ([evidence-photos.md](evidence-photos.md)). Photo paper works well |
| **Prop money** | 24 notes | 130 mm wide | 12 per deep-red envelope |
| **Passport, taxi note, two slips** | 1 each | | Typeset in the studio |
| **Round dividers and Game Master references** | 8 + 8 | A4 | Dividers by release step; references are the run sheet, props list, Spinny and finale scripts |

**Paper.** Print on A4 cream paper or card, single-sided, at **Actual size / 100%** with automatic page orientation. Handout backgrounds are left unfilled so the paper supplies the colour; the burgundy branding stays. Table signs print single-sided and fold across the dashed centre line, so no trimming is needed.

**Brand and ink.** In the studio, **Brand & print settings** changes the brand name, accent colour and subtitle, or switches to black and white. These never change card text. On the command line: `--brand`, `--colour`, `--ink-saver`.

**Large print.** `--large-print` makes one card per A4 page in large type, for a guest who needs it: `node scripts/print.mjs --guest 'Guest 12' --large-print --output output/guest-12.pdf`.

## Command line

Run these from `print-studio/`:

```bash
node scripts/print.mjs --category clues --round 2 --output output/round-2.pdf
node scripts/print.mjs --category badges --output output/badges.pdf
node scripts/print.mjs --id seating-plan --no-manifest --output output/seating-plan.pdf
node scripts/print.mjs --guest 'Guest 01' --output output/guest-01-pack.pdf
node scripts/print.mjs --category stationery --ink-saver --output output/stationery.pdf
node scripts/print.mjs --help
```

No filter prints everything. A JSON manifest accompanies each PDF, and by default the first pages are a packing checklist for the Game Master (`--no-manifest` leaves it off). `--sort round|table|guest` sets the packing order.

## Order of work

1. **Print the clue cards by round**, cut them, and put each in its envelope with the label printed for it. Items that go inside an envelope with a card (the passport, the taxi note, the laboratory reports, the photograph packs, the deep-red envelopes) are listed on the "Clue envelope inclusions" sheet in the Game Master references, in the order the envelopes print.
2. **Round 1** envelopes sit at the place settings. **Rounds 2 and 3** are collected into one A4 (C4) envelope per table, placed on the table beforehand; the front is printed on A4 and stuck on.
3. **Badges, place cards and table signs** by table.
4. **Question notes** go in with each round's cards. They print in key order, table by table.
5. **Accusation slips and private notes** go in a box.
6. **Game Master references and dividers** go in a folder. Keep the finale sheet, Spinny's sheet and the murderer's speech apart; each has its own private copies.

## Direct envelope printing

The studio can print a guest's name straight onto a C5 envelope (229 × 162 mm) instead of a label. Some printers feed envelopes with a different orientation from the paper: if the text comes out upside down, rotate it in the print dialog or your printer's envelope options and test on a spare first.

## Troubleshooting

| Symptom | Fix |
|---|---|
| "Photograph not supplied" | Run `npm run photos` once (needs Pillow) |
| "STALE" from `check:data` | `npm run snapshot` after any change to the database, `data/event.json` or the story files |
| A card does not fit | The generator raises an error rather than shrinking type below its minimum. Shorten the card text |
| Names clipped on a badge | Names must fit the badge; shorten the `guest` value or the brand name |
| The studio shows old guests | The snapshot is a file (`print-studio/lib/event.json`); regenerate it |
