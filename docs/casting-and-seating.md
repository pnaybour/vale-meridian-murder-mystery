# Casting and seating

The kit ships with a **sample roster**: "Guest 01" to "Guest 54" already assigned to characters and seated across eight tables. The tables, seats and characters are the tested arrangement. What you change is **who plays each character**.

> **Keep your guests' names private.** Once you import real names, `data/valemeridian-event.sqlite` and `print-studio/lib/event.json` contain them. Work in a private copy of the repository, and do not push either file to a public repository. See [Privacy](#privacy).

## Quick version

```bash
python3 scripts/roster.py export                  # writes roster.csv
# open roster.csv in a spreadsheet and fill in the guest column
python3 scripts/roster.py import roster.csv       # preview: shows what would change
python3 scripts/roster.py import roster.csv --apply
cd print-studio && npm run snapshot               # refresh badges, place cards, signs and so on
```

`import` makes a backup of the database in `data/backups/` before it writes, and refuses to run if anything in the file does not match the plan.

## The roster file

One row per seat; the first three columns identify the seat and must not be edited.

| Column | Meaning |
|---|---|
| `table`, `seat`, `character` | Which seat this is, and the character who sits there. Checked against the plan on import |
| `guest` | The player's name as it should print on badges, place cards, signs and the seating plan. Required, and unique |
| `group` | Optional. Guests with the same value belong together (a couple, a family, a work party). The first guest named in a group is recorded as its booking contact. Blank for none |
| `dietary` | Optional. Printed on the table signs as short flags: `GF`, `V`, `VEGAN`, `PESC`, `HALAL`, `KOSHER`, `NUT ALLERGY`, `NO SHELLFISH`, `DAIRY FREE`. Anything the studio does not recognise, or that contains "no", "not", "without" or "except", prints as `DIET: CHECK NOTE` so a person reads it |

## Choosing who plays whom

- **Start with the people who perform.** Settle the Game Master (the "Family Solicitor"), Vincent/Peter Vale, DJ Spinny T, Inspector Donna Reed and the murderer first. See [host-guide.md](host-guide.md) for what each has to do. Everyone else only has to talk.
- **The murderer's player should enjoy a reveal.** They do not know the finale will name them until it does, and they read a short speech cold (or have it read to them).
- **Use the briefings.** Every character has a one-paragraph briefing with dress guidance in [../story/cards.md](../story/cards.md). A nod towards the character or the 1980s television theme is plenty.
- **Seat people who should be together by choosing characters, not tables.** Every character already belongs to a table, arranged so that most conversations are with someone nearby. Put the people who should sit together on characters at the same table. The `group` column records who belongs together.
- **The child.** One seat is a child's cameo, the Helicopter Pilot. It has no clues and no duties. Put it beside two adults who will look after them.
- **Which characters are "core suspects".** Seventeen are marked as core suspects in the database (`characters.character_type`). They carry the main plot. Give them to guests who will enjoy being in the thick of it.

## Seat numbers

Some tables skip a seat number (for example table 1 has seats 1 and 3 to 8). That is deliberate: it is the arrangement the plan was tested with. Seats print in order and the numbers do no harm.

## Different numbers and groups of people

