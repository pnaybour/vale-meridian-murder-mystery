# Host guide

A plan for running Vale Meridian, from the first email to the last bow. The Game Master's own running order, with every release and cue, is [../story/gm-run-sheet.md](../story/gm-run-sheet.md); this guide is the wider preparation around it. The timings are suggestions; the kit itself fixes no schedule beyond the order of the rounds.

Read [the-game.md](the-game.md) first. **This guide and everything it links to give away the solution.**

A lot of the preparation below (casting, rewording cards, cue sheets, briefing emails, the shopping list) goes faster with [Claude Code](using-claude-code.md), which this repository is set up for.

## Is it right for your party?

- **Size.** The cards, the tables and the clue network are built for 54 seats at eight tables: 52 players, a Game Master and one child. The network has some redundancy, but the story is written for the full cast. If you have fewer guests, read [different numbers and groups of people](casting-and-seating.md#different-numbers-and-groups-of-people) before committing.
- **Setting.** A reception followed by a seated meal at round tables. Guests move around freely in Round 0 and are mostly at their tables for Rounds 1–3. Cards never mention tables, so you can reseat people.
- **Time.** Round 0 is the reception; Rounds 1–3 are paced by you; Round 4 follows when the tables have talked. Allow time for the finale, which has four music cues, a standing elimination, a speech, an arrest and the credits.
- **Nerves.** Nobody has to act. About nine people have short parts. The only speech is the murderer's, and the Game Master offers to read it for them. Nobody is restrained or searched, and nobody is asked to enact the poisoning.
- **Preparation.** Plan a few evenings: casting, printing, collecting props and a short rehearsal. The printed items run to several hundred pieces ([printing.md](printing.md)).

## Roles to settle first

| Role | Why it needs choosing early |
|---|---|
| **Game Master** | You, usually. Facilitates, never testifies. Needs the running order and the closing sheet |
| **Vincent Vale / Peter Vale** | One performer: the toast, the collapse, then a quick change into the twin brother, entering at fictional 19:55 with no real wait |
| **DJ Spinny T** | Runs the music: one cue at the toast, four in the finale. Wants a reliable playlist and a clear spoken-cue habit |
| **Inspector Donna Reed** | Hands a laboratory report to every table in Round 3 and makes the arrest |
| **The murderer** | Does not know the finale will name them until it does. Reads (or has read) a short speech cold |
| **Leo Lights, Wanda Wires** | Change the stage lights on Spinny's cue. Need a look at the venue's lighting beforehand |
| **Scooter, Dakota Steele** | Carry and recover the sealed silver compact |
| **Vance Vellum** | Takes Polaroids all evening and hands out nine photograph packs in Round 2 |

Brief these people **privately and in person** before you send general briefings. Their extra instructions arrive on private cards in the right envelopes at the right moment; the general briefings do not mention them.

## Suggested timeline

### Weeks before

1. **Fix the event details** in [../data/event.json](../data/event.json) (hosts, date, venue). See [printing.md](printing.md).
2. **Cast the characters** and **seat the guests** with [casting-and-seating.md](casting-and-seating.md). Every character already has a table, arranged around the clue network. To keep couples and families together, choose which guest plays which character: put people who should sit together on characters at the same table.
3. **Plan the room.** The Print Studio draws a floor plan and a "Find your table" sheet from the layout in the database; record yours with `scripts/register_room_layout.py` (see [../scripts/README.md](../scripts/README.md)).
4. **Order or gather props** from [../story/physical-props.md](../story/physical-props.md) (39 items, each marked required, recommended, optional or story-only). Source early the decanter with a removable stopper, a silver compact marked VV, two matching deep-red envelopes and a Polaroid-style camera.
5. **Make the pictures** ([evidence-photos.md](evidence-photos.md)). Allow time: there are eleven, and the decanter frame must match whoever plays the murderer.
6. **Send the briefings.** Each character has a briefing, dress guidance and a secret in [../story/cards.md](../story/cards.md); `python3 scripts/render_briefings.py` fills the email template in [../templates/](../templates/character-briefing-email.html) for every guest and writes the files to `briefings/`; nothing is sent for you. The renderer warns if a briefing mentions the murder; see [known-issues.md](known-issues.md).
7. **Plan the music**: one track for the toast and four for the finale are named in the Round 0 and Round 4 sheets. The kit gives you the cues, not the recordings.

### The week of

1. **Refresh and check** the Print Studio: `npm run snapshot`, then `npm run check:data`.
2. **Print everything** and **sort it into envelopes** by round and by table ([printing.md](printing.md)). The "Clue envelope inclusions" list says exactly what goes inside which envelope.
3. **Rehearse** with the performers: the toast, the staged collapse, Peter's re-entry, the lighting cue, the finale. At least once, read the finale aloud with the Game Master's, Spinny's and Donna's copies in hand.
4. **Check the practical handling**: card sorting, how the compact is passed, and how the Game Master retrieves it from the drinks table after the collapse.

### On the night

Follow [../story/gm-run-sheet.md](../story/gm-run-sheet.md). In outline:

| Moment | You do |
|---|---|
| **Before guests arrive** | Sort cards and exhibits by release. Put the Round 1 envelopes at the place settings and each table's Round 2 and 3 envelopes on its table. Set out the decanter and the private drinks table |
| **Round 0, arrival** | Give out the 51 arrival envelopes. Tell guests only: "Your card names a small group; go and find them." Give Scooter the sealed compact (Spinny's own envelope already holds a deep-red envelope). Give the Vincent performer their private card |
| **Round 0, toast** | Give Spinny the toast card just before the cue. Spinny raises the music for twenty seconds; the stage lights drop; the murderer sets the compact by the decanter; Vincent toasts, drinks and collapses. House lights stay on |
| **Round 1** | Announce Round 1 and release the cards. Peter re-enters; give him the taxi note. Dakota is handed the recovered, unsealed compact |
| **Round 2** | Release the cards together. Hand Vance his nine photograph packs |
| **Round 3** | Release the cards. Donna puts a laboratory report on every table |
| **Round 4** | When the tables have talked, hand the finale sheet to Spinny and Donna and open yours. Follow it line by line |
| **After the credits** | Hand the room back to the party |

### Your welcome speech

Keep it short. Say that guests play their characters, use the facts on the cards they are given, and talk to the people their card names or to anyone else who interests them. Personal notes are optional. The times and sightlines in the story describe the fiction; nobody has to reproduce them in the room.

## Rules of thumb for the Game Master

- **Facilitate; never testify.** You help people find each other. You do not tell the room what a witness saw or summarise the case before the conclusion.
- **Release rounds together.** Do not hand cards out piecemeal.
- **Evidence only through the envelopes and the named handouts.** You may hand over physical exhibits (the report, the photographs, the taxi note). Their meaning is the guests' to work out.
- **Nothing new after the accusations.** No decisive evidence appears once the tables have written their conclusions.
- **Keep the finale withheld until its cues.** The speech, the arrest and the credits wait for their moments.
- **Offer to read.** Anyone with a performing part can hand it to you.
- **Use plain paper.** A guest who wants to jot a note may. Twelve blank private notes are printed for the purpose.
- **Rehearse the three set pieces**: the toast, the arrest and the credits.

## If something goes wrong on the night

The advice here is judgement, not part of the kit's tested design.

- **A guest cancels.** Take the nearest equivalent player to cover the part, or play it yourself for the performing parts. Losing a minor character is rarely fatal to the network; losing Vincent/Peter, Spinny, Donna or the murderer matters most, so choose cover for those first and brief them privately.
- **Someone arrives late.** Give them their envelopes for the rounds already released and let them join in. Their Round 0 card names a group to find; the group will fill them in.
- **People cannot find a named character.** Help them. A short introduction is enough.
- **The room is flagging.** Move to the closing round when conversations have had reasonable time. Do not wait for everyone to have heard everything.
- **The music or lights fail.** The finale is triggered by spoken words, not by the music, so carry on speaking.
