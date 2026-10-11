# Data

| File | What it is |
|---|---|
| [valemeridian-event.sqlite](valemeridian-event.sqlite) | The event database: the single source of truth for characters, cards, the clue network, seating, props and review history. See [../docs/data-model.md](../docs/data-model.md) |
| [event.json](event.json) | Your party's details: `hosts`, `date` and `venue` print in card footers, the seating plan and signs; `name` and `subtitle` are the brand; `fictionalDate` is the date inside the story |
| [artwork/](artwork/README.md) | Your pictures; the Print Studio turns them into the evidence prints |
| `backups/` | Created by the scripts that write to the database; ignored by git |

The database ships with an anonymous **sample roster** ("Guest 01" to "Guest 54"). Putting your own guests in is covered in [../docs/casting-and-seating.md](../docs/casting-and-seating.md); after that the database holds their names, so keep your copy private.

`review-comments.json` and `review-status.json` appear here when you use the studio's review features (comments on a handout, "reviewed" and "approved" marks). They are ignored by git.
