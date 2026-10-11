# Developing your evening with Claude Code

**Essential for tailoring the evening.** Vale Meridian is a database of characters and clue cards, a few dozen scripts and a print studio. You can run it entirely by hand, but making it *your* party (your guests, your venue, your jokes, fewer seats, a different occasion) means editing that database carefully and re-running checks. That is exactly what [Claude Code](https://code.claude.com/docs/en/overview) is good at, and you do not need to be a programmer to use it: you describe what you want in plain English and it reads the files, makes the change, runs the checks and tells you what it did.

**Which tool?** The developer of this kit settled on **Claude Code**, built it with it, and wrote every guide and example prompt for it, so we recommend it. [OpenAI Codex](https://developers.openai.com/codex) or any similar AI coding agent that can read files and run commands will do the same job; where this guide says "Claude Code", read "your agent".

This repository is set up for either. [`CLAUDE.md`](../CLAUDE.md) in the root tells the agent how the kit fits together and the rules that keep 52 people able to play without a referee, so it starts every session already knowing them; [`AGENTS.md`](../AGENTS.md), the file Codex and many other agents look for, points to it.

## What it helps with

| You want to | Claude Code can |
|---|---|
| Understand the game before you commit | Read the story and brief you on it, in the order you choose, with or without the solution |
| Fit it to your party | Set the hosts, date and venue; reword the few "anniversary" references for a birthday, retirement or reunion; check nothing else assumes the original occasion |
| Cast your guests | Turn a list of guests (with who sits together and who would enjoy acting) into a roster file, preview it, and apply it |
| Cope with fewer (or awkward) guests | Propose which characters to retire, re-route the cards that pointed at them, and run the network review to show what you lost |
| Rewrite or add a card or character | Draft in the character's voice, keep it to one named person, update the clue network and question notes, and run the checks |
| Proofread the whole story | Read all 211 cards for continuity and tone and give you a list by card id, changing nothing until you approve |
| Prepare the Game Master and performers | Turn the scripts into one-page cue sheets for each performer, a printable timeline, and a rehearsal plan |
| Write the briefing emails | Fill the template for each guest, add a personal opening line, and check no briefing mentions the murder |
| Get the pictures made | Adapt the prompts in [../story/photo-briefs.md](../story/photo-briefs.md) to your cast's costumes, ready to paste into an image generator such as ChatGPT. (Claude Code writes the prompts; it cannot draw the pictures) |
| Print | Build the PDFs you ask for and tell you what to feed the printer. You still press Print |
| Rehearse the finale | Play the Game Master's lines back to you cue by cue, or read the speech aloud with you |

## Getting started

1. **Install Claude Code.** Follow Anthropic's [setup guide](https://code.claude.com/docs/en/overview). It runs in a terminal, in an IDE, in the desktop app and in the browser; any of them will do. (Using Codex or another agent? Install it from its own documentation instead.)
2. **Get this repository** onto your computer (`git clone`, or download and unzip it) and **open the folder** in Claude Code. In a terminal that is `cd vale-meridian-murder-mystery` and `claude` (or your agent's command).
3. **Install the print tools once**, or ask Claude Code to: *"Set up the Print Studio so I can run it."* (It needs Node.js 22.13 or later and Python with Pillow; it will tell you if something is missing.)
4. **Start with a question, not a change:** *"Read the README and docs/the-game.md, then explain what an evening looks like and what I need to decide first."*

## A good first few sessions

1. **Orientation.** The prompt above, then: *"What are the five biggest decisions I have to make before sending invitations?"*
2. **Your party.** *"My party is [occasion] at [venue] on [date], with about [number] guests. Set data/event.json, and list every place the cards or scripts assume a different occasion. Don't change the cards yet."*
3. **Cast.** Give it first names or initials and who sits together (see the privacy note below), then: *"Propose which guest plays which character, keeping couples and families at the same table, and put the performing roles with people who would enjoy them. Make the roster file and show me the preview before you apply anything."*
4. **Proofread.** *"Read story/cards.md in full, following docs/design-principles.md. List problems by card id. Do not edit anything."* Then approve the fixes you agree with.
5. **Props and rehearsal.** *"From story/physical-props.md and the running order, write me a shopping list, a week-by-week timeline to [date], and a rehearsal plan for the performers."*
6. **Print.** *"Build the Round 1 pack and the badges, and tell me how to print them."*

## Ready-made prompts

**Making a change**
- *"Reword card CLUE_R1_BEVERLY_01 so it's funnier but keeps the same facts and the same person to talk to. Show me before and after, then run the checks."*
- *"The person playing the murderer is [description]. Change the decanter photograph brief to match their hair, clothes and jewellery, and tell me what they should wear."*
- *"Retire the character [name] and re-route everyone who was sent to them. Show me the plan first (use plan mode) and the network review before and after."*
- *"Add a new character, [description], who is a red herring about [something]. Follow docs/editing-the-story.md, and don't change the solution."*

**Checking**
- *"Run the whole set of checks listed in CLAUDE.md and tell me in plain language whether anything is wrong."*
- *"Does any briefing or Round 0 card give away who dies or who did it?"*
- *"Compare the network review now with the one in reports/ and tell me what changed."*

**Understanding**
- *"Who would be stuck if [character] doesn't come? What would they miss?"*
- *"Draw me the timeline of the fictional evening, with who saw what and when."*

## Different numbers and groups of people

Your party will not be 54 people in the shipped groups. Describe the people you have and let Claude Code do the fitting; this is what it should do in each case, and what you should check. The details and the commands are in [casting-and-seating.md](casting-and-seating.md#different-numbers-and-groups-of-people); how the checks score a plan is in [network-analysis.md](network-analysis.md).

**Your own guests, in your own groups**

> *"I have 50 guests. These are the groups: [Ann, Bob, and their two children], [Chris and Dee], [Ed, Flo, Gus], [...]. Anyone not in a group is on their own. [Ann, Chris and Gus] would enjoy performing. Work out who plays whom and keep every group at one table. Show me the preview before you apply anything."*

Claude Code exports the roster with `scripts/roster.py`, gives each group characters at one table (every character already has a table, and table 7 holds four performers), puts the willing guests on the performing seats, and runs `roster.py import` in preview. The preview reports every group split across tables and how many of your names change. **You check:** the "Groups: N; N sit together at one table" line, who has been given the parts, and that it showed you the preview first.

**Fewer guests**

> *"I only have 42 players. Use scripts/retirement_cost.py to choose the characters to retire, never the performers, and never half of a couple or a pair of alibi witnesses. Use plan mode: show me the plan and the cards you will edit first."*

Claude Code runs `retirement_cost.py --count 10` and `--remove`, then proposes the characters and the exact cards to reword. Once you approve, it rewrites those cards so they no longer name or send anyone to the retired characters, retires their cards, question notes and answer contracts, frees their seats, re-spaces the chairs, regenerates everything and runs the review and the print tests (which count from the database, so they need no editing). **You check:** the plan before it starts, each reworded card (read it aloud), and the review's summary lines before and after: `Pair capture`, `mean solve index` and any "never approached" or unresolved targets. In a trial, retiring two characters moved pair capture from 59.7% to 59.4%.

**More guests than characters**

> *"I have 60 guests. Let couples share a character by writing both names in the guest column, and tell me which characters it works best for. If we still need more, propose two new minor characters in plan mode and don't write any cards yet."*

Pairs sharing a character is the cheap answer (the badge prints "Ann & Bob"). New characters are a real writing job: ask for the plan first, then the cards one at a time, each followed by the review.

**A different table layout**

> *"My room has six round tables of nine. Run the seating optimiser and tell me what pair capture we would get, and compare it with eight tables of seven. Don't change anything yet."*

Claude Code runs `scripts/optimise_seating.py --tables 6 --size 9` and explains the trade-off (more people per table keeps more conversations at the table). Applying a new layout is the least exercised path in the kit, so ask for a plan, a backup first, and the review before and after.

**Whichever you choose**

- *"Run the whole set of checks in CLAUDE.md and tell me in plain English whether anything is wrong."*
- *"Does every guest still have a card in every round, a badge, a place card and a table sign?"*
- *"List the performers, who has been given each part, and which table each is at."*

## Working safely

- **Use plan mode for anything big** (retheming, changing the cast, rewriting a round): ask for a plan, read it, then approve it.
- **Keep it under version control.** Run `git init` if you downloaded a zip, and commit after each change that worked, so you can always go back. The database is a single file, and scripts that change it back it up to `data/backups/` first.
- **Read what it writes.** Claude Code is thorough, but it can be wrong, and the checks only catch structure: answerability, names, counts, who is sent to whom. Whether a line is funny, a clue is fair or a speech is kind is for you, and for a rehearsal with friends.
- **Test the whole thing on people.** Run it through once with a handful of friends before the night, even in your kitchen.
- **Do not let a change loose on the solution** without reading it. Say so in your prompt ("don't change the solution") and check `story/solution-and-canon.md` afterwards.

## Your guests' privacy

Claude Code works by reading your files and sending what it needs to Anthropic's servers to answer, so whatever is in this folder, and whatever you paste, is in scope. The kit is built so you can do almost all the development without real names:

1. **Develop with the sample roster** ("Guest 01" and so on). Casting, proofreading, checks and rehearsal plans need no names.
2. **Cast with first names or initials** when you want help matching people to characters, and only the details that matter (who sits with whom, who would enjoy acting). Do not include emails, phone numbers, addresses, dietary or medical information, or anything a guest would not want repeated.
3. **Import the real names last**, with `scripts/roster.py`, once the story is finished, and print.
4. **Keep your copy private.** After the import the database and `print-studio/lib/event.json` hold your guests' names; do not push them to a public repository (see [casting-and-seating.md](casting-and-seating.md#privacy)).

If you would rather no AI saw your guest list at all, do steps 1 and 3 yourself and skip step 2: the roster is a spreadsheet you fill in by hand.

## What it cannot do

It cannot print for you, buy the decanter, make the photographs, brief your performers or run the room. It will not know your friends' sense of humour. And it should not decide the creative things that make the evening yours: it is built to ask before it does.

## Without Claude Code

Everything works without it. The guides in this folder cover each step by hand: [host-guide.md](host-guide.md), [casting-and-seating.md](casting-and-seating.md), [printing.md](printing.md) and [editing-the-story.md](editing-the-story.md). Any text editor and a SQLite client such as [DB Browser for SQLite](https://sqlitebrowser.org) will do for the editing.
