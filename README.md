# Vale Meridian: a 1980s TV-studio murder mystery

*A Night of Glamour & Hidden Truths.* A complete murder mystery party for up to 54 guests and a Game Master, set at a television gala on 10 October 1986: characters, clue cards, a running order, props, a scripted finale, and a print studio that turns it all into badges, place cards, table signs and A4 handouts.

> **Spoilers.** Everything in this repository except the guest-facing printouts gives the solution away. If you are going to play, not run, this game, stop reading here.

> **Disclaimer.** Vale Meridian is a work of fiction. "Vale Meridian", "Vale Meridian Studios", every character, event, organisation and logo in it are invented for a party game. It is not connected with, endorsed by or in any way linked to any real company, brand, product or person called Vale Meridian or anything similar, and any resemblance is coincidental. The logo and artwork are made-up game props, not a trade mark.

## Essential: develop your evening with an AI coding agent

**Use an AI coding agent to develop your evening: [Claude Code](https://code.claude.com/docs/en/overview), [OpenAI Codex](https://developers.openai.com/codex) or a similar tool. We treat it as essential.** The developer of this kit settled on **Claude Code**, so the guides, prompts and examples assume it; any agent that can read files and run commands will do the same job.

This kit is a database of 52 characters and 207 clue cards that depend on one another: every card sends its player to a named person who holds the other half of the story. Fitting it to your party means changing that network without breaking it: your guests, your occasion, fewer or more people, who sits with whom. You can do that by hand, but it is slow and easy to get wrong. An agent reads the whole story, makes the change, runs the checks and tells you in plain English what it did. You do not need to be a programmer.

This repository is set up for it. [`CLAUDE.md`](CLAUDE.md) (and [`AGENTS.md`](AGENTS.md), the file Codex and many other agents look for, which points to it) teaches the agent how the kit fits together and the rules that keep 52 people able to play without a referee, so every session starts informed.

**Get started in three steps**

1. [Install Claude Code](https://code.claude.com/docs/en/overview) (it runs in a terminal, an IDE, the desktop app or the browser), or your agent of choice.
2. Download this repository and open its folder in the agent.
3. Ask: *"Read the README and docs/the-game.md, then tell me what I need to decide before I send invitations."*

**Then tell it about your party**

- *"My party is a [retirement / birthday / reunion] at [venue] on [date] for about [number] guests. Set it up, and list anything in the story that assumes a different occasion."*
- *"I have 44 guests, in these groups: [Ann, Bob and their two children], [Chris and Dee], [...]. Work out who plays whom, keep each group at one table, and show me the preview before you apply anything."*
- *"Read story/cards.md and list problems by card id, following docs/design-principles.md. Don't change anything."*

An agent can reword cards, cast guests and keep groups together, cope with a smaller cast, write cue sheets and briefing emails, and run every check. It cannot print, buy the decanter or make the pictures, and it should ask before it changes anything creative. [docs/using-claude-code.md](docs/using-claude-code.md) has the full list, safe habits, and how to keep your guests' names out of the conversation until you need them.

## The idea

The founder of Vale Meridian Studios, Vincent Vale, hosts a glittering gala. He raises a toast, drinks from his private decanter and collapses. Fifty-odd guests, each playing a character with something to hide, have the rest of the evening to work out who did it.

It is designed for a real party, not a seminar. Nobody has to hear every fact or reach the right answer; the mystery gives people a reason to talk, gossip and question one another. Each card is short, written in the character's voice, and sends its player to one named person with a reason to talk to them. The Game Master hands out envelopes, keeps time, and gives a scripted conclusion.

| | |
|---|---|
| **Guests** | Up to 54 seats at eight tables: 52 players, a Game Master (the host, a non-acting "Family Solicitor") and a child's cameo role |
| **Characters** | 52 player roles, each with a pre-party briefing, dress guidance and a secret (17 core suspects, 34 supporting, and the victim, who is played by the same person as his twin) |
| **Cards** | 207 clue cards: 51 arrival cards (Round 0) and 52 in each of Rounds 1–3; plus 3 private performer cards and a laboratory report |
| **Structure** | Round 0 (arrival and the staged murder), Rounds 1–3 (investigation), Round 4 (accusations, a standing elimination, the arrest and the credits) |
| **Props and evidence** | Compact, envelopes, passport, taxi note, a laboratory report, 11 photographs and prop money, all specified and printable |
| **Setting** | The reception and a seated dinner. The cards never mention tables, so seating can change on the night |

## What is in the box

| You want to | Go to |
|---|---|
| Understand the game and how an evening runs | [docs/the-game.md](docs/the-game.md) |
| Develop your evening with an AI coding agent (essential) | [docs/using-claude-code.md](docs/using-claude-code.md) |
| Run it: a timeline from invitations to the last bow | [docs/host-guide.md](docs/host-guide.md) |
| Put your own guests on the plan | [docs/casting-and-seating.md](docs/casting-and-seating.md) |
| Print the cards, badges, signs and envelopes | [docs/printing.md](docs/printing.md) and [print-studio/](print-studio/README.md) |
| Make the photographs and props | [docs/evidence-photos.md](docs/evidence-photos.md) |
| Read every card and the Game Master's scripts | [story/](story/README.md) |
| Know the solution | [story/solution-and-canon.md](story/solution-and-canon.md) |
| Edit or extend the story | [docs/editing-the-story.md](docs/editing-the-story.md) and [docs/design-principles.md](docs/design-principles.md) |
| Query the data | [docs/data-model.md](docs/data-model.md) |
| Understand the conversation graph and table capture scores | [docs/network-analysis.md](docs/network-analysis.md) |
| Run the tools | [scripts/README.md](scripts/README.md) |
| Check what is known to be imperfect | [docs/known-issues.md](docs/known-issues.md) |
| Look up a term | [docs/glossary.md](docs/glossary.md) |

## Quick start

You need [Node.js](https://nodejs.org) 22.13 or later and Python 3.10 or later with [Pillow](https://python-pillow.org) (`pip install pillow`).

```bash
git clone https://github.com/pnaybour/vale-meridian-murder-mystery.git
cd vale-meridian-murder-mystery/print-studio
npm ci
npm run photos       # makes placeholder pictures; see docs/evidence-photos.md
npm run dev          # open the address it prints, normally http://localhost:3000
```

On a Mac you can double-click `print-studio/start-print-studio.command` instead.

The studio opens with a **sample roster** ("Guest 01", "Guest 02" and so on) already seated. Browse the cards, open any PDF proof, and download a print pack. To use your own guests, follow [docs/casting-and-seating.md](docs/casting-and-seating.md); it takes a spreadsheet and one command.

To print without the browser, for example every Round 2 card:

```bash
cd print-studio   # if you are not there already
node scripts/print.mjs --category clues --round 2 --output output/round-2.pdf
```

## Make it yours

1. **Event details.** Edit [data/event.json](data/event.json): hosts, date and venue print in the card footers, seating plans and signs. Then `npm run snapshot` in `print-studio/`.
2. **Guests.** Export the roster with `python3 scripts/roster.py export`, fill in the guest column, import it with `python3 scripts/roster.py import roster.csv --apply`.
3. **Pictures.** The photographs are placeholders that carry their own brief. Put your pictures in [data/artwork/](data/artwork/README.md) under the file names it lists and run `npm run photos`.
4. **Pre-party briefings.** Each character's briefing is in [story/cards.md](story/cards.md). `python3 scripts/render_briefings.py` writes one ready-to-send HTML email per guest from the template in [templates/](templates/character-briefing-email.html); nothing is sent for you.
5. **Props and rehearsal.** Work through [story/physical-props.md](story/physical-props.md), then rehearse the three scripted moments (the toast, the arrest, the credits) with the people who perform them.

## Repository layout

```
data/            the event database (SQLite), event details, artwork folder
story/           readable story: every card, the Game Master's running order, the finale script, the solution
docs/            guides for hosts and editors
scripts/         tools that read or edit the database: roster, seating, reviews, readers
print-studio/    web app and command-line generator for every printed item
templates/       email template for sending character briefings
reports/         an example network review of the conversation graph
```

## How it fits together

The **database** ([data/valemeridian-event.sqlite](data/valemeridian-event.sqlite)) is the single source of truth for characters, clue cards, who each card sends its player to, seating, props and release order. Everything else is derived from it:

```
data/valemeridian-event.sqlite ──► scripts/export_story_reader.py ──► story/cards.md, conversation-map.md
            │
            └──────────────────► print-studio/scripts/export_snapshot.py ──► lib/event.json ──► Print Studio ──► PDFs
```

Edit the database, regenerate the derived files, print. [docs/editing-the-story.md](docs/editing-the-story.md) explains how to edit safely and which checks to run.

## Tests and checks

```bash
cd print-studio && npm test          # 15 tests; renders every printable, takes about two minutes
cd print-studio && npm run check:data  # is the Print Studio snapshot current with the database?
python3 scripts/review_current_social_graph.py   # scores the conversation network and the seating
```

## Author

Created by [@pnaybour](https://github.com/pnaybour). Issues and pull requests are welcome ([CONTRIBUTING.md](CONTRIBUTING.md)).

## Licence

The code (the Print Studio and everything in `scripts/`) is under the [MIT licence](LICENSE). The story, characters, clue text and artwork are under [Creative Commons Attribution-NonCommercial-ShareAlike 4.0](LICENSE-CONTENT.md): you are welcome to run it at your own party, adapt it and share your changes, but not to sell it.

Print Studio embeds Liberation Sans, licensed under the SIL Open Font Licence (see `print-studio/source/LICENSE_LIBERATION`).