The shipped plan has 54 seats at eight tables, and your party will not. This section covers each case. The shortest route through all of them is [Claude Code](using-claude-code.md#different-numbers-and-groups-of-people), which does the editing and the checking; what follows is what it does, and what you can do by hand.

### The shape you are fitting into

| Table | Seats | Who is there |
|---:|---:|---|
| 1 | 7 | The murderer (who performs a closing speech) |
| 2 | 9 | The largest table |
| 3 | 5 | Scooter (carries the compact) |
| 4 | 7 | Vincent / Peter Vale (the performer who plays both twins) |
| 5 | 7 | Vance Vellum (photographs), and the child's cameo seat |
| 6 | 6 | |
| 7 | 7 | DJ Spinny T, Inspector Donna Reed, Dakota Steele, Leo Lights, and the Game Master's seat |
| 8 | 6 | Wanda Wires |

Each character already belongs to a table, arranged so that most conversations are with someone nearby ([network-analysis.md](network-analysis.md)). Fitting your guests in means choosing who plays whom, not where the characters sit.

### Groups: couples, families and friends

Put each group in the `group` column of the roster: guests with the same label are one group. Then give a group characters **at the same table**. A group of up to the table's size can fit; the largest table seats nine, so a group of ten or more cannot sit together and has to split.

- `scripts/roster.py import` previews the result and reports every group that is **split across tables**, naming the group, its guests and the tables. Fix the split, or accept it, before you apply.
- The first guest named in a group is recorded as its booking contact. Groups are otherwise only a label (they are not printed).
- **The performing seats are not interchangeable.** Table 7 holds four performers and the Game Master. A group that sits there should be willing to take those parts; a group that would rather not should be at table 2 or 6, which have no performers. The murderer's seat is at table 1, Vincent/Peter's at table 4.
- **Groups cost a little capture.** The shipped plan was built so that real families and couples sit together, and gives up about 1.5 points of pair capture for it (59.7% against 61.2% for an unconstrained search). Keep groups together; the loss is small. See [network-analysis.md](network-analysis.md#the-optimiser).

After importing, check with the review script and with this query, which should return no rows:

```sql
SELECT real_world_group, COUNT(DISTINCT table_number) AS tables
FROM seat_assignments WHERE real_world_group IS NOT NULL
GROUP BY real_world_group HAVING tables > 1;
```

### The same number of guests (or up to 52 players)

Export the roster, fill in the guest column, import it ([quick version](#quick-version)). Nothing about the story changes.

### Fewer guests

Each character you drop takes their four cards with them, and every other card that sends a player to them, or mentions them, needs editing. Use the cost tool to choose whom:

```bash
python3 scripts/retirement_cost.py                    # the cheapest characters to retire, one at a time
python3 scripts/retirement_cost.py --count 6          # a suggested six, in order
python3 scripts/retirement_cost.py --remove "Cassette Carl,Wendy Woke"   # exactly which cards to edit
```

It never suggests a performer, and never a set that leaves a case pillar with nobody to supply it. For the shipped cast the cheapest characters cost four card edits each; retiring the first six it suggests (Cassette Carl, Wendy Woke, Lady Helena de Brissac, Sasha Smirnoff, Chuck Chambers, Brenda Blip) needs nine cards edited in all, and twelve needs about fourteen, out of 207. The network is resilient, so cost is not the limit; **whether the story still holds is**. The tool counts network cost only. It cannot see that two characters are a couple (Frankie Faith and Lola Lasalle), mutual alibis (Cassie Chase and Beverly Steele), or watch each other across the evening (Johnny Maxwell and Robbie Rayne, DJ Spinny T and Ricky Blaze): retire both of a pair or neither, and read the cards of anyone you retire.

To retire a character (this is the whole procedure, and it was run end to end on a copy, retiring two characters from the shipped cast):

1. **Edit the cards that name them** (`retirement_cost.py --remove ...` lists them): reword the card text and update `clues.targets_json` and the `clue_targets` rows.
2. **Retire their cards and the character:** `UPDATE clues SET status='retired' WHERE character_name IN (...)` and `UPDATE characters SET status='retired' WHERE character_name IN (...)`.
3. **Retire their question notes and answer contracts:** set `local_cross_table_notes.status='retired'` for notes from or to them, and `clue_answer_contracts.status='superseded'` where they are the target or owner.
4. **Free their seats:** delete their rows from `seat_assignments`, `character_assignments`, `event_guests`, `local_seat_positions`, `menu_orders` and `people`.
5. **Re-space the chairs:** `python3 scripts/register_seat_positions.py --apply`.
6. **Regenerate and check** ([editing-the-story.md](editing-the-story.md)).

On the copy, the two retirements left 50 players and 52 seats; every tool ran; pair capture moved from 59.7% to 59.4% and the mean solve index from 68.6% to 67.5%; and all 15 print tests passed with no edits, because they count from the database. One tool needed a fix along the way (the question-note check refused to run while it held drafts for retired cards; it now ignores them).

### More guests than 52 players

The cast is fixed at 52 players, so the options are:

- **Two people share a character.** Put both names in the `guest` column, for example `Ann & Bob`; they read the same cards and play the part together. The badge, place card and table sign print the combined name (a 40-character name fits). Good for couples who would rather not be apart, and for a child with a parent.
- **Guests who do not play**, who watch, help the Game Master or serve. Nothing in the kit needs them.
- **New characters.** Claude Code can write them to the [design principles](design-principles.md), add them to the network and run the review, but it is a real piece of writing: use plan mode, and read every card.

### A different number or size of tables

Tables are arranged around the clue network, so changing them changes capture. Find out first:

```bash
python3 scripts/optimise_seating.py --tables 6 --size 9
```

For the shipped cast the optimiser reaches 66.2% pair capture with six tables of nine, 62.6% with seven of eight, 61.2% with eight of seven, 59.7% with ten of six and 56.8% with nine of six: bigger tables keep more conversations at the table. It changes nothing; applying a new arrangement means updating `seat_assignments`, `ROTATIONS` in `scripts/register_seat_positions.py` and `TABLES` in `scripts/register_room_layout.py`, re-drafting the question notes for cards that have newly become cross-table, then re-running the review. There is no one-command script for it; Claude Code can do it, but of the cases here it is the least exercised. Prefer to keep the eight tables and change who is at them.

## Menus and dietary requirements

- The `dietary` column of the roster fills the table-sign flags.
- Place cards print a three-course menu if the database has one. The sample roster has none, so the cards show only the guest, the character and the table. To add menus, insert rows into `menu_orders` (`starter`, `main`, `dessert` per `person_id`; the person ids are `guest-01` to `guest-54`) and run `npm run snapshot`. Menu text is trimmed at a dash or bracket so that it fits.

## Privacy

The `people`, `event_guests`, `seat_assignments`, `character_assignments` and `children` tables, and the Print Studio snapshot `print-studio/lib/event.json`, are where guests' names, groups and dietary notes live. If you publish your own fork, either keep the sample roster in the public branch and your real roster in a private one, or add these files to `.gitignore` in your private copy and regenerate the snapshot when needed:

```bash
git update-index --skip-worktree data/valemeridian-event.sqlite print-studio/lib/event.json
```

Do not put the guest email addresses of your own party into the repository; this kit does not store them.
