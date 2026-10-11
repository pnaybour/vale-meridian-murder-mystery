# Contributing

Thank you for wanting to improve Vale Meridian. Whether you have fixed a clue that did not add up, drawn the pictures, or run the party and have notes, issues and pull requests are welcome.

## Before you start

- Read [docs/the-game.md](docs/the-game.md) and [docs/design-principles.md](docs/design-principles.md). If you use Claude Code, `CLAUDE.md` already carries the rules. They are short, and a change that fights them will not fit.
- **Do not add real people's information.** No guests' names, emails, photographs or dietary notes; no venue or event details that identify a private party. The sample roster is "Guest 01" and so on, on purpose. If a change needs a roster, use those.
- Keep the **solution out of guest-facing printouts**. The cards guests receive must not name the murderer or the method.

## Changing the story

Follow [docs/editing-the-story.md](docs/editing-the-story.md): back up, edit the database, regenerate the derived files, run the checks. In your pull request:

1. Say which cards changed and why, by card id (`CLUE...`).
2. Include the regenerated files (`story/cards.md`, `story/conversation-map.md`, `print-studio/lib/event.json`) and the database.
3. Paste the summary line of `python3 scripts/review_current_social_graph.py` before and after.
4. Run `npm test` and `npm run check:data` in `print-studio/`.

A card is "done" when you have read it aloud, and read the card of the person it sends you to.

## Changing the code

- `npm test` in `print-studio/` must pass; it takes about two minutes.
- The PDF renderer is `print-studio/lib/pdf.mjs`. If you add a printable, add it to `scripts/export_snapshot.py` and make sure a test covers its layout.
- Scripts that write the database must preview first, write only with `--apply`, and back up before writing.
- Keep it working on Python 3.10 and use only the standard library, apart from Pillow for pictures.

## Style

British English in cards and documents. Short sentences. Describe what a thing does, not how clever it is.

## Licence

By contributing you agree that your contribution is licensed as the rest of the repository: code under the MIT licence (`LICENSE`), story, data and artwork under CC BY-NC-SA 4.0 (`LICENSE-CONTENT.md`).
