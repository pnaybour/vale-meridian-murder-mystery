# Evidence pictures and props

The game uses eleven pictures, one banknote and one laboratory report. The repository ships the laboratory report and **placeholders for everything else**, because the original photographs were made for one particular cast. Each placeholder carries its own brief, so you can see what to make. The full briefs are in [../story/photo-briefs.md](../story/photo-briefs.md).

## Getting your own pictures in

1. Make or find a picture for each entry in [../story/photo-briefs.md](../story/photo-briefs.md). The briefs are written as prompts for an AI image tool: the original pictures were generated with ChatGPT, and Claude (or any assistant) can adapt a brief to your cast and refine your prompts. Claude writes the brief; it does not draw the picture. Portrait, about 1130 × 1390 px suits the photographs; the passport is landscape, 1536 × 1024 px.
2. Save each in `data/artwork/` under the file name in its brief (for example `decanter-frame.png`).
3. Run `npm run photos` in `print-studio/` (needs Pillow, `pip install pillow`). It writes the screen copies and the data the PDF generator uses, and still makes placeholders for any you have not supplied.
4. Print from the studio, Evidence category. Photographs print four to an A4 sheet at 95 × 124 mm.

Run `python3 scripts/register_evidence_photos.py` to re-record the pictures' sizes and fingerprints after adding artwork. It previews by default and writes only with `--apply`. If a picture's dimensions differ from the brief, the registration updates them.

## The set

| Picture | Who holds it | Round | Prints |
|---|---|---:|---:|
| Decanter photograph (the key picture) | Vance Vellum | 2 | 9 |
| Eight other reception pictures (lobby signing, greeting, dance, group toast, champagne service, Lucien at the mirror, a quiet word, two guests) | Vance Vellum | 2 | 9 each |
| Vincent Vale at the microphone | Game Master | 4 | 1 |
| An old British passport | Nikki Neon | 2 | 1 |
| Prop banknote, "Vale Meridian Glamour Pounds" | In two deep-red envelopes | 0 and 2 | 24 |
| Laboratory report | Inspector Donna Reed | 3 | 8 |

## Rules for the set

These are what make the pictures work in the game, whoever draws them.

1. **The decanter frame is never handed over on its own.** It goes out in Round 2 inside Vance's pack of nine pictures, nine packs (one per table plus his own), so each table has to find it among eight ordinary pictures. The Print Studio's tests assert that every picture in the pack shares a round and a quantity, so the frame cannot be separated by accident.
2. **The decanter frame must match whoever plays the murderer.** It shows the murderer from behind with a hand on the stopper: no face, no powder in the wine, black and white. What can be recognised is their hair, their clothes and a wide cuff bracelet. That is enough for Nikki and Dakota to stand by their identifications in Round 3, and not enough to settle it alone. The shipped brief describes long blonde hair, a dark draped gown with a line of pearls along the shoulder, and a wide pearl cuff on the reaching wrist. Adapt the brief to whoever plays the murderer, and dress them to match.
3. **No other picture may show someone who could be mistaken for the figure in the decanter frame.** In particular, nobody seen from behind with the same hair and dark clothes. An early draft of two other frames did, and each read as that figure a minute earlier, so they were redrawn.
4. **The lobby signing hides the signer's face on purpose.** Its subject is also a suspect, so the picture corroborates without doing the witness's job. The time written on the border (7:28 pm) also shows that Vance dates his frames.
5. **Time-stamp the borders in Vance's hand.** The mirror portrait reads 7:05 pm, the lobby 7:28 pm; the decanter frame's caption gives 19:29:10, which Vance explains in Round 3.
6. **The toast portrait of Vale is for the finale only.** Keep it out of sight until the credits: it shows the private wine in his hand.
7. **The passport is invented.** Every number and office is made up, and it is watermarked for game use. Crease it once so it does not look freshly printed.

## Pictures of real people

The original photographs were generated. If you use photographs of your own guests, get their consent first, and remember that a picture of a real person in your repository is personal data.

## The prop banknote

The studio can print "Glamour Pounds" (24 notes at 130 mm wide, twelve per deep-red envelope). With no `data/artwork/valemeridian-prop-money.png` it draws a plain note using the Vale Meridian logo; supply your own picture, 1836 × 857 px, to replace it. If you add your own text to a note, check it carries your event, not mine.

## The laboratory report

`data/artwork/valemeridian-lab-report.png` is the report that Donna hands to every table in Round 3. It is invented: a typeset report from a fictional "Nailsworth & Stroud Forensic Science Laboratory", and nothing in it reflects a real laboratory. The studio prints it as a full A4 page; if the image is missing it draws a plain text version instead.
