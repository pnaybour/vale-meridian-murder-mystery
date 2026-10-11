# Vale Meridian — social graph, clue capture and table solve index

Read-only review of plan **approved-plan** (Eight-table plan: 54 guests, every role allocated, status approved). No optimisation, seat changes, clue changes or database writes.

**Pair capture 59.7%** (83/139 pair-rounds). **Directed capture 62.2%** (97/156 card directions). **Whole-clue capture 62.2%** (97/156 clues with every target local).

52 investigators, 54 seats, 8 tables.

> The plan record stores no capture score (`clue_capture` is NULL), so there is no historical figure to compare against. The scores above are computed fresh.

## Capture by round

| Round | Same-table pairs | Pair capture | Same-table directions | Directed capture | Cross-table |
|---|---:|---:|---:|---:|---:|
| 1 | 35/43 | 81.4% | 44/52 | 84.6% | 8 |
| 2 | 21/45 | 46.7% | 26/52 | 50.0% | 26 |
| 3 | 27/51 | 52.9% | 27/52 | 51.9% | 25 |
| **All** | **83/139** | **59.7%** | **97/156** | **62.2%** | **59** |

## Clue capture per table

A clue is *fully captured* when every target named on it sits at its owner’s table. Partly captured means some targets are local and some elsewhere.

| Table | Seats | Clues owned | Fully captured | Partly | Not captured | Clue capture |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 7 | 21 | 13 | 0 | 8 | 61.9% |
| 2 | 9 | 27 | 23 | 0 | 4 | 85.2% |
| 3 | 5 | 15 | 9 | 0 | 6 | 60.0% |
| 4 | 7 | 21 | 12 | 0 | 9 | 57.1% |
| 5 | 7 | 18 | 10 | 0 | 8 | 55.6% |
| 6 | 6 | 18 | 11 | 0 | 7 | 61.1% |
| 7 | 7 | 18 | 12 | 0 | 6 | 66.7% |
| 8 | 6 | 18 | 7 | 0 | 11 | 38.9% |

## Table solve index

Seven case pillars are taken from the GM public conclusion (CLUE_GM_R4). A pillar scores 1.0 when one of its owners is seated at the table and 0.60 when an owner is one planned conversation away. **This is evidence access, not a probability.**

| Table | Pillars seated | One conversation away | Absent | Solve index |
|---|---:|---:|---:|---:|
| 7 | 5 | 2 | 0 | 88.6% |
| 1 | 3 | 4 | 0 | 77.1% |
| 2 | 2 | 5 | 0 | 71.4% |
| 5 | 1 | 6 | 0 | 65.7% |
| 6 | 1 | 6 | 0 | 65.7% |
| 8 | 1 | 6 | 0 | 65.7% |
| 4 | 3 | 2 | 2 | 60.0% |
| 3 | 2 | 3 | 2 | 54.3% |

Mean across tables: **68.6%**.

### Pillars absent from each table

- **Table 1** — none
- **Table 2** — none
- **Table 3** — Laboratory link between compact and fatal wine, The two envelope deliveries identified
- **Table 4** — The two envelope deliveries identified, What the payments bought: distraction and silence
- **Table 5** — none
- **Table 6** — none
- **Table 7** — none
- **Table 8** — none

## Table traffic

| Table | Seats / investigators | Own directions | Local | Own-card capture | Outgoing | Incoming |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 7 / 7 | 21 | 13 | 61.9% | 8 | 9 |
| 2 | 9 / 9 | 27 | 23 | 85.2% | 4 | 5 |
| 3 | 5 / 5 | 15 | 9 | 60.0% | 6 | 2 |
| 4 | 7 / 7 | 21 | 12 | 57.1% | 9 | 11 |
| 5 | 7 / 6 | 18 | 10 | 55.6% | 8 | 2 |
| 6 | 6 / 6 | 18 | 11 | 61.1% | 7 | 8 |
| 7 | 7 / 6 | 18 | 12 | 66.7% | 6 | 17 |
| 8 | 6 / 6 | 18 | 7 | 38.9% | 11 | 5 |

## Workload hotspots

