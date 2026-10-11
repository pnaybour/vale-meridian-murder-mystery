"""Check that the print snapshot matches the current local event database.

This is read-only. Run it after editing data/valemeridian-event.sqlite and before
handouts are printed.
"""

import hashlib
import json
import sqlite3
import sys
from pathlib import Path


APP = Path(__file__).resolve().parents[1]
ROOT = APP.parent
DATABASE = ROOT / "data/valemeridian-event.sqlite"
SNAPSHOT = APP / "lib/event.json"


def stale(messages):
    print("STALE: the Print Studio is not using the latest database.")
    for message in messages:
        print(f"- {message}")
    print("\nRefresh it with the Reload from database button or: npm run snapshot")
    return 1


def main():
    if not DATABASE.exists():
        return stale([f"Database not found: {DATABASE}"])
    if not SNAPSHOT.exists():
        return stale([f"Print snapshot not found: {SNAPSHOT}"])

    snapshot = json.loads(SNAPSHOT.read_text())
    source = snapshot.get("source", {})
    current_hash = hashlib.sha256(DATABASE.read_bytes()).hexdigest()
    errors = []
    if source.get("databaseHash") != current_hash:
        errors.append("the database file has changed since the snapshot was created")

    connection = sqlite3.connect(f"file:{DATABASE}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        database_clues = {
            row["clue_id"]: dict(row)
            for row in connection.execute(
                """
                select clue_id, clue_title, clue_content, round
                from clues
                where status='active'
                """
            )
        }
        printed_clues = {
            item["id"]: item
            for item in snapshot.get("items", [])
            if item.get("source") == "Local database"
        }

        missing = sorted(set(database_clues) - set(printed_clues))
        extra = sorted(set(printed_clues) - set(database_clues))
        if missing:
            errors.append(f"active clues missing from print data: {', '.join(missing)}")
        if extra:
            errors.append(f"retired or unknown clues remain in print data: {', '.join(extra)}")

        for clue_id in sorted(set(database_clues) & set(printed_clues)):
            database_clue = database_clues[clue_id]
            printed = printed_clues[clue_id]
            expected_round = 0 if database_clue["round"] is None else database_clue["round"]
            changed = []
            if printed.get("title") != database_clue["clue_title"]:
                changed.append("title")
            if printed.get("content") != database_clue["clue_content"]:
                changed.append("wording")
            if printed.get("round") != expected_round:
                changed.append("round")
            if changed:
                errors.append(f"{clue_id} differs in {', '.join(changed)}")

        approved = list(
            connection.execute(
                "select plan_id from seating_plans where status='approved'"
            )
        )
        if len(approved) != 1:
            errors.append(f"expected one approved seating plan; found {len(approved)}")
        elif source.get("seatingPlan") != approved[0]["plan_id"]:
            errors.append("the approved seating plan has changed")
    finally:
        connection.close()

    if errors:
        return stale(errors)

    print("CURRENT: the Print Studio matches the latest local database.")
    print(f"- {len(database_clues)} active clues verified")
    print(f"- database fingerprint: {current_hash[:12]}")
    print(f"- snapshot created: {source.get('capturedAt', 'unknown')}")
    print(f"- approved seating plan: {source.get('seatingPlan', 'unknown')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
