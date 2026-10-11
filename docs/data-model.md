# The event database

[`data/valemeridian-event.sqlite`](../data/valemeridian-event.sqlite) is the single source of truth: the characters, every clue card, the conversation network, the seating, the props and the review history. The Print Studio and the story readers are generated from it. Open it with any SQLite client (`sqlite3`, DB Browser for SQLite, a notebook); the scripts open it read-only unless they say otherwise.

The sample roster is anonymous, so the file is safe to browse. Once you import your own guests it holds their names; see [casting-and-seating.md](casting-and-seating.md#privacy).

## Conventions

- **`local_*` tables** hold the editorial and event data added around the core story tables: overrides, conversation records, reviews, seating positions, the room layout.
- **`plan_id`** on many tables names the editing pass that wrote the row (for example `social-clue-rewrite-v5-2026-09-09` or `cross-table-notes-2026-09-19`), so a row can be traced to the change that made it. `status` values you will meet: `active`, `retired`, `superseded`, `source_checked`.
- **Clue ids** are stable and not always descriptive: `CLUE122` and `CLUE_VV_R2` are Donna's two separate Round 3 records, and `CLUE_GM_R3_01` lives in Round 4 despite its name. Never renumber a card; add a new one.
- **Rounds** are 0 to 3; `NULL` means the private toast cue, released in Round 0.
- **Names in targets** must match `characters.character_name` exactly. A target that matches nobody is reported by the review script.

## The story

| Table | Rows | What it holds |
|---|---:|---|
| `characters` | 57 | One row per character: `character_name`, `character_type` (Core Suspect, Supporting, Victim, Host, Non-acting host role), `assigned_subplot`, `status`, `description` (the pre-party briefing, ending in the private objective and dress guidance), `dress_guidance`, `secret`, `evidence_role`, `gameplay_function` |
| `plots` | 10 | The nine subplots and a Game Master canon note: title, description, the character who is the legitimate suspect |
| `clues` | 226 | One row per card. `clue_content` is what prints; `clue_text_original` is the card's original brief, a one-line note of what it was first meant to do; `targets_json` lists the named people the card sends the player to; `who_reveals` is the owner's name; `status` is `active` (211) or `retired` (15) |
| `clue_targets` | 311 | The same targets, one per row, in order (`target_order`) |
| `local_clue_record_kinds` | 226 | The kind of each card: `ordinary` (printed to guests), `performance` (private to a performer), `facilitation` (private to the Game Master) or `artifact` (a shared exhibit, the laboratory report) |
| `local_clue_overrides` | 226 | The approved text of each card at its last editing pass, with a `change_summary` and the editorial `criterion` it satisfied |
| `local_character_overrides` | 2 | Approved changes to a character's briefing or secret |
| `local_character_case_facts` | 54 | The canon per character: motive strength, means and access, opportunity at the decanter, alibi status, a case summary and the cards that evidence it |
| `local_clue_release_steps` | 8 | The release steps printed on the round dividers |
| `game_prop_requirements` | 6 | The physical props the story needs, by round |
| `local_evidence_photos` | 12 | Each picture: file name, title, who holds it, round, printed caption, brief, size, copies (see [evidence-photos.md](evidence-photos.md)) |
| `local_cross_table_notes` | 60 | The pre-printed question notes. `note_key` (Q1-01 ...) never changes; `clue_sha` fingerprints the card text so a note is flagged stale if the card changes after the draft was written |

## Checks and history

| Table | Rows | What it holds |
|---|---:|---|
| `clue_answer_contracts` | 636 | For each question card, what the person it sends you to can answer, from which source card, available by which round. 143 are `source_checked`, 493 are `superseded` |
| `local_clue_conversations` | 311 | Every conversation card: speaker, target, kind (`social`, `question`, `tell`), purpose and the source quotations |
| `local_clue_exchange_sources` | 149 | The exact passages that answer a question, and the tables of the two people |
| `local_handshake_reviews` | 544 | A person's recorded read of an introduction, a third-party mention or a question, with a fingerprint of both cards so a change reopens it. The review script reports unread and changed items |
| `clue_quality_findings` | 655 | Findings from the editorial reviews and how each was resolved |
| `local_quality_change_log` | 920 | Hashes of cards and characters before and after each editing pass |
| `local_story_decisions` | 62 | The design decisions and the reasons for them, in plain prose: a useful read for anyone editing the story |

## Guests and seating

These tables hold the **sample roster**. Replacing it is what [casting-and-seating.md](casting-and-seating.md) is about.

| Table | Rows | What it holds |
|---|---:|---|
| `events` | 1 | The event record (`valemeridian`) |
| `people` | 54 | `person_id` (`guest-01` ...), `display_name`, optional `dietary_notes` |
| `event_guests` | 54 | Attendance, party size, `real_world_group` and booking contact |
| `character_assignments` | 54 | Which person plays which character, and how the assignment was made |
| `children` | 0 | Optional: a child guest's name and who they sit with (empty in the sample; the cameo seat is an ordinary seat) |
| `menu_orders` | 0 | Optional starter, main and dessert per person, printed on place cards |
| `seating_plans` | 1 | The approved plan (`approved-plan`) |
| `seat_assignments` | 54 | The plan itself: `table_number`, `seat_number`, guest and character |
| `local_seat_positions` | 54 | The angle of each chair around its table, for the seating diagrams |
| `local_room_plan` / `local_room_layout` | 1 / 8 | The floor outline, room names, and where each table stands |
| `current_guest_summary` | view | Guests joined to their characters, briefings and dress guidance |

## Reading it

A few queries to start with:

```sql
-- Every active card in Round 2, with its owner
SELECT clue_id, character_name, clue_title FROM clues WHERE status='active' AND round=2 ORDER BY character_name;

-- The characters most often asked about
SELECT t.target_name, COUNT(*) AS cards
FROM clue_targets t JOIN clues c USING (clue_id)
WHERE c.status='active' GROUP BY 1 ORDER BY cards DESC LIMIT 10;

-- Who sits at table 7
SELECT seat_number, guest_name, character_name FROM seat_assignments WHERE table_number=7 ORDER BY seat_number;

-- Cards that are private to a performer or the Game Master
SELECT c.clue_id, c.character_name, k.record_kind
FROM clues c JOIN local_clue_record_kinds k USING (clue_id)
WHERE c.status='active' AND k.record_kind IN ('performance','facilitation');
```

For a readable view of the same data, use [../story/cards.md](../story/cards.md) and [../story/conversation-map.md](../story/conversation-map.md), generated by `scripts/export_story_reader.py`.

## Writing to it

Do not edit the file by hand while the Print Studio is running a snapshot. To change a card or the roster, follow [editing-the-story.md](editing-the-story.md): take a backup, edit, regenerate the derived files, run the checks.
