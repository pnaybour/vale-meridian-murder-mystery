# Editing the story

The cards, the clue network and the roster live in one SQLite file. This guide is how to change them without breaking the evening. Read [design-principles.md](design-principles.md) first: it is the rule book the checks enforce.

You do not have to do this by hand. [Claude Code](using-claude-code.md) can make each of these changes, run the checks and report; the steps below are what it does for you.

## The loop

Every change follows the same five steps.

1. **Back up.** `mkdir -p data/backups && cp data/valemeridian-event.sqlite data/backups/before-my-change.sqlite`. `data/backups/` is ignored by git.
2. **Edit** the database (below).
3. **Regenerate** what is derived from it:
   ```bash
   python3 scripts/export_story_reader.py            # story/cards.md, conversation-map.md, photo-briefs.md
   python3 scripts/export_current_seating.py          # story/seating-plan.md
   cd print-studio && npm run snapshot                # lib/event.json, for the studio and the PDFs
   ```
4. **Check.**
   ```bash
   python3 scripts/review_current_social_graph.py     # network, seating, answerability, handshakes, question notes
   python3 scripts/cross_table_notes.py               # question notes: missing, stale, orphaned
   cd print-studio && npm run check:data && npm test
   ```
5. **Read it.** Automated checks supplement a human reading; they do not prove that every conversation happens. Read the changed card aloud, then read the card of the person it sends you to.

## Editing a card

Use any SQLite client. For example, to reword a card:

```sql
UPDATE clues SET clue_content = 'New wording ...' WHERE clue_id = 'CLUE_R1_BEVERLY_01';
```

The tools read `clues.clue_content`, and the print snapshot prints it. Keep the card short and in the character's voice ([design-principles.md](design-principles.md)).

To change **who a card sends its player to**, update `targets_json` *and* the `clue_targets` rows that mirror it (the reviewers read `targets_json`; the story readers and some queries read `clue_targets`):

```sql
UPDATE clues SET targets_json = '["Dakota Steele"]' WHERE clue_id = 'CLUE_R2_BEVERLY_01';
DELETE FROM clue_targets WHERE clue_id = 'CLUE_R2_BEVERLY_01';
INSERT INTO clue_targets (clue_id, target_name, target_order) VALUES ('CLUE_R2_BEVERLY_01', 'Dakota Steele', 1);
```

Names must match `characters.character_name` exactly. Then check, in order:

- Can the person now sent to answer the question, from facts on their own cards by that round? (`scripts/review_current_social_graph.py` lists open items; the `clue_answer_contracts` table records the intended answer source.)
- Does the card still need a **question note**? A card that sends someone to a character at another table gets one. `python3 scripts/cross_table_notes.py` says which are missing or stale; add missing ones with `--apply` after drafting them in the script (`--redraft KEY` re-drafts a stale note).
- Does anything **else** quote or rely on this card? Run `python3 scripts/record_handshake_reviews.py` (or the review) to list the introductions and mentions that are new or changed since they were last read, read them, and record your verdict by re-running it with `--apply` (see its `--help`).

## Adding a card

Insert into `clues` (the owner's `character_id`, `round`, `clue_title`, `clue_content`, `targets_json`, `status='active'`) and `local_clue_record_kinds` (`ordinary`, `performance`, `facilitation` or `artifact`). The snapshot export needs a record kind for every active card. Then mirror `clue_targets`, and follow the checks above. The Print Studio tests count cards, seats, badges and pictures from the database, so they need no edits.

## Retiring a card or a character

Set `clues.status` to `'retired'` rather than deleting. Re-route every card that sent someone to the retired character (`clue_targets` shows who), move any fact that only they supplied, and run the review: it reports cards that point at a retired character and facts nobody can still be asked about. The full procedure, with the commands, is in [casting-and-seating.md](casting-and-seating.md#fewer-guests); `scripts/retirement_cost.py` shows what each retirement costs. The original production did this twice; see `local_story_decisions` for the reasoning.

## Editing a character's briefing

Change `characters.description` (the whole briefing, ending with the private objective and dress guidance) and, if the dress guidance changed, `characters.dress_guidance` and `characters.secret`. Briefings are a promise: do not change one after you have sent it ([design-principles.md](design-principles.md#9-pre-party-briefings-are-a-promise)).

## Editing the Game Master scripts

The running order, the Round 0 sheet for Spinny, the finale and the murderer's speech are Markdown files in [../story/](../story/). The Print Studio reads them when it builds the snapshot, so run `npm run snapshot` afterwards. The finale marks what each reader may see: text between `<!-- GM -->` and `<!-- /GM -->` prints on the Game Master's copy only; text between `<!-- SHARED -->` and `<!-- /SHARED -->` prints on Spinny's and Donna's copies only. One source, so the copies cannot drift apart. The shared copies must never contain the murderer's name; a test checks it.

The props checklist is generated from [`print-studio/source/physical-preparation.json`](../print-studio/source/physical-preparation.json): edit that file and run `python3 print-studio/scripts/preparation.py` to rewrite `story/physical-props.md`.

## The editing history inside the database

The tables that end in `change_log`, `findings`, `contracts` and `decisions` record how the cards got to where they are: what was reviewed, what was decided and why. They are not needed to run the game. `local_story_decisions` in particular is worth reading before you reverse a decision; it gives the reason each rule exists.

## Sending a change back

If you improve the kit, please open an issue or pull request. Run the whole check list above first, include the regenerated files, and say which cards changed and why. See [../CONTRIBUTING.md](../CONTRIBUTING.md).
