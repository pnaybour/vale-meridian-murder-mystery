# Vale Meridian: notes for AI coding agents (written for Claude Code; also read as AGENTS.md)

A murder-mystery party kit. The people using it are hosts planning an evening, not necessarily programmers: explain what you are doing in plain language, and ask before creative decisions (what a character does for a living, who knows what). Mechanical fixes can go ahead.

Start with `README.md`. The rules for writing cards are in `docs/design-principles.md`; the facts of the case are in `story/solution-and-canon.md`. Use British English.

## What is where

- `data/valemeridian-event.sqlite`: the source of truth for characters, clue cards, who each card sends its player to, seating, props. Schema in `docs/data-model.md`.
- `data/event.json`: the party's hosts, date and venue, printed on the handouts.
- `story/`: the Game Master's scripts, written by hand (`gm-run-sheet.md`, `round0-spinny-running-order.md`, `round4-closing-sequence.md`, `round4-murderer-speech.md`), and readers generated from the database (`cards.md`, `conversation-map.md`, `photo-briefs.md`, `seating-plan.md`, `physical-props.md`). Never edit a generated file by hand; regenerate it.
- `scripts/`: Python tools (`roster.py`, `optimise_seating.py`, `render_briefings.py`, `review_current_social_graph.py` and others). See `scripts/README.md`.
- `print-studio/`: the web app and PDF generator (Node 22.13 or later; first `npm ci`, then `npm run photos`).

## Rules

1. **Back up before you write to the database.** `mkdir -p data/backups && cp data/valemeridian-event.sqlite data/backups/<what-you-are-doing>.sqlite`. `data/backups/` is ignored by git. Scripts that write preview first and only write with `--apply`: show the preview before applying.
2. **Editing a card.** Change `clues.clue_content`. If the people it sends the player to change, update `clues.targets_json` **and** the matching `clue_targets` rows; names must match `characters.character_name` exactly. A new active card also needs a row in `local_clue_record_kinds`. Never renumber a card id.
3. **Follow `docs/design-principles.md`.** Short prose in the character's voice; one named person to speak to next (Round 0 names a small group); full character names; **never** a table name, seat number or "your table" on a card; nothing in a briefing or a Round 0 card says who dies or who did it; never invent a scandal to fill a gap; do not add decisive evidence after the accusations.
4. **Keep the solution out of anything guests see.** Everything under `story/` is for the host. A briefing, badge, place card or sign must not name the murderer or the method. `python3 scripts/render_briefings.py` warns about briefings that mention the murder.
5. **Privacy.** The shipped roster is anonymous ("Guest 01"). If the user imports real guest names (`scripts/roster.py`), the database and `print-studio/lib/event.json` then hold personal data: never commit them to a public repository, and do not put guests' names or contact details into documents, commit messages or issues. Prefer working with the sample roster and importing names last.
6. **Do not guess canon.** If `story/solution-and-canon.md` does not settle a fact, ask the user rather than inventing one.
7. **Read your work.** After changing a card, read it aloud (in your head) and read the card of the person it sends the player to. The checks below catch structure, not whether a line works at a party.

## After any change to the database

```bash
python3 scripts/export_story_reader.py              # story/cards.md, conversation-map.md, photo-briefs.md
python3 scripts/export_current_seating.py           # story/seating-plan.md
python3 print-studio/scripts/export_snapshot.py     # print-studio/lib/event.json (or: cd print-studio && npm run snapshot)
python3 scripts/review_current_social_graph.py      # compare its summary before and after
python3 scripts/cross_table_notes.py                # question notes: missing, stale, orphaned
cd print-studio && npm run check:data && npm test   # npm test takes about two minutes
```

The tests count cards, seats, badges and pictures from the database, so adding or retiring characters needs no test edits.

## Different numbers and groups of people

Read `docs/casting-and-seating.md` and `docs/network-analysis.md` first. In short:

- **Same shape, different guests or groups:** `scripts/roster.py` (export, fill in, import). Put each group at one table by choosing which guests play which characters; every character already has a table. The import preview reports groups split across tables. Show the preview before `--apply`.
- **Fewer players:** `scripts/retirement_cost.py` chooses characters (never performers, never half of a couple or pair of mutual witnesses) and lists the cards to edit. To retire a character: reword the cards that name them (text, `targets_json` and `clue_targets`); set their `clues.status` and `characters.status` to `'retired'`; retire their `local_cross_table_notes` and supersede their `clue_answer_contracts`; delete their rows from `seat_assignments`, `character_assignments`, `event_guests`, `local_seat_positions`, `menu_orders` and `people`; run `python3 scripts/register_seat_positions.py --apply`; then regenerate and check. Use plan mode and show the user the plan first.
- **More players:** two guests can share a character (`Ann & Bob` in the guest column). New characters are a large writing job: plan first.
- **Different tables:** `scripts/optimise_seating.py --tables N --size M` shows the cost; applying a new layout is the least exercised path, so back up and compare the review before and after.

## Things that surprise people

- A card that sends its player to someone at another table needs a pre-printed question note: `scripts/cross_table_notes.py` lists the missing ones.
- The finale (`story/round4-closing-sequence.md`) has `<!-- GM -->` and `<!-- SHARED -->` blocks. The shared copy must never name the murderer; a test checks it.
- The pictures are placeholders until the user adds their own to `data/artwork/` (see `docs/evidence-photos.md`). The decanter photograph must never be handed out on its own.
- Some handshake reviews and one question note (Q3-19) are flagged stale. That is known (`docs/known-issues.md`), not something you broke.
- For help with using Claude Code to plan the evening, see `docs/using-claude-code.md`.