Flag: four or more distinct conversation partners in one round.

| Round | Character — guest | Table | Partners | Across tables |
|---|---|---:|---:|---:|
| 2 | Barry Byte — Guest 36 | 6 | 4 | 3 |
| 2 | DJ Spinny T — Guest 43 | 7 | 4 | 3 |
| 3 | Fiona Fringe — Guest 38 | 6 | 4 | 3 |
| 3 | Inspector Donna Reed — Guest 44 | 7 | 5 | 3 |
| 3 | Ronnie Reels — Guest 10 | 2 | 5 | 3 |

## Peer-review audit

**Answerability.** 143 live answer contracts cover 103 question cards; 53 disclosure cards need none. 0 answers not available by the asking round; 0 question cards without a contract.

**Coverage.** 0 investigators never approached; 2 character-rounds with more than three incoming; 0 character-rounds with no direction at all.
- Ronnie Reels round 3: 4 incoming
- Inspector Donna Reed round 3: 5 incoming

**Consistency.** 5 spoken-name collisions; 0 unresolved clue targets.
- shared_first_name: Peter Packard, Peter Vale
- shared_first_name: Ronnie Redhand, Ronnie Reels
- shared_first_name: Tina 'Tank' Thatcher, Tina Tanktop
- shared_surname: Dakota Steele, Dr. Beverly Steele, Rex 'Razor' Steele
- homophone_first_name: Roxie Runway, Roxy Riot

