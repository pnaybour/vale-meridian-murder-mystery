# Artwork

The Print Studio looks here for the pictures it prints. Only the laboratory report ships with the repository; every other picture is a placeholder until you add yours.

| File | Used for | Size |
|---|---|---|
| `valemeridian-lab-report.png` | The laboratory report (shipped) | 1414 × 2000 px, A4 portrait |
| `valemeridian-prop-money.png` | Prop banknote, "Vale Meridian Glamour Pounds" | 1836 × 857 px |
| `decanter-frame.png`, `lobby-signing-1928.png`, `reception-greeting.png`, `reception-dance.png`, `reception-group-toast.png`, `champagne-service.png`, `lucien-luxe-mirror.png`, `reception-red-wine-pair.png`, `reception-two-women.png` | Vance's nine photographs | About 1130 × 1390 px, portrait |
| `vale-at-the-microphone.png` | The toast portrait, used in the credits | About 1130 × 1390 px |
| `passport-patricia-thatcher.png` | The passport | 1536 × 1024 px, landscape |

What each picture must show, and the rules that make the set work, are in [../../story/photo-briefs.md](../../story/photo-briefs.md) and [../../docs/evidence-photos.md](../../docs/evidence-photos.md). After adding or changing a file run `npm run photos` in `print-studio/`.

Use pictures you have the right to use. Photographs of real people are personal data: only use them with the person's consent.

## Logo brief

The Print Studio ships a plain typographic logo (`print-studio/public/valemeridian-logo.png`). To replace it with a proper one, give this brief to a designer or an AI image tool such as ChatGPT.

**Subject.** The logo of *Vale Meridian Television*, a fictional 1980s British television company, founded by the showman Vincent Vale. It appears at the top of clue cards, name badges, table signs and the prop banknote, and it is the title card of the evening.

**Look.** A confident, glamorous 1980s broadcaster ident. Think a bold, slightly condensed serif or a clean geometric sans wordmark, with a simple monogram of **V** and **M** (a shield, roundel, or interlocking letters). Optional nods to the period: a subtle meridian line or arc, a horizon, or a rising sun. Keep it flat and vector-like, as if it had been printed on 1980s letterhead and a studio gate sign.

**Wording.** "VALE MERIDIAN", with "TELEVISION" smaller beneath or beside it. No other text, no slogan.

**Colour.** One colour, burgundy `#732B40`, on a transparent background, with a cream `#F4ECDD` for any knocked-out detail. It must still read when printed in black and white (the Print Studio's ink-saver mode).

**Format.** PNG, **2000 × 731 px** (landscape, about 2.7 : 1), transparent background, generous margin around the artwork. Save it as `print-studio/public/valemeridian-logo.png`.

**Must work small.** Legible at about 40 mm wide on a card, and when cut from the corner of a banknote.

**Avoid.** Anything resembling a real broadcaster's mark (BBC, ITV, Channel 4, CBS, NBC and similar), real company names or logos, eyes, peacocks, globes and satellites that echo existing idents, photographic textures, gradients and drop shadows, and the word "Vision".

After replacing the file run `npm run photos` in `print-studio/` (the prop banknote uses the logo) and print a proof.
