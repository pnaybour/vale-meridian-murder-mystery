# Scripts

Command-line tools that read or edit the event database. Run them from the repository root: `python3 scripts/<name>.py`. They need Python 3.10 or later (developed on 3.11); `register_evidence_photos.py` also needs Pillow (`pip install pillow`).

**Safe by default.** Anything that can write to the database previews first and only writes with `--apply`, after copying the database to `data/backups/`. Anything else opens it read-only.

## For hosts

| Script | What it does |
|---|---|
| [`roster.py`](roster.py) | Puts your own guests on the seating plan. `export` writes a spreadsheet; `import` reads it back (preview, then `--apply`); the preview reports any group that would sit at more than one table. See [../docs/casting-and-seating.md](../docs/casting-and-seating.md) |
| [`retirement_cost.py`](retirement_cost.py) | Fewer players? Ranks the characters by how many other cards would need editing if they were retired, suggests a set (`--count N`), and lists the exact cards to edit (`--remove "A,B"`). Never suggests a performer. Reads only |
| [`optimise_seating.py`](optimise_seating.py) | Suggests which characters should share a table, for a different number or size of tables. Reads the clue network and changes nothing. `--tables`, `--size`, `--fix NAME=TABLE`, `--apart A,B`, `--seed`, `--time` |
| [`render_briefings.py`](render_briefings.py) | Writes one HTML briefing per guest from `templates/character-briefing-email.html`: character, briefing, dress guidance and menu. Nothing is sent |
| [`export_story_reader.py`](export_story_reader.py) | Writes `story/cards.md`, `conversation-map.md` and `photo-briefs.md` from the database |
| [`export_current_seating.py`](export_current_seating.py) | Writes `story/seating-plan.md` from the approved plan |

## Layout and pictures

| Script | What it does |
|---|---|
| [`register_room_layout.py`](register_room_layout.py) | Records the venue: the floor outline, the rooms and where each table stands. Edit `TABLES`, `OUTLINE` and `ROOMS` in the file, preview, then `--apply` |
| [`register_seat_positions.py`](register_seat_positions.py) | Records the angle of every chair, evenly spaced around its table. Edit `ROTATIONS` to turn a table |
| [`check_room_clearances.py`](check_room_clearances.py) | Reports the space behind and between tables on the assumed room: whether people can get past |
| [`register_evidence_photos.py`](register_evidence_photos.py) | Records each picture's brief, size and fingerprint. `--tidy` moves unused artwork aside |

## For editors

| Script | What it does |
|---|---|
| [`review_current_social_graph.py`](review_current_social_graph.py) | The main check, explained in [../docs/network-analysis.md](../docs/network-analysis.md). Scores the clue network against the seating (how many conversations are within a table), the reachability of the seven case pillars from each table, the load on each character, answerability of every question, name collisions, and the handshake and question-note audits. Writes `reports/current-social-graph-<plan>/review.md` and `analysis.json` |
| [`cross_table_notes.py`](cross_table_notes.py) | Checks the pre-printed question notes: missing, stale, orphaned. `--apply` adds missing notes; `--redraft KEY` re-drafts a stale one |
| [`record_handshake_reviews.py`](record_handshake_reviews.py) | Lists introductions, mentions and questions that are new or changed since they were last read, and records your verdicts with `--apply` |
| [`handshake_items.py`](handshake_items.py) | The module that finds those items; used by the review and the recorder |
| [`graph_builder.py`](graph_builder.py), [`seating_optimiser.py`](seating_optimiser.py) | Libraries: build the interaction graph from the cards, and partition it into tables by simulated annealing |

See [../docs/editing-the-story.md](../docs/editing-the-story.md) for how these fit together when you change a card.

## Print Studio scripts

The Print Studio has its own scripts in [`../print-studio/scripts/`](../print-studio/README.md): `export_snapshot.py` (database to print data), `check_snapshot.py`, `build_photos.py`, `print.mjs` (the command-line generator), `table-tents.mjs`, `seating-list.mjs`, and the tests.