**Handshakes.** 406 items (300 exchange, 106 mention): 230 read and fine, 0 by design, 0 open gaps, 20 never read, 156 changed since they were read.
- changed since read: R0 Angie Vixen → Veronica Vane (`CLUE_ANGIE_R0`, exchange)
- changed since read: R0 Angie Vixen → Lucien Luxe (`CLUE_ANGIE_R0`, exchange)
- changed since read: R0 Brenda Blip → Veronica Vane (`CLUE_BRENDA_R0`, mention)
- changed since read: R0 Cassie Chase → Dr. Beverly Steele (`CLUE_CASSIE_R0`, exchange)
- changed since read: R0 Dakota Steele → Dr. Beverly Steele (`CLUE_DAKOTA_R0`, exchange)
- changed since read: R0 Dr. Beverly Steele → Cassie Chase (`CLUE_BEVERLY_R0`, exchange)
- changed since read: R0 Dr. Beverly Steele → Dakota Steele (`CLUE_BEVERLY_R0`, exchange)
- changed since read: R0 Dr. Beverly Steele → Inspector Donna Reed (`CLUE_BEVERLY_R0`, exchange)
- changed since read: R0 Fiona Fringe → Veronica Vane (`CLUE_FIONA_R0`, exchange)
- changed since read: R0 Fiona Fringe → Lucien Luxe (`CLUE_FIONA_R0`, exchange)
- changed since read: R0 Glenda Gold → Miss Cherry Bomb (`CLUE_GLENDA_R0`, exchange)
- changed since read: R0 Glenda Gold → Graham Greenwell (`CLUE_GLENDA_R0`, exchange)
- changed since read: R0 Graham Greenwell → Glenda Gold (`CLUE_GREENWELL_R0`, exchange)
- changed since read: R0 Graham Greenwell → Miss Cherry Bomb (`CLUE_GREENWELL_R0`, exchange)
- changed since read: R0 Graham Greenwell → Dr. Beverly Steele (`CLUE_GREENWELL_R0`, mention)
- changed since read: R0 Inspector Donna Reed → Dr. Beverly Steele (`CLUE_DONNA_R0`, exchange)
- changed since read: R0 Johnny 'Jet' Maxwell → Rex 'Razor' Steele (`CLUE_JOHNNY_R0`, exchange)
- changed since read: R0 Johnny 'Jet' Maxwell → Roxy Riot (`CLUE_JOHNNY_R0`, exchange)
- changed since read: R0 Larry Loveboat → Rex 'Razor' Steele (`CLUE_LARRY_R0`, mention)
- changed since read: R0 Larry Loveboat → Rex 'Razor' Steele (`CLUE_LARRY_R0`, mention)
- changed since read: R0 Lucien Luxe → Veronica Vane (`CLUE_LUCIEN_R0`, exchange)
- changed since read: R0 Lucien Luxe → Angie Vixen (`CLUE_LUCIEN_R0`, exchange)
- changed since read: R0 Lucien Luxe → Fiona Fringe (`CLUE_LUCIEN_R0`, exchange)
- changed since read: R0 Marianne Moonbeam → Tina Tanktop (`CLUE_MARIANNE_R0`, exchange)
- changed since read: R0 Marianne Moonbeam → Ronnie Reels (`CLUE_MARIANNE_R0`, exchange)
- changed since read: R0 Marianne Moonbeam → Roxie Runway (`CLUE_MARIANNE_R0`, exchange)
- changed since read: R0 Miss Cherry Bomb → Glenda Gold (`CLUE_CHERRY_R0`, exchange)
- changed since read: R0 Miss Cherry Bomb → Graham Greenwell (`CLUE_CHERRY_R0`, exchange)
- changed since read: R0 Miss Cherry Bomb → Dr. Beverly Steele (`CLUE_CHERRY_R0`, mention)
- changed since read: R0 Miss Cherry Bomb → Dr. Beverly Steele (`CLUE_CHERRY_R0`, mention)
- … 126 more changed since read
- never read: R0 Dr. Beverly Steele → Miss Cherry Bomb (`CLUE_BEVERLY_R0`, mention)
- never read: R0 Dr. Beverly Steele → Graham Greenwell (`CLUE_BEVERLY_R0`, mention)
- never read: R0 Dr. Beverly Steele → Ronnie Reels (`CLUE_BEVERLY_R0`, mention)
- never read: R0 Dr. Beverly Steele → Veronica Vane (`CLUE_BEVERLY_R0`, mention)
- never read: R0 Dr. Beverly Steele → Scooter (`CLUE_BEVERLY_R0`, mention)
- never read: R0 Glenda Gold → Polly Premium (`CLUE_GLENDA_R0`, exchange)
- never read: R0 Graham Greenwell → Polly Premium (`CLUE_GREENWELL_R0`, exchange)
- never read: R0 Marianne Moonbeam → Vincent Vale (`CLUE_MARIANNE_R0`, exchange)
- never read: R0 Miss Cherry Bomb → Polly Premium (`CLUE_CHERRY_R0`, exchange)
- never read: R0 Polly Premium → Glenda Gold (`CLUE_POLLY_R0`, exchange)
- never read: R0 Polly Premium → Miss Cherry Bomb (`CLUE_POLLY_R0`, exchange)
- never read: R0 Polly Premium → Graham Greenwell (`CLUE_POLLY_R0`, exchange)
- never read: R0 Veronica Vane → DJ Spinny T (`CLUE_VER_R0`, mention)
- never read: R1 Polly Premium → Lola Lasalle (`CLUE_POLLY_R1`, exchange)
- never read: R1 Polly Premium → Frankie Faith (`CLUE_POLLY_R1`, mention)
- never read: R2 Glenda Gold → Marianne Moonbeam (`CLUE006`, exchange)
- never read: R2 Polly Premium → Barry Byte (`CLUE_POLLY_R2`, exchange)
- never read: R2 Scooter → Dakota Steele (`CLUE_SC_R2`, mention)
- never read: R3 Lola Lasalle → Polly Premium (`CLUE131`, exchange)
- never read: R3 Polly Premium → Inspector Donna Reed (`CLUE_POLLY_R3`, exchange)
- Read these, then record verdicts with `scripts/record_handshake_reviews.py`.

## Limitations

- Capture is seating convenience, not the percentage of facts actually heard or understood.
- These are suggested conversations. Incoming/outgoing describes the named direction, not a guaranteed meeting.
- The solve index measures evidence access from a table, not a probability. It assumes every planned conversation is attempted and ignores unplanned mingling, which in play is a major route.
- Four partners is a workload flag for rehearsal, not an automatic failure.
- A connected graph does not guarantee that all evidence travels to every guest.
