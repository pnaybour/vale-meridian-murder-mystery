# The social network graph and table capture

The clue cards are a network: each card sends its player to a named person, so the whole story is a web of conversations. `scripts/review_current_social_graph.py` turns that web into numbers. It tells you how many of the conversations the seating makes easy (**capture**), whether each table can reach the evidence it needs (**solve index**), and whether every question has an answer. Run it whenever you change the cards, the cast or the seating, and compare the summary before and after.

```bash
python3 scripts/review_current_social_graph.py
```

It reads the database and writes `reports/current-social-graph-<plan>/review.md` (a readable report) and `analysis.json` (everything, for tools). It never changes the database, and it checks that it did not: the file's SHA-256 is compared before and after, and the script stops if it differs. A worked example from the shipped plan is in [../reports/current-social-graph-approved-plan/review.md](../reports/current-social-graph-approved-plan/review.md).

Options: `--plan ID` (default: the one approved plan), `--output DIR`, and `--reachable-weight 0.6` (see [solve index](#table-solve-index)).

## The graph

- **Nodes** are the investigating characters: 52 in the shipped cast.
- **Edges** join two characters when a card sends one to the other. Directions are ignored for the graph: if A's card names B and B's card names A in the same round, that is one edge-round, not two.
- **Edge weight** is the number of distinct rounds in which the pair is connected, so at most 3.
- **Pair-round** is the unit used throughout: one pair in one round. The shipped cast has 139 of them (43 in Round 1, 45 in Round 2, 51 in Round 3).
- **Direction** is a single card sending its player to a single target. There are 156 in Rounds 1 to 3.

**What is in scope.** Only the ordinary guest cards of **Rounds 1 to 3** with explicit targets. Left out on purpose: Round 0 (arrival mingling, which has no seating), the Game Master's and performers' private cards, the laboratory report and the closing sequence. Unplanned chatting is also not modelled, and in play it is a major route; capture is a measure of *how convenient the planned conversations are*, not of how much people will hear.

The graph is built by `scripts/graph_builder.py` from `clues.targets_json`. The review script also cross-checks it: the set of (card, owner, round, target) it derives must equal the targets written on the active cards, or the script stops.

## Capture: how many conversations stay at a table

Seating the people who talk to each other at the same table makes those conversations a few words across the table instead of a walk across the room. Capture counts that, three ways.

| Measure | What it counts | Shipped plan |
|---|---|---:|
| **Pair capture** | Pair-rounds where both people sit at the same table, out of all pair-rounds | 83 of 139 = **59.7%** |
| **Directed capture** | Card directions where the target sits at the owner's table, out of all directions (a reciprocal pair counts twice) | 97 of 156 = **62.2%** |
| **Whole-clue capture** | Cards whose **every** target is at the owner's table, out of all cards. With one target per card in Rounds 1 to 3 it equals directed capture | 97 of 156 = **62.2%** |

**By round.** In the shipped plan, capture is highest in Round 1 and lower after it. That is the design, not a flaw: Round 1 is the first conversation at the seated meal, and Rounds 2 and 3 deliberately send people across the room (with a pre-printed [question note](glossary.md) to carry the question), so the story moves from table to table.

| Round | Pair capture | Directed capture | Cross-table conversations |
|---|---:|---:|---:|
| 1 | 81.4% | 84.6% | 8 |
| 2 | 46.7% | 50.0% | 26 |
| 3 | 52.9% | 51.9% | 25 |

### Clue capture per table

The same idea per table: of the cards **owned** by the characters seated at a table, how many are fully captured, partly captured (some targets local, some not), or not captured. It answers "how much of this table's evening stays at the table?".

| Table | Cards owned | Fully captured | Capture |
|---|---:|---:|---:|
| 2 | 27 | 23 | 85.2% |
| 7 | 18 | 12 | 66.7% |
| 1 | 21 | 13 | 61.9% |
| 6 | 18 | 11 | 61.1% |
| 3 | 15 | 9 | 60.0% |
| 4 | 21 | 12 | 57.1% |
| 5 | 18 | 10 | 55.6% |
| 8 | 18 | 7 | 38.9% |

*(Excerpt of the report; the full table also has seats, partly and not-captured columns.)* A table with low capture is not wrong, but its players will do more walking or more note-passing. Table 8 here is the busiest traveller: 11 of its cards send someone elsewhere.

### Table traffic

For each table: how many directions its own characters hold, how many are local, and how many cross tables **outgoing** (its players walking out) and **incoming** (visitors arriving). A table with high incoming, like table 7 in the sample (17 incoming), is where the Game Master's evidence holders sit: visitors will come to it.

### Workload hotspots

Any character with **four or more distinct conversation partners** in one round is listed, and any character with **more than three incoming** approaches in a round is flagged under Coverage. Four partners is a rehearsal flag, not a failure: it means that person will be busy in that round, so tell them.

## Table solve index

Capture says how convenient the conversations are. The solve index asks a different question: **from this table, can people reach the evidence the conclusion rests on?**

The conclusion rests on **seven case pillars** (listed in [../story/solution-and-canon.md](../story/solution-and-canon.md#the-seven-pillars-of-the-case)): motive, means, opportunity, forensic, arrangement, payment purpose and elimination. Each pillar has a list of characters who can supply it first-hand. For each table:

- a pillar scores **1.0** if one of its owners is seated at the table;
- **0.6** if none is, but one of its owners is one planned conversation away (a neighbour in the graph sits here);
- **0** otherwise (the pillar is *absent*).

The index is the average over the seven pillars, as a percentage. The 0.6 is `--reachable-weight`.

In the shipped plan the mean across tables is **68.6%**. Table 7 scores 88.6% (it holds Donna, Spinny, Dakota and Leo, so five pillars are seated); tables 3 and 4 score lowest, with two pillars absent each, so those tables depend on visitors and on walking. The report lists the absent pillars per table: a short list of what each table must go and ask for.

**This is evidence access, not a probability of solving.** It assumes every planned conversation is attempted and ignores unplanned mingling.

## Round connectivity

For each round the script also computes the **connected components** of that round's graph: the sizes of the groups of characters linked, directly or through others, by that round's conversations (in `analysis.json`, under `rounds[].component_sizes`). A round whose graph falls apart into many small pieces would mean whole sets of players never touch the rest of the story. The overall graph for Rounds 1 to 3 is checked the same way (`totals.all_rounds_component_sizes`), and "never approached" in the audit lists anyone nobody is sent to.

## The peer-review audits

These are mechanical checks that supplement a human reading.

- **Answerability.** Every *question* card (one whose last line contains "Ask" or "Find out") needs an **answer contract**: a record that the person it sends you to can answer from their own card, by that round. The report counts the live contracts (143 in the shipped data, covering 103 question cards), any answer available only in a later round than the question, and any question without a contract. "Disclosure" cards (the speaker owns the fact) need none.
- **Coverage.** Characters nobody is sent to; characters with more than three incoming approaches in one round; characters with no direction at all in a round.
- **Consistency.** Spoken-name collisions (two characters who share a first name or surname, or sound alike when said aloud: Peter Packard and Peter Vale, the three Steeles, Roxy and Roxie), and card targets that match no active character, which stops the script.
- **Handshakes.** Every introduction, third-party mention and question, listed against a recorded human read of the same text. Items that are new or changed since they were read are listed for rereading ([editing-the-story.md](editing-the-story.md)).
- **Question notes.** The pre-printed cross-table notes are checked against their cards: current, stale, orphaned or missing.

## Using it when you configure the evening

The review is your safety net for every change. Run it before and after, and look at the summary lines (`Pair capture`, `directed capture`, `mean solve index`, and the question-note line) and at the audit sections.

| You changed | Watch for |
|---|---|
| Who plays whom, but not the tables | Nothing in the graph changes: capture depends on *characters*, not people. Check only that groups stay together |
| A card's target | The target must exist and be able to answer (answerability); the handshake list shows the new introduction to read; a card that now crosses tables needs a question note |
| **Retiring characters** | Unresolved targets (the script stops until you re-route them); "never approached"; coverage; pillars. In a test, retiring Cassette Carl and Wendy Woke gave 50 investigators, pair capture 59.4% (from 59.7%) and mean solve index 67.5% (from 68.6%) |
| The number or size of tables | Everything moves. Try [`optimise_seating.py`](../scripts/README.md) first: for the shipped cast, 6 tables of 9 reaches 66.2% pair capture, 7 of 8 reaches 62.6%, 8 of 7 reaches 61.2%, 10 of 6 reaches 59.7% and 9 of 6 reaches 56.8%. Larger tables capture more, because more people can reach each other. After reseating, re-run the review and check each table's pillars |

### The optimiser

`scripts/optimise_seating.py` searches for the grouping of characters into tables that **maximises pair capture** (the same quantity as above, over the same graph) by simulated annealing, subject to the table sizes you give it, characters you pin to a table (`--fix`) and pairs you keep apart (`--apart`). It reads the database and changes nothing. For the shipped cast and eight tables of seven it finds 61.2% against the shipped plan's 59.7%: the shipped plan gives up a little capture so that real families and couples can sit together.

That trade-off is real. In an earlier comparison from the original production, a plan tuned only for capture reached 74% but kept only 74% of the real-world pairs together; the plan chosen kept 93% of them together at about 60% capture. If your guests include groups who must sit together, accept a few points of capture.

## Limitations

These are stated in every report too.

- Capture is seating convenience, not the share of facts actually heard or understood.
- These are suggested conversations. Incoming and outgoing describe the named direction, not a guaranteed meeting.
- The solve index measures evidence access from a table; it is not a probability, and it ignores unplanned mingling.
- Four partners in a round is a workload flag for rehearsal, not an automatic failure.
- A connected graph does not guarantee that all evidence travels to every guest.
- The graph covers Rounds 1 to 3 only. The Round 0 reception and the finale are not scored.
