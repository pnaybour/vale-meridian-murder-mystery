"""Export the accepted database seats to Markdown without changing any records."""
from pathlib import Path
from datetime import datetime
import argparse
import hashlib
import sqlite3


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', help='Defaults to the single approved plan')
    args = parser.parse_args()
    database = root / 'data/valemeridian-event.sqlite'
    before = hashlib.sha256(database.read_bytes()).hexdigest()
    connection = sqlite3.connect(database.as_uri() + '?mode=ro', uri=True)
    connection.row_factory = sqlite3.Row
    try:
        if not args.plan:
            plans = connection.execute("SELECT plan_id FROM seating_plans WHERE status='approved'").fetchall()
            if len(plans) != 1:
                raise SystemExit('Expected one approved plan; supply --plan explicitly.')
            args.plan = plans[0]['plan_id']
        rows = connection.execute(
            'SELECT table_number, seat_number, guest_name, character_name '
            'FROM seat_assignments WHERE plan_id=? ORDER BY table_number, seat_number',
            (args.plan,),
        ).fetchall()
    finally:
        connection.close()
    if not rows:
        raise SystemExit(f'No seats found for {args.plan}; existing export was not changed.')
    tables = sorted({row['table_number'] for row in rows})
    lines = [
        '# Vale Meridian seating plan',
        f'Read from [the event database](../data/valemeridian-event.sqlite) on {datetime.now():%d %B %Y}. '
        f'Plan: `{args.plan}`. {len(rows)} seats across {len(tables)} tables. '
        'This is a reference export of the sample roster; replace the guests with your own (docs/casting-and-seating.md).',
        'No seats were changed or optimised when producing this document.',
    ]
    escape = lambda value: str(value or '').replace('|', '\\|').replace('\n', ' ')
    for table in tables:
        seats = [row for row in rows if row['table_number'] == table]
        lines.extend([f'## Table {table} — {len(seats)} seats', '| Seat | Guest | Character |\n|---:|---|---|'])
        lines.append('\n'.join(
            f"| {row['seat_number']} | {escape(row['guest_name'])} | {escape(row['character_name'])} |"
            for row in seats
        ))
    after = hashlib.sha256(database.read_bytes()).hexdigest()
    if before != after:
        raise SystemExit('The local working database changed during export; retry from the latest copy.')
    output = root / 'story/seating-plan.md'
    output.write_text('\n\n'.join(lines) + '\n')
    print(f'Exported {len(rows)} seats from {args.plan} to {output}. Database unchanged.')


if __name__ == '__main__':
    main()
