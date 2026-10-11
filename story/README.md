# The story

Everything a host needs to read. **All of it gives the solution away.** The files marked *generated* are produced from the database by a script and should not be edited by hand; the others are written by hand and are read by the Print Studio when it prints them.

| File | For | What it is |
|---|---|---|
| [solution-and-canon.md](solution-and-canon.md) | Host, editors | The case, the timeline, the witness limits, the evidence and the seven pillars |
| [gm-run-sheet.md](gm-run-sheet.md) | Game Master | The running order: what to release, hand over and say, step by step, round by round |
| [round0-spinny-running-order.md](round0-spinny-running-order.md) | DJ Spinny T | Everything Spinny does in Round 0: the arrival, the people to meet, the one music cue at the toast |
| [round4-closing-sequence.md](round4-closing-sequence.md) | Game Master, Spinny, Donna | The finale in one script: every line, four music cues, the standing elimination, the arrest, the credits. Contains `GM` and `SHARED` blocks (see below) |
| [round4-murderer-speech.md](round4-murderer-speech.md) | The murderer's player | The short closing speech, read cold, handed over once |
| [physical-props.md](physical-props.md) | Host | *Generated.* The 39-item preparation checklist: toast and event setup, evidence, accessories, printing, and story-only references. Source: `print-studio/source/physical-preparation.json` |
| [cards.md](cards.md) | Host, editors | *Generated.* Every character with their pre-party briefing and every card, round by round, and who each card sends the player to |
| [conversation-map.md](conversation-map.md) | Editors | *Generated.* A table of every "who is sent to whom", by round, with the tables involved |
| [photo-briefs.md](photo-briefs.md) | Host | *Generated.* What each of the eleven pictures must show |
| [seating-plan.md](seating-plan.md) | Host | *Generated.* The sample seating, by table |

## How the finale marks its readers

The finale sheet is one source printed as three copies. Text between `<!-- GM -->` and `<!-- /GM -->` prints on the Game Master's copy only. Text between `<!-- SHARED -->` and `<!-- /SHARED -->` prints on the copies for Spinny and Donna only, where the murderer's name appears as **[THE NAME]**. Everything else prints on all copies. Because it is one file, the copies cannot drift apart, and a test checks that the shared copy never names the murderer.

The speech is separate on purpose: it is handed over once, at step 6, to someone who has never seen it.

## Regenerating

```bash
python3 scripts/export_story_reader.py      # cards.md, conversation-map.md, photo-briefs.md
python3 scripts/export_current_seating.py   # seating-plan.md
python3 print-studio/scripts/preparation.py # physical-props.md
```
