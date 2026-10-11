# Design principles

The rules this story was written to. They matter if you edit a card, add a character or rewrite a scene: following them is what keeps 52 people able to play without a referee. They are distilled from the production notes of the original party and from the review checks in [`scripts/`](../scripts/README.md). The facts of the case itself are in [../story/solution-and-canon.md](../story/solution-and-canon.md).

## 1. A party first, a puzzle second

Vale Meridian is meant to get people talking, gossiping, questioning and making discoveries. The mystery gives those conversations a purpose; it does not have to be solved by everyone. Different guests hear different stories and form different suspicions, and the differences are what they will discuss.

So the test of a change is *does it give guests an understandable clue and an interesting reason to talk*, not *can we prove every guest receives every fact*. Do not turn play into a rigorous evidence-distribution exercise.

## 2. The network is the game

Evidence travels because one guest has a reason to speak to another. Each of them has their own interests and their own conversations.

**Do not replace conversations with:**

- designated information hubs;
- meetings of seven contacts;
- players collecting and redistributing complete case summaries;
- group evidence briefings;
- delivery confirmations or listener checklists;
- anyone responsible for making sure everybody knows everything;
- a Game Master speech that supplies facts which failed to circulate.

If a fact must travel from A to B to C, give each pair its own reason to talk in its own card. Do not make A responsible for briefing B and C.

A core fact may have more than one route so that a missed conversation does not stop the evening. That is redundancy, not a requirement that every route is completed.

## 3. Writing a card

A normal card should naturally answer three questions *for the writer* (never as printed headings or a three-part template):

1. What do you know?
2. Why does it matter now?
3. Which **one** named person should you speak to next?

Then:

- **Prose in the character's voice**, short and explicit. A guest at a busy party should understand it in roughly 20 to 40 seconds. In practice the original Round 1 to 3 cards were trimmed to roughly 65 to 80 words; evidence cards and a dramatic revelation may run longer.
- **One next person.** The exception is Round 0, where a card names a small group of three or four who are all sent to each other.
- **Use full character names** for directions. Never put seat numbers, table names, "your table" or "go and tell your table" on a card: guests will be reseated, and the cards must still work.
- **Give the conversation a purpose**: a suspicion to test, a secret to confront, an object to compare, something the other person may understand.
- **Remind, do not assume.** A short reminder of a relevant earlier fact helps (say what scandal a character paid to keep quiet, not just "protect your name"). If earlier cards never define a secret, flag the gap; do not invent a new scandal to fill it.
- **Do not duplicate** the same fact in the narrative, a message block and two delivery instructions.
- **Do not add "PLAY NOTE" or supplied-recollection paragraphs.** The card carries what the character knows.

## 4. Every question has an answer

A person who is sent to ask a question must be able to get an answer from the facts the other person has been given by that round, **without assuming that an earlier conversation took place** and without relying on anyone's private knowledge. The `clue_answer_contracts` and `local_clue_exchange_sources` tables record exactly where each answer sits, and `scripts/review_current_social_graph.py` checks them. When you change a question, check its answer; when you change an answer, check who asks.

Introductions and third-party mentions get the same care. [`scripts/handshake_items.py`](../scripts/handshake_items.py) lists every place one card relies on another character having something to say back. A person reads them and records a verdict with `record_handshake_reviews.py`; the review reports anything new or changed since it was read.

## 5. Shared discovery

**The murderer discovers their own guilt from the evidence alongside everyone else.** Nobody, the murderer's player included, is handed the solution in advance.

Before the conclusion, do not label the murderer as such, give them a remembered poisoning, or have them insist they are innocent. Their Round 0 card gives them a motive (Vale means to play a recording that would expose the contract wrecking their comeback) and a task: Scooter hands them a sealed compact, "Beverly's sample, for Vale", and they set it unseen beside his decanter while Spinny's music distracts the room. Nothing says what the compact holds. That comes out progressively, with everyone else: in Round 2 they ask what the ingredient is for, in Round 3 they recall that Beverly called it an undiluted multi-dose sample, and they read the laboratory report on their table like every other guest.

This is a convention of shared discovery, not an amnesia subplot. The murderer's player knows what they did on the night (they set the compact by the decanter); what the evidence reveals, with everybody else, is what it meant. What is new to them at the finale is the confession and being named in front of the room, which is why their speech is handed over cold and the Game Master offers to read it for them.

Round 0 is arrival mingling before the murder. The arrival cards must not say who will die or when.

## 6. The Game Master facilitates

The Game Master hands out cards, explains the session, manages time and staging, and helps people find the person named on a card. The Game Master may hand out evidence such as a laboratory report, photographs or a taxi-driver note.

The Game Master does **not** announce witness accounts, summarise the case or invent missing testimony during Rounds 1 to 3. The first public explanation of the evidence is the conclusion in Round 4, after the tables have written their own answers. Keep new physical evidence to one or two items per round; this is an allowance for exhibits, not a reason to produce a packet for every guest.

Donna is an investigator, not the evidence's courier or communications manager. Donna hands the laboratory report to every table because it is a physical object, and does not collect confirmations.

## 7. Evidence is practical

- Use dummy props: an empty compact, dummy payments, ordinary glassware. Nothing real is added to food or drink; nobody swabs real clothing.
- The "laboratory findings" are one typed report. It states what the chemistry shows and what it cannot show.
- Sightings, movements and alibis do not belong in the laboratory report. They reach Donna through conversations with guests who can credibly supply them.
- A photograph or a document is released only when a guest has a reason to hold it, and never so that it identifies the culprit on its own.

## 8. Honest limits

A witness knows only what they could see, from where they stood, for the interval stated. Do not strengthen an account with invented staff calls or statements, and do not make an innocent character prove a complete alibi where none is supplied. Corroborating each other is not an independent alibi. Clear a red herring by giving the character supplied facts, not a blanket claim of innocence.

## 9. Pre-party briefings are a promise

Characters receive their briefing before the party. Do not change what a briefing says after it has been sent; add new facts through arrival and later-round cards instead. This is why a few cards open by developing something the briefing only hints at (Beverly's separate dish, Peter's twin-brother role). If you need to change a briefing, send the new one.

## 10. The finale holds nothing back for the room's sake

Do not introduce decisive new evidence after the accusations. Keep the murderer's confession withheld until the public conclusion; offer to read it. The arrest involves no physical restraint. Return the room to the party promptly.

## 11. Pre-printed question notes

A note's draft is written in the asker's voice and never carries the answer, or the asker's own secret, because other guests may carry the note across the room. Keys (`Q2-06`) never change once issued: a new cross-table card takes the next free number in its round. `scripts/cross_table_notes.py` reports notes that are missing, stale or orphaned.

## 12. Tone and period

1980s glamour, affectionate satire, an Agatha Christie atmosphere, PG-13. Fictional evidence belongs to 10 October 1986; keep that date distinct from your party's. Use British English throughout the cards, and do not invent a new scandal merely to fill a gap.
