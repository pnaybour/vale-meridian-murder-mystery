# Known issues

What is known to be imperfect, so you can plan around it. None of these stops the game.

## Check before you send briefings

**Briefings must not give away the murder.** `python3 scripts/render_briefings.py` warns about any briefing that uses a word like "death", "murder", "poison" or "collapsed", so a spoiler cannot slip through when you edit one. The shipped briefings are clean: an earlier draft of Graham Greenwell's said "Vale's death has made the whole arrangement dangerous", and it has been reworded to match his Round 0 card.

Peter Vale's briefing says Peter arrives "after Vincent has already collapsed". That is fine, because it goes to the same performer who plays Vincent; do not send it to anyone else (the renderer only writes the briefing for Vincent).

## Review items still open

- **126 handshake items are marked "changed since read" and 20 are "never read".** Each handshake item is a place where one card relies on another character having something to say back. The recorded verdicts were made earlier in the project, and Round 0 and some Round 1 to 3 cards were rewritten afterwards, so those verdicts no longer match the current text. Nothing is known to be wrong; the verdicts simply need another read. `python3 scripts/review_current_social_graph.py` lists them.
- **Question note Q3-19 is stale.** Its card, its partner or a table changed after the draft was written. Re-read the draft against the card and re-draft it (`scripts/cross_table_notes.py --apply --redraft Q3-19`) if needed.

## Practical

- **The studio's browser interactions have no automated tests.** `npm test` covers the PDF generator, the data and the print layouts, not the clicks in the web app.
- **`npm test` takes about two minutes.** One test renders every printable on its own.
- **A few parts are macOS-only.** `print-studio/start-print-studio.command` is a macOS launcher (use `npm run dev` elsewhere), and `print-studio/scripts/table-tents.mjs` uses `sips` to turn the logo. Everything else is cross-platform.
- **Pictures are placeholders.** See [evidence-photos.md](evidence-photos.md). The prop banknote is a plain drawing.
- **A few places are written for eight tables.** The room-layout and seat-position scripts have a per-table list (`TABLES`, `ROTATIONS`), and `table-tents.mjs` defaults to tables 1 to 8. Fewer or more tables means editing them; see [casting-and-seating.md](casting-and-seating.md#a-different-number-or-size-of-tables).
- **Some seat numbers are skipped** (table 1 has no seat 2, for instance). It is the tested arrangement; see [casting-and-seating.md](casting-and-seating.md#seat-numbers).
- **The seating diagrams and floor plan are illustrative.** The coordinates describe a sample venue; replace them with your own room.

## Design limits you may bump into

- **The cast is fixed.** More than 54 seats is not supported, and fewer needs hand editing.
- **The story is British and set in 1986.** Money, television and music references are of that time and place.
- **Two retired characters remain in the database.** Sheila Sparks and Felix Fortune were removed from the original cast; their cards are retired, and nobody is sent to them. They are harmless, but they appear in `characters` and, as retired cards, in `clues`.
- **Music is not included.** The scripts name the tracks used at the original party for five cues; supply your own.

## Reporting a problem

Open an issue that names the card id (`CLUE...`) or script, and says what you expected. For a story problem, quote the card text and the card it sends to.
