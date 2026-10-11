# Vale Meridian Print Studio

A web app and a command-line generator that print everything the game puts in guests' hands: clue cards, name badges, place cards, table signs, envelope labels, question notes, evidence, accusation slips and the Game Master's references. It reads the event database; it never writes to it.

Output is A4 PDF. Text stays selectable and fonts are embedded, so a proof looks the same on every machine.

## Quick start

You need [Node.js](https://nodejs.org) 22.13 or later (the scripts use the built-in `node:sqlite`), and Python 3.10 or later with [Pillow](https://python-pillow.org) for the pictures.

```bash
npm ci
npm run photos     # builds the screen and print copies of the pictures (placeholders for any you have not supplied)
npm run dev        # then open the address it prints, normally http://localhost:3000
```

On a Mac you can double-click `start-print-studio.command` instead. Keep its window open while you work; press Control-C to stop.

## Using the studio

1. Choose a document type in the sidebar.
2. Search by guest, character, clue title or wording; filter by round, table or review state.
3. Select an item to read its screen proof. **Open PDF proof** shows its exact printable layout.
4. Mark it reviewed or approved. Marks are tied to the card's current text: if the card changes, the mark is cleared.
5. Tick items to add them to your pack, choose **Prepare print pack**, adjust copies and sorting, and download the PDF.
6. Print on A4 cream paper or card, single-sided, at **Actual size / 100%** with automatic page orientation. Handout backgrounds are unfilled, so the paper provides the colour; the burgundy branding stays. Cut at the corner marks; fold place cards at the centre line.

A screen proof is a reading preview. The PDF is the authoritative layout proof.

**Name badges.** *Download badge sheets* exports every badge your filters show, eight per A4 sheet at 90 × 56 mm. Badges carry a public introduction of the character (from `source/character-introductions.json`). Vincent and Peter share one performer: the combined introduction is split between their two badges so Vincent's arrival badge does not disclose Peter, and Peter's badge prints on its own private sheet. The Helicopter Pilot has no introduction and gets a name-only badge.

**Private notes** have **To**, **From** and a large lined **Message** area. They are A5 (148 × 210 mm), two side by side on landscape A4. Trim the 1 mm centre strip using the guides.

**Table signs** use one portrait A4 sheet each. Both halves carry the same label, with character names followed by real names in brackets and dietary flags; the upper half is upside down. Print single-sided and fold across the dashed centre line to make an A5 standing sign. No trimming is needed. The key explains `GF` (gluten free), `V` (vegetarian) and `PESC` (pescatarian); other recognised requirements are written out, and any note the studio does not recognise is flagged `DIET: CHECK NOTE`.

**Seating and place cards.** *Download seating plan* makes a single landscape A4 sheet for the venue and guests, listing all eight tables in seat order with guests' names and their public arrival characters. It also appears as a selectable item for multi-copy packs. **Find your table** is a portrait sheet with a floor plan and names by table: no characters, no seat numbers.

**Brand and print settings** change the brand name, colour and table-sign subtitle, or print in black and white. They never rewrite clue text. Evidence has its own plain document styling.

**Source and preparation** shows the 39-item physical checklist (and its PDF), the database snapshot and **Reload from database**. Download the review record to keep a readable copy of your marks outside the browser.

## What it prints

At the default quantities there are 646 selectable items and about 800 pieces: 207 clue cards (51 arrival cards and 52 in each of Rounds 1 to 3); 3 private performer and Game Master cards; the laboratory report (8 copies); 55 badges; 54 place cards; 8 table signs; a seating plan, a "Find your table" sheet and a room plan; 207 envelope labels and 16 table-envelope fronts; 59 question notes; 56 accusation slips; 12 private notes; 11 pictures and the prop money; 8 round dividers; and the Game Master's references. [../docs/printing.md](../docs/printing.md) has the sizes and paper for each.

Cards are 186 × 130 mm, two per A4 sheet; badges 90 × 56 mm, eight per sheet (two columns, four rows, 6 mm gaps); place cards 90 × 80 mm before folding. The long closing speech has a full-page layout. Oversized content **raises an error** rather than being silently clipped or shrunk below the minimum type size.

## Command line

```bash
node scripts/print.mjs --category badges --output output/name-badges.pdf
node scripts/print.mjs --id seating-plan --no-manifest --output output/seating-plan.pdf
node scripts/print.mjs --category clues --round 2 --output output/round-2.pdf
node scripts/print.mjs --guest 'Guest 07' --output output/guest-07-pack.pdf
node scripts/print.mjs --id CLUE_VV_R2 --output output/laboratory-report.pdf
node scripts/print.mjs --category stationery --ink-saver --output output/stationery.pdf
node scripts/print.mjs --help
```

No filter exports the whole inventory. Filters intersect. `--copies` overrides the quantity of every selected item; `--sort` accepts `round`, `table` or `guest`, with private sheets and document types always kept apart. A JSON manifest accompanies each PDF, and the first pages are a Game Master packing checklist unless you pass `--no-manifest`. Other flags: `--full-page`, `--large-print`, `--no-cut-marks`, `--envelopes`, `--brand NAME`, `--colour '#732b40'`.

Two more generators: `node scripts/seating-list.mjs` (one page of guests A to Z with character and table) and `node scripts/table-tents.mjs` (cut-and-fold triangular table numbers; macOS only because it uses `sips`).

## npm scripts

| Command | What it does |
|---|---|
| `npm run dev` | Starts the studio on localhost |
| `npm run dev:printer` | Starts it on every network interface so a machine beside the printer can use it; see below |
| `npm run build` | Builds the app |
| `npm test` | 15 tests of the PDF generator and the data; takes about two minutes |
| `npm run check:data` | Read-only: is `lib/event.json` current with the database and `data/event.json`? |
| `npm run snapshot` | Rebuilds `lib/event.json` from the database |
| `npm run photos` | Rebuilds the picture copies in `public/evidence/` and `lib/photos.json` |
| `npm run print` | Same as `node scripts/print.mjs` |
| `npm run lint`, `npm run format`, `npm run typecheck` | Code quality |

## Where the data comes from

```
data/valemeridian-event.sqlite ─┐
data/event.json              ├─► scripts/export_snapshot.py ──► lib/event.json ──► the studio, print.mjs
story/*.md                   ─┤
source/*.json                ─┘
data/artwork/*.png ──► scripts/build_photos.py ──► public/evidence/*.jpg, lib/photos.json
```

The snapshot is a saved, checked copy of what the database says. It contains **no email addresses or contact details**, only what appears on the printed pieces (guest names, characters, tables, dietary flags, card text). Refresh it after any change to the database, the event details, or the Markdown in `story/`:

```bash
npm run snapshot       # or press "Reload from database" in the studio
npm run check:data     # confirms they agree
```

`export_snapshot.py` opens the database read-only. It stops with an error if the database has more than one approved seating plan, or if an active card has no record kind.

## Printing from another machine

The print pack is built in the browser, so any machine that can open the studio can produce it, with nothing else installed beside the printer.

```bash
npm run dev:printer
```

That binds the development server to every network interface and prints a `Network:` address such as `http://192.168.1.20:3000/`. Open it on the machine by the printer and use the studio as normal.

**Only do this on a network you trust.** It is a development server, and its endpoints write review comments and approvals straight into the repository's `data/` folder.

## Review comments and approvals

In development, the studio lets you leave comments on a handout and mark handouts reviewed or approved. They are stored beside the database in `data/review-comments.json` and `data/review-status.json` (created on first use; ignored by git), so they survive a browser change and can be read by anyone editing the cards. The endpoints (`/api/comments`, `/api/reviews`, `/api/reload-data`) exist only in the development server.

## How it is built

| Path | What it is |
|---|---|
| `app/page.tsx`, `app/globals.css` | The web app (React on [vinext](https://www.npmjs.com/package/vinext), a Vite-based runtime for Next.js apps) |
| `lib/pdf.mjs` | The one PDF renderer shared by the app and the command line, built on [jsPDF](https://github.com/parallax/jsPDF). No screenshots: it draws text and shapes |
| `lib/event.json` | The print snapshot (generated) |
| `lib/fonts.json` | Liberation Sans, embedded in every PDF |
| `lib/photos.json`, `public/evidence/` | Generated picture copies (git-ignored) |
| `source/` | Hand-edited inputs: `character-introductions.json` (badge text) and `physical-preparation.json` (the props checklist) |
| `scripts/` | `export_snapshot.py`, `check_snapshot.py`, `build_photos.py`, `print.mjs`, `table-tents.mjs`, `seating-list.mjs`, and `pdf.test.mjs` |
| `components/` | UI components, many from [shadcn/ui](https://ui.shadcn.com) |

## What the tests cover

`npm test` checks that every active card in the database is printed exactly once; that the seating, badges and place cards agree with the roster and that the twin performer has two badges (Peter's on its own private sheet); that every printable fits at a readable minimum type size; that a full pack places every required copy exactly once and keeps private cards apart; that the seating plan and the guest table plan give nothing away (no character names or seat numbers on the guest sheet, no Peter on the public plan); that the finale's shared copy never names the murderer; that pictures print only when supplied, and that the decanter frame cannot be separated from the rest of Vance's pack; that question notes match their cards; and that cards and envelopes print in the same order.

It does not cover clicks in the browser app.

## Troubleshooting

| Problem | Fix |
|---|---|
| `Photograph not supplied` | `npm run photos` (needs Pillow) |
| `STALE` from `check:data`, or the studio shows old guests | `npm run snapshot` |
| `ExperimentalWarning: SQLite` | Harmless: the tests and some scripts use the built-in `node:sqlite` |
| A card or badge does not fit | Shorten the text. The generator will not shrink type below its minimum |
| `Cannot find module` | Run `npm ci` in this folder |

## Licences

Liberation Sans is licensed under the SIL Open Font Licence 1.1 (`source/LICENSE_LIBERATION`). The libraries are listed in `package.json` with their own licences.
